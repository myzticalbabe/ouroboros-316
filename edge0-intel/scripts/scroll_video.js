#!/usr/bin/env node
/**
 * scroll_video.js — deterministic scrolling-video capture.
 *
 * Why frame-stepping instead of a real-time screen recorder: a screen recorder
 * samples whatever the compositor happened to paint, so a heavy page drops
 * frames and the result judders. Here every frame is chosen, not sampled —
 * `window.scrollTo(y)` from the schedule, `CAINClock.seek(t)` for the ambience,
 * two animation frames to let the compositor flush, one screenshot. Frame N is
 * byte-identical on every run, and the encode is exactly `fps` frames/second.
 *
 * The scroll distance comes from the page, and speed is fixed in px/second
 * (default 260), so duration adapts to the document instead of the scroll
 * racing a longer or shorter page. All five themes therefore read at one pace.
 *
 * Reveal animations must be scroll-driven (`animation-timeline: view()`) for
 * this to be exact: an IntersectionObserver reveal fires in a task that a
 * single-frame scroll jump never waits for. The generated pages do this.
 *
 * Usage:
 *   node scripts/scroll_video.js --html variants/oxford_compact__oxford.html \
 *        --out oxford_compact_oxford.mp4 --fps 30 --px-per-sec 260
 *   node scripts/scroll_video.js --html ... --stills 4      # comparison stills
 *
 * The 260 px/s default is the *stills* pace. The published videos are recorded
 * slower for readability: `--px-per-sec 140` (see variants/README.md). Without
 * that flag a re-record comes out ~1.9x shorter than the shipped artifact.
 *
 * Env: CAIN_CHROME overrides the Chrome path, CAIN_FFMPEG the encoder path.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawnSync } = require('child_process');
const puppeteer = require('puppeteer');

const DEFAULTS = {
  chrome: process.env.CAIN_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  ffmpeg: process.env.CAIN_FFMPEG || 'ffmpeg',
  width: 1920,
  height: 1080,
  fps: 30,
  pxPerSec: 260,
  quality: 92,
  crf: 26,
  codec: 'hevc',
  holdSeconds: 2.5,
};

function parseArgs(argv) {
  const args = { ...DEFAULTS, html: null, out: null, framesDir: null, stills: 0, keepFrames: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--html') args.html = next();
    else if (a === '--out') args.out = next();
    else if (a === '--frames-dir') args.framesDir = next();
    else if (a === '--fps') args.fps = parseInt(next(), 10);
    else if (a === '--px-per-sec') args.pxPerSec = parseFloat(next());
    else if (a === '--crf') args.crf = parseInt(next(), 10);
    else if (a === '--codec') args.codec = next();
    else if (a === '--stills') args.stills = parseInt(next(), 10);
    else if (a === '--keep-frames') args.keepFrames = true;
    else if (a === '--chrome') args.chrome = next();
    else throw new Error(`unknown argument: ${a}`);
  }
  if (!args.html) throw new Error('--html is required');
  if (!args.stills && !args.out) throw new Error('--out (or --stills) is required');
  return args;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function fileUrl(p) {
  return 'file:///' + path.resolve(p).replace(/\\/g, '/');
}

/** Frames the page is fully painted and the clock is parked at t=0. */
async function prepare(page, args) {
  await page.setViewport({ width: args.width, height: args.height, deviceScaleFactor: 1 });
  await page.goto(fileUrl(args.html), { waitUntil: 'load', timeout: 120000 });
  await page.waitForFunction('window.__SCENE_READY__ === true', { timeout: 30000 });
  await page.waitForFunction(() => document.fonts && document.fonts.status === 'loaded',
                             { timeout: 15000 }).catch(() => {});
  // Park the clock so nothing advances between frames on its own.
  await page.evaluate(() => { document.querySelectorAll('*').forEach(() => {}); });
  await page.evaluate(() => window.CAINClock.freeze());
  await page.evaluate(() => window.scrollTo(0, 0));
  await flush(page);
}

/** Two animation frames: the compositor has painted by the second callback. */
async function flush(page) {
  await page.evaluate(() => new Promise((r) =>
    requestAnimationFrame(() => requestAnimationFrame(() => r()))));
}

/**
 * Viewport-only screenshot.
 *
 * `captureBeyondViewport: false` is load-bearing on puppeteer 19, whose default
 * is the opposite: without it Chrome returns the WHOLE document (1920x5847),
 * which is not a scrolled view and whose odd height libx265 rejects.
 *
 * Measured at scrollY=3000 on the generated page:
 *   plain                      -> 1920x5847, 2512 KB  (whole document)
 *   captureBeyondViewport:false -> 1920x1080,  985 KB  (correct viewport)
 *   clip only                  -> 1920x1080,  385 KB  (wrong region)
 *   clip + captureBeyond false -> 1920x1080,    8 KB  (blank)
 * The clip must NOT be added: the two together capture an empty region, which
 * encodes to a near-static video that still plays at the right length, so the
 * failure is silent. Do not "tidy" this into a clip.
 */
function shoot(page, args, file, type = 'jpeg', quality) {
  const opts = { path: file, type, captureBeyondViewport: false };
  if (quality !== undefined) opts.quality = quality;
  return page.screenshot(opts);
}

async function seekAndScroll(page, y, t) {
  await page.evaluate(({ y, t }) => {
    window.scrollTo(0, y);
    window.CAINClock.seek(t);
  }, { y, t });
  await flush(page);
}

async function measure(page, args) {
  const info = await page.evaluate(() => ({
    scrollHeight: Math.max(document.body.scrollHeight, document.documentElement.scrollHeight),
    jpeg: true,
  }));
  const distance = Math.max(0, info.scrollHeight - args.height);
  const pxPerFrame = args.pxPerSec / args.fps;
  const frames = Math.max(1, Math.ceil(distance / pxPerFrame));
  return { distance, frames, pxPerFrame };
}

/** Four stills at fixed scroll fractions — the comparison artifact. */
async function captureStills(page, args, plan) {
  const dir = path.join(path.dirname(args.html), 'stills', path.basename(args.html, '.html'));
  fs.mkdirSync(dir, { recursive: true });
  const fractions = [0.02, 0.30, 0.58, 0.88];
  for (let i = 0; i < fractions.length; i++) {
    const y = Math.round(plan.distance * fractions[i]);
    await seekAndScroll(page, y, (y / Math.max(1, plan.distance)) * 12);
    const file = path.join(dir, `${i + 1}.png`);
    await shoot(page, args, file, 'png');
    console.log(`  still ${i + 1}/${fractions.length} -> ${file}`);
  }
  return dir;
}

/**
 * Did the capture actually capture anything?
 *
 * A blank or wedged page still produces `frames` correctly-named files and a
 * video of exactly the right length — it encodes to ~0.3 MB instead of several,
 * which is the only clue. So sample frames across the run and refuse to encode
 * if they are all byte-identical: scroll/navigation failures must be loud.
 */
function verifyFrames(framesDir, count) {
  const picks = [...new Set([1, Math.round(count * 0.25), Math.round(count * 0.5),
                             Math.round(count * 0.75), count])].filter((i) => i >= 1);
  const hashes = picks.map((i) => {
    const f = path.join(framesDir, `frame_${String(i).padStart(6, '0')}.jpg`);
    if (!fs.existsSync(f)) return 'missing';
    return crypto.createHash('md5').update(fs.readFileSync(f)).digest('hex');
  });
  return { sampled: hashes.length, distinct: new Set(hashes).size, picks };
}

function encode(args, framesDir) {
  const out = path.resolve(args.out);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  // JPEG inputs decode as yuvj420p (full-range); both encoders need yuv420p
  // stated explicitly or libx265 aborts with -22 (invalid argument).
  const codecArgs = args.codec === 'hevc'
    ? ['-c:v', 'libx265', '-crf', String(args.crf), '-preset', 'medium',
       '-pix_fmt', 'yuv420p', '-tag:v', 'hvc1']
    : ['-c:v', 'libx264', '-crf', String(args.crf), '-preset', 'medium', '-pix_fmt', 'yuv420p'];
  // Color tags must be set on the FRAMES (setparams), not via the -color_*
  // output options: those set AVCodecContext fields that the decoded frames'
  // own properties override, so the encode silently ships unknown/unknown
  // primaries+transfer (probe: -color_primaries bt709 -> ffprobe 'unknown').
  //
  // The values come from a measured probe of Chrome's JPEG encoder (solid
  // known colors -> raw YUV vs matrix predictions): full-range BT.601 with
  // ZERO error, BT.709 off by 119 total abs levels (red Y 76 vs 54). So the
  // matrix stays bt470bg (BT.601 — retagging it bt709 WOULD shift color),
  // while primaries/transfer are bt709 (sRGB chromaticities; bt709 transfer
  // is within noise of the sRGB curve) and range stays pc (full).
  const vf = 'setparams=range=pc:color_primaries=bt709:color_trc=bt709:colorspace=bt470bg';
  const cmd = [
    '-y', '-framerate', String(args.fps),
    '-i', path.join(framesDir, 'frame_%06d.jpg'),
    '-vf', vf,
    ...codecArgs, '-r', String(args.fps), '-an',
    '-movflags', '+faststart', out,
  ];
  console.log(`  ffmpeg ${args.codec}: ${path.basename(out)}`);
  const res = spawnSync(args.ffmpeg, cmd, { stdio: ['ignore', 'ignore', 'pipe'] });
  if (res.status !== 0) {
    throw new Error(`ffmpeg failed (${res.status}): ${(res.stderr || '').toString().slice(-400)}`);
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv);
  let browser;
  try {
    if (!fs.existsSync(args.chrome)) throw new Error(`chrome not found: ${args.chrome}`);
    browser = await puppeteer.launch({
      headless: 'new',
      executablePath: args.chrome,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage',
             '--disable-extensions', '--disable-background-networking', '--disable-sync',
             '--no-first-run', '--mute-audio', '--force-color-profile=srgb',
             '--hide-scrollbars', '--font-render-hinting=none'],
    });
    const page = await browser.newPage();
    page.on('console', (m) => {
      const t = m.text();
      if (!t.startsWith('Scroll')) console.log(`  [browser] ${t}`);
    });
    page.on('pageerror', (e) => console.log(`  [browser:error] ${e.message}`));

    console.log(`Loading: ${args.html}`);
    await prepare(page, args);

    const plan = await measure(page, args);
    const durationSec = plan.frames / args.fps;
    console.log(`Page scroll: ${plan.distance}px · ${plan.frames} frames · `
                + `${durationSec.toFixed(1)}s @ ${args.fps}fps (${args.pxPerSec}px/s)`);

    if (args.stills) {
      const dir = await captureStills(page, args, plan);
      console.log(`Stills written: ${dir}`);
      return;
    }

    const framesDir = args.framesDir
      ? path.resolve(args.framesDir)
      : path.join(path.dirname(path.resolve(args.out)), 'frames_' + path.basename(args.out, '.mp4'));
    fs.mkdirSync(framesDir, { recursive: true });

    for (let i = 0; i < plan.frames; i++) {
      const t = i / args.fps;
      const y = Math.round((i / plan.frames) * plan.distance);
      await seekAndScroll(page, y, t);
      const file = path.join(framesDir, `frame_${String(i + 1).padStart(6, '0')}.jpg`);
      await shoot(page, args, file, 'jpeg', args.quality);
      if (i === 0 || (i + 1) % 50 === 0 || i === plan.frames - 1) {
        console.log(`  frame ${i + 1}/${plan.frames} (${Math.round((i + 1) / plan.frames * 100)}%) t=${t.toFixed(2)}s y=${y}px`);
      }
    }

    // Hold the final frame so the last line of the document is readable.
    if (args.holdSeconds > 0) {
      const holdFrames = Math.round(args.holdSeconds * args.fps);
      const last = plan.frames;
      for (let h = 0; h < holdFrames; h++) {
        const n = last + h + 1;
        await seekAndScroll(page, plan.distance, (last + h) / args.fps);
        await shoot(page, args,
                    path.join(framesDir, `frame_${String(n).padStart(6, '0')}.jpg`),
                    'jpeg', args.quality);
      }
      console.log(`  held final frame for ${args.holdSeconds}s (+${holdFrames} frames)`);
    }

    const check = verifyFrames(framesDir, plan.frames + Math.round(args.holdSeconds * args.fps));
    console.log(`  frame diversity: ${check.distinct}/${check.sampled} sampled frames distinct`);
    if (check.distinct <= 1) {
      throw new Error(`capture is blank/static (frames ${check.picks.join(',')} are byte-identical) — `
        + 'refusing to encode. Check that the page scrolls and that scroll-driven '
        + 'reveals are visible at a scrolled position (see scripts/validate_page.js).');
    }

    const out = encode(args, framesDir);
    const size = fs.statSync(out).size;
    console.log(`Video: ${out} (${(size / 1024 / 1024).toFixed(1)} MB)`);
    if (!args.keepFrames) {
      fs.rmSync(framesDir, { recursive: true, force: true });
      console.log('  frames cleaned up (pass --keep-frames to keep)');
    }
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
}

main().catch((err) => {
  console.error(`FAILED: ${err.message}`);
  process.exit(1);
});

#!/usr/bin/env node
/**
 * validate_page.js — structural checks on a generated Compact page.
 *
 * These are the checks that a screenshot cannot make for you: a page can look
 * plausible in one frame while overflowing horizontally, dropping an element,
 * or running an `animation-name` that has no `@keyframes` (which renders as a
 * frozen element and looks almost intentional).
 *
 * Checks:
 *   1. no horizontal overflow (document scrollWidth within the viewport)
 *   2. the document's structure is present (3 powers, 5 articles, 3 flow charts)
 *   3. every computed `animation-name` resolves to an emitted @keyframes rule
 *   4. the scene clock is loaded and seeking is observable
 *
 * Usage: node scripts/validate_page.js --html variants/oxford_compact__oxford.html
 */

const path = require('path');
const puppeteer = require('puppeteer');

const CHROME = process.env.CAIN_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';

function arg(name, fallback) {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

(async () => {
  const html = arg('html');
  if (!html) { console.error('--html is required'); process.exit(2); }
  const width = parseInt(arg('width', '1920'), 10);

  const browser = await puppeteer.launch({
    headless: 'new', executablePath: CHROME,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars'],
  });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width, height: 1080 });
    await page.goto('file:///' + path.resolve(html).replace(/\\/g, '/'), { waitUntil: 'load' });
    await page.waitForFunction('window.__SCENE_READY__ === true');

    const report = await page.evaluate((viewportWidth) => {
      const doc = document.documentElement;

      // 3. animation names used vs keyframes emitted
      const emitted = new Set();
      const walk = (rules) => {
        for (const r of rules || []) {
          if (r.type === CSSRule.KEYFRAMES_RULE) emitted.add(r.name);
          else if (r.cssRules) walk(r.cssRules);
        }
      };
      for (const sheet of document.styleSheets) {
        try { walk(sheet.cssRules); } catch (e) {}
      }
      const used = new Set();
      const unknown = [];
      for (const el of document.querySelectorAll('*')) {
        const name = getComputedStyle(el).animationName;
        if (!name || name === 'none') continue;
        for (const n of name.split(',').map((s) => s.trim())) {
          if (!n) continue;
          used.add(n);
          if (!emitted.has(n) && !unknown.includes(n)) unknown.push(n);
        }
      }

      // 4. clock observability
      let clock = null;
      try {
        window.CAINClock.seek(3.5);
        clock = { version: window.CAINClock.version, t: window.__CAIN_TIME__ };
        window.CAINClock.freeze();
      } catch (e) { clock = { error: e.message }; }

      return {
        scrollWidth: doc.scrollWidth,
        clientWidth: doc.clientWidth,
        scrollHeight: Math.max(document.body.scrollHeight, doc.scrollHeight),
        overflowX: doc.scrollWidth - viewportWidth,
        powers: document.querySelectorAll('.power').length,
        articles: document.querySelectorAll('.article').length,
        flows: document.querySelectorAll('.flow svg').length,
        emoji: document.querySelectorAll('.em').length,
        usedAnimations: [...used].sort(),
        unknownAnimations: unknown,
        scrollDriven: (() => {
          try { return CSS.supports('animation-timeline', 'view()'); } catch (e) { return false; }
        })(),
        clock,
      };
    }, width);

    // 5. Scroll-driven reveals must actually be visible once scrolled into
    // view. This is the check that catches the expensive mistake: seeking a
    // scroll-timeline animation pins every .reveal at its `from` keyframe
    // (opacity 0), so a capture of the document after the hero comes out blank
    // while every other check still passes.
    await page.evaluate(() => window.scrollTo(0, Math.round(document.documentElement.scrollHeight * 0.45)));
    await page.evaluate(() => new Promise((r) =>
      requestAnimationFrame(() => requestAnimationFrame(() => r()))));
    const reveals = await page.evaluate(() => {
      const els = [...document.querySelectorAll('.reveal')];
      const inView = els.filter((e) => {
        const r = e.getBoundingClientRect();
        return r.top < window.innerHeight * 0.85 && r.bottom > 0;
      });
      /*
       * Judge only reveals that are substantially ON SCREEN. A figure still
       * entering from the bottom edge is legitimately mid-reveal (its opacity
       * is climbing by design), so counting it failed healthy pages. The bug
       * this guard exists for — a seek-pinned scroll animation stuck at its
       * `from` keyframe — leaves *fully visible* reveals at 0, which this
       * still catches.
       */
      const judged = inView.filter((e) => {
        const r = e.getBoundingClientRect();
        return r.top < window.innerHeight * 0.5 && r.bottom > window.innerHeight * 0.1;
      });
      const pick = judged.length ? judged : inView;
      const op = pick.map((e) => parseFloat(getComputedStyle(e).opacity));
      return {
        inView: inView.length,
        judged: judged.length,
        minOpacity: op.length ? Math.min(...op) : null,
        sample: op.slice(0, 5),
      };
    });

    const problems = [];
    if (reveals.inView > 0 && reveals.minOpacity !== null && reveals.minOpacity < 0.5) {
      problems.push(`scroll-driven reveals blank mid-scroll (min opacity ${reveals.minOpacity})`);
    }
    if (report.overflowX > 1) problems.push(`horizontal overflow: +${report.overflowX}px`);
    if (report.powers !== 3) problems.push(`expected 3 power cards, found ${report.powers}`);
    if (report.articles !== 5) problems.push(`expected 5 covenant articles, found ${report.articles}`);
    if (report.flows !== 3) problems.push(`expected 3 flow charts, found ${report.flows}`);
    if (report.emoji < 8) problems.push(`expected emoji, found ${report.emoji}`);
    if (report.unknownAnimations.length) {
      problems.push(`animation-name without @keyframes: ${report.unknownAnimations.join(', ')}`);
    }
    if (!report.clock || report.clock.error || report.clock.t !== 3.5) {
      problems.push(`scene clock not seekable: ${JSON.stringify(report.clock)}`);
    }

    console.log(`${path.basename(html)}`);
    console.log(`  height ${report.scrollHeight}px · overflow-x ${report.overflowX}px · `
                + `scroll-driven ${report.scrollDriven}`);
    console.log(`  powers ${report.powers} · articles ${report.articles} · flows ${report.flows} · emoji ${report.emoji}`);
    console.log(`  animations used: ${report.usedAnimations.join(', ')}`);
    console.log(`  clock: ${JSON.stringify(report.clock)}`);
    console.log(`  reveals mid-scroll: ${reveals.judged}/${reveals.inView} substantially visible, `
                + `min opacity ${reveals.minOpacity ?? 'n/a'}`);
    if (problems.length) {
      console.log(`  FAIL (${problems.length}):`);
      for (const p of problems) console.log(`    - ${p}`);
      process.exitCode = 1;
    } else {
      console.log('  OK — no structural problems');
    }
  } finally {
    await browser.close().catch(() => {});
  }
})().catch((e) => { console.error('FAILED:', e.message); process.exit(1); });

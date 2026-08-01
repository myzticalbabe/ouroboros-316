const puppeteer = require('puppeteer');
const { PuppeteerScreenRecorder } = require('puppeteer-screen-recorder');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  
  const htmlPath = path.resolve(process.argv[2] || 'disclosure_render.html');
  const outputPath = path.resolve(process.argv[3] || 'DISCLOSURE_WHITEPAPER_FINAL.mp4');
  
  console.log('Loading: ' + htmlPath);
  await page.goto('file://' + htmlPath, { waitUntil: 'networkidle0', timeout: 60000 });
  await page.waitForFunction(() => document.title.includes('RENDER_READY'), { timeout: 30000 });
  console.log('Page loaded. RENDER_READY confirmed.');
  
  const height = await page.evaluate(() => document.body.scrollHeight);
  const viewports = (height / 1080).toFixed(1);
  console.log('Page height: ' + height + 'px (' + viewports + ' viewports)');
  
  const scrollSpeed = 175;
  const duration = Math.ceil(height / scrollSpeed);
  console.log('Scroll duration: ' + duration + 's at ' + scrollSpeed + 'px/s');
  
  const recorder = new PuppeteerScreenRecorder(page, {
    followNewTab: false,
    fps: 25,
    videoFrame: { width: 1920, height: 1080 },
    videoCrf: 18,
    videoCodec: 'libx264',
    videoPreset: 'medium',
    videoBitrate: 8000,
    aspectRatio: '16:9',
  });
  
  await recorder.start(outputPath);
  console.log('Recording started -> ' + outputPath);
  
  await page.evaluate((totalHeight, scrollDuration) => {
    return new Promise((resolve) => {
      const viewportH = window.innerHeight;
      const startTime = performance.now();
      const fps = 25;
      const interval = 1000 / fps;
      let lastTime = 0;
      function scroll(timestamp) {
        if (timestamp - lastTime < interval) {
          requestAnimationFrame(scroll);
          return;
        }
        lastTime = timestamp;
        const elapsed = (performance.now() - startTime) / 1000;
        const progress = Math.min(elapsed / scrollDuration, 1.0);
        window.scrollTo(0, progress * (totalHeight - viewportH));
        if (progress < 1.0) {
          requestAnimationFrame(scroll);
        } else {
          setTimeout(resolve, 2000);
        }
      }
      requestAnimationFrame(scroll);
    });
  }, height, duration);
  
  console.log('Scroll complete. Stopping recorder...');
  await recorder.stop();
  await browser.close();
  
  const stats = fs.statSync(outputPath);
  console.log('DONE: ' + outputPath + ' (' + (stats.size/1024/1024).toFixed(1) + ' MB)');
  
  // Verify moov atom
  const fd = fs.openSync(outputPath, 'r');
  const buf = Buffer.alloc(100);
  fs.readSync(fd, buf, 0, 100, stats.size - 100);
  fs.closeSync(fd);
  if (buf.includes(Buffer.from('moov'))) {
    console.log('MOOV FOUND - file is COMPLETE');
  } else {
    console.log('WARNING: moov not found in last 100 bytes');
  }
})().catch(err => { console.error('FATAL:', err.message); process.exit(1); });

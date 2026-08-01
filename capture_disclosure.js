const puppeteer = require('puppeteer');
const { PuppeteerScreenRecorder } = require('puppeteer-screen-recorder');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  
  // Load the HTML file
  const htmlPath = path.resolve('disclosure_render.html');
  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0', timeout: 30000 });
  
  // Wait for marked.js to finish rendering
  await page.waitForFunction(() => document.title.includes('RENDER_READY'), { timeout: 15000 });
  
  // Get total page height
  const height = await page.evaluate(() => document.body.scrollHeight);
  console.log(`Page height: ${height}px (${(height/1080).toFixed(1)} viewports)`);
  
  // Scroll speed: faster than before since we're using direct capture
  const scrollSpeed = 300; // pixels per second
  const duration = height / scrollSpeed;
  console.log(`Estimated duration: ${Math.ceil(duration)}s at ${scrollSpeed}px/s`);
  
  const outputPath = path.resolve('DISCLOSURE_WHITEPAPER.mp4');
  
  // Start recording
  const recorder = new PuppeteerScreenRecorder(page, {
    followNewTab: false,
    fps: 25,
    videoFrame: { width: 1920, height: 1080 },
    videoCrf: 23,
    videoCodec: 'libx264',
    videoPreset: 'medium',
    videoBitrate: 4000,
    aspectRatio: '16:9',
  });
  
  await recorder.start(outputPath);
  console.log('Recording started...');
  
  // Smooth scroll from top to bottom
  await page.evaluate((totalHeight, totalDuration) => {
    return new Promise((resolve) => {
      const viewportHeight = window.innerHeight;
      const startTime = performance.now();
      
      function scroll() {
        const elapsed = (performance.now() - startTime) / 1000;
        const progress = Math.min(elapsed / totalDuration, 1.0);
        const scrollTarget = progress * (totalHeight - viewportHeight);
        window.scrollTo(0, scrollTarget);
        
        if (progress < 1.0) {
          requestAnimationFrame(scroll);
        } else {
          // Hold at bottom for 3 seconds
          setTimeout(resolve, 3000);
        }
      }
      
      requestAnimationFrame(scroll);
    });
  }, height, duration);
  
  console.log('Scroll complete. Stopping recorder...');
  await recorder.stop();
  await browser.close();
  
  // Check output
  const fs = require('fs');
  const stats = fs.statSync(outputPath);
  console.log(`Done! Output: ${outputPath} (${(stats.size / 1024 / 1024).toFixed(1)} MB)`);
  
})().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});

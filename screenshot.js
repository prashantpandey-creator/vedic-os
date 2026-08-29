
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({headless: 'new'});
  const page = await browser.newPage();
  await page.goto(process.argv[2], {waitUntil: 'networkidle2'});
  await page.screenshot({path: 'screenshot.png'});
  await browser.close();
})();

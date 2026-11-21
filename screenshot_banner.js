const { chromium } = require("playwright");
const path = require("path");

const TIMES = {
  "t01_intro": 1.0,
  "t02_portrait": 4.0,
};

async function shootTheme(browser, theme) {
  const page = await browser.newPage({ viewport: { width: 1180, height: 610 } });
  const filePath = "file:///" + path.resolve(`${theme}.svg`).replace(/\\/g, "/");
  await page.goto(filePath);
  const svgHandle = await page.$("svg");
  for (const [label, t] of Object.entries(TIMES)) {
    await page.evaluate((time) => {
      const svg = document.querySelector("svg");
      svg.pauseAnimations();
      svg.setCurrentTime(time);
    }, t);
    await page.waitForTimeout(50);
    await svgHandle.screenshot({ path: `shot_${theme}_${label}.png` });
  }
  await page.close();
}

async function run() {
  const browser = await chromium.launch();
  await shootTheme(browser, "dark");
  await shootTheme(browser, "light");
  await browser.close();
  console.log("done");
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});

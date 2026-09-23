// Browser regression for the pinned Verso output. Run after bash site/build.sh.
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const http = require("node:http");
const path = require("node:path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "_out/html-multi");
const types = {
  ".css": "text/css",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".ttf": "font/ttf",
};

const server = http.createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, "http://local").pathname);
    let filename = path.resolve(root, `.${pathname}`);
    if (filename !== root && !filename.startsWith(root + path.sep)) {
      response.writeHead(403).end();
      return;
    }
    if ((await fs.stat(filename)).isDirectory()) filename = path.join(filename, "index.html");
    response.setHeader("Content-Type", types[path.extname(filename)] || "application/octet-stream");
    response.end(await fs.readFile(filename));
  } catch {
    response.writeHead(404).end();
  }
});

async function main() {
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROME_PATH || undefined,
  });
  try {
    const context = await browser.newContext();
    await context.route("**/*", (route) =>
      new URL(route.request().url()).origin === origin ? route.continue() : route.abort()
    );
    // The marker changes only this local browser page if HTML is parsed as markup.
    const marker = '<img src=x onerror="document.documentElement.dataset.sleanReviewXss=1">';
    for (const locale of ["", "en/"]) {
      for (const [route, parameter] of [["", "terms"], ["find/", "name"]]) {
        const page = await context.newPage();
        const errors = [];
        page.on("pageerror", (error) => errors.push(error.message));
        await page.goto(`${origin}/${locale}${route}?${parameter}=${encodeURIComponent(marker)}`);
        await page.waitForTimeout(200);
        const result = await page.evaluate(() => ({
          executed: document.documentElement.dataset.sleanReviewXss === "1",
          injected: document.querySelectorAll("img[onerror]").length,
          heading: document.querySelector("#title")?.textContent || "",
        }));
        assert.equal(result.executed, false, `${locale}${route}: URL text executed`);
        assert.equal(result.injected, 0, `${locale}${route}: URL text became an element`);
        assert.deepEqual(errors, [], `${locale}${route}: browser errors`);
        if (route) assert.ok(result.heading.includes(marker), "xref query should remain visible as text");
        await page.close();
      }

      const domainPage = await context.newPage();
      const domainErrors = [];
      domainPage.on("pageerror", (error) => domainErrors.push(error.message));
      await domainPage.goto(
        `${origin}/${locale}find/?name=missing&domain=${encodeURIComponent(marker)}`
      );
      await domainPage.waitForTimeout(200);
      assert.equal(
        await domainPage.evaluate(() => document.documentElement.dataset.sleanReviewXss),
        undefined,
        "xref domain must not execute"
      );
      assert.equal(await domainPage.locator("img[onerror]").count(), 0);
      assert.deepEqual(domainErrors, []);
      await domainPage.close();

      const page = await context.newPage();
      await page.goto(`${origin}/${locale}?terms=observation`);
      assert.ok(await page.locator(".text-search-results").count() > 0, "normal term highlighting");
      await page.goto(`${origin}/${locale}`);
      const input = page.locator("#cb1-input");
      await input.click();
      await input.pressSequentially("protocol");
      await page.locator(".search-result").first().waitFor();
      await input.press("Home");
      assert.equal(await page.evaluate(() => window.getSelection()?.anchorOffset), 0);
      await page.close();
    }
    for (const [slug, locale, target] of [
      ["lire-la-decision", "", "lire-la-decision"],
      ["Slean--Read-the-decision", "en/", "Read-the-decision"],
    ]) {
      const page = await context.newPage();
      await page.goto(`${origin}/${locale}find/?name=${encodeURIComponent(slug)}`);
      await page.waitForURL((url) => url.pathname === `/${locale}${target}/`);
      await page.close();
    }
    console.log("FR/EN URL text, search, highlights, keyboard and xref passed");
  } finally {
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

main().catch((error) => {
  console.error(error);
  server.close();
  process.exitCode = 1;
});

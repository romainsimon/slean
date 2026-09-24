// Browser regression for the Explorer's clean, changed, and unknown source states.
// Run after bash site/build.sh so the checked Slean CLI is available.
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const fs = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const statuses = [
  [true, ""],
  [false, " · source tree changed"],
  [null, " · source cleanliness unknown"],
];

async function main() {
  const temporary = await fs.mkdtemp(path.join(os.tmpdir(), "slean-explorer-identity-"));
  let browser;
  try {
    const artifact = path.join(temporary, "artifact");
    const rendered = spawnSync("python3", [
      "explorer/render.py", "examples/valid.json", "--output", artifact,
    ], { cwd: root, encoding: "utf8", env: process.env });
    assert.equal(rendered.status, 0, rendered.stderr || rendered.error?.message);

    const original = await fs.readFile(path.join(artifact, "index.html"), "utf8");
    const embedded = /(<script id="slean-data" type="application\/json">)([^<]*)(<\/script>)/;
    const match = original.match(embedded);
    assert.ok(match, "Explorer artifact must contain a checked timeline");
    const bundle = JSON.parse(match[2]);
    const revision = bundle.build.base_revision.slice(0, 8);

    browser = await chromium.launch({
      headless: true,
      executablePath: process.env.CHROME_PATH || undefined,
    });
    for (const [status, suffix] of statuses) {
      bundle.build.source_tree_clean = status;
      const encoded = JSON.stringify(bundle).replace(/[<>&]/g, (character) => ({
        "<": "\\u003c", ">": "\\u003e", "&": "\\u0026",
      })[character]);
      const variant = path.join(artifact, `identity-${String(status)}.html`);
      await fs.writeFile(variant, original.replace(embedded, (_match, open, _payload, close) => open + encoded + close));
      for (const width of status === null ? [1280, 390] : [1280]) {
        const page = await browser.newPage({ viewport: { width, height: 800 } });
        const errors = [];
        page.on("pageerror", (error) => errors.push(error.message));
        await page.goto(pathToFileURL(variant).href);
        assert.equal(await page.locator("#build-revision").textContent(), `Base ${revision}${suffix}`);
        assert.equal(await page.locator("#prefix-slider").inputValue(), "8");
        await page.locator("#previous").click();
        assert.equal(await page.locator("#prefix-slider").inputValue(), "7");
        if (width === 390) {
          await page.locator("#mobile-event-select").selectOption("3");
          assert.equal(await page.locator("#prefix-slider").inputValue(), "3");
        }
        const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
        assert.ok(scrollWidth <= width + 1, `${width}px viewport overflows to ${scrollWidth}px`);
        assert.deepEqual(errors, [], "Explorer browser errors");
        await page.close();
      }
    }
    console.log("Explorer source states and desktop/mobile interactions passed");
  } finally {
    if (browser) await browser.close();
    await fs.rm(temporary, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

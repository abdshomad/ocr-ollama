import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

const SCAN_MODES = [
  { label: "Fast", id: "tesseract" }, // Fallback path
  { label: "Standard", id: "trocr" }, // Default
  { label: "High Quality", id: "paligemma" },
  { label: "Granite Docling", id: "granite" }
];

const SAMPLE_IMAGE_PATH = path.resolve(__dirname, '../SAMPLES/IMAGES/1.jpeg');

test.describe('Browser Scan Verification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://127.0.0.1:3036/scan');
    // Wait for the scan container
    await expect(page.locator('h2:has-text("Browser scan")')).toBeVisible({ timeout: 10000 });
  });

  for (const mode of SCAN_MODES) {
    test(`Verify scan mode: ${mode.label}`, async ({ page }) => {
      console.log(`Testing scan mode: ${mode.label}`);
      
      // 1. Select the mode (tier)
      const select = page.locator('select');
      await expect(select).toBeEnabled({ timeout: 60000 });
      await select.selectOption(mode.id);

      // 2. Upload image
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(SAMPLE_IMAGE_PATH);
      
      // 3. Wait for workers to load (might take time for ONNX)
      // The page shows "Loading model…" text
      const progressText = page.locator('.progress-wrap');
      if (await progressText.isVisible()) {
        await expect(progressText).not.toBeVisible({ timeout: 300000 }); // 5 mins for PaliGemma
      }

      // 4. Run Scan
      const scanButton = page.getByRole('button', { name: /Run scan/i });
      await expect(scanButton).toBeEnabled({ timeout: 300000 });
      await scanButton.click();
      
      // 5. Verify results
      // Wait for scanning to finish (button becomes "Scanning..." then back)
      await expect(page.locator('button.primary')).toContainText('Scanning', { timeout: 15000 }).catch(() => {});
      await expect(scanButton).toBeEnabled({ timeout: 120000 });
      
      const ocrText = page.locator('.ocr-text');
      const scanFields = page.locator('.scan-fields');
      
      await expect(ocrText.or(scanFields).first()).toBeVisible({ timeout: 20000 });
      
      const text = await ocrText.first().textContent().catch(() => "") || await scanFields.first().textContent();
      expect(text?.trim().length).toBeGreaterThan(0);
      
      console.log(`Scan mode ${mode.label} PASSED.`);
      
      const screenshotPath = path.resolve(__dirname, `screenshots/scan_${mode.id}.png`);
      if (!fs.existsSync(path.dirname(screenshotPath))) {
        fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
      }
      await page.screenshot({ path: screenshotPath });
    });
  }
});

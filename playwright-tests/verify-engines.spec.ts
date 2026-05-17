import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

const TARGET_MODELS = [
  "deepseek-ai/DeepSeek-OCR",
  "deepseek-ai/DeepSeek-OCR-2",
  "tencent/HunyuanOCR",
  "rednote-hilab/dots.mocr",
  "docling-project/SmolDocling-256M-preview",
  "nvidia/nemotron-ocr-v2",
  "rapidocr",
  "onnxtr",
  "easyocr",
  "doctr",
  "paddleocr",
  "docling",
  "lanyocr",
  "litparse",
  "tesseract"
];

const SAMPLE_IMAGE_PATH = path.resolve(__dirname, '../SAMPLES/IMAGES/1.jpeg');

test.describe('OCR Engine Verification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://127.0.0.1:3036/');
    // Wait for models to load
    await expect(page.locator('.model-card')).not.toHaveCount(0, { timeout: 10000 });
  });

  for (const modelName of TARGET_MODELS) {
    test(`Verify engine: ${modelName}`, async ({ page }) => {
      console.log(`Testing model: ${modelName}`);
      
      // 1. Select the model
      // Use a locator that matches the exact model name in the .model-card-name span
      const modelCard = page.locator('.model-card').filter({ 
        has: page.locator('.model-card-name').filter({ hasText: new RegExp(`^${modelName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`) }) 
      });
      
      await expect(modelCard).toBeVisible({ timeout: 10000 });
      
      // Wait for model to be online (not offline and not probing)
      await expect(modelCard).not.toHaveClass(/model-card-offline/, { timeout: 30000 });
      await expect(modelCard).not.toHaveClass(/model-card-probing/, { timeout: 30000 });

      await modelCard.click();
      
      // 2. Upload sample image
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(SAMPLE_IMAGE_PATH);
      
      // 3. Run OCR
      const runButton = page.getByRole('button', { name: /Run OCR/i });
      await expect(runButton).toBeEnabled();
      await runButton.click();
      
      // 4. Wait for results
      // Wait for button to be enabled again (finish)
      await expect(runButton).toBeEnabled({ timeout: 180000 });
      
      // 5. Verify results
      const errorBanner = page.locator('.error-banner');
      if (await errorBanner.isVisible()) {
        const errText = await errorBanner.textContent();
        console.error(`Model ${modelName} FAILED with UI error: ${errText}`);
        throw new Error(`UI Error: ${errText}`);
      }

      const resultPanel = page.locator('section.card:has-text("Result")');
      await expect(resultPanel).toBeVisible({ timeout: 10000 });
      
      const ocrText = await resultPanel.locator('.ocr-text').textContent();
      if (!ocrText?.trim()) {
        console.error(`Model ${modelName} returned EMPTY result.`);
        throw new Error("Empty OCR result");
      }
      
      // Check for common error messages in the text
      const lowerText = ocrText.toLowerCase();
      if (lowerText.includes('error') || lowerText.includes('failed')) {
         console.warn(`Model ${modelName} result contains suspicious keywords: "${ocrText.substring(0, 50)}..."`);
      }
      
      console.log(`Model ${modelName} PASSED. Result length: ${ocrText.length}`);
      
      // 6. Capture screenshot for evidence
      const screenshotPath = path.resolve(__dirname, `screenshots/${modelName.replace(/\//g, '_')}.png`);
      if (!fs.existsSync(path.dirname(screenshotPath))) {
        fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });
      }
      await page.screenshot({ path: screenshotPath });
    });
  }
});

import { defineConfig } from '@playwright/test';
import { existsSync } from 'node:fs';

const localChrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
// An explicit path supports local installations; CI uses Playwright's pinned Chromium.
const executablePath = process.env.PLAYWRIGHT_EXECUTABLE_PATH ||
  (!process.env.CI && process.env.PLAYWRIGHT_BROWSER !== 'chromium' && existsSync(localChrome)
    ? localChrome : undefined);

export default defineConfig({
  testDir: './tests',
  timeout: 90000,
  globalTimeout: 15 * 60 * 1000,
  forbidOnly: !!process.env.CI,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:8777',
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    launchOptions: {
      executablePath,
      args: ['--no-sandbox', '--enable-unsafe-swiftshader'],
    },
  },
});

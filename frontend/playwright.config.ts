import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:4173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    // Use installed Chrome channel locally to avoid driver/binary download issues; default to chromium in CI
    channel: process.env.CI ? undefined : (process.env.PLAYWRIGHT_CHANNEL || 'chrome'),
    headless: true,
  },
  webServer: {
    command: 'npm run preview -- --port 4173 --host 127.0.0.1',
    port: 4173,
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
  },
  projects: [
    {
      name: 'Desktop Chrome',
      use: {
        ...devices['Desktop Chrome'],
        channel: process.env.CI ? undefined : (process.env.PLAYWRIGHT_CHANNEL || 'chrome'),
      },
    },
    {
      name: 'Mobile Chrome',
      use: {
        ...devices['Pixel 5'],
        channel: process.env.CI ? undefined : (process.env.PLAYWRIGHT_CHANNEL || 'chrome'),
      },
    },
  ],
});

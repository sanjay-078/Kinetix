import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'https://kinetix-app.onrender.com',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    channel: process.env.CI ? undefined : (process.env.PLAYWRIGHT_CHANNEL || 'chrome'),
    headless: true,
  },
  projects: [
    {
      name: 'Desktop Chrome (Production)',
      use: {
        ...devices['Desktop Chrome'],
        channel: process.env.CI ? undefined : (process.env.PLAYWRIGHT_CHANNEL || 'chrome'),
      },
    },
    {
      name: 'Mobile Chrome (Production)',
      use: {
        ...devices['Pixel 5'],
        channel: process.env.CI ? undefined : (process.env.PLAYWRIGHT_CHANNEL || 'chrome'),
      },
    },
  ],
});

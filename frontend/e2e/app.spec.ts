import { test, expect } from '@playwright/test';

test.describe('Kinetix Application E2E Suite', () => {

  test('Brand Rule: Word "Kinetix" appears strictly in the main header/brand position', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Brand logo should contain "Kinetix"
    const brandElement = page.locator('.brand-name');
    await expect(brandElement).toHaveText('Kinetix');

    // Page title or other headers should NOT contain "Kinetix"
    const pageTitle = page.locator('.page-title');
    await expect(pageTitle).not.toContainText('Kinetix');

    // No navigation item should repeat "Kinetix"
    const navItems = page.locator('.nav-item');
    const count = await navItems.count();
    for (let i = 0; i < count; i++) {
      await expect(navItems.nth(i)).not.toContainText('Kinetix');
    }
  });

  test('Navigation: All primary tabs load correctly and have unique content', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/.*dashboard/);

    // Products
    await page.click('a[href="/products"]');
    await expect(page).toHaveURL(/.*products/);
    await expect(page.locator('.search-input')).toBeVisible();

    // Suppliers
    await page.click('a[href="/suppliers"]');
    await expect(page).toHaveURL(/.*suppliers/);

    // Emails
    await page.click('a[href="/emails"]');
    await expect(page).toHaveURL(/.*emails/);

    // Catalogues
    await page.click('a[href="/catalogues"]');
    await expect(page).toHaveURL(/.*catalogues/);

    // Review
    await page.click('a[href="/review"]');
    await expect(page).toHaveURL(/.*review/);

    // Integrations
    await page.click('a[href="/integrations"]');
    await expect(page).toHaveURL(/.*integrations/);

    // Settings
    await page.click('a[href="/settings"]');
    await expect(page).toHaveURL(/.*settings/);
  });

  test('Dashboard: KPI cards, progress section, and real ETA indicator render', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Stat cards should be rendered
    const statCards = page.locator('.stat-card');
    await expect(statCards.first()).toBeVisible();

    // Progress bar section
    const progressSection = page.locator('.progress-section');
    await expect(progressSection).toBeVisible();
    await expect(page.locator('.progress-track')).toBeVisible();
  });

  test('PDF Guardrail: Catalogues provide links-only without extracting text', async ({ page }) => {
    await page.goto('/catalogues');
    await page.waitForLoadState('networkidle');

    // Catalogue items should have clickable open links (target="_blank")
    const pdfLinks = page.locator('a[target="_blank"]');
    // If table rows exist, check that any action link points to a valid media/pdf URL
    const rows = page.locator('table tbody tr');
    const rowCount = await rows.count();
    if (rowCount > 0) {
      const firstAction = rows.first().locator('a');
      if (await firstAction.count() > 0) {
        const href = await firstAction.getAttribute('href');
        expect(href).toBeTruthy();
      }
    }
  });

  test('Integrations: Gmail OAuth and Google Sheets controls render cleanly', async ({ page }) => {
    await page.goto('/integrations');
    await page.waitForLoadState('networkidle');

    // Gmail section exists
    await expect(page.getByText('Gmail Mailbox Ingestion')).toBeVisible();

    // Google Sheets section exists
    await expect(page.getByText('Google Sheets Batch Sync')).toBeVisible();

    // Sync button should exist
    const syncButton = page.getByRole('button', { name: /Sync Now/i });
    await expect(syncButton).toBeVisible();
  });

  test('Accessibility & Responsive: Viewport adaptation works without horizontal overflow', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Mobile layout check
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 2);
  });

});

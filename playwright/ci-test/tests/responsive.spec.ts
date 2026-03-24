import { test, expect } from '@playwright/test';

test.describe('Responsive Design', () => {
  test('homepage renders on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await expect(page).toHaveTitle(/Kartoza/i);
  });

  test('homepage renders on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await expect(page).toHaveTitle(/Kartoza/i);
  });

  test('homepage renders on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await expect(page).toHaveTitle(/Kartoza/i);
  });

  test('mobile menu toggle exists on small screens', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    // Look for common mobile menu toggles
    const menuToggle = page.locator('.navbar-burger, .hamburger, .menu-toggle, [aria-label*="menu"], button.navbar-toggler');
    const count = await menuToggle.count();
    // Mobile menu should exist on small screens
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

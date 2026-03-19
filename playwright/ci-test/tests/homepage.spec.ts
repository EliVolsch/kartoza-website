import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test('should load successfully', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Kartoza/i);
  });

  test('should display main navigation', async ({ page }) => {
    await page.goto('/');
    const nav = page.locator('nav, .navbar, .navigation, header');
    await expect(nav.first()).toBeVisible();
  });

  test('should display footer', async ({ page }) => {
    await page.goto('/');
    // Use the main site footer (footer-new class) to avoid matching other footer elements
    const footer = page.locator('footer.footer-new');
    await expect(footer).toBeVisible();
  });

  test('should have working links in navigation', async ({ page }) => {
    await page.goto('/');
    // Check that at least one navigation link exists
    const navLinks = page.locator('nav a, .navbar a, header a');
    const count = await navLinks.count();
    expect(count).toBeGreaterThan(0);
  });
});

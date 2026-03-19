import { test, expect } from '@playwright/test';

test.describe('Site Navigation', () => {
  test('about page loads', async ({ page }) => {
    await page.goto('/about/');
    await expect(page).toHaveURL(/about/);
  });

  test('portfolio page loads', async ({ page }) => {
    await page.goto('/portfolio/');
    await expect(page).toHaveURL(/portfolio/);
  });

  test('contact page loads', async ({ page }) => {
    await page.goto('/contact-us/');
    await expect(page).toHaveURL(/contact/);
  });

  test('team page loads', async ({ page }) => {
    await page.goto('/the_team/');
    await expect(page).toHaveURL(/team/);
  });

  test('services page loads', async ({ page }) => {
    await page.goto('/services/');
    await expect(page).toHaveURL(/services/);
  });
});

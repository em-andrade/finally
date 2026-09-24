import { test, expect } from '@playwright/test';

test.describe('Watchlist management (UI)', () => {
  test('add and remove a ticker', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('watchlist-row-AAPL')).toBeVisible();

    // Add PYPL.
    await page.getByLabel('Add ticker').fill('PYPL');
    await page.getByRole('button', { name: 'Add' }).click();
    await expect(page.getByTestId('watchlist-row-PYPL')).toBeVisible({ timeout: 10_000 });
    // Newly added ticker should start streaming a price shortly after being added to the
    // running market data source.
    await expect(page.getByTestId('price-PYPL')).not.toHaveText('—', { timeout: 10_000 });

    // Remove it again.
    await page.getByLabel('Remove PYPL from watchlist').click();
    await expect(page.getByTestId('watchlist-row-PYPL')).toBeHidden({ timeout: 10_000 });
  });
});

import { test, expect } from '@playwright/test';

test.describe('Sell trade', () => {
  test('cash increases and the position disappears once fully sold', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('watchlist-row-MSFT')).toBeVisible();

    // Buy first so there's something to sell.
    await page.getByLabel('Trade ticker').fill('MSFT');
    await page.getByLabel('Trade quantity').fill('3');
    await page.getByRole('button', { name: 'Buy' }).click();
    await expect(page.getByTestId('position-MSFT')).toBeVisible({ timeout: 10_000 });

    const cashAfterBuy = await page.getByTestId('cash-balance').textContent();

    // Sell the full position.
    await page.getByLabel('Trade ticker').fill('MSFT');
    await page.getByLabel('Trade quantity').fill('3');
    await page.getByRole('button', { name: 'Sell' }).click();

    // Position disappears once fully sold.
    await expect(page.getByTestId('position-MSFT')).toBeHidden({ timeout: 10_000 });

    // Cash increased back up from the post-buy balance.
    await expect
      .poll(
        async () => {
          const text = (await page.getByTestId('cash-balance').textContent()) ?? '';
          return Number(text.replace(/[$,]/g, ''));
        },
        { timeout: 10_000 },
      )
      .toBeGreaterThan(Number((cashAfterBuy ?? '$0').replace(/[$,]/g, '')));
  });
});

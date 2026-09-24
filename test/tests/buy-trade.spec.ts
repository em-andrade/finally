import { test, expect } from '@playwright/test';

test.describe('Buy trade', () => {
  test('cash decreases, position appears, total value updates', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('watchlist-row-AAPL')).toBeVisible();

    const cashBefore = await page.getByTestId('cash-balance').textContent();
    expect(cashBefore).toBe('$10,000.00');

    await page.getByLabel('Trade ticker').fill('AAPL');
    await page.getByLabel('Trade quantity').fill('5');
    await page.getByRole('button', { name: 'Buy' }).click();

    // Position appears in the table.
    await expect(page.getByTestId('position-AAPL')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('position-AAPL')).toContainText('5');

    // Cash balance decreased (polled every 5s per app/page.tsx — wait for the poll).
    await expect
      .poll(async () => page.getByTestId('cash-balance').textContent(), { timeout: 10_000 })
      .not.toBe('$10,000.00');

    // Total portfolio value stays approximately $10,000 (cash converted to equity 1:1, modulo
    // the ~500ms of price drift between quote-and-fill).
    const totalText = (await page.getByTestId('total-value').textContent()) ?? '';
    const total = Number(totalText.replace(/[$,]/g, ''));
    expect(total).toBeGreaterThan(9900);
    expect(total).toBeLessThan(10100);
  });
});

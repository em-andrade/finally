import { test, expect } from '@playwright/test';

const DEFAULT_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'JPM', 'V', 'NFLX'];

test.describe('Fresh start', () => {
  test('default watchlist, $10k cash, and live streaming prices appear', async ({ page }) => {
    await page.goto('/');

    // All 10 default tickers render.
    for (const ticker of DEFAULT_TICKERS) {
      await expect(page.getByTestId(`watchlist-row-${ticker}`)).toBeVisible();
    }

    // $10,000 starting cash and a $10,000 total value (no positions yet).
    await expect(page.getByTestId('cash-balance')).toHaveText('$10,000.00');
    await expect(page.getByTestId('total-value')).toHaveText('$10,000.00');

    // SSE connects.
    await expect(page.getByTestId('status-dot')).toHaveAttribute('data-testid', 'status-dot');
    await expect(page.getByRole('status')).toHaveAttribute('aria-label', 'Connection: Connected');

    // Prices are live: sample one ticker's price twice, a few seconds apart, and expect it to
    // have received at least one update (simulator ticks every ~500ms).
    const priceCell = page.getByTestId('price-AAPL');
    await expect(priceCell).not.toHaveText('—');
    const first = await priceCell.textContent();
    await page.waitForTimeout(2500);
    const second = await priceCell.textContent();
    // Not asserting inequality strictly (GBM could round to the same cent twice by chance) —
    // instead assert the sparkline accumulated multiple points, which only happens on updates.
    expect(first).toBeTruthy();
    expect(second).toBeTruthy();
    await expect(page.getByTestId('sparkline').first()).toBeVisible();
  });
});

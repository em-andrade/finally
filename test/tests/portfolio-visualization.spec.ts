import { test, expect } from '@playwright/test';

test.describe('Portfolio visualization', () => {
  test('heatmap and P&L chart render after a trade', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('watchlist-row-NVDA')).toBeVisible();

    await page.getByLabel('Trade ticker').fill('NVDA');
    await page.getByLabel('Trade quantity').fill('2');
    await page.getByRole('button', { name: 'Buy' }).click();
    await expect(page.getByTestId('position-NVDA')).toBeVisible({ timeout: 10_000 });

    // Heatmap: no longer showing the empty state, and a treemap cell for NVDA rendered as SVG.
    await expect(page.getByText('No open positions yet.')).toBeHidden();
    const heatmapPanel = page.getByText('Portfolio Heatmap').locator('..');
    await expect(heatmapPanel.locator('svg')).toBeVisible({ timeout: 10_000 });
    await expect(heatmapPanel.locator('text=NVDA')).toBeVisible({ timeout: 10_000 });

    // P&L chart needs >1 snapshot to render a line (snapshots are recorded on every trade, plus
    // a 30s background task) — a trade just recorded one; wait for a second one via the app's
    // 5s portfolio-history poll, or trigger a second trade to force a second snapshot quickly.
    await page.getByLabel('Trade ticker').fill('NVDA');
    await page.getByLabel('Trade quantity').fill('1');
    await page.getByRole('button', { name: 'Buy' }).click();
    await expect(page.getByTestId('position-NVDA')).toContainText('3', { timeout: 10_000 });

    await expect(page.getByText('Not enough history yet.')).toBeHidden({ timeout: 15_000 });
    const pnlPanel = page.getByText('Portfolio Value').locator('..');
    await expect(pnlPanel.locator('svg')).toBeVisible({ timeout: 10_000 });
  });
});

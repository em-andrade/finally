import { test, expect } from '@playwright/test';

// Exercises the deterministic LLM_MOCK=true rules (verbatim from the LLM Engineer, checked
// case-insensitively, first match wins):
//   1. "buy N TICKER" | "buy N shares of TICKER"       -> trade, "Buying N shares of TICKER."
//   2. "sell N TICKER" | "sell N shares of TICKER"     -> trade, "Selling N shares of TICKER."
//   3. "add TICKER" (optionally "to the watchlist")    -> watchlist add, "Adding TICKER to your watchlist."
//   4. "remove/delete TICKER" (optionally "from watchlist") -> watchlist remove
//   5. anything else                                    -> generic portfolio-summary message

test.describe('AI chat (LLM_MOCK)', () => {
  test('buy rule executes a trade and confirms inline', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Chat message').fill('buy 2 shares of GOOGL');
    await page.getByRole('button', { name: 'Send' }).click();

    await expect(page.getByTestId('chat-loading')).toBeVisible();
    const assistantMsgs = page.getByTestId('chat-message-assistant');
    await expect(assistantMsgs.last()).toContainText('Buying 2 shares of GOOGL.', { timeout: 10_000 });
    await expect(assistantMsgs.last()).toContainText('Bought 2 GOOGL');

    await expect(page.getByTestId('position-GOOGL')).toBeVisible({ timeout: 10_000 });
  });

  test('sell rule executes a trade', async ({ page }) => {
    await page.goto('/');
    // Ensure a position exists to sell first (manual buy via trade bar, not chat).
    await page.getByLabel('Trade ticker').fill('TSLA');
    await page.getByLabel('Trade quantity').fill('4');
    await page.getByRole('button', { name: 'Buy' }).click();
    await expect(page.getByTestId('position-TSLA')).toBeVisible({ timeout: 10_000 });

    await page.getByLabel('Chat message').fill('sell 4 shares of TSLA');
    await page.getByRole('button', { name: 'Send' }).click();

    const assistantMsgs = page.getByTestId('chat-message-assistant');
    await expect(assistantMsgs.last()).toContainText('Selling 4 shares of TSLA.', { timeout: 10_000 });
    await expect(page.getByTestId('position-TSLA')).toBeHidden({ timeout: 10_000 });
  });

  test('add rule updates the watchlist', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Chat message').fill('add PYPL to the watchlist');
    await page.getByRole('button', { name: 'Send' }).click();

    const assistantMsgs = page.getByTestId('chat-message-assistant');
    await expect(assistantMsgs.last()).toContainText('Adding PYPL to your watchlist.', { timeout: 10_000 });
    await expect(page.getByTestId('watchlist-row-PYPL')).toBeVisible({ timeout: 10_000 });
  });

  test('remove rule updates the watchlist', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('watchlist-row-JPM')).toBeVisible();

    await page.getByLabel('Chat message').fill('remove JPM from watchlist');
    await page.getByRole('button', { name: 'Send' }).click();

    const assistantMsgs = page.getByTestId('chat-message-assistant');
    await expect(assistantMsgs.last()).toContainText('Removing JPM from your watchlist.', { timeout: 10_000 });
    await expect(page.getByTestId('watchlist-row-JPM')).toBeHidden({ timeout: 10_000 });
  });

  test('generic message returns a portfolio summary with no actions', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Chat message').fill('how is my portfolio doing?');
    await page.getByRole('button', { name: 'Send' }).click();

    const assistantMsgs = page.getByTestId('chat-message-assistant');
    await expect(assistantMsgs.last()).toContainText('portfolio is currently worth', { timeout: 10_000 });
  });
});

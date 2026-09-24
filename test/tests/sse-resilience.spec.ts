import { test, expect } from '@playwright/test';
import http from 'node:http';

// Real network-drop emulation (`context.setOffline(true)`) doesn't reliably interrupt an
// already-open EventSource/SSE connection to localhost in this environment — the browser
// just keeps delivering bytes over the existing socket regardless of the "offline" flag, so
// the status dot never leaves "Connected" (confirmed: it timed out waiting for
// "Reconnecting…" in CI). `page.route(...).abort()` registered *after* the page has already
// connected has the same problem: it only affects requests made from that point on, and
// EventSource doesn't issue a new request until its current one errors — so there's nothing
// new for the route to intercept, and the live connection just keeps flowing regardless.
//
// So we take over the connection via route interception from the very first request instead:
// proxy the real backend stream for a short, bounded window, then end the forwarded response
// early. That's a genuine HTTP connection close as far as the browser is concerned, which
// EventSource reacts to exactly as it would a real network drop — it fires `error` and,
// per the backend's `retry: 1000` directive, automatically issues a new request, which we
// pass straight through to the real server so the reconnect succeeds for real.
//
// Note: because the truncated first response is delivered as one already-complete HTTP
// response (not a live stream we sever later), the browser processes "open" and "error" for
// that attempt back-to-back in the same tick, which React batches into a single render — so
// the intermediate "Reconnecting…" label is never reliably observable in the DOM (confirmed
// empirically: a MutationObserver on the status element's aria-label only ever recorded the
// initial default value and the final "Connected", never a distinct reconnecting frame). What
// *is* reliably observable, and what actually matters, is that a second real connection
// attempt happens automatically and succeeds — that's the reconnect behavior this test exists
// to verify.
function proxySseFor(url: string, ms: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const req = http.get(url, (res) => {
      const chunks: Buffer[] = [];
      res.on('data', (chunk) => chunks.push(chunk));
      const timer = setTimeout(() => {
        req.destroy();
        resolve(Buffer.concat(chunks).toString('utf-8'));
      }, ms);
      res.on('end', () => {
        clearTimeout(timer);
        resolve(Buffer.concat(chunks).toString('utf-8'));
      });
      res.on('error', (err) => {
        clearTimeout(timer);
        reject(err);
      });
    });
    req.on('error', reject);
  });
}

test.describe('SSE resilience', () => {
  test('status dot shows connected on load', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('status')).toHaveAttribute('aria-label', 'Connection: Connected', {
      timeout: 10_000,
    });
    await expect(page.getByTestId('status-dot')).toBeVisible();
  });

  test('recovers to connected after a simulated network drop', async ({ page, baseURL }) => {
    let attempts = 0;
    await page.route('**/api/stream/prices', async (route) => {
      attempts += 1;
      if (attempts === 1) {
        const streamUrl = new URL('/api/stream/prices', baseURL).toString();
        const truncatedBody = await proxySseFor(streamUrl, 1000);
        await route.fulfill({ status: 200, contentType: 'text/event-stream', body: truncatedBody });
      } else {
        await route.continue();
      }
    });

    await page.goto('/');

    // The truncated first connection forces an error; EventSource's built-in retry then
    // reconnects against the real, unintercepted stream and the status settles on "Connected".
    await expect(page.getByRole('status')).toHaveAttribute('aria-label', 'Connection: Connected', {
      timeout: 15_000,
    });

    // Confirm a reconnect genuinely happened — the client made a second real request to the
    // stream endpoint on its own, not just one lucky connection.
    expect(attempts).toBeGreaterThan(1);
  });
});

import { defineConfig, devices } from '@playwright/test';

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:8000';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false, // Trades/watchlist mutate shared server state (single-user, default seed).
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : [['list']],
  timeout: 30_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    // `fresh-start.spec.ts` asserts pristine state (default $10k cash, default watchlist) and
    // must run first, exactly once, before any other spec mutates shared server/DB state.
    // Playwright doesn't guarantee cross-file execution order within a single project (file
    // discovery order isn't a documented contract), so we split it into its own project and
    // make the main project formally `dependencies` on it — Playwright always runs a
    // dependency project to completion before any project that depends on it starts.
    {
      name: 'fresh-start',
      testMatch: /fresh-start\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'chromium',
      testIgnore: /fresh-start\.spec\.ts/,
      dependencies: ['fresh-start'],
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});

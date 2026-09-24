'use client';

import { useEffect, useRef, useState } from 'react';
import Sparkline from './Sparkline';
import { formatPercent, formatPrice } from '@/lib/format';
import type { PricePoint } from '@/lib/useSSE';
import type { PriceDirection } from '@/lib/types';

interface WatchlistRowProps {
  ticker: string;
  price: number | undefined;
  direction: PriceDirection;
  history: PricePoint[];
  selected: boolean;
  onSelect: (ticker: string) => void;
  onRemove: (ticker: string) => void;
}

function changePercent(history: PricePoint[]): number | null {
  if (history.length < 2) return null;
  const first = history[0].price;
  const last = history[history.length - 1].price;
  if (first === 0) return null;
  return ((last - first) / first) * 100;
}

function WatchlistRow({ ticker, price, direction, history, selected, onSelect, onRemove }: WatchlistRowProps) {
  const [flashClass, setFlashClass] = useState('');
  const mounted = useRef(false);

  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true;
      return;
    }
    if (direction === 'up') {
      setFlashClass('flash-up');
    } else if (direction === 'down') {
      setFlashClass('flash-down');
    } else {
      return;
    }
    const timeout = setTimeout(() => setFlashClass(''), 500);
    return () => clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [price]);

  const pct = changePercent(history);
  const pctColor = pct === null ? 'text-slate-500' : pct >= 0 ? 'text-up' : 'text-down';

  return (
    <tr
      className={`cursor-pointer border-b border-border/60 transition-colors hover:bg-base-700 ${
        selected ? 'bg-base-700' : ''
      }`}
      onClick={() => onSelect(ticker)}
      data-testid={`watchlist-row-${ticker}`}
    >
      <td className="px-3 py-2 font-mono font-semibold text-slate-100">{ticker}</td>
      <td className={`px-3 py-2 text-right font-mono ${flashClass}`} data-testid={`price-${ticker}`}>
        {price === undefined ? '—' : formatPrice(price)}
      </td>
      <td className={`px-3 py-2 text-right font-mono text-xs ${pctColor}`}>
        {pct === null ? '—' : formatPercent(pct)}
      </td>
      <td className="px-3 py-2">
        <Sparkline history={history} direction={direction} />
      </td>
      <td className="px-2 py-2 text-right">
        <button
          type="button"
          aria-label={`Remove ${ticker} from watchlist`}
          className="text-xs text-slate-600 hover:text-down"
          onClick={(e) => {
            e.stopPropagation();
            onRemove(ticker);
          }}
        >
          ✕
        </button>
      </td>
    </tr>
  );
}

export interface WatchlistEntry {
  ticker: string;
  price?: number;
  direction: PriceDirection;
  history: PricePoint[];
}

interface WatchlistProps {
  entries: WatchlistEntry[];
  selectedTicker: string | null;
  onSelect: (ticker: string) => void;
  onAdd: (ticker: string) => void;
  onRemove: (ticker: string) => void;
}

export default function Watchlist({ entries, selectedTicker, onSelect, onAdd, onRemove }: WatchlistProps) {
  const [newTicker, setNewTicker] = useState('');

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    const ticker = newTicker.trim().toUpperCase();
    if (!ticker) return;
    onAdd(ticker);
    setNewTicker('');
  };

  return (
    <div className="panel flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Watchlist</h2>
        <form onSubmit={handleAdd} className="flex items-center gap-1">
          <input
            value={newTicker}
            onChange={(e) => setNewTicker(e.target.value)}
            placeholder="TICKER"
            aria-label="Add ticker"
            className="w-20 rounded border border-border bg-base-900 px-2 py-1 text-xs uppercase text-slate-200 outline-none focus:border-accent-blue"
          />
          <button
            type="submit"
            className="rounded bg-accent-blue px-2 py-1 text-xs font-semibold text-base-900 hover:opacity-90"
          >
            Add
          </button>
        </form>
      </div>
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-base-800 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2 text-left">Ticker</th>
              <th className="px-3 py-2 text-right">Price</th>
              <th className="px-3 py-2 text-right">Chg %</th>
              <th className="px-3 py-2 text-left">Trend</th>
              <th className="px-2 py-2" />
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <WatchlistRow
                key={entry.ticker}
                ticker={entry.ticker}
                price={entry.price}
                direction={entry.direction}
                history={entry.history}
                selected={entry.ticker === selectedTicker}
                onSelect={onSelect}
                onRemove={onRemove}
              />
            ))}
          </tbody>
        </table>
        {entries.length === 0 && (
          <p className="px-3 py-4 text-center text-xs text-slate-600">No tickers watched yet.</p>
        )}
      </div>
    </div>
  );
}

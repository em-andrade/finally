'use client';

import { useState } from 'react';
import type { TradeSide } from '@/lib/types';

interface TradeBarProps {
  defaultTicker?: string | null;
  onTrade: (ticker: string, quantity: number, side: TradeSide) => Promise<void> | void;
  error?: string | null;
}

export default function TradeBar({ defaultTicker, onTrade, error }: TradeBarProps) {
  const [ticker, setTicker] = useState(defaultTicker ?? '');
  const [quantity, setQuantity] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async (side: TradeSide) => {
    const qty = Number(quantity);
    const sym = ticker.trim().toUpperCase();
    if (!sym || !qty || qty <= 0) return;
    setSubmitting(true);
    try {
      await onTrade(sym, qty, side);
      setQuantity('');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="panel flex items-center gap-3 p-3">
      <input
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        placeholder="TICKER"
        aria-label="Trade ticker"
        className="w-24 rounded border border-border bg-base-900 px-2 py-1.5 text-sm uppercase text-slate-200 outline-none focus:border-accent-blue"
      />
      <input
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        type="number"
        min="0"
        step="any"
        placeholder="Qty"
        aria-label="Trade quantity"
        className="w-24 rounded border border-border bg-base-900 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-accent-blue"
      />
      <button
        type="button"
        disabled={submitting}
        onClick={() => submit('buy')}
        className="rounded bg-up px-4 py-1.5 text-sm font-semibold text-base-900 hover:opacity-90 disabled:opacity-50"
      >
        Buy
      </button>
      <button
        type="button"
        disabled={submitting}
        onClick={() => submit('sell')}
        className="rounded bg-down px-4 py-1.5 text-sm font-semibold text-base-900 hover:opacity-90 disabled:opacity-50"
      >
        Sell
      </button>
      {error && <span className="text-xs text-down">{error}</span>}
    </div>
  );
}

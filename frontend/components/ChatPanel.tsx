'use client';

import { useState } from 'react';
import type { ChatMessage } from '@/lib/types';
import { formatQuantity } from '@/lib/format';

interface ChatPanelProps {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (message: string) => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
}

function ActionSummary({ actions }: { actions: ChatMessage['actions'] }) {
  if (!actions) return null;
  const trades = actions.trades ?? [];
  const watchlistChanges = actions.watchlist_changes ?? [];
  if (trades.length === 0 && watchlistChanges.length === 0) return null;

  return (
    <div className="mt-2 space-y-1 border-t border-border/60 pt-2 text-xs">
      {trades.map((t, i) => {
        const failed = t.status === 'failed';
        return (
          <div key={`${t.ticker}-${i}`} className={failed ? 'text-down' : t.side === 'buy' ? 'text-up' : 'text-down'}>
            {failed ? (
              <>✗ Failed to {t.side} {formatQuantity(t.quantity)} {t.ticker}{t.error ? `: ${t.error}` : ''}</>
            ) : (
              <>
                ✓ {t.side === 'buy' ? 'Bought' : 'Sold'} {formatQuantity(t.quantity)} {t.ticker}
                {typeof t.price === 'number' ? ` @ ${t.price.toFixed(2)}` : ''}
              </>
            )}
          </div>
        );
      })}
      {watchlistChanges.map((w, i) => {
        const failed = w.status === 'failed';
        return (
          <div key={`${w.ticker}-${i}`} className={failed ? 'text-down' : 'text-accent-blue'}>
            {failed
              ? `✗ Failed to ${w.action === 'add' ? 'add' : 'remove'} ${w.ticker}${w.error ? `: ${w.error}` : ''}`
              : `${w.action === 'add' ? '✓ Added' : '✓ Removed'} ${w.ticker} ${w.action === 'add' ? 'to' : 'from'} watchlist`}
          </div>
        );
      })}
    </div>
  );
}

export default function ChatPanel({ messages, loading, onSend, collapsed, onToggleCollapsed }: ChatPanelProps) {
  const [draft, setDraft] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || loading) return;
    onSend(text);
    setDraft('');
  };

  if (collapsed) {
    return (
      <button
        type="button"
        onClick={onToggleCollapsed}
        className="panel flex h-full w-10 flex-col items-center justify-center gap-2 text-accent-yellow"
        aria-label="Expand AI chat panel"
      >
        <span className="[writing-mode:vertical-rl]">AI Chat</span>
      </button>
    );
  }

  return (
    <div className="panel flex h-full w-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">AI Assistant</h2>
        <button
          type="button"
          onClick={onToggleCollapsed}
          aria-label="Collapse AI chat panel"
          className="text-xs text-slate-500 hover:text-slate-300"
        >
          ⟨⟨
        </button>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-3" data-testid="chat-history">
        {messages.length === 0 && (
          <p className="text-xs text-slate-600">
            Ask FinAlly about your portfolio, or tell it to make a trade.
          </p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                m.role === 'user' ? 'bg-accent-blue text-base-900' : 'bg-base-700 text-slate-200'
              }`}
              data-testid={`chat-message-${m.role}`}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
              <ActionSummary actions={m.actions} />
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-lg bg-base-700 px-3 py-2 text-sm text-slate-400" data-testid="chat-loading">
              Thinking…
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-border p-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask FinAlly…"
          aria-label="Chat message"
          className="flex-1 rounded border border-border bg-base-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-accent-blue"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-accent-purple px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}

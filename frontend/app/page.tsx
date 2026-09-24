'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Header from '@/components/Header';
import Watchlist, { type WatchlistEntry } from '@/components/Watchlist';
import MainChart from '@/components/MainChart';
import PortfolioHeatmap from '@/components/PortfolioHeatmap';
import PnLChart from '@/components/PnLChart';
import PositionsTable from '@/components/PositionsTable';
import TradeBar from '@/components/TradeBar';
import ChatPanel from '@/components/ChatPanel';
import { api, ApiError } from '@/lib/api';
import { usePriceStream } from '@/lib/useSSE';
import type { ChatMessage, Portfolio, PortfolioSnapshot, WatchlistItem } from '@/lib/types';

const PORTFOLIO_POLL_MS = 5000;

export default function Home() {
  const { prices, status } = usePriceStream();

  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [history, setHistory] = useState<PortfolioSnapshot[]>([]);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [tradeError, setTradeError] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatCollapsed, setChatCollapsed] = useState(false);

  const refreshWatchlist = useCallback(async () => {
    try {
      const data = await api.getWatchlist();
      setWatchlist(data);
      setSelectedTicker((current) => current ?? data[0]?.ticker ?? null);
    } catch {
      // Backend not reachable yet — leave watchlist as-is; the UI stays usable.
    }
  }, []);

  const refreshPortfolio = useCallback(async () => {
    try {
      setPortfolio(await api.getPortfolio());
    } catch {
      // Ignored — polled again shortly.
    }
  }, []);

  const refreshHistory = useCallback(async () => {
    try {
      setHistory(await api.getPortfolioHistory());
    } catch {
      // Ignored — polled again shortly.
    }
  }, []);

  useEffect(() => {
    refreshWatchlist();
    refreshPortfolio();
    refreshHistory();
    const interval = setInterval(() => {
      refreshPortfolio();
      refreshHistory();
    }, PORTFOLIO_POLL_MS);
    return () => clearInterval(interval);
  }, [refreshWatchlist, refreshPortfolio, refreshHistory]);

  const watchlistEntries: WatchlistEntry[] = useMemo(
    () =>
      watchlist.map((item) => {
        const tick = prices[item.ticker];
        return {
          ticker: item.ticker,
          price: tick?.latest.price,
          direction: tick?.latest.direction ?? 'flat',
          history: tick?.history ?? [],
        };
      }),
    [watchlist, prices],
  );

  const handleAdd = async (ticker: string) => {
    try {
      await api.addToWatchlist(ticker);
      await refreshWatchlist();
    } catch {
      // Optimistically ignore failures here; a future toast/error surface can report them.
    }
  };

  const handleRemove = async (ticker: string) => {
    try {
      await api.removeFromWatchlist(ticker);
      if (selectedTicker === ticker) setSelectedTicker(null);
      await refreshWatchlist();
    } catch {
      // See handleAdd.
    }
  };

  const handleTrade = async (ticker: string, quantity: number, side: 'buy' | 'sell') => {
    setTradeError(null);
    try {
      await api.postTrade({ ticker, quantity, side });
      await Promise.all([refreshPortfolio(), refreshHistory()]);
    } catch (err) {
      setTradeError(err instanceof ApiError ? err.message : 'Trade failed');
    }
  };

  const handleSendChat = async (message: string) => {
    const userMessage: ChatMessage = {
      id: `local-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, userMessage]);
    setChatLoading(true);
    try {
      const response = await api.sendChatMessage({ message });
      const assistantMessage: ChatMessage = {
        id: `local-${Date.now()}-assistant`,
        role: 'assistant',
        content: response.message,
        actions: { trades: response.trades, watchlist_changes: response.watchlist_changes },
        created_at: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, assistantMessage]);
      if (response.trades?.length || response.watchlist_changes?.length) {
        await Promise.all([refreshPortfolio(), refreshHistory(), refreshWatchlist()]);
      }
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        {
          id: `local-${Date.now()}-error`,
          role: 'assistant',
          content:
            err instanceof ApiError
              ? `Sorry, that failed: ${err.message}`
              : 'Sorry, I could not reach the assistant.',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const selectedHistory = selectedTicker ? prices[selectedTicker]?.history ?? [] : [];

  return (
    <div className="flex h-screen flex-col">
      <Header
        totalValue={portfolio?.total_value ?? null}
        cashBalance={portfolio?.cash_balance ?? null}
        status={status}
      />

      <main
        className="flex-1 gap-3 overflow-hidden p-3"
        style={{
          display: 'grid',
          gridTemplateColumns: `280px 1fr 1fr ${chatCollapsed ? '56px' : '340px'}`,
          gridTemplateRows: '2fr 1.2fr auto 1fr',
          gridTemplateAreas:
            '"watchlist chart chart chat" "watchlist heatmap pnl chat" "tradebar tradebar tradebar chat" "positions positions positions chat"',
        }}
      >
        <section style={{ gridArea: 'watchlist' }} className="min-h-0">
          <Watchlist
            entries={watchlistEntries}
            selectedTicker={selectedTicker}
            onSelect={setSelectedTicker}
            onAdd={handleAdd}
            onRemove={handleRemove}
          />
        </section>

        <section style={{ gridArea: 'chart' }} className="min-h-0">
          <MainChart ticker={selectedTicker} history={selectedHistory} />
        </section>

        <section style={{ gridArea: 'chat' }} className="min-h-0">
          <ChatPanel
            messages={chatMessages}
            loading={chatLoading}
            onSend={handleSendChat}
            collapsed={chatCollapsed}
            onToggleCollapsed={() => setChatCollapsed((c) => !c)}
          />
        </section>

        <section style={{ gridArea: 'heatmap' }} className="min-h-0">
          <PortfolioHeatmap positions={portfolio?.positions ?? []} />
        </section>

        <section style={{ gridArea: 'pnl' }} className="min-h-0">
          <PnLChart snapshots={history} />
        </section>

        <section style={{ gridArea: 'tradebar' }}>
          <TradeBar defaultTicker={selectedTicker} onTrade={handleTrade} error={tradeError} />
        </section>

        <section style={{ gridArea: 'positions' }} className="min-h-0">
          <PositionsTable positions={portfolio?.positions ?? []} />
        </section>
      </main>
    </div>
  );
}

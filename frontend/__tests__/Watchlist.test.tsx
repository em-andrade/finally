import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Watchlist, { type WatchlistEntry } from '@/components/Watchlist';

const baseEntry = (overrides: Partial<WatchlistEntry> = {}): WatchlistEntry => ({
  ticker: 'AAPL',
  price: 190.12,
  direction: 'flat',
  history: [],
  ...overrides,
});

describe('Watchlist', () => {
  it('renders a row per entry with ticker and price', () => {
    render(
      <Watchlist
        entries={[baseEntry()]}
        selectedTicker={null}
        onSelect={vi.fn()}
        onAdd={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    expect(screen.getByTestId('watchlist-row-AAPL')).toBeInTheDocument();
    expect(screen.getByTestId('price-AAPL')).toHaveTextContent('190.12');
  });

  it('shows an empty state with no entries', () => {
    render(<Watchlist entries={[]} selectedTicker={null} onSelect={vi.fn()} onAdd={vi.fn()} onRemove={vi.fn()} />);
    expect(screen.getByText(/no tickers watched yet/i)).toBeInTheDocument();
  });

  it('calls onSelect when a row is clicked', () => {
    const onSelect = vi.fn();
    render(
      <Watchlist entries={[baseEntry()]} selectedTicker={null} onSelect={onSelect} onAdd={vi.fn()} onRemove={vi.fn()} />,
    );
    fireEvent.click(screen.getByTestId('watchlist-row-AAPL'));
    expect(onSelect).toHaveBeenCalledWith('AAPL');
  });

  it('calls onRemove without triggering onSelect when the remove button is clicked', () => {
    const onSelect = vi.fn();
    const onRemove = vi.fn();
    render(
      <Watchlist entries={[baseEntry()]} selectedTicker={null} onSelect={onSelect} onAdd={vi.fn()} onRemove={onRemove} />,
    );
    fireEvent.click(screen.getByLabelText('Remove AAPL from watchlist'));
    expect(onRemove).toHaveBeenCalledWith('AAPL');
    expect(onSelect).not.toHaveBeenCalled();
  });

  it('adds a normalized ticker via the add form', () => {
    const onAdd = vi.fn();
    render(<Watchlist entries={[]} selectedTicker={null} onSelect={vi.fn()} onAdd={onAdd} onRemove={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Add ticker'), { target: { value: 'pypl' } });
    fireEvent.click(screen.getByText('Add'));

    expect(onAdd).toHaveBeenCalledWith('PYPL');
  });

  describe('price flash animation', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });
    afterEach(() => {
      vi.useRealTimers();
    });

    it('applies a flash-up class when the price ticks up, then removes it', () => {
      const { rerender } = render(
        <Watchlist
          entries={[baseEntry({ price: 100, direction: 'flat' })]}
          selectedTicker={null}
          onSelect={vi.fn()}
          onAdd={vi.fn()}
          onRemove={vi.fn()}
        />,
      );

      rerender(
        <Watchlist
          entries={[baseEntry({ price: 101, direction: 'up' })]}
          selectedTicker={null}
          onSelect={vi.fn()}
          onAdd={vi.fn()}
          onRemove={vi.fn()}
        />,
      );

      expect(screen.getByTestId('price-AAPL')).toHaveClass('flash-up');

      act(() => {
        vi.advanceTimersByTime(500);
      });

      expect(screen.getByTestId('price-AAPL')).not.toHaveClass('flash-up');
    });
  });
});

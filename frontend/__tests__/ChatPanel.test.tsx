import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ChatPanel from '@/components/ChatPanel';
import type { ChatMessage } from '@/lib/types';

const messages: ChatMessage[] = [
  { id: '1', role: 'user', content: 'How is my portfolio doing?', created_at: '2026-01-01T00:00:00Z' },
  {
    id: '2',
    role: 'assistant',
    content: "You're up 5% today.",
    created_at: '2026-01-01T00:00:01Z',
    actions: {
      trades: [{ ticker: 'AAPL', side: 'buy', quantity: 5, price: 190, status: 'executed' }],
      watchlist_changes: [{ ticker: 'PYPL', action: 'add', status: 'executed' }],
    },
  },
];

describe('ChatPanel', () => {
  it('renders user and assistant messages with executed action summaries', () => {
    render(
      <ChatPanel messages={messages} loading={false} onSend={vi.fn()} collapsed={false} onToggleCollapsed={vi.fn()} />,
    );

    expect(screen.getByTestId('chat-message-user')).toHaveTextContent('How is my portfolio doing?');
    expect(screen.getByTestId('chat-message-assistant')).toHaveTextContent("You're up 5% today.");
    expect(screen.getByTestId('chat-message-assistant')).toHaveTextContent(/Bought 5 AAPL/);
    expect(screen.getByTestId('chat-message-assistant')).toHaveTextContent(/Added PYPL to watchlist/);
  });

  it('renders a failed trade without crashing on a missing price', () => {
    const failedMessages: ChatMessage[] = [
      {
        id: '3',
        role: 'assistant',
        content: 'Could not complete that trade.',
        created_at: '2026-01-01T00:00:02Z',
        actions: {
          trades: [
            { ticker: 'AAPL', side: 'buy', quantity: 999, price: null, status: 'failed', error: 'Insufficient cash' },
          ],
        },
      },
    ];
    render(
      <ChatPanel
        messages={failedMessages}
        loading={false}
        onSend={vi.fn()}
        collapsed={false}
        onToggleCollapsed={vi.fn()}
      />,
    );
    expect(screen.getByTestId('chat-message-assistant')).toHaveTextContent(/Failed to buy 999 AAPL: Insufficient cash/);
  });

  it('shows a loading indicator while waiting for a response', () => {
    render(<ChatPanel messages={[]} loading onSend={vi.fn()} collapsed={false} onToggleCollapsed={vi.fn()} />);
    expect(screen.getByTestId('chat-loading')).toBeInTheDocument();
  });

  it('submits a typed message and clears the input', () => {
    const onSend = vi.fn();
    render(<ChatPanel messages={[]} loading={false} onSend={onSend} collapsed={false} onToggleCollapsed={vi.fn()} />);

    const input = screen.getByLabelText('Chat message') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Buy 5 AAPL' } });
    fireEvent.click(screen.getByText('Send'));

    expect(onSend).toHaveBeenCalledWith('Buy 5 AAPL');
    expect(input.value).toBe('');
  });

  it('does not submit an empty message', () => {
    const onSend = vi.fn();
    render(<ChatPanel messages={[]} loading={false} onSend={onSend} collapsed={false} onToggleCollapsed={vi.fn()} />);
    fireEvent.click(screen.getByText('Send'));
    expect(onSend).not.toHaveBeenCalled();
  });

  it('renders collapsed as a toggle button', () => {
    const onToggle = vi.fn();
    render(<ChatPanel messages={[]} loading={false} onSend={vi.fn()} collapsed onToggleCollapsed={onToggle} />);
    fireEvent.click(screen.getByLabelText('Expand AI chat panel'));
    expect(onToggle).toHaveBeenCalled();
  });
});

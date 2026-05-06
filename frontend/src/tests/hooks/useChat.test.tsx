import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useChat } from '../../hooks/useChat';
import { chatApi } from '../../api/client';

describe('useChat Hook', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('loads history on call', async () => {
    const mockHistory = [
      { id: '1', role: 'user', content: 'Hello' },
      { id: '2', role: 'assistant', content: 'Hi' },
    ];
    vi.spyOn(chatApi, 'getHistory').mockResolvedValue({ data: mockHistory } as any);

    const { result } = renderHook(() => useChat('session-1'));

    await act(async () => {
      await result.current.loadHistory();
    });

    expect(result.current.messages).toEqual(mockHistory);
  });

  it('handles streaming messages', async () => {
    // Mock async generator
    async function* mockStream() {
      yield { content: 'The', done: false };
      yield { content: ' sky', done: false };
      yield { content: ' is blue.', done: false };
      yield { done: true, timestamps: [{ start: 1, end: 2, text: 'blue' }] };
    }
    vi.spyOn(chatApi, 'sendMessageStream').mockReturnValue(mockStream() as any);

    const { result } = renderHook(() => useChat('session-1'));

    await act(async () => {
      await result.current.sendMessage('What color is the sky?');
    });

    // Check intermediate state
    expect(result.current.messages.length).toBe(2);
    expect(result.current.messages[0].content).toBe('What color is the sky?');
    
    // Wait for full stream
    await waitFor(() => {
      const assistantMsg = result.current.messages[1];
      expect(assistantMsg.content).toBe('The sky is blue.');
      expect(assistantMsg.timestamps).toEqual([{ start: 1, end: 2, text: 'blue' }]);
      expect(assistantMsg.isStreaming).toBe(false);
    });
  });

  it('handles stream errors', async () => {
    vi.spyOn(chatApi, 'sendMessageStream').mockImplementation(async function* () {
      throw new Error('Stream failed');
    } as any);

    const { result } = renderHook(() => useChat('session-1'));

    await act(async () => {
      await result.current.sendMessage('Fail me');
    });

    await waitFor(() => {
      const assistantMsg = result.current.messages[1];
      expect(assistantMsg.content).toContain('Sorry, an error occurred');
      expect(assistantMsg.isStreaming).toBe(false);
    });
  });
});

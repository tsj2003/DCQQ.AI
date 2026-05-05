/**
 * Custom hook for chat functionality with streaming support.
 */

import { useState, useCallback, useRef } from 'react';
import { chatApi } from '../api/client';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamps?: Array<{ start: number; end: number; text: string }>;
  sources?: Array<{ page: number; text: string }>;
  isStreaming?: boolean;
}

export function useChat(sessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef(false);

  const loadHistory = useCallback(async () => {
    if (!sessionId) return;
    try {
      const response = await chatApi.getHistory(sessionId);
      setMessages(response.data);
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  }, [sessionId]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!sessionId || !content.trim()) return;

      // Add user message
      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: content.trim(),
      };
      setMessages((prev) => [...prev, userMsg]);

      // Add placeholder assistant message
      const assistantId = `assistant-${Date.now()}`;
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: '',
        isStreaming: true,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      setIsLoading(true);
      abortRef.current = false;

      try {
        let fullContent = '';
        let timestamps: ChatMessage['timestamps'] = undefined;
        let sources: ChatMessage['sources'] = undefined;

        for await (const data of chatApi.sendMessageStream(sessionId, content)) {
          if (abortRef.current) break;

          if (data.content && !data.done) {
            fullContent += data.content;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantId
                  ? { ...msg, content: fullContent }
                  : msg
              )
            );
          }

          if (data.timestamps) {
            timestamps = data.timestamps;
          }
          if (data.sources) {
            sources = data.sources;
          }

          if (data.done) {
            fullContent = data.content || fullContent;
          }
        }

        // Finalize the message
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? {
                  ...msg,
                  content: fullContent,
                  timestamps,
                  sources,
                  isStreaming: false,
                }
              : msg
          )
        );
      } catch (err) {
        console.error('Chat error:', err);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? {
                  ...msg,
                  content: 'Sorry, an error occurred. Please try again.',
                  isStreaming: false,
                }
              : msg
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId]
  );

  const stopStreaming = useCallback(() => {
    abortRef.current = true;
  }, []);

  return {
    messages,
    isLoading,
    sendMessage,
    stopStreaming,
    loadHistory,
  };
}

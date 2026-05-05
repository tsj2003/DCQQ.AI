/**
 * Chat window component with streaming message display.
 * Revamped with 'Wonder Makers' aesthetic and DaisyUI.
 */

import React, { useEffect, useRef, useState } from 'react';
import { Send, StopCircle, Sparkles, Command } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '../hooks/useChat';
import { ChatMessage } from './ChatMessage';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatWindowProps {
  messages: ChatMessageType[];
  isLoading: boolean;
  onSendMessage: (content: string) => void;
  onStopStreaming: () => void;
  onPlayTimestamp?: (start: number) => void;
}

export function ChatWindow({
  messages,
  isLoading,
  onSendMessage,
  onStopStreaming,
  onPlayTimestamp,
}: ChatWindowProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#000000] selection:bg-wonder-lime selection:text-black">
      <div className="flex-1 overflow-y-auto px-6 py-10 scroll-smooth" id="chat-messages">
        <AnimatePresence>
          {messages.length === 0 ? (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto"
            >
              <div className="w-20 h-20 rounded-[2.5rem] bg-wonder-lime/10 border border-wonder-lime/20 flex items-center justify-center text-wonder-lime mb-8 shadow-[0_0_50px_rgba(217,255,0,0.1)]">
                <Sparkles size={40} />
              </div>
              <h3 className="text-4xl font-black tracking-tighter mb-4 italic uppercase">Ready to Assist</h3>
              <p className="text-white/40 font-medium leading-relaxed">
                Ask anything about the document. I can extract insights, find timestamps, and summarize complex topics instantly.
              </p>
              <div className="mt-10 flex flex-wrap gap-2 justify-center">
                 {['Key Insights', 'Extract Timestamps', 'Main Summary'].map(tag => (
                   <button 
                    key={tag}
                    onClick={() => setInput(tag)}
                    className="px-4 py-2 rounded-xl bg-white/5 border border-white/5 text-[10px] font-black uppercase tracking-widest text-white/40 hover:border-wonder-lime hover:text-wonder-lime transition-all"
                   >
                     {tag}
                   </button>
                 ))}
              </div>
            </motion.div>
          ) : (
            messages.map((msg, idx) => (
              <ChatMessage
                key={msg.id || idx}
                message={msg}
                onPlayTimestamp={onPlayTimestamp}
              />
            ))
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      <div className="p-6 md:p-10 max-w-[900px] w-full mx-auto">
        <form 
          className={`relative group transition-all duration-500 rounded-[2rem] p-1.5 flex items-end gap-2 border-2 ${isLoading ? 'border-wonder-lime bg-wonder-lime/5 shadow-[0_0_30px_rgba(217,255,0,0.1)]' : 'border-white/10 bg-white/5 focus-within:border-wonder-lime focus-within:bg-white/10'}`} 
          onSubmit={handleSubmit}
        >
          <div className="flex-none p-4 text-white/20">
            <Command size={20} />
          </div>
          <textarea
            ref={inputRef}
            className="flex-1 bg-transparent border-none text-white font-bold py-4 focus:ring-0 resize-none outline-none max-h-32 placeholder:text-white/20"
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask AI anything..."
            rows={1}
            disabled={isLoading}
          />

          <div className="flex-none p-2">
            {isLoading ? (
              <motion.button
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
                type="button"
                className="w-12 h-12 rounded-2xl bg-wonder-lime text-black flex items-center justify-center hover:bg-red-500 hover:text-white transition-colors"
                onClick={onStopStreaming}
                id="stop-streaming-btn"
              >
                <StopCircle size={20} fill="currentColor" />
              </motion.button>
            ) : (
              <button
                type="submit"
                className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 ${input.trim() ? 'bg-wonder-lime text-black shadow-[0_0_20px_rgba(217,255,0,0.3)]' : 'bg-white/5 text-white/20'}`}
                disabled={!input.trim()}
                id="send-message-btn"
              >
                <Send size={20} className={input.trim() ? 'translate-x-0.5 -translate-y-0.5' : ''} />
              </button>
            )}
          </div>
        </form>
        <p className="text-center mt-4 text-[9px] font-black uppercase tracking-[0.3em] text-white/10">
          DocQA AI — Advanced Context Retrieval
        </p>
      </div>
    </div>
  );
}

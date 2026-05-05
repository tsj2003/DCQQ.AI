/**
 * Individual chat message with timestamp Play buttons and source references.
 * Revamped with 'Wonder Makers' aesthetic and DaisyUI.
 */

import { Play, FileText, Clock, User, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { ChatMessage as ChatMessageType } from '../hooks/useChat';
import { formatTimestamp } from '../utils/formatTime';
import { motion } from 'framer-motion';

interface ChatMessageProps {
  message: ChatMessageType;
  onPlayTimestamp?: (start: number) => void;
}

export function ChatMessage({ message, onPlayTimestamp }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-6 mb-12 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      <div className={`flex-none w-10 h-10 rounded-2xl flex items-center justify-center border ${isUser ? 'bg-white/5 border-white/10 text-white/40' : 'bg-wonder-lime border-wonder-lime shadow-[0_0_20px_rgba(217,255,0,0.2)] text-black'}`}>
        {isUser ? <User size={20} /> : <Sparkles size={20} />}
      </div>

      <div className={`flex flex-col gap-4 max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`relative px-8 py-6 rounded-[2rem] text-sm leading-relaxed ${isUser ? 'bg-white/5 text-white/80 rounded-tr-none' : 'glass-panel bg-white/[0.03] text-white/90 rounded-tl-none border border-white/10 shadow-2xl'}`}>
          {message.isStreaming && !message.content ? (
            <div className="flex gap-2 py-2">
              <div className="w-1.5 h-1.5 rounded-full bg-wonder-lime animate-bounce" />
              <div className="w-1.5 h-1.5 rounded-full bg-wonder-lime animate-bounce [animation-delay:0.2s]" />
              <div className="w-1.5 h-1.5 rounded-full bg-wonder-lime animate-bounce [animation-delay:0.4s]" />
            </div>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-strong:text-wonder-lime prose-code:text-wonder-lime prose-code:bg-white/5 prose-code:px-1.5 prose-code:rounded">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}

          {message.isStreaming && message.content && (
            <span className="inline-block w-2 h-4 bg-wonder-lime ml-1 animate-pulse" />
          )}
        </div>

        {/* Timestamp references with Play buttons */}
        {!isUser && message.timestamps && message.timestamps.length > 0 && (
          <div className="w-full space-y-3 mt-2">
            <div className="flex items-center gap-2 text-[10px] font-black tracking-widest text-white/20 uppercase px-2">
              <Clock size={12} />
              <span>Multimedia References</span>
            </div>
            <div className="grid grid-cols-1 gap-2">
              {message.timestamps.map((ts, idx) => (
                <button
                  key={idx}
                  className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-wonder-lime hover:bg-wonder-lime/5 transition-all group text-left"
                  onClick={() => onPlayTimestamp?.(ts.start)}
                  id={`play-timestamp-${idx}`}
                >
                  <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-white/20 group-hover:bg-wonder-lime group-hover:text-black transition-all">
                    <Play size={12} fill="currentColor" />
                  </div>
                  <div className="flex-1 min-width-0">
                     <p className="text-[10px] font-black text-wonder-lime uppercase tracking-tighter">
                       {formatTimestamp(ts.start)} — {formatTimestamp(ts.end)}
                     </p>
                     <p className="text-xs text-white/40 truncate italic group-hover:text-white/60">
                       "{ts.text}"
                     </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Source page references */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-2 px-2 mt-2">
            <div className="flex items-center gap-2 text-[10px] font-black tracking-widest text-white/20 uppercase mr-2">
              <FileText size={12} />
              <span>Sources:</span>
            </div>
            {message.sources.map((src, idx) => (
              <div key={idx} className="px-3 py-1 rounded-lg bg-white/5 border border-white/5 text-[10px] font-black text-white/60 uppercase">
                Page {src.page}
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

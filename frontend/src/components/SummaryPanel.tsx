/**
 * Summary panel — displays document summary in a collapsible section.
 * Revamped with 'Wonder Makers' aesthetic and DaisyUI.
 */

import { useState } from 'react';
import { ChevronDown, RefreshCw, AlignLeft } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';

interface SummaryPanelProps {
  summary: string | null;
  isLoading: boolean;
  onRegenerate?: () => void;
}

export function SummaryPanel({ summary, isLoading, onRegenerate }: SummaryPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="glass-card rounded-3xl overflow-hidden border border-white/5">
      <button
        className="w-full flex items-center justify-between p-5 bg-white/5 hover:bg-white/10 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
        id="summary-toggle"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-wonder-lime/10 flex items-center justify-center text-wonder-lime">
            <AlignLeft size={16} />
          </div>
          <span className="text-sm font-black uppercase tracking-widest text-white/80">Analysis Report</span>
        </div>
        <div className={`transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}>
          <ChevronDown size={18} className="text-white/20" />
        </div>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-6 pt-2">
              {isLoading ? (
                <div className="space-y-3 py-4">
                  <div className="h-4 bg-white/5 rounded-full shimmer w-full" />
                  <div className="h-4 bg-white/5 rounded-full shimmer w-[90%]" />
                  <div className="h-4 bg-white/5 rounded-full shimmer w-[75%]" />
                </div>
              ) : summary ? (
                <div className="group relative">
                  <div className="prose prose-invert prose-sm max-w-none prose-p:text-white/60 prose-p:leading-relaxed prose-headings:text-white prose-strong:text-wonder-lime prose-strong:font-black">
                    <ReactMarkdown>{summary}</ReactMarkdown>
                  </div>
                  
                  {onRegenerate && (
                    <div className="mt-6 flex justify-end">
                      <button
                        className="btn btn-ghost btn-sm rounded-xl normal-case gap-2 text-white/30 hover:text-wonder-lime hover:bg-wonder-lime/10"
                        onClick={onRegenerate}
                        id="regenerate-summary-btn"
                      >
                        <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
                        Update Analysis
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-8 text-center">
                   <p className="text-sm font-bold text-white/20 uppercase tracking-widest">Generating Analysis...</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

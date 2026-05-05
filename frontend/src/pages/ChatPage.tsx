/**
 * Chat page — main Q&A interface with document context.
 * Revamped with 'Wonder Makers' aesthetic and DaisyUI.
 */

import { useEffect, useState, useCallback } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, FileText, Music, Video, Sparkles } from 'lucide-react';
import { useChat } from '../hooks/useChat';
import { useMediaPlayer } from '../hooks/useMediaPlayer';
import { ChatWindow } from '../components/ChatWindow';
import { SummaryPanel } from '../components/SummaryPanel';
import { MediaPlayer } from '../components/MediaPlayer';
import { documentsApi, mediaApi } from '../api/client';
import { motion } from 'framer-motion';

interface DocumentDetail {
  id: string;
  filename: string;
  file_type: string;
  status: string;
  summary: string | null;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  pdf: <FileText size={18} />,
  audio: <Music size={18} />,
  video: <Video size={18} />,
};

export function ChatPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const docId = searchParams.get('docId') || '';

  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  const { messages, isLoading, sendMessage, stopStreaming, loadHistory } = useChat(sessionId || null);
  const {
    mediaRef,
    isPlaying,
    currentTime,
    duration,
    seekTo,
    togglePlay,
    onTimeUpdate,
    onLoadedMetadata,
  } = useMediaPlayer();

  useEffect(() => {
    if (docId) {
      documentsApi.get(docId).then((res) => setDocument(res.data));
    }
    if (sessionId) {
      loadHistory();
    }
  }, [docId, sessionId, loadHistory]);

  const handleRegenSummary = useCallback(async () => {
    if (!docId) return;
    setSummaryLoading(true);
    try {
      const res = await documentsApi.regenerateSummary(docId);
      setDocument((prev) => prev ? { ...prev, summary: res.data.summary } : null);
    } finally {
      setSummaryLoading(false);
    }
  }, [docId]);

  const mediaUrl = document?.file_type !== 'pdf' ? mediaApi.getMediaUrl(docId) : null;

  return (
    <div className="flex h-[calc(100vh-80px)] overflow-hidden bg-black selection:bg-wonder-lime selection:text-black">
      {/* Left Sidebar: Control Center */}
      <motion.aside 
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-[400px] flex-shrink-0 bg-[#0a0a0a] border-r border-white/5 flex flex-col overflow-hidden"
      >
        <div className="p-6 border-b border-white/5">
          <button 
            className="flex items-center gap-2 text-xs font-black tracking-widest text-white/40 hover:text-wonder-lime transition-colors uppercase mb-8"
            onClick={() => navigate('/')}
            id="back-btn"
          >
            <ArrowLeft size={16} />
            Dashboard
          </button>

          {document ? (
            <div className="flex flex-col gap-4">
               <div className="flex items-start justify-between">
                  <div className="p-4 rounded-2xl bg-white/5 text-wonder-lime shadow-[0_0_20px_rgba(217,255,0,0.1)]">
                    {TYPE_ICONS[document.file_type]}
                  </div>
                  <div className="px-3 py-1 rounded-full bg-wonder-lime/10 border border-wonder-lime/20 text-wonder-lime text-[10px] font-black uppercase tracking-widest">
                    {document.file_type}
                  </div>
               </div>
               <h2 className="text-2xl font-black tracking-tight leading-none truncate" title={document.filename}>
                 {document.filename}
               </h2>
            </div>
          ) : (
            <div className="h-24 animate-pulse bg-white/5 rounded-3xl" />
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-8 scroll-smooth">
          {document ? (
            <>
              <section>
                <div className="flex items-center gap-2 text-[10px] font-black tracking-[0.2em] text-white/20 uppercase mb-4">
                  <Sparkles size={12} className="text-wonder-lime" />
                  AI Summary
                </div>
                <SummaryPanel
                  summary={document.summary}
                  isLoading={summaryLoading}
                  onRegenerate={handleRegenSummary}
                />
              </section>

              {mediaUrl && document.file_type !== 'pdf' && (
                <section>
                   <div className="flex items-center gap-2 text-[10px] font-black tracking-[0.2em] text-white/20 uppercase mb-4">
                    {document.file_type === 'audio' ? <Music size={12} /> : <Video size={12} />}
                    Media Controller
                  </div>
                  <MediaPlayer
                    ref={mediaRef}
                    src={mediaUrl}
                    type={document.file_type as 'audio' | 'video'}
                    filename={document.filename}
                    isPlaying={isPlaying}
                    currentTime={currentTime}
                    duration={duration}
                    onTogglePlay={togglePlay}
                    onTimeUpdate={onTimeUpdate}
                    onLoadedMetadata={onLoadedMetadata}
                  />
                </section>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <Loader2 size={32} className="animate-spin text-wonder-lime opacity-20" />
            </div>
          )}
        </div>
      </motion.aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col relative bg-[#000000]">
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSendMessage={sendMessage}
          onStopStreaming={stopStreaming}
          onPlayTimestamp={seekTo}
        />
      </main>
    </div>
  );
}

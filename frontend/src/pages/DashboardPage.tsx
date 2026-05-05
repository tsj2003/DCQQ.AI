/**
 * Dashboard page — document list and file upload.
 * Revamped with 'Wonder Makers' aesthetic and DaisyUI.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Music, Video, Trash2, Loader2, Plus, ArrowUpRight } from 'lucide-react';
import { documentsApi, chatApi } from '../api/client';
import { FileUpload } from '../components/FileUpload';
import { formatFileSize, formatRelativeTime } from '../utils/formatTime';
import { motion, AnimatePresence } from 'framer-motion';

interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  summary: string | null;
  created_at: string;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  pdf: <FileText size={24} />,
  audio: <Music size={24} />,
  video: <Video size={24} />,
};

const TYPE_COLORS: Record<string, string> = {
  pdf: 'text-wonder-lime',
  audio: 'text-blue-400',
  video: 'text-purple-400',
};

export function DashboardPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const navigate = useNavigate();

  const fetchDocuments = useCallback(async () => {
    try {
      const response = await documentsApi.list();
      setDocuments(response.data.documents);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 5000);
    return () => clearInterval(interval);
  }, [fetchDocuments]);

  const handleDelete = async (e: React.MouseEvent, docId: string) => {
    e.stopPropagation();
    if (!confirm('Delete this document?')) return;
    try {
      await documentsApi.delete(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const handleOpenChat = async (doc: Document) => {
    if (doc.status !== 'ready') return;
    try {
      const response = await chatApi.createSession(doc.id);
      navigate(`/chat/${response.data.id}?docId=${doc.id}`);
    } catch (err) {
      console.error('Failed to create chat session:', err);
    }
  };

  return (
    <div className="min-h-full p-6 md:p-12 max-w-[1400px] mx-auto overflow-y-auto selection:bg-wonder-lime selection:text-black">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <h1 className="text-5xl font-black tracking-tighter mb-2">MY DOCUMENTS</h1>
          <p className="text-white/40 font-bold tracking-widest uppercase text-xs">
            {documents.length} Files • {documents.filter(d => d.status === 'ready').length} Ready
          </p>
        </motion.div>

        <motion.button
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          onClick={() => setIsUploadOpen(!isUploadOpen)}
          className={`btn ${isUploadOpen ? 'btn-wonder-outline' : 'btn-wonder'} flex items-center gap-2`}
        >
          {isUploadOpen ? (
            <>Cancel Upload</>
          ) : (
            <>
              <Plus size={20} />
              Upload New
            </>
          )}
        </motion.button>
      </div>

      <AnimatePresence>
        {isUploadOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-12 overflow-hidden"
          >
            <FileUpload onUploadComplete={() => {
              fetchDocuments();
              setIsUploadOpen(false);
            }} />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="glass-card p-6 rounded-3xl h-[160px] shimmer" />
          ))
        ) : documents.length === 0 ? (
          <div className="col-span-full py-32 text-center">
            <div className="w-20 h-20 rounded-3xl bg-white/5 flex items-center justify-center mx-auto mb-6 text-white/20">
              <FileText size={40} />
            </div>
            <h3 className="text-2xl font-bold mb-2">No documents found</h3>
            <p className="text-white/40 mb-8">Upload your first file to get started with AI analysis.</p>
            <button 
              onClick={() => setIsUploadOpen(true)}
              className="btn btn-wonder-outline"
            >
              Start Upload
            </button>
          </div>
        ) : (
          documents.map((doc, idx) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className={`glass-card p-6 rounded-[2rem] flex flex-col justify-between group cursor-pointer ${doc.status !== 'ready' ? 'opacity-70' : ''}`}
              onClick={() => handleOpenChat(doc)}
              id={`document-${doc.id}`}
            >
              <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-2xl bg-white/5 ${TYPE_COLORS[doc.file_type]} group-hover:bg-wonder-lime group-hover:text-black transition-all duration-500`}>
                  {TYPE_ICONS[doc.file_type]}
                </div>
                <div className="flex items-center gap-2">
                  {doc.status === 'processing' ? (
                    <div className="badge badge-warning font-bold text-[10px] uppercase gap-1 bg-wonder-warning/10 border-wonder-warning/20 text-wonder-warning">
                      <Loader2 size={10} className="animate-spin" />
                      Processing
                    </div>
                  ) : doc.status === 'ready' ? (
                    <div className="badge badge-success font-bold text-[10px] uppercase bg-wonder-lime/10 border-wonder-lime/20 text-wonder-lime">
                      Ready
                    </div>
                  ) : (
                    <div className="badge badge-error font-bold text-[10px] uppercase bg-red-500/10 border-red-500/20 text-red-500">
                      Error
                    </div>
                  )}
                  <button 
                    onClick={(e) => handleDelete(e, doc.id)}
                    className="p-2 hover:bg-red-500/10 hover:text-red-500 rounded-lg text-white/20 transition-all"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-bold truncate mb-1 group-hover:text-wonder-lime transition-colors">
                  {doc.filename}
                </h3>
                <p className="text-xs font-bold text-white/30 uppercase tracking-widest">
                  {formatFileSize(doc.file_size || 0)} • {formatRelativeTime(doc.created_at)}
                </p>
              </div>

              <div className="mt-6 flex items-center justify-between">
                <div className="flex -space-x-2">
                   <div className="w-6 h-6 rounded-full border-2 border-black bg-white/10" />
                   <div className="w-6 h-6 rounded-full border-2 border-black bg-white/5" />
                </div>
                {doc.status === 'ready' && (
                  <div className="flex items-center gap-2 text-xs font-bold text-wonder-lime opacity-0 group-hover:opacity-100 translate-x-4 group-hover:translate-x-0 transition-all">
                    START CHAT
                    <ArrowUpRight size={14} />
                  </div>
                )}
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}

/**
 * File upload component with drag-and-drop support.
 * Revamped with 'Wonder Makers' aesthetic and DaisyUI.
 */

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { X, CheckCircle, Loader2, FileUp, Sparkles } from 'lucide-react';
import { documentsApi } from '../api/client';
import { formatFileSize } from '../utils/formatTime';
import { motion, AnimatePresence } from 'framer-motion';

interface FileUploadProps {
  onUploadComplete: () => void;
}

const ACCEPTED_TYPES: Record<string, string[]> = {
  'application/pdf': ['.pdf'],
  'audio/mpeg': ['.mp3'],
  'audio/wav': ['.wav'],
  'audio/mp4': ['.m4a'],
  'video/mp4': ['.mp4'],
  'video/webm': ['.webm'],
  'video/quicktime': ['.mov'],
};

export function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [uploadState, setUploadState] = useState<{
    file: File | null;
    progress: number;
    status: 'idle' | 'uploading' | 'success' | 'error';
    error?: string;
  }>({ file: null, progress: 0, status: 'idle' });

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setUploadState({ file, progress: 0, status: 'uploading' });

      try {
        await documentsApi.upload(file, (progress) => {
          setUploadState((prev) => ({ ...prev, progress }));
        });

        setUploadState((prev) => ({ ...prev, status: 'success', progress: 100 }));

        setTimeout(() => {
          setUploadState({ file: null, progress: 0, status: 'idle' });
          onUploadComplete();
        }, 2000);
      } catch (err: unknown) {
        const error = err as { response?: { data?: { detail?: string } } };
        setUploadState((prev) => ({
          ...prev,
          status: 'error',
          error: error.response?.data?.detail || 'Upload failed',
        }));
      }
    },
    [onUploadComplete]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: 100 * 1024 * 1024, // 100MB
    disabled: uploadState.status === 'uploading',
  });

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`relative overflow-hidden group border-2 border-dashed rounded-[2.5rem] p-12 text-center transition-all duration-500 cursor-pointer
          ${isDragActive ? 'border-wonder-lime bg-wonder-lime/5 shadow-[0_0_50px_rgba(217,255,0,0.1)]' : 'border-white/10 bg-white/5 hover:border-white/20'}
          ${uploadState.status === 'uploading' ? 'pointer-events-none' : ''}
        `}
        id="file-dropzone"
      >
        <input {...getInputProps()} id="file-input" />
        
        <AnimatePresence mode="wait">
          {uploadState.status === 'idle' && (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col items-center gap-6"
            >
              <div className="w-20 h-20 rounded-[2rem] bg-wonder-lime flex items-center justify-center text-black group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 shadow-[0_0_30px_rgba(217,255,0,0.2)]">
                <FileUp size={36} />
              </div>
              <div>
                <h3 className="text-2xl font-black tracking-tight mb-2">
                  {isDragActive ? 'DROP IT HERE' : 'SELECT A FILE'}
                </h3>
                <p className="text-white/40 font-bold uppercase tracking-widest text-xs">
                  Drag & Drop or <span className="text-wonder-lime underline">Browse</span>
                </p>
              </div>
              <div className="flex gap-2 flex-wrap justify-center">
                {['PDF', 'MP3', 'WAV', 'MP4', 'MOV'].map(ext => (
                  <span key={ext} className="px-4 py-1.5 rounded-full bg-white/5 border border-white/5 text-[10px] font-black tracking-widest text-white/40 uppercase">
                    {ext}
                  </span>
                ))}
              </div>
            </motion.div>
          )}

          {uploadState.status === 'uploading' && (
            <motion.div
              key="uploading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center gap-6 w-full max-w-md mx-auto"
            >
              <Loader2 size={40} className="text-wonder-lime animate-spin" />
              <div className="w-full">
                <div className="flex justify-between items-end mb-2">
                  <div className="text-left">
                    <p className="text-lg font-bold truncate max-w-[250px]">{uploadState.file?.name}</p>
                    <p className="text-xs font-bold text-white/40 uppercase tracking-widest">{formatFileSize(uploadState.file?.size || 0)}</p>
                  </div>
                  <p className="text-2xl font-black text-wonder-lime">{uploadState.progress}%</p>
                </div>
                <div className="w-full h-3 bg-white/5 rounded-full overflow-hidden border border-white/5 p-0.5">
                  <motion.div
                    className="h-full bg-wonder-lime rounded-full shadow-[0_0_10px_rgba(217,255,0,0.5)]"
                    initial={{ width: 0 }}
                    animate={{ width: `${uploadState.progress}%` }}
                    transition={{ ease: "linear" }}
                  />
                </div>
              </div>
            </motion.div>
          )}

          {uploadState.status === 'success' && (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center gap-4"
            >
              <div className="w-20 h-20 rounded-full bg-wonder-lime flex items-center justify-center text-black">
                <CheckCircle size={40} />
              </div>
              <div>
                <h3 className="text-2xl font-black tracking-tight">UPLOAD COMPLETE</h3>
                <p className="text-wonder-lime font-bold uppercase tracking-widest text-xs flex items-center justify-center gap-2">
                  <Sparkles size={14} /> Initializing AI processing...
                </p>
              </div>
            </motion.div>
          )}

          {uploadState.status === 'error' && (
            <motion.div
              key="error"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center gap-6"
            >
              <div className="w-20 h-20 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center text-red-500">
                <X size={40} />
              </div>
              <div>
                <h3 className="text-2xl font-black tracking-tight text-red-500 uppercase">UPLOAD FAILED</h3>
                <p className="text-white/40 font-bold text-sm mt-1">{uploadState.error}</p>
              </div>
              <button
                className="btn btn-wonder-outline text-red-400 border-red-500/20 hover:bg-red-500 hover:text-white"
                onClick={(e) => {
                  e.stopPropagation();
                  setUploadState({ file: null, progress: 0, status: 'idle' });
                }}
              >
                Try Again
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

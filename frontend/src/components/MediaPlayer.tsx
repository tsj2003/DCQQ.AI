/**
 * Media player component for audio and video playback.
 * Revamped with 'Wonder Makers' aesthetic and DaisyUI.
 */

import React, { forwardRef } from 'react';
import { Play, Pause, Volume2, Maximize2 } from 'lucide-react';
import { formatTimestamp } from '../utils/formatTime';
import { motion } from 'framer-motion';

interface MediaPlayerProps {
  src: string;
  type: 'audio' | 'video';
  filename: string;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  onTogglePlay: () => void;
  onTimeUpdate: () => void;
  onLoadedMetadata: () => void;
}

export const MediaPlayer = forwardRef<HTMLAudioElement | HTMLVideoElement, MediaPlayerProps>(
  (
    { src, type, filename, isPlaying, currentTime, duration, onTogglePlay, onTimeUpdate, onLoadedMetadata },
    ref
  ) => {
    return (
      <div className="glass-card rounded-3xl overflow-hidden border border-white/5 bg-[#0d0d0d]" id="media-player">
        <div className="flex items-center justify-between p-4 bg-white/5 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Volume2 size={14} className="text-wonder-lime" />
            <span className="text-[10px] font-black uppercase tracking-widest text-white/40 truncate max-w-[200px]">
              {filename}
            </span>
          </div>
          {type === 'video' && <Maximize2 size={14} className="text-white/20 hover:text-white transition-colors cursor-pointer" />}
        </div>

        <div className="relative group">
          {type === 'video' ? (
            <video
              ref={ref as React.Ref<HTMLVideoElement>}
              src={src}
              className="w-full aspect-video bg-black cursor-pointer"
              onTimeUpdate={onTimeUpdate}
              onLoadedMetadata={onLoadedMetadata}
              onClick={onTogglePlay}
              controls={false}
              id="video-player"
            />
          ) : (
            <div className="py-12 flex items-center justify-center bg-gradient-to-br from-white/5 to-transparent">
               <motion.div 
                animate={{ scale: isPlaying ? [1, 1.1, 1] : 1 }}
                transition={{ duration: 2, repeat: Infinity }}
                className="w-20 h-20 rounded-full bg-wonder-lime/10 border border-wonder-lime/20 flex items-center justify-center text-wonder-lime shadow-[0_0_50px_rgba(217,255,0,0.1)]"
               >
                 <Volume2 size={32} />
               </motion.div>
               <audio
                ref={ref as React.Ref<HTMLAudioElement>}
                src={src}
                onTimeUpdate={onTimeUpdate}
                onLoadedMetadata={onLoadedMetadata}
                id="audio-player"
              />
            </div>
          )}
          
          {!isPlaying && type === 'video' && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-[2px] transition-all">
              <button 
                onClick={onTogglePlay}
                className="w-16 h-16 rounded-full bg-wonder-lime text-black flex items-center justify-center shadow-2xl scale-110 hover:scale-125 transition-all"
              >
                <Play size={32} fill="currentColor" />
              </button>
            </div>
          )}
        </div>

        <div className="p-6">
          <div className="flex items-center gap-4 mb-4">
            <button
              className="w-12 h-12 rounded-2xl bg-white/5 hover:bg-wonder-lime hover:text-black flex items-center justify-center transition-all duration-300 group"
              onClick={onTogglePlay}
              id="media-play-toggle"
            >
              {isPlaying ? <Pause size={20} fill={isPlaying ? "currentColor" : "none"} /> : <Play size={20} className="ml-1" fill="currentColor" />}
            </button>

            <div className="flex-1">
              <div className="flex justify-between text-[10px] font-black text-white/30 uppercase tracking-tighter mb-2">
                <span>{formatTimestamp(currentTime)}</span>
                <span>{formatTimestamp(duration)}</span>
              </div>
              <div className="relative h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  className="absolute top-0 left-0 h-full bg-wonder-lime shadow-[0_0_10px_rgba(217,255,0,0.5)]"
                  initial={{ width: 0 }}
                  animate={{ width: duration > 0 ? `${(currentTime / duration) * 100}%` : '0%' }}
                  transition={{ ease: "linear" }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
);

MediaPlayer.displayName = 'MediaPlayer';

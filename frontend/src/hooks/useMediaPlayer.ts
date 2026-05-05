/**
 * Custom hook for media player control with timestamp seeking.
 */

import { useRef, useState, useCallback } from 'react';

export function useMediaPlayer() {
  const mediaRef = useRef<HTMLAudioElement | HTMLVideoElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const seekTo = useCallback((timeInSeconds: number) => {
    const player = mediaRef.current;
    if (player) {
      player.currentTime = timeInSeconds;
      player.play();
      setIsPlaying(true);
    }
  }, []);

  const togglePlay = useCallback(() => {
    const player = mediaRef.current;
    if (player) {
      if (player.paused) {
        player.play();
        setIsPlaying(true);
      } else {
        player.pause();
        setIsPlaying(false);
      }
    }
  }, []);

  const onTimeUpdate = useCallback(() => {
    if (mediaRef.current) {
      setCurrentTime(mediaRef.current.currentTime);
    }
  }, []);

  const onLoadedMetadata = useCallback(() => {
    if (mediaRef.current) {
      setDuration(mediaRef.current.duration);
    }
  }, []);

  return {
    mediaRef,
    isPlaying,
    currentTime,
    duration,
    seekTo,
    togglePlay,
    onTimeUpdate,
    onLoadedMetadata,
  };
}

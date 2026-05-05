import { describe, it, expect } from 'vitest';
import { formatTimestamp, formatDuration, formatFileSize, formatRelativeTime } from '../formatTime';

describe('formatTime utils', () => {
  it('formatTimestamp formats seconds correctly', () => {
    expect(formatTimestamp(0)).toBe('00:00');
    expect(formatTimestamp(59)).toBe('00:59');
    expect(formatTimestamp(60)).toBe('01:00');
    expect(formatTimestamp(3599)).toBe('59:59');
    expect(formatTimestamp(3600)).toBe('60:00');
  });

  it('formatDuration formats seconds correctly', () => {
    expect(formatDuration(0)).toBe('00:00');
    expect(formatDuration(59)).toBe('00:59');
    expect(formatDuration(60)).toBe('01:00');
    expect(formatDuration(3661)).toBe('1:01:01');
  });

  it('formatFileSize formats bytes correctly', () => {
    expect(formatFileSize(500)).toBe('500.0 B');
    expect(formatFileSize(1024)).toBe('1.0 KB');
    expect(formatFileSize(1048576)).toBe('1.0 MB');
    expect(formatFileSize(1073741824)).toBe('1.0 GB');
  });

  it('formatRelativeTime formats dates correctly', () => {
    const now = new Date();
    
    // Just now
    expect(formatRelativeTime(now.toISOString())).toBe('Just now');
    
    // Minutes ago
    const minutesAgo = new Date(now.getTime() - 5 * 60000);
    expect(formatRelativeTime(minutesAgo.toISOString())).toBe('5m ago');
    
    // Hours ago
    const hoursAgo = new Date(now.getTime() - 2 * 3600000);
    expect(formatRelativeTime(hoursAgo.toISOString())).toBe('2h ago');
    
    // Days ago
    const daysAgo = new Date(now.getTime() - 3 * 86400000);
    expect(formatRelativeTime(daysAgo.toISOString())).toBe('3d ago');
  });
});

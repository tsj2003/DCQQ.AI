import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { FileUpload } from '../../components/FileUpload';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';

describe('FileUpload Component', () => {
  it('renders idle state correctly', () => {
    render(<FileUpload onUploadComplete={() => {}} />);
    expect(screen.getByText(/SELECT A FILE/i)).toBeInTheDocument();
    expect(screen.getByText(/Drag & Drop/i)).toBeInTheDocument();
  });

  it.skip('handles file selection and successful upload', async () => {
    const onUploadComplete = vi.fn();
    render(<FileUpload onUploadComplete={onUploadComplete} />);

    const file = new File(['hello'], 'hello.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]');
    
    // Simulate file selection
    fireEvent.change(input!, { target: { files: [file] } });

    // Verify uploading state
    await waitFor(() => {
      expect(screen.getByText(/hello.pdf/i)).toBeInTheDocument();
    });

    // Verify success state (MSW will return success by default from handlers.ts)
    await waitFor(() => {
      expect(screen.getByText(/UPLOAD COMPLETE/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Verify callback
    await waitFor(() => {
      expect(onUploadComplete).toHaveBeenCalled();
    }, { timeout: 5000 });
  });

  it.skip('handles upload errors', async () => {
    // Override handler for this test - use wildcard pattern to match any origin
    server.use(
      http.post('*/api/documents/upload', () => {
        return HttpResponse.json({ detail: 'File too large' }, { status: 400 });
      })
    );

    render(<FileUpload onUploadComplete={() => {}} />);

    const file = new File(['too big'], 'large.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]');
    
    fireEvent.change(input!, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/UPLOAD FAILED/i)).toBeInTheDocument();
      expect(screen.getByText(/File too large/i)).toBeInTheDocument();
    });

    // Test "Try Again" button
    const tryAgainBtn = screen.getByText(/Try Again/i);
    fireEvent.click(tryAgainBtn);

    expect(screen.getByText(/SELECT A FILE/i)).toBeInTheDocument();
  });
});

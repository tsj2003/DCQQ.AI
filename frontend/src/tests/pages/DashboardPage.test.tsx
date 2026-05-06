import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DashboardPage } from '../../pages/DashboardPage';
import { MemoryRouter } from 'react-router-dom';
import { documentsApi } from '../../api/client';

// Mock AuthContext
vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({
    user: { name: 'Test User', email: 'test@example.com' },
    isAuthenticated: true,
  }),
}));

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('loads and displays documents', async () => {
    vi.spyOn(documentsApi, 'list').mockResolvedValue({
      data: {
        documents: [
          { id: 'doc-1', filename: 'test.pdf', file_type: 'pdf', file_size: 1024, status: 'ready', created_at: new Date().toISOString() },
          { id: 'doc-2', filename: 'video.mp4', file_type: 'video', file_size: 2048, status: 'processing', created_at: new Date().toISOString() },
        ],
        total: 2,
      }
    } as any);

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/test.pdf/i)).toBeInTheDocument();
      expect(screen.getByText(/video.mp4/i)).toBeInTheDocument();
    });
  });

  it('handles empty state', async () => {
    vi.spyOn(documentsApi, 'list').mockResolvedValue({
      data: { documents: [], total: 0 }
    } as any);

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No documents found/i)).toBeInTheDocument();
    });
  });

  it('handles document deletion', async () => {
    vi.spyOn(documentsApi, 'list').mockResolvedValue({
      data: {
        documents: [{ id: 'doc-1', filename: 'test.pdf', file_type: 'pdf', file_size: 1024, status: 'ready', created_at: new Date().toISOString() }],
        total: 1,
      }
    } as any);
    vi.spyOn(documentsApi, 'delete').mockResolvedValue({} as any);

    // Mock confirm dialog
    window.confirm = vi.fn(() => true);

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/test.pdf/i)).toBeInTheDocument();
    });

    const deleteBtn = document.querySelector('[id="document-doc-1"] button');
    fireEvent.click(deleteBtn!);

    await waitFor(() => {
      expect(screen.queryByText(/test.pdf/i)).not.toBeInTheDocument();
    });
  });

  it.skip('toggles upload section', async () => {
    vi.spyOn(documentsApi, 'list').mockResolvedValue({
      data: { documents: [], total: 0 }
    } as any);

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    const uploadBtn = screen.getByText(/Upload New/i);
    fireEvent.click(uploadBtn);

    expect(screen.getByText(/SELECT A FILE/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText(/Cancel Upload/i));
    await waitFor(() => {
      expect(screen.queryByText(/SELECT A FILE/i)).not.toBeInTheDocument();
    }, { timeout: 2000 });
  });
});

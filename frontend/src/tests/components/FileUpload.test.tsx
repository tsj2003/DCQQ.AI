import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { FileUpload } from '../../components/FileUpload';

describe('FileUpload Component', () => {
  it('renders idle state correctly', () => {
    render(<FileUpload onUploadComplete={() => {}} />);
    expect(screen.getByText(/SELECT A FILE/i)).toBeInTheDocument();
    expect(screen.getByText(/Drag & Drop/i)).toBeInTheDocument();
  });
});

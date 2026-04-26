import { render, screen, waitFor } from '@testing-library/react';
import NewsSection from '../components/NewsSection';
import * as api from '../api';

// Mock the API module
jest.mock('../api');

describe('NewsSection Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading skeletons initially', () => {
    api.getNews.mockResolvedValueOnce({ data: { news: [] } });
    render(<NewsSection />);
    expect(screen.getByTestId('news-section')).toBeInTheDocument();
    // Skeleton cards should be present while loading
  });

  it('fetches and displays news articles', async () => {
    const mockNews = [
      { news_id: '1', title: 'Test News 1', summary: 'Summary 1', category: 'finance', date: '2026-04-26' },
      { news_id: '2', title: 'Test News 2', summary: 'Summary 2', category: 'banking', date: '2026-04-25' }
    ];
    
    api.getNews.mockResolvedValueOnce({ 
      data: { news: mockNews, is_live: true, fetched_at: '2026-04-26T10:00:00Z', total_pages: 1 } 
    });

    render(<NewsSection />);

    await waitFor(() => {
      expect(screen.getByText('Test News 1')).toBeInTheDocument();
      expect(screen.getByText('Test News 2')).toBeInTheDocument();
    });
  });

  it('shows live badge when news is live', async () => {
    api.getNews.mockResolvedValueOnce({ 
      data: { news: [], is_live: true, fetched_at: new Date().toISOString() } 
    });

    render(<NewsSection />);

    await waitFor(() => {
      expect(screen.getByText(/Live/i)).toBeInTheDocument();
    });
  });
});

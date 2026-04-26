import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Calendar, ExternalLink, Radio } from 'lucide-react';
import { getNews } from '../api';

const MEDIA_MAP = {
  dubai_skyline_news_1: 'https://images.unsplash.com/photo-1726533765275-a69cfd7f9897?w=600&q=80',
  dubai_skyline_news_2: 'https://images.unsplash.com/photo-1768069794857-9306ac167c6e?w=600&q=80',
  credit_card_mockup: 'https://images.unsplash.com/photo-1687720106084-d6e235ad226c?w=600&q=80',
  arabic_business: 'https://images.unsplash.com/photo-1720722023471-61abfe6f36d1?w=600&q=80',
  investment_chart: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600&q=80',
  lending_finance: 'https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=600&q=80',
};

const CATEGORY_COLORS = {
  monetary_policy: 'bg-blue-50 text-blue-700',
  real_estate: 'bg-emerald-50 text-emerald-700',
  investment: 'bg-purple-50 text-purple-700',
  banking: 'bg-amber-50 text-amber-700',
  insurance: 'bg-teal-50 text-teal-700',
  lending: 'bg-rose-50 text-rose-700',
};

function SkeletonCard() {
  return (
    <div className="bg-bg border border-border rounded-xl overflow-hidden animate-pulse">
      <div className="h-40 bg-surface" />
      <div className="p-5 space-y-3">
        <div className="h-3 bg-surface rounded w-1/3" />
        <div className="h-4 bg-surface rounded w-full" />
        <div className="h-4 bg-surface rounded w-4/5" />
        <div className="h-3 bg-surface rounded w-full" />
        <div className="h-3 bg-surface rounded w-3/4" />
        <div className="h-10 bg-surface rounded-lg" />
      </div>
    </div>
  );
}

export default function NewsSection() {
  const [news, setNews] = useState([]);
  const [isLive, setIsLive] = useState(false);
  const [fetchedAt, setFetchedAt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    loadNews();
  }, []);

  const loadNews = async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await getNews();
      setNews(res.data.news);
      setIsLive(res.data.is_live || false);
      setFetchedAt(res.data.fetched_at || null);
    } catch (err) {
      console.error('Failed to load news:', err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const timeAgo = (isoString) => {
    if (!isoString) return null;
    const diff = Math.floor((Date.now() - new Date(isoString)) / 60000);
    if (diff < 2) return 'just now';
    if (diff < 60) return `${diff}m ago`;
    const h = Math.floor(diff / 60);
    return `${h}h ago`;
  };

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-12" data-testid="news-section">
      <div className="mb-10 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <span className="text-xs tracking-[0.2em] uppercase font-semibold text-text-secondary">
            Stay Informed
          </span>
          <h2 className="font-heading text-2xl sm:text-3xl lg:text-4xl tracking-tight font-bold text-primary mt-2">
            Financial News & Insights
          </h2>
          <p className="text-text-secondary mt-2 max-w-2xl">
            Latest updates from the UAE financial landscape with actionable takeaways.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {isLive && (
            <span className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-full text-xs font-semibold text-emerald-700">
              <Radio className="w-3 h-3" />
              Live
              {fetchedAt && <span className="font-normal text-emerald-600">· {timeAgo(fetchedAt)}</span>}
            </span>
          )}
          <button
            onClick={loadNews}
            disabled={loading}
            className="text-xs font-semibold text-primary hover:underline disabled:opacity-40"
          >
            {loading ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-6">
          Could not load news. <button onClick={loadNews} className="underline font-semibold">Try again</button>
        </p>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="news-grid">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
          : news.map((item, i) => (
              <motion.article
                key={item.news_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                className="bg-bg border border-border rounded-xl overflow-hidden hover:-translate-y-1 hover:shadow-lg transition-all duration-200 group flex flex-col"
                data-testid={`news-card-${item.news_id}`}
              >
                <div className="relative h-40 overflow-hidden shrink-0">
                  <img
                    src={MEDIA_MAP[item.image_key] || MEDIA_MAP.dubai_skyline_news_1}
                    alt={item.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                  <span className={`absolute bottom-3 left-3 px-2.5 py-1 rounded text-xs font-semibold ${CATEGORY_COLORS[item.category] || 'bg-gray-50 text-gray-700'}`}>
                    {(item.category || '').replace('_', ' ')}
                  </span>
                </div>

                <div className="p-5 flex flex-col flex-1">
                  <div className="flex items-center gap-3 text-xs text-text-secondary mb-3">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(item.date).toLocaleDateString('en-AE', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </span>
                    <span className="truncate max-w-[120px]">{item.source}</span>
                  </div>

                  <h3 className="font-heading font-bold text-primary text-base leading-tight mb-2">
                    {item.title}
                  </h3>
                  <p className="text-sm text-text-secondary mb-3 line-clamp-3 flex-1">
                    {item.summary}
                  </p>

                  {item.impact && (
                    <div className="p-3 bg-accent/5 border border-accent/10 rounded-lg mb-3">
                      <p className="text-xs font-semibold text-accent flex items-center gap-1.5">
                        <TrendingUp className="w-3 h-3" />
                        Insight
                      </p>
                      <p className="text-xs text-text-secondary mt-1">{item.impact}</p>
                    </div>
                  )}

                  {item.url && (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs font-semibold text-primary hover:underline mt-auto"
                    >
                      Read full article <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </motion.article>
            ))}
      </div>
    </div>
  );
}

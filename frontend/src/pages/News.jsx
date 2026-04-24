import { useEffect, useState } from "react";
import NewsCard from "../components/NewsCard";
import { sampleNews } from "../data/newsData";

function News() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await fetch("http://localhost:3000/news");
        if (!response.ok) {
          throw new Error("Failed to fetch news");
        }
        const data = await response.json();
        setArticles(data);
      } catch (err) {
        setError("Unable to load live news. Showing curated UAE news.");
        setArticles(sampleNews);
      } finally {
        setLoading(false);
      }
    };
    fetchNews();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-6 md:px-10">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-4 mb-8">
          <div>
            <h1 className="text-4xl font-bold">UAE Financial News</h1>
            <p className="text-gray-600 mt-2">Latest UAE banking, insurance, real estate, and investment headlines.</p>
          </div>
          <div className="text-right text-sm text-gray-500">
            <p>Updated: {new Date().toLocaleDateString()}</p>
            <p className="mt-1">Source: Local UAE news and curated feed</p>
          </div>
        </div>

        {loading && <p className="text-center text-gray-700">Loading news...</p>}
        {error && <p className="text-center text-orange-600 mb-6">{error}</p>}

        <div className="grid gap-6 md:grid-cols-2">
          {articles.map((article) => (
            <NewsCard key={article.id} article={article} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default News;

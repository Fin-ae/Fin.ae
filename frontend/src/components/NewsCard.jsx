function NewsCard({ article }) {
  return (
    <article className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition">
      <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4">
        <div className="min-w-0">
          <p className="text-sm text-blue-600 uppercase tracking-[0.2em] font-semibold">{article.category.replace(/_/g, " ")}</p>
          <h3 className="text-xl font-bold mt-2">{article.title}</h3>
          <p className="text-gray-600 mt-3 line-clamp-3">{article.summary}</p>
        </div>
        <div className="text-right text-sm text-gray-500 whitespace-nowrap">
          <p>{article.source}</p>
          <p>{article.date}</p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {article.keywords?.map((keyword) => (
          <span key={keyword} className="bg-slate-100 text-slate-700 text-xs px-2 py-1 rounded-full">
            {keyword}
          </span>
        ))}
      </div>
      <div className="mt-4 flex items-center justify-between">
        <a href={article.url} target="_blank" rel="noreferrer" className="text-blue-600 underline">
          Read more
        </a>
        <span className="text-xs text-green-700 bg-green-100 px-2 py-1 rounded-full">
          Relevance {Math.round(article.relevance_score * 100)}%
        </span>
      </div>
    </article>
  );
}

export default NewsCard;

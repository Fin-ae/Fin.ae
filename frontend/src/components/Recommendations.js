import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Star, Check, Plus, ArrowRight, Loader2, Filter } from 'lucide-react';
import { getPolicies, recommendPolicies } from '../api';

const CATEGORIES = [
  { key: '', label: 'All Products' },
  { key: 'insurance', label: 'Insurance' },
  { key: 'loan', label: 'Loans' },
  { key: 'credit_card', label: 'Credit Cards' },
  { key: 'investment', label: 'Investments' },
  { key: 'bank_account', label: 'Bank Accounts' },
];

export default function Recommendations({ sessionId, userProfile, recommendations, onRecommendationsLoaded, onCompare }) {
  const [policies, setPolicies] = useState([]);
  const [activeCategory, setActiveCategory] = useState('');
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState('');
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  const [hasRecommended, setHasRecommended] = useState(false);

  useEffect(() => {
    loadPolicies();
  }, [activeCategory]);

  useEffect(() => {
    if (userProfile && !hasRecommended) {
      loadRecommendations();
    }
  }, [userProfile]);

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const params = {};
      if (activeCategory) params.category = activeCategory;
      const res = await getPolicies(params);
      setPolicies(res.data.policies);
    } catch (err) {
      console.error('Failed to load policies:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      const res = await recommendPolicies(sessionId, activeCategory || undefined);
      if (res.data.recommendations?.length) {
        setPolicies(res.data.recommendations);
        setExplanation(res.data.explanation || '');
        setHasRecommended(true);
        onRecommendationsLoaded(res.data);
      }
    } catch (err) {
      console.error('Recommendations error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleCompare = (policyId) => {
    setSelectedForCompare(prev => {
      if (prev.includes(policyId)) return prev.filter(id => id !== policyId);
      if (prev.length >= 4) return prev;
      return [...prev, policyId];
    });
  };

  const getCategoryColor = (cat) => {
    const colors = {
      insurance: 'bg-blue-50 text-blue-700 border-blue-200',
      loan: 'bg-amber-50 text-amber-700 border-amber-200',
      credit_card: 'bg-purple-50 text-purple-700 border-purple-200',
      investment: 'bg-green-50 text-green-700 border-green-200',
      bank_account: 'bg-teal-50 text-teal-700 border-teal-200',
    };
    return colors[cat] || 'bg-gray-50 text-gray-700 border-gray-200';
  };

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-12" data-testid="recommendations-section">
      <div className="mb-10">
        <span className="text-xs tracking-[0.2em] uppercase font-semibold text-text-secondary">
          Financial Products
        </span>
        <h2 className="font-heading text-2xl sm:text-3xl lg:text-4xl tracking-tight font-bold text-primary mt-2">
          {userProfile ? 'Recommended for you' : 'Explore UAE financial products'}
        </h2>
        {userProfile && (
          <p className="text-text-secondary mt-2 max-w-2xl">
            Based on your profile, we've found the best matching products from leading UAE institutions.
          </p>
        )}
      </div>

      {/* Category filters */}
      <div className="flex flex-wrap gap-2 mb-8" data-testid="category-filters">
        {CATEGORIES.map(cat => (
          <button
            key={cat.key}
            data-testid={`filter-${cat.key || 'all'}`}
            onClick={() => setActiveCategory(cat.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 border ${
              activeCategory === cat.key
                ? 'bg-primary text-white border-primary'
                : 'bg-surface text-text-secondary border-border hover:border-primary/30 hover:text-primary'
            }`}
          >
            {cat.label}
          </button>
        ))}
        {userProfile && (
          <button
            data-testid="ai-recommend-btn"
            onClick={loadRecommendations}
            disabled={loading}
            className="ml-auto px-4 py-2 rounded-lg text-sm font-semibold bg-accent text-white hover:bg-accent-hover transition-all duration-200 flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Star className="w-4 h-4" />}
            AI Recommend
          </button>
        )}
      </div>

      {/* AI Explanation */}
      {explanation && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 p-5 bg-primary/5 border border-primary/10 rounded-xl"
          data-testid="ai-explanation"
        >
          <h4 className="font-heading font-semibold text-primary mb-2 flex items-center gap-2">
            <Star className="w-4 h-4 text-accent" /> Fin-ae's Analysis
          </h4>
          <div className="text-sm text-text-secondary leading-relaxed whitespace-pre-line">
            {explanation}
          </div>
        </motion.div>
      )}

      {/* Compare bar */}
      {selectedForCompare.length >= 2 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 bg-accent/10 border border-accent/30 rounded-xl flex items-center justify-between"
          data-testid="compare-bar"
        >
          <p className="text-sm font-medium text-text-primary">
            {selectedForCompare.length} products selected for comparison
          </p>
          <button
            data-testid="compare-btn"
            onClick={() => onCompare(selectedForCompare)}
            className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary-hover transition-all flex items-center gap-2"
          >
            Compare Now <ArrowRight className="w-4 h-4" />
          </button>
        </motion.div>
      )}

      {/* Policy Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="policy-grid">
          {policies.map((policy, i) => (
            <motion.div
              key={policy.policy_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="relative bg-surface border border-border rounded-xl p-5 hover:-translate-y-1 hover:shadow-lg transition-all duration-200 group"
              data-testid={`policy-card-${policy.policy_id}`}
            >
              {/* Compare checkbox */}
              <button
                data-testid={`compare-toggle-${policy.policy_id}`}
                onClick={() => toggleCompare(policy.policy_id)}
                className={`absolute top-4 right-4 w-6 h-6 rounded border-2 flex items-center justify-center transition-all ${
                  selectedForCompare.includes(policy.policy_id)
                    ? 'bg-primary border-primary text-white'
                    : 'border-border hover:border-primary/40'
                }`}
              >
                {selectedForCompare.includes(policy.policy_id) && <Check className="w-3 h-3" />}
              </button>

              {/* Category badge */}
              <span className={`inline-flex px-2.5 py-1 rounded text-xs font-semibold border ${getCategoryColor(policy.category)}`}>
                {policy.category.replace('_', ' ')}
              </span>

              {/* Rating */}
              <div className="flex items-center gap-1 mt-3 mb-2">
                <Star className="w-3.5 h-3.5 text-accent fill-accent" />
                <span className="text-sm font-semibold text-text-primary">{policy.rating}</span>
              </div>

              <h3 className="font-heading font-bold text-lg text-primary mb-1 pr-8 leading-tight">
                {policy.name}
              </h3>
              <p className="text-xs text-text-secondary mb-3">{policy.provider}</p>
              <p className="text-sm text-text-secondary mb-4 line-clamp-2">{policy.description}</p>

              {/* Key features */}
              <div className="space-y-1.5 mb-4">
                {policy.benefits?.slice(0, 3).map((b, j) => (
                  <div key={j} className="flex items-start gap-2">
                    <Check className="w-3.5 h-3.5 text-accent mt-0.5 flex-shrink-0" />
                    <span className="text-xs text-text-secondary">{b}</span>
                  </div>
                ))}
              </div>

              {/* Pricing */}
              <div className="flex items-baseline gap-1 mb-4">
                {policy.annual_cost != null && policy.annual_cost > 0 ? (
                  <>
                    <span className="text-lg font-bold text-primary">AED {policy.annual_cost.toLocaleString()}</span>
                    <span className="text-xs text-text-secondary">/year</span>
                  </>
                ) : policy.features?.interest_rate ? (
                  <>
                    <span className="text-lg font-bold text-primary">{policy.features.interest_rate}</span>
                    <span className="text-xs text-text-secondary">rate</span>
                  </>
                ) : policy.features?.expected_return ? (
                  <>
                    <span className="text-lg font-bold text-primary">{policy.features.expected_return}</span>
                    <span className="text-xs text-text-secondary">return</span>
                  </>
                ) : (
                  <span className="text-lg font-bold text-accent">Free</span>
                )}
              </div>

              {/* Salary req */}
              <p className="text-xs text-text-secondary">
                Min. salary: AED {policy.min_salary?.toLocaleString()}
                {policy.sharia_compliant && (
                  <span className="ml-2 text-accent font-semibold">Sharia Compliant</span>
                )}
              </p>
            </motion.div>
          ))}
        </div>
      )}

      {!loading && policies.length === 0 && (
        <div className="text-center py-20" data-testid="no-policies-msg">
          <Filter className="w-12 h-12 text-border mx-auto mb-4" />
          <p className="text-text-secondary">No products found. Try adjusting your filters.</p>
        </div>
      )}
    </div>
  );
}

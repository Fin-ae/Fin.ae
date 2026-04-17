import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Check, X, Star, ArrowRight } from 'lucide-react';
import { comparePolicies } from '../api';

export default function PolicyComparison({ compareIds }) {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadComparison();
  }, [compareIds]);

  const loadComparison = async () => {
    try {
      setLoading(true);
      const res = await comparePolicies(compareIds);
      setPolicies(res.data.policies);
    } catch (err) {
      console.error('Comparison error:', err);
    } finally {
      setLoading(false);
    }
  };

  const allFeatureKeys = [...new Set(policies.flatMap(p => Object.keys(p.features || {})))];

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 md:px-12 flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-12" data-testid="policy-comparison-section">
      <div className="mb-10">
        <span className="text-xs tracking-[0.2em] uppercase font-semibold text-text-secondary">
          Side by Side
        </span>
        <h2 className="font-heading text-2xl sm:text-3xl lg:text-4xl tracking-tight font-bold text-primary mt-2">
          Policy Comparison
        </h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse" data-testid="comparison-table">
          <thead>
            <tr>
              <th className="text-left p-4 bg-bg border-b border-r border-border font-heading font-semibold text-sm text-text-secondary w-48">
                Feature
              </th>
              {policies.map(p => (
                <th key={p.policy_id} className="p-4 bg-bg border-b border-r border-border text-left min-w-[220px]">
                  <div className="space-y-1">
                    <p className="font-heading font-bold text-primary text-sm">{p.name}</p>
                    <p className="text-xs text-text-secondary">{p.provider}</p>
                    <div className="flex items-center gap-1">
                      <Star className="w-3 h-3 text-accent fill-accent" />
                      <span className="text-xs font-semibold">{p.rating}</span>
                    </div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="p-4 border-b border-r border-border text-sm font-medium text-text-secondary">Category</td>
              {policies.map(p => (
                <td key={p.policy_id} className="p-4 border-b border-r border-border text-sm capitalize">
                  {p.category.replace('_', ' ')}
                </td>
              ))}
            </tr>
            <tr>
              <td className="p-4 border-b border-r border-border text-sm font-medium text-text-secondary">Risk Level</td>
              {policies.map(p => (
                <td key={p.policy_id} className="p-4 border-b border-r border-border text-sm capitalize">
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                    p.risk_level === 'low' ? 'bg-green-50 text-green-700' :
                    p.risk_level === 'medium' ? 'bg-amber-50 text-amber-700' :
                    'bg-red-50 text-red-700'
                  }`}>
                    {p.risk_level}
                  </span>
                </td>
              ))}
            </tr>
            <tr>
              <td className="p-4 border-b border-r border-border text-sm font-medium text-text-secondary">Annual Cost</td>
              {policies.map(p => (
                <td key={p.policy_id} className="p-4 border-b border-r border-border text-sm font-semibold text-primary">
                  {p.annual_cost ? `AED ${p.annual_cost.toLocaleString()}` : 'N/A'}
                </td>
              ))}
            </tr>
            <tr>
              <td className="p-4 border-b border-r border-border text-sm font-medium text-text-secondary">Min. Salary</td>
              {policies.map(p => (
                <td key={p.policy_id} className="p-4 border-b border-r border-border text-sm">
                  AED {p.min_salary?.toLocaleString()}
                </td>
              ))}
            </tr>
            <tr>
              <td className="p-4 border-b border-r border-border text-sm font-medium text-text-secondary">Sharia Compliant</td>
              {policies.map(p => (
                <td key={p.policy_id} className="p-4 border-b border-r border-border text-sm">
                  {p.sharia_compliant ? (
                    <Check className="w-5 h-5 text-accent" />
                  ) : (
                    <X className="w-5 h-5 text-border" />
                  )}
                </td>
              ))}
            </tr>
            <tr>
              <td className="p-4 border-b border-r border-border text-sm font-medium text-text-secondary">Benefits</td>
              {policies.map(p => (
                <td key={p.policy_id} className="p-4 border-b border-r border-border">
                  <ul className="space-y-1">
                    {p.benefits?.map((b, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs text-text-secondary">
                        <Check className="w-3 h-3 text-accent mt-0.5 flex-shrink-0" />
                        {b}
                      </li>
                    ))}
                  </ul>
                </td>
              ))}
            </tr>
            {allFeatureKeys.map(fk => (
              <tr key={fk}>
                <td className="p-4 border-b border-r border-border text-sm font-medium text-text-secondary capitalize">
                  {fk.replace(/_/g, ' ')}
                </td>
                {policies.map(p => (
                  <td key={p.policy_id} className="p-4 border-b border-r border-border text-sm">
                    {p.features?.[fk] || '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

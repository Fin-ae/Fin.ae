import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, Clock, CheckCircle, AlertCircle, Loader2, Plus, LogIn } from 'lucide-react';
import { getApplications, createApplication, getPolicies } from '../api';
import { useAuth } from '../AuthContext';

const STATUS_MAP = {
  submitted: { label: 'Submitted', icon: FileText, color: 'text-blue-600 bg-blue-50' },
  under_review: { label: 'Under Review', icon: Clock, color: 'text-amber-600 bg-amber-50' },
  approved: { label: 'Approved', icon: CheckCircle, color: 'text-green-600 bg-green-50' },
  rejected: { label: 'Rejected', icon: AlertCircle, color: 'text-red-600 bg-red-50' },
};

export default function ApplicationTracker({ sessionId, userProfile, onOpenAuth }) {
  const { user } = useAuth();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [policies, setPolicies] = useState([]);
  const [selectedPolicy, setSelectedPolicy] = useState('');
  const [applying, setApplying] = useState(false);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    if (user) {
      loadApplications();
    } else {
      setApplications([]);
    }
  }, [user]);

  const loadApplications = async () => {
    try {
      setLoading(true);
      const res = await getApplications();
      setApplications(res.data.applications);
    } catch (err) {
      console.error('Failed to load applications:', err);
    } finally {
      setLoading(false);
    }
  };

  const openApplyModal = async () => {
    if (!user) {
      onOpenAuth?.();
      return;
    }
    setShowApplyModal(true);
    try {
      const res = await getPolicies({});
      setPolicies(res.data.policies);
    } catch (e) {}
    if (userProfile) {
      setFormData({
        name: userProfile.name || '',
        age: userProfile.age || '',
        nationality: userProfile.nationality || '',
        monthly_salary: userProfile.monthly_salary || '',
        employment_type: userProfile.employment_type || '',
        email: user?.email || '',
        phone: '',
      });
    } else {
      setFormData({ email: user?.email || '' });
    }
  };

  const handleApply = async () => {
    if (!selectedPolicy) return;
    try {
      setApplying(true);
      await createApplication(selectedPolicy, formData, sessionId);
      setShowApplyModal(false);
      setSelectedPolicy('');
      loadApplications();
    } catch (err) {
      console.error('Application error:', err);
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-12" data-testid="application-tracker-section">
      <div className="flex items-start justify-between mb-10">
        <div>
          <span className="text-xs tracking-[0.2em] uppercase font-semibold text-text-secondary">
            Track Progress
          </span>
          <h2 className="font-heading text-2xl sm:text-3xl lg:text-4xl tracking-tight font-bold text-primary mt-2">
            Your Applications
          </h2>
          {user && (
            <p className="text-sm text-text-secondary mt-1">
              Signed in as <span className="font-semibold text-primary">{user.name}</span>
            </p>
          )}
        </div>
        <button
          data-testid="new-application-btn"
          onClick={openApplyModal}
          className="flex items-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary-hover transition-all"
        >
          <Plus className="w-4 h-4" />
          Apply Now
        </button>
      </div>

      {!user ? (
        <div className="text-center py-16 border border-dashed border-border rounded-xl">
          <LogIn className="w-12 h-12 text-border mx-auto mb-4" />
          <p className="text-text-secondary mb-2 font-semibold">Sign in to track your applications</p>
          <p className="text-sm text-text-secondary mb-6">
            Create an account to submit applications and monitor their status across sessions.
          </p>
          <button
            onClick={onOpenAuth}
            className="px-6 py-2.5 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary-hover transition-all"
          >
            Sign In / Register
          </button>
        </div>
      ) : loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 text-primary animate-spin" />
        </div>
      ) : applications.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-border rounded-xl" data-testid="no-applications-msg">
          <FileText className="w-12 h-12 text-border mx-auto mb-4" />
          <p className="text-text-secondary mb-2">No applications yet</p>
          <p className="text-sm text-text-secondary">
            Start by chatting with Fin-ae to get personalized recommendations, then apply.
          </p>
        </div>
      ) : (
        <div className="space-y-4" data-testid="applications-list">
          {applications.map((app, i) => {
            const status = STATUS_MAP[app.status] || STATUS_MAP.submitted;
            const StatusIcon = status.icon;
            return (
              <motion.div
                key={app.application_number}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="bg-surface border border-border rounded-xl p-5 hover:shadow-md transition-all"
                data-testid={`application-card-${app.application_number}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-heading font-bold text-primary">{app.policy_name}</p>
                    <p className="text-xs text-text-secondary mt-0.5">{app.provider}</p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className="text-xs font-mono bg-primary/5 text-primary border border-primary/20 px-2 py-0.5 rounded">
                        {app.application_number}
                      </span>
                      <span className="text-xs text-text-secondary">
                        Applied {new Date(app.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${status.color}`}>
                    <StatusIcon className="w-3.5 h-3.5" />
                    {status.label}
                  </span>
                </div>

                {app.status_history?.length > 1 && (
                  <div className="mt-4 ml-2 border-l-2 border-border pl-4 space-y-3">
                    {app.status_history.map((sh, j) => (
                      <div key={j} className="relative">
                        <div className={`absolute -left-[21px] top-0.5 w-3 h-3 rounded-full border-2 ${
                          j === app.status_history.length - 1
                            ? 'bg-primary border-primary'
                            : 'bg-accent border-accent'
                        }`} />
                        <p className="text-xs text-text-secondary">
                          <span className="font-semibold capitalize">{sh.status.replace('_', ' ')}</span>
                          <span className="ml-2">{new Date(sh.timestamp).toLocaleString()}</span>
                        </p>
                        {sh.note && (
                          <p className="text-xs text-text-secondary/70 mt-0.5">{sh.note}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Apply Modal */}
      {showApplyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm" data-testid="apply-modal">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md bg-surface rounded-2xl shadow-2xl border border-border overflow-hidden"
          >
            <div className="px-6 py-4 border-b border-border bg-primary text-white">
              <h3 className="font-heading font-bold">Apply for a Product</h3>
            </div>
            <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
              <div>
                <label className="text-xs font-semibold text-text-secondary block mb-1.5">Select Product</label>
                <select
                  data-testid="policy-select"
                  value={selectedPolicy}
                  onChange={(e) => setSelectedPolicy(e.target.value)}
                  className="w-full px-3 py-2.5 bg-bg border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                >
                  <option value="">Choose a product...</option>
                  {policies.map((p) => (
                    <option key={p.policy_id} value={p.policy_id}>
                      {p.name} - {p.provider}
                    </option>
                  ))}
                </select>
              </div>
              {['name', 'email', 'phone', 'age', 'nationality', 'monthly_salary', 'employment_type'].map((field) => (
                <div key={field}>
                  <label className="text-xs font-semibold text-text-secondary block mb-1.5 capitalize">
                    {field.replace('_', ' ')}
                  </label>
                  <input
                    data-testid={`apply-field-${field}`}
                    type={
                      field === 'age' || field === 'monthly_salary'
                        ? 'number'
                        : field === 'email'
                        ? 'email'
                        : 'text'
                    }
                    value={formData[field] || ''}
                    onChange={(e) => setFormData((prev) => ({ ...prev, [field]: e.target.value }))}
                    className="w-full px-3 py-2.5 bg-bg border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    placeholder={`Enter your ${field.replace('_', ' ')}`}
                  />
                </div>
              ))}
            </div>
            <div className="px-6 py-4 border-t border-border flex justify-end gap-3">
              <button
                data-testid="cancel-apply-btn"
                onClick={() => setShowApplyModal(false)}
                className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
              >
                Cancel
              </button>
              <button
                data-testid="submit-application-btn"
                onClick={handleApply}
                disabled={!selectedPolicy || applying}
                className="px-5 py-2 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary-hover disabled:opacity-40 transition-all flex items-center gap-2"
              >
                {applying && <Loader2 className="w-4 h-4 animate-spin" />}
                Submit Application
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}

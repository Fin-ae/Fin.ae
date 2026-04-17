import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { X, Send, Sparkles, UserCircle, CheckCircle, ChevronRight, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { chatMessage, extractProfile, recommendPolicies, createApplication, agentAction } from '../api';

// Renders markdown with design-system styling
function MdContent({ children }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0 text-sm leading-relaxed">{children}</p>,
        strong: ({ children }) => <strong className="font-semibold text-primary">{children}</strong>,
        em: ({ children }) => <em className="italic">{children}</em>,
        ul: ({ children }) => <ul className="mt-1 mb-2 space-y-1 list-none">{children}</ul>,
        ol: ({ children }) => <ol className="mt-1 mb-2 space-y-1 list-decimal list-inside">{children}</ol>,
        li: ({ children }) => (
          <li className="text-sm flex items-start gap-1.5">
            <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-accent flex-shrink-0" />
            <span>{children}</span>
          </li>
        ),
        h1: ({ children }) => <h1 className="font-heading font-bold text-base text-primary mb-1">{children}</h1>,
        h2: ({ children }) => <h2 className="font-heading font-semibold text-sm text-primary mb-1 mt-2">{children}</h2>,
        h3: ({ children }) => <h3 className="font-semibold text-sm text-primary mb-1 mt-2">{children}</h3>,
        code: ({ children }) => (
          <code className="bg-accent/10 text-accent px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
        ),
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-accent pl-3 my-2 text-text-secondary italic text-sm">
            {children}
          </blockquote>
        ),
      }}
    >
      {children}
    </ReactMarkdown>
  );
}

export default function AvatarChat({ sessionId, onClose, onProfileExtracted, onGetRecommendations }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello! I'm **Fin-ae**, your AI financial assistant. I'm here to help you find the best financial products in the UAE.\n\nWhat are you looking for today? **Insurance**, a **personal loan**, **credit card**, **investment options**, or a **bank account**?",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [profileExtracted, setProfileExtracted] = useState(false);
  const [profile, setProfile] = useState(null);
  const [messageCount, setMessageCount] = useState(0);
  const [chatPhase, setChatPhase] = useState('gathering'); // 'gathering' | 'policy_selection' | 'applied'
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const fetchAndShowPolicies = async (currentProfile) => {
    try {
      const recRes = await recommendPolicies(sessionId);
      const recs = recRes.data;
      if (recs.recommendations && recs.recommendations.length > 0) {
        setChatPhase('policy_selection');
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            type: 'policy_selection',
            content: recs.explanation,
            policies: recs.recommendations.slice(0, 4),
          },
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: "I couldn't find policies matching your profile right now. You can explore all available options in the **Recommendations** section below.",
          },
        ]);
      }
    } catch (e) {
      // Silent — user can browse from the recommendations section
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setLoading(true);
    const newCount = messageCount + 1;
    setMessageCount(newCount);

    try {
      const res = await chatMessage(sessionId, text);
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);

      // Auto-extract profile after 3+ user messages
      if (newCount >= 3 && !profileExtracted) {
        try {
          const profileRes = await extractProfile(sessionId);
          const p = profileRes.data.profile;
          if (p && p.completeness_score >= 40) {
            setProfile(p);
            setProfileExtracted(true);
            onProfileExtracted(p);
            await fetchAndShowPolicies(p);
          }
        } catch (e) {
          // Profile extraction is optional
        }
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: "I apologize, I'm having trouble connecting. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyPolicy = async (policy) => {
    if (!profile || loading) return;
    setLoading(true);
    try {
      const appRes = await createApplication(sessionId, policy.policy_id, profile);
      const app = appRes.data.application;
      // Let the agent generate the confirmation message
      const actionRes = await agentAction(sessionId, 'application_submitted', {
        application_id: app.application_id,
        policy_name: policy.name,
        provider: policy.provider,
      });
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          type: 'applied',
          content: actionRes.data.response,
          application: app,
        },
      ]);
      setChatPhase('applied');
    } catch (e) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: "Sorry, there was an issue submitting your application. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleGetRecommendations = async () => {
    setLoading(true);
    try {
      if (!profileExtracted) {
        const profileRes = await extractProfile(sessionId);
        const p = profileRes.data.profile;
        setProfile(p);
        setProfileExtracted(true);
        onProfileExtracted(p);
        await fetchAndShowPolicies(p);
      } else {
        await fetchAndShowPolicies(profile);
      }
    } catch (e) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: "Let me gather a bit more information first. Could you tell me about your **income** and what type of financial product you're interested in?",
        },
      ]);
    } finally {
      setLoading(false);
    }
    onGetRecommendations();
  };

  const renderMessage = (msg, i) => {
    const isUser = msg.role === 'user';

    if (msg.type === 'policy_selection') {
      return (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="flex gap-3"
        >
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-1">
            <Sparkles className="w-4 h-4 text-primary" />
          </div>
          <div className="flex-1 max-w-[90%]">
            {/* AI explanation */}
            <div className="bg-bg border border-border rounded-xl rounded-tl-sm px-4 py-3 mb-3 text-text-primary">
              <MdContent>{msg.content}</MdContent>
            </div>
            {/* Policy cards */}
            <div className="space-y-2">
              {msg.policies.map(policy => (
                <div
                  key={policy.policy_id}
                  className="bg-surface border border-border rounded-xl p-3 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-xs text-primary leading-tight">{policy.name}</p>
                      <p className="text-xs text-text-secondary mt-0.5">{policy.provider}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      {policy.monthly_cost ? (
                        <p className="text-xs font-bold text-accent">AED {policy.monthly_cost}/mo</p>
                      ) : policy.annual_cost ? (
                        <p className="text-xs font-bold text-accent">AED {policy.annual_cost}/yr</p>
                      ) : null}
                      <p className="text-xs text-text-secondary mt-0.5">★ {policy.rating}</p>
                    </div>
                  </div>
                  {policy.benefits && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {policy.benefits.slice(0, 3).map((b, idx) => (
                        <span
                          key={idx}
                          className="text-xs bg-primary/8 text-primary px-2 py-0.5 rounded-full"
                        >
                          {b}
                        </span>
                      ))}
                    </div>
                  )}
                  <button
                    onClick={() => handleApplyPolicy(policy)}
                    disabled={loading || chatPhase === 'applied'}
                    className="w-full text-xs font-semibold bg-primary hover:bg-primary-hover disabled:opacity-40 text-white rounded-lg py-2 transition-colors flex items-center justify-center gap-1"
                  >
                    <FileText className="w-3 h-3" />
                    Apply Now
                    <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      );
    }

    if (msg.type === 'applied') {
      return (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="flex gap-3"
        >
          <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-1">
            <CheckCircle className="w-4 h-4 text-green-600" />
          </div>
          <div className="max-w-[80%] bg-green-50 border border-green-200 rounded-xl rounded-tl-sm px-4 py-3 text-text-primary">
            <MdContent>{msg.content}</MdContent>
          </div>
        </motion.div>
      );
    }

    // Default text message
    return (
      <motion.div
        key={i}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
      >
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0">
            <UserCircle className="w-4 h-4 text-accent" />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-4 h-4 text-primary" />
          </div>
        )}
        <div
          className={`max-w-[80%] px-4 py-3 rounded-xl ${
            isUser
              ? 'bg-primary text-white rounded-tr-sm text-sm leading-relaxed'
              : 'bg-bg border border-border text-text-primary rounded-tl-sm'
          }`}
        >
          {isUser ? (
            msg.content
          ) : (
            <MdContent>{msg.content}</MdContent>
          )}
        </div>
      </motion.div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/30 backdrop-blur-sm"
      data-testid="avatar-chat-modal"
    >
      <motion.div
        initial={{ y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 40, opacity: 0 }}
        className="w-full max-w-lg bg-surface rounded-2xl shadow-2xl border border-border overflow-hidden flex flex-col"
        style={{ maxHeight: '85vh' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border bg-primary text-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
              <svg viewBox="0 0 40 40" className="w-7 h-7">
                <circle cx="20" cy="14" r="8" fill="#D4AF37" />
                <ellipse cx="20" cy="32" rx="12" ry="8" fill="#D4AF37" />
                <circle cx="17" cy="13" r="1.5" fill="#0A3224" />
                <circle cx="23" cy="13" r="1.5" fill="#0A3224" />
                <path d="M17 17 Q20 20 23 17" stroke="#0A3224" strokeWidth="1" fill="none" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <h3 className="font-heading font-bold text-sm">Fin-ae</h3>
              <p className="text-xs text-white/60">
                {chatPhase === 'gathering' && 'Gathering your details...'}
                {chatPhase === 'policy_selection' && 'Policies matched — select to apply'}
                {chatPhase === 'applied' && 'Application submitted!'}
              </p>
            </div>
          </div>
          <button
            data-testid="close-avatar-chat"
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Progress indicator */}
        <div className="flex items-center px-5 py-2 bg-primary/5 border-b border-border gap-0">
          {['Gather info', 'Match policies', 'Apply'].map((step, idx) => {
            const phaseIdx = { gathering: 0, policy_selection: 1, applied: 2 }[chatPhase];
            const active = idx === phaseIdx;
            const done = idx < phaseIdx;
            return (
              <React.Fragment key={step}>
                <div className="flex items-center gap-1">
                  <div
                    className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                      done
                        ? 'bg-primary text-white'
                        : active
                        ? 'bg-accent text-white'
                        : 'bg-border text-text-secondary'
                    }`}
                  >
                    {done ? '✓' : idx + 1}
                  </div>
                  <span
                    className={`text-xs font-medium ${
                      active ? 'text-primary' : done ? 'text-primary/70' : 'text-text-secondary'
                    }`}
                  >
                    {step}
                  </span>
                </div>
                {idx < 2 && <div className="flex-1 h-px bg-border mx-2" />}
              </React.Fragment>
            );
          })}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4" data-testid="chat-messages">
          {messages.map((msg, i) => renderMessage(msg, i))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-4 h-4 text-primary" />
              </div>
              <div className="bg-bg border border-border rounded-xl px-4 py-3 rounded-tl-sm">
                <div className="flex gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-text-secondary/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 rounded-full bg-text-secondary/40 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 rounded-full bg-text-secondary/40 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Profile badge */}
        {profileExtracted && profile && chatPhase === 'gathering' && (
          <div className="px-5 py-2 border-t border-border bg-accent/5">
            <div className="flex items-center justify-between">
              <p className="text-xs text-text-secondary">
                Profile: <span className="font-semibold text-primary">{profile.completeness_score || 0}% complete</span>
              </p>
              <button
                data-testid="get-recommendations-btn"
                onClick={handleGetRecommendations}
                className="text-xs font-semibold text-accent hover:text-accent-hover transition-colors"
              >
                View Matching Policies
              </button>
            </div>
          </div>
        )}

        {/* Input */}
        {chatPhase !== 'applied' && (
          <div className="px-5 py-4 border-t border-border bg-surface">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                data-testid="chat-input"
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendMessage()}
                placeholder={
                  chatPhase === 'policy_selection'
                    ? 'Ask about a policy or click Apply Now above...'
                    : 'Type your message...'
                }
                className="flex-1 px-4 py-2.5 bg-bg border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                disabled={loading}
              />
              <button
                data-testid="send-message-btn"
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="w-10 h-10 bg-primary hover:bg-primary-hover disabled:opacity-40 text-white rounded-lg flex items-center justify-center transition-all duration-200"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            {messageCount >= 3 && !profileExtracted && (
              <button
                data-testid="extract-profile-btn"
                onClick={handleGetRecommendations}
                className="mt-2 w-full text-center text-xs font-semibold text-primary hover:text-primary-hover transition-colors py-1"
              >
                Ready for recommendations? Click here
              </button>
            )}
          </div>
        )}

        {chatPhase === 'applied' && (
          <div className="px-5 py-4 border-t border-border bg-surface">
            <button
              onClick={onClose}
              className="w-full text-sm font-semibold bg-primary hover:bg-primary-hover text-white rounded-lg py-2.5 transition-colors"
            >
              Track Application Below
            </button>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}

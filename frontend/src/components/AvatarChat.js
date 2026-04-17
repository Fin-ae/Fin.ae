import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Sparkles, UserCircle } from 'lucide-react';
import { chatMessage, extractProfile, recommendPolicies } from '../api';

export default function AvatarChat({ sessionId, onClose, onProfileExtracted, onGetRecommendations }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hello! I'm Fin-ae, your AI financial assistant. I'm here to help you find the best financial products in the UAE.\n\nWhat are you looking for today? Insurance, a personal loan, credit card, investment options, or a bank account?" }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [profileExtracted, setProfileExtracted] = useState(false);
  const [profile, setProfile] = useState(null);
  const [messageCount, setMessageCount] = useState(0);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setLoading(true);
    setMessageCount(prev => prev + 1);

    try {
      const res = await chatMessage(sessionId, text);
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
      
      // Auto-extract profile after 4+ user messages
      if (messageCount >= 3 && !profileExtracted) {
        try {
          const profileRes = await extractProfile(sessionId);
          const p = profileRes.data.profile;
          if (p && p.completeness_score >= 40) {
            setProfile(p);
            setProfileExtracted(true);
            onProfileExtracted(p);
          }
        } catch (e) {
          // Profile extraction is optional
        }
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "I apologize, I'm having trouble connecting. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleGetRecommendations = async () => {
    if (!profileExtracted) {
      // Extract profile first
      try {
        setLoading(true);
        const profileRes = await extractProfile(sessionId);
        const p = profileRes.data.profile;
        setProfile(p);
        setProfileExtracted(true);
        onProfileExtracted(p);
      } catch (e) {
        setMessages(prev => [...prev, { role: 'assistant', content: "Let me gather a bit more information first. Could you tell me about your income and what type of financial product you're interested in?" }]);
        setLoading(false);
        return;
      } finally {
        setLoading(false);
      }
    }
    onGetRecommendations();
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
        style={{ maxHeight: '80vh' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border bg-primary text-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
              <svg viewBox="0 0 40 40" className="w-7 h-7">
                <circle cx="20" cy="14" r="8" fill="#D4AF37"/>
                <ellipse cx="20" cy="32" rx="12" ry="8" fill="#D4AF37"/>
                <circle cx="17" cy="13" r="1.5" fill="#0A3224"/>
                <circle cx="23" cy="13" r="1.5" fill="#0A3224"/>
                <path d="M17 17 Q20 20 23 17" stroke="#0A3224" strokeWidth="1" fill="none" strokeLinecap="round"/>
              </svg>
            </div>
            <div>
              <h3 className="font-heading font-bold text-sm">Fin-ae</h3>
              <p className="text-xs text-white/60">Financial Assistant</p>
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

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4" data-testid="chat-messages">
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              {msg.role === 'assistant' ? (
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-4 h-4 text-primary" />
                </div>
              ) : (
                <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0">
                  <UserCircle className="w-4 h-4 text-accent" />
                </div>
              )}
              <div
                className={`max-w-[80%] px-4 py-3 rounded-xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-primary text-white rounded-tr-sm'
                    : 'bg-bg border border-border text-text-primary rounded-tl-sm'
                }`}
              >
                {msg.content.split('\n').map((line, j) => (
                  <p key={j} className={j > 0 ? 'mt-2' : ''}>{line}</p>
                ))}
              </div>
            </motion.div>
          ))}

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

        {/* Profile Badge */}
        {profileExtracted && profile && (
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
                View Recommendations
              </button>
            </div>
          </div>
        )}

        {/* Input */}
        <div className="px-5 py-4 border-t border-border bg-surface">
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              data-testid="chat-input"
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder="Type your message..."
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
      </motion.div>
    </motion.div>
  );
}

import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Shield, TrendingUp, CreditCard, Building2 } from 'lucide-react';

const FEATURES = [
  { icon: Shield, label: 'Insurance', desc: 'Health, life & property' },
  { icon: TrendingUp, label: 'Investments', desc: 'Funds & sukuk' },
  { icon: CreditCard, label: 'Cards & Loans', desc: 'Best rates in UAE' },
  { icon: Building2, label: 'Banking', desc: 'Savings & current' },
];

export default function Hero({ onStartChat }) {
  return (
    <div className="relative min-h-screen flex items-center overflow-hidden pt-16" data-testid="hero-section">
      {/* Background texture */}
      <div className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%230A3224' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }}
      />

      <div className="max-w-7xl mx-auto px-6 md:px-12 w-full">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left Content */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, ease: 'easeOut' }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/5 border border-primary/10 mb-6">
              <span className="w-2 h-2 rounded-full bg-accent" />
              <span className="text-xs tracking-[0.2em] uppercase font-semibold text-text-secondary">
                AI-Powered Financial Assistant
              </span>
            </div>

            <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl tracking-tighter font-black leading-none text-primary mb-6">
              Your smart path to{' '}
              <span className="text-accent">better</span>{' '}
              financial decisions
            </h1>

            <p className="text-lg text-text-secondary leading-relaxed mb-8 max-w-lg">
              Fin-ae compares insurance, loans, investments, and banking products across UAE institutions. 
              Talk to our AI assistant and get personalized recommendations in minutes.
            </p>

            <div className="flex flex-wrap gap-4 mb-12">
              <button
                data-testid="hero-start-chat-btn"
                onClick={onStartChat}
                className="inline-flex items-center gap-2 px-6 py-3.5 bg-primary text-white rounded-lg font-semibold hover:bg-primary-hover transition-all duration-200 hover:-translate-y-0.5 shadow-lg shadow-primary/20"
              >
                Talk to Fin-ae
                <ArrowRight className="w-4 h-4" />
              </button>
              <button
                data-testid="hero-explore-btn"
                onClick={() => document.getElementById('recommendations')?.scrollIntoView({ behavior: 'smooth' })}
                className="inline-flex items-center gap-2 px-6 py-3.5 border border-border text-text-primary rounded-lg font-semibold hover:border-primary hover:text-primary transition-all duration-200"
              >
                Explore Products
              </button>
            </div>

            {/* Feature pills */}
            <div className="grid grid-cols-2 gap-3">
              {FEATURES.map((f, i) => (
                <motion.div
                  key={f.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + i * 0.1, duration: 0.5 }}
                  className="flex items-center gap-3 p-3 rounded-lg border border-border bg-surface hover:border-primary/20 hover:-translate-y-0.5 transition-all duration-200 cursor-default"
                >
                  <div className="w-10 h-10 rounded-lg bg-primary/5 flex items-center justify-center flex-shrink-0">
                    <f.icon className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text-primary">{f.label}</p>
                    <p className="text-xs text-text-secondary">{f.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Right - Avatar */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative flex items-center justify-center"
          >
            <div className="relative">
              {/* Ambient glow */}
              <div className="absolute inset-0 bg-accent/10 rounded-full blur-3xl scale-110" />
              
              {/* Avatar container */}
              <div className="avatar-float relative">
                <svg
                  viewBox="0 0 300 380"
                  className="w-64 h-80 md:w-80 md:h-96 drop-shadow-2xl"
                  data-testid="hero-avatar"
                >
                  {/* Body */}
                  <ellipse cx="150" cy="310" rx="80" ry="55" fill="#0A3224" />
                  <ellipse cx="150" cy="305" rx="70" ry="45" fill="#0F4C3A" />
                  
                  {/* Tie/Accent */}
                  <polygon points="150,258 142,290 150,310 158,290" fill="#D4AF37" />
                  
                  {/* Neck */}
                  <rect x="137" y="230" width="26" height="35" rx="8" fill="#F5DEB3" />
                  
                  {/* Head */}
                  <ellipse cx="150" cy="170" rx="65" ry="75" fill="#F5DEB3" />
                  
                  {/* Hair */}
                  <ellipse cx="150" cy="115" rx="60" ry="35" fill="#1A1D1C" />
                  <rect x="90" y="105" width="20" height="50" rx="10" fill="#1A1D1C" />
                  <rect x="190" y="105" width="20" height="50" rx="10" fill="#1A1D1C" />
                  
                  {/* Eyes */}
                  <ellipse cx="125" cy="165" rx="10" ry="11" fill="white" />
                  <ellipse cx="175" cy="165" rx="10" ry="11" fill="white" />
                  <circle cx="127" cy="166" r="5" fill="#0A3224" />
                  <circle cx="177" cy="166" r="5" fill="#0A3224" />
                  <circle cx="128" cy="164" r="1.5" fill="white" />
                  <circle cx="178" cy="164" r="1.5" fill="white" />
                  
                  {/* Eyebrows */}
                  <path d="M112 148 Q125 140 140 148" stroke="#1A1D1C" strokeWidth="3" fill="none" strokeLinecap="round" />
                  <path d="M160 148 Q175 140 188 148" stroke="#1A1D1C" strokeWidth="3" fill="none" strokeLinecap="round" />
                  
                  {/* Nose */}
                  <path d="M147 180 Q150 190 153 180" stroke="#D4A574" strokeWidth="1.5" fill="none" />
                  
                  {/* Smile */}
                  <path d="M130 198 Q150 215 170 198" stroke="#1A1D1C" strokeWidth="2.5" fill="none" strokeLinecap="round" />
                  
                  {/* Ears */}
                  <ellipse cx="85" cy="170" rx="10" ry="15" fill="#F5DEB3" />
                  <ellipse cx="215" cy="170" rx="10" ry="15" fill="#F5DEB3" />
                </svg>

                {/* Chat bubble */}
                <motion.div
                  initial={{ opacity: 0, scale: 0, x: 20 }}
                  animate={{ opacity: 1, scale: 1, x: 0 }}
                  transition={{ delay: 1, duration: 0.4, type: 'spring' }}
                  className="absolute -right-4 top-8 bg-surface border border-border rounded-xl px-4 py-2.5 shadow-lg max-w-[180px]"
                >
                  <p className="text-sm font-medium text-text-primary">Hi! I'm Fin-ae</p>
                  <p className="text-xs text-text-secondary mt-0.5">How can I help you today?</p>
                  <div className="absolute -left-2 top-4 w-4 h-4 bg-surface border-l border-b border-border rotate-45" />
                </motion.div>
              </div>

              {/* Floating badges */}
              <motion.div
                animate={{ y: [0, -8, 0] }}
                transition={{ repeat: Infinity, duration: 3, delay: 0.5 }}
                className="absolute -left-8 top-20 bg-surface border border-border rounded-lg px-3 py-2 shadow-md"
              >
                <p className="text-xs font-semibold text-accent">4.5% APR</p>
              </motion.div>
              <motion.div
                animate={{ y: [0, -6, 0] }}
                transition={{ repeat: Infinity, duration: 3.5, delay: 1 }}
                className="absolute -right-4 bottom-32 bg-surface border border-border rounded-lg px-3 py-2 shadow-md"
              >
                <p className="text-xs font-semibold text-primary">12 Policies</p>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

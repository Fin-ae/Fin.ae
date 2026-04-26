import React from 'react';
import { MessageCircle, BarChart3, FileText, Newspaper } from 'lucide-react';

const NAV_ITEMS = [
  { id: 'hero', label: 'Home' },
  { id: 'recommendations', label: 'Products' },
  { id: 'tracker', label: 'Applications' },
  { id: 'news', label: 'Insights' },
];

export default function Header({ activeSection, scrollTo, onOpenChat, children }) {
  return (
    <header
      data-testid="main-header"
      className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-white/70 border-b border-white/40 shadow-sm"
    >
      <div className="max-w-7xl mx-auto px-6 md:px-12 flex items-center justify-between h-16">
        <button
          data-testid="logo-btn"
          onClick={() => scrollTo('hero')}
          className="flex items-center gap-2 group"
        >
          <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-accent font-heading font-black text-sm">F</span>
          </div>
          <span className="font-heading font-bold text-xl text-primary tracking-tight">
            Fin-ae
          </span>
        </button>

        <nav className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              data-testid={`nav-${item.id}`}
              onClick={() => scrollTo(item.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                activeSection === item.id
                  ? 'bg-primary text-white'
                  : 'text-text-secondary hover:text-primary hover:bg-primary/5'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          {children}
          <button
            data-testid="header-chat-btn"
            onClick={onOpenChat}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary-hover transition-all duration-200"
          >
            <MessageCircle className="w-4 h-4" />
            <span className="hidden sm:inline">Ask Fin-ae</span>
          </button>
        </div>
      </div>
    </header>
  );
}

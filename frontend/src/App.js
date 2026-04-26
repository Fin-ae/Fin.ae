import React, { useState, useCallback } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import AvatarChat from './components/AvatarChat';
import Recommendations from './components/Recommendations';
import PolicyComparison from './components/PolicyComparison';
import ApplicationTracker from './components/ApplicationTracker';
import NewsSection from './components/NewsSection';
import OpenChat from './components/OpenChat';
import Footer from './components/Footer';
import AuthModal from './components/AuthModal';
import { AuthProvider, useAuth } from './AuthContext';

function AppInner() {
  const { user, logout } = useAuth();
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`);
  const [activeSection, setActiveSection] = useState('hero');
  const [showAvatarChat, setShowAvatarChat] = useState(false);
  const [showOpenChat, setShowOpenChat] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [compareIds, setCompareIds] = useState([]);

  const handleProfileExtracted = useCallback((profile) => {
    setUserProfile(profile);
  }, []);

  const handleRecommendationsLoaded = useCallback((recs) => {
    setRecommendations(recs);
  }, []);

  const handleCompare = useCallback((ids) => {
    setCompareIds(ids);
    setActiveSection('compare');
    setTimeout(() => {
      document.getElementById('compare')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }, []);

  const scrollTo = (id) => {
    setActiveSection(id);
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-bg" data-testid="app-container">
      <Header
        activeSection={activeSection}
        scrollTo={scrollTo}
        onOpenChat={() => setShowOpenChat(true)}
      >
        {/* Auth button injected into Header via children */}
        <div className="flex items-center gap-2">
          {user ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-secondary hidden sm:block">
                {user.name}
              </span>
              <button
                onClick={logout}
                className="px-3 py-1.5 text-xs font-semibold border border-border rounded-lg hover:bg-surface transition-colors text-text-secondary"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowAuthModal(true)}
              className="px-4 py-1.5 bg-primary text-white text-xs font-semibold rounded-lg hover:bg-primary-hover transition-all"
            >
              Sign In
            </button>
          )}
        </div>
      </Header>

      <main>
        <section id="hero">
          <Hero onStartChat={() => setShowAvatarChat(true)} />
        </section>

        <section id="recommendations" className="py-16 md:py-24">
          <Recommendations
            sessionId={sessionId}
            userProfile={userProfile}
            recommendations={recommendations}
            onRecommendationsLoaded={handleRecommendationsLoaded}
            onCompare={handleCompare}
          />
        </section>

        {compareIds.length >= 2 && (
          <section id="compare" className="py-16 md:py-24 bg-surface">
            <PolicyComparison compareIds={compareIds} />
          </section>
        )}

        <section id="tracker" className="py-16 md:py-24">
          <ApplicationTracker
            sessionId={sessionId}
            userProfile={userProfile}
            onOpenAuth={() => setShowAuthModal(true)}
          />
        </section>

        <section id="news" className="py-16 md:py-24 bg-surface">
          <NewsSection />
        </section>
      </main>

      <Footer />

      {showAvatarChat && (
        <AvatarChat
          sessionId={sessionId}
          onClose={() => setShowAvatarChat(false)}
          onProfileExtracted={handleProfileExtracted}
          onGetRecommendations={() => {
            setShowAvatarChat(false);
            scrollTo('recommendations');
          }}
        />
      )}

      {showOpenChat && (
        <OpenChat
          sessionId={sessionId}
          onClose={() => setShowOpenChat(false)}
        />
      )}

      {showAuthModal && (
        <AuthModal onClose={() => setShowAuthModal(false)} />
      )}

      {!showAvatarChat && !showOpenChat && !showAuthModal && (
        <button
          data-testid="floating-chat-btn"
          onClick={() => setShowAvatarChat(true)}
          className="fixed bottom-6 right-6 z-40 w-16 h-16 bg-primary hover:bg-primary-hover text-white rounded-full shadow-2xl flex items-center justify-center transition-all duration-200 hover:scale-110 group"
        >
          <svg className="w-7 h-7" viewBox="0 0 80 80" fill="none">
            <circle cx="40" cy="28" r="14" fill="#D4AF37"/>
            <ellipse cx="40" cy="58" rx="20" ry="14" fill="#D4AF37"/>
            <circle cx="35" cy="26" r="2" fill="#0A3224"/>
            <circle cx="45" cy="26" r="2" fill="#0A3224"/>
            <path d="M36 32 Q40 36 44 32" stroke="#0A3224" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
          </svg>
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-accent rounded-full pulse-ring"/>
        </button>
      )}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}

export default App;

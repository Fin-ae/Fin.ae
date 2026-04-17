import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-primary text-white/80 py-12" data-testid="footer">
      <div className="max-w-7xl mx-auto px-6 md:px-12">
        <div className="grid md:grid-cols-3 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                <span className="text-accent font-heading font-black text-sm">F</span>
              </div>
              <span className="font-heading font-bold text-lg text-white">Fin-ae</span>
            </div>
            <p className="text-sm text-white/50 leading-relaxed">
              Your smart companion for comparing and choosing the best financial products in the UAE.
            </p>
          </div>
          <div>
            <h4 className="font-heading font-semibold text-white text-sm mb-3">Products</h4>
            <ul className="space-y-2 text-sm text-white/50">
              <li>Health Insurance</li>
              <li>Personal Loans</li>
              <li>Credit Cards</li>
              <li>Investments & Sukuk</li>
              <li>Bank Accounts</li>
            </ul>
          </div>
          <div>
            <h4 className="font-heading font-semibold text-white text-sm mb-3">Disclaimer</h4>
            <p className="text-xs text-white/40 leading-relaxed">
              Fin-ae is a technology-enabled comparison platform and does not provide regulated financial advice. 
              All information is for educational purposes. Please consult a licensed financial advisor before making 
              investment or insurance decisions. Product details are indicative and subject to change by respective institutions.
            </p>
          </div>
        </div>
        <div className="border-t border-white/10 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-xs text-white/30">2026 Fin-ae. Built for the UAE market.</p>
          <p className="text-xs text-white/30">Built for the UAE market</p>
        </div>
      </div>
    </footer>
  );
}

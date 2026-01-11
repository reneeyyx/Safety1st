import React, { useState } from 'react';
import { useAccessibility, AccessibilityMode } from '../contexts/AccessibilityContext';

const AccessibilitySettings: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { mode, setMode, isReducedMotion, toggleReducedMotion } = useAccessibility();

  const modes: { value: AccessibilityMode; label: string; description: string }[] = [
    { value: 'default', label: 'Default', description: 'Standard appearance' },
    { value: 'high-contrast', label: 'High Contrast', description: 'Enhanced contrast for better visibility' },
    { value: 'colorblind-safe', label: 'Colorblind Safe', description: 'Color palette safe for color blindness' },
    { value: 'dyslexia-friendly', label: 'Dyslexia Friendly', description: 'OpenDyslexic font and spacing' },
    { value: 'large-text', label: 'Large Text', description: 'Increased text size throughout' },
  ];

  return (
    <>
      {/* Accessibility Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 p-4 rounded-full shadow-lg hover:scale-110 transition-all duration-300 glow-button"
        style={{
          background: 'linear-gradient(135deg, rgba(220, 60, 140, 0.9) 0%, rgba(160, 80, 200, 0.9) 100%)',
        }}
        aria-label="Accessibility Settings"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          style={{ color: '#000000' }}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
          />
        </svg>
      </button>

      {/* Settings Panel */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />

          {/* Modal */}
          <div className="relative bg-safety-gray/30 border-2 border-safety-orange/50 rounded-lg p-8 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto shadow-[0_0_15px_rgba(220,60,140,0.2),0_0_30px_rgba(160,80,200,0.15)] transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent" style={{ fontFamily: 'Poppins, sans-serif' }}>
                Accessibility Settings
              </h2>
              <button
                onClick={() => setIsOpen(false)}
                className="text-safety-orange/60 hover:text-safety-orange transition-colors"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Mode Selection */}
            <div className="space-y-3 mb-6">
              <h3 className="text-lg font-semibold mb-3 bg-gradient-to-r from-[rgba(220,60,140,0.5)] to-[rgba(160,80,200,0.5)] bg-clip-text text-transparent">Display Mode</h3>
              {modes.map((modeOption) => (
                <button
                  key={modeOption.value}
                  onClick={() => setMode(modeOption.value)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    mode === modeOption.value
                      ? 'border-safety-orange bg-safety-orange/20 text-safety-orange'
                      : 'border-safety-orange/30 bg-safety-black/30 text-safety-orange/70 hover:border-safety-orange/50'
                  }`}
                >
                  <div className="font-semibold text-safety-orange">{modeOption.label}</div>
                  <div className="text-sm text-safety-orange/70 mt-1">{modeOption.description}</div>
                </button>
              ))}
            </div>

            {/* Reduced Motion Toggle */}
            <div className="pt-4 border-t border-safety-orange/30">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={isReducedMotion}
                  onChange={toggleReducedMotion}
                  className="mr-3 w-5 h-5"
                />
                <div>
                  <div className="font-semibold text-safety-orange">Reduced Motion</div>
                  <div className="text-sm text-safety-orange/70">Minimize animations and transitions</div>
                </div>
              </label>
            </div>

            {/* Close Button */}
            <button
              onClick={() => setIsOpen(false)}
              className="w-full mt-6 py-4 px-6 text-lg font-bold rounded-2xl transition-all duration-300 hover:scale-105 backdrop-blur-md border border-safety-orange/30 glow-button"
              style={{
                background: 'radial-gradient(circle at center, rgba(220, 60, 140, 0.2) 0%, rgba(0, 0, 0, 0.8) 100%)',
                color: 'rgba(220, 60, 140, 0.95)',
                fontFamily: 'Poppins, sans-serif'
              }}
            >
              Apply Settings
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default AccessibilitySettings;

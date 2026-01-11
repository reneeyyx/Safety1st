import React, { createContext, useContext, useState, useEffect } from 'react';

export type AccessibilityMode =
  | 'default'
  | 'high-contrast'
  | 'colorblind-safe'
  | 'dyslexia-friendly'
  | 'large-text'
  | 'reduced-motion';

interface AccessibilityContextType {
  mode: AccessibilityMode;
  setMode: (mode: AccessibilityMode) => void;
  isReducedMotion: boolean;
  toggleReducedMotion: () => void;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

export const AccessibilityProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mode, setModeState] = useState<AccessibilityMode>(() => {
    const saved = localStorage.getItem('accessibility-mode');
    return (saved as AccessibilityMode) || 'default';
  });

  const [isReducedMotion, setIsReducedMotion] = useState(() => {
    const saved = localStorage.getItem('reduced-motion');
    return saved === 'true';
  });

  const setMode = (newMode: AccessibilityMode) => {
    setModeState(newMode);
    localStorage.setItem('accessibility-mode', newMode);
  };

  const toggleReducedMotion = () => {
    const newValue = !isReducedMotion;
    setIsReducedMotion(newValue);
    localStorage.setItem('reduced-motion', String(newValue));
  };

  useEffect(() => {
    // Apply mode class to document root
    document.documentElement.className = '';
    if (mode !== 'default') {
      document.documentElement.classList.add(`accessibility-${mode}`);
    }
    if (isReducedMotion) {
      document.documentElement.classList.add('reduced-motion');
    }
  }, [mode, isReducedMotion]);

  return (
    <AccessibilityContext.Provider value={{ mode, setMode, isReducedMotion, toggleReducedMotion }}>
      {children}
    </AccessibilityContext.Provider>
  );
};

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within AccessibilityProvider');
  }
  return context;
};

import React from 'react';

interface LandingPageProps {
  onStart: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onStart }) => {
  return (
    <div
      className="min-h-screen flex flex-col"
      style={{
        background: 'radial-gradient(circle at center, rgba(26, 26, 26, 1) 0%, rgba(0, 0, 0, 1) 60%)'
      }}
    >
      {/* Header with Logo and Title */}
      <header className="backdrop-blur-sm" style={{ background: 'transparent' }}>
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center">
            {/* Logo on left */}
            <img
              src="/logo.png"
              alt="Safety1st Logo"
              className="h-16 w-16 object-contain mr-4"
            />

            {/* Title next to logo */}
            <h1 className="text-3xl" style={{ color: '#E5B53F', fontFamily: 'Poppins, sans-serif' }}>
              Safety1st
            </h1>
          </div>
        </div>
      </header>

      {/* Main Content - Centered */}
      <div className="flex-1 flex flex-col items-center justify-center px-6">
        <div className="max-w-4xl text-center space-y-8">
          {/* Main Headline */}
          <h2
            className="text-6xl md:text-7xl lg:text-8xl leading-tight animate-slideUpFadeIn"
            style={{
              color: '#e8901eff',
              fontFamily: 'Poppins, sans-serif',
              fontWeight: '500'
            }}
          >
            Car safety wasn't built for her.
          </h2>

          {/* Statistic */}
          <p
            className="text-2xl md:text-3xl lg:text-3xl leading-relaxed animate-slideUpFadeIn"
            style={{
              color: 'rgba(218, 165, 32, 0.6)',
              fontFamily: 'Poppins, sans-serif',
              fontWeight: '300',
              animationDelay: '0.2s'
            }}
          >
            Women are 17–73% more likely to be seriously injured in the same crash.
          </p>

          {/* Start Button */}
          <div className="pt-8 animate-slideUpFadeIn" style={{ animationDelay: '0.4s' }}>
            <button
              onClick={onStart}
              className="px-12 py-5 text-lg font-medium rounded-2xl transition-all duration-300 hover:scale-105 backdrop-blur-md border border-safety-orange/30 glow-button"
              style={{
                background: 'radial-gradient(circle at center, rgba(229, 181, 63, 0.2) 0%, rgba(0, 0, 0, 0.8) 100%)',
                color: 'rgba(229, 181, 63, 0.95)',
                fontFamily: 'Poppins, sans-serif',
              }}
            >
              Start Designing Safer Cars
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;

import React, { useEffect, useRef, useState } from 'react';

interface UnitySimulationProps {
  gender: 'male' | 'female';
  crashSide: 'frontal' | 'left' | 'right';
}

/**
 * Maps simulation parameters to available Unity build paths
 * Returns null if no simulation available for the given parameters
 */
const getSimulationPath = (gender: 'male' | 'female', crashSide: 'frontal' | 'left' | 'right'): string | null => {
  // Map of available simulations
  // Add new simulations here as they become available
  const simulationMap: Record<string, string> = {
    // Male simulations (currently available)
    'male_frontal': '/front_man/index.html',
    'male_left': '/left_man/index.html',
    'male_right': '/right_man/index.html',

    // Female simulations (to be added - uncomment when available)
    // 'female_frontal': '/front_woman/index.html',
    // 'female_left': '/left_woman/index.html',
    // 'female_right': '/right_woman/index.html',

    // Pregnant female simulations (to be added - uncomment when available)
    // Note: You may want to track pregnancy status separately if these need different models
    // 'pregnant_frontal': '/front_pregnant/index.html',
    // 'pregnant_left': '/left_pregnant/index.html',
    // 'pregnant_right': '/right_pregnant/index.html',
  };

  const key = `${gender}_${crashSide}`;
  return simulationMap[key] || null;
};

const UnitySimulation: React.FC<UnitySimulationProps> = ({ gender, crashSide }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const simulationPath = getSimulationPath(gender, crashSide);

  useEffect(() => {
    setIsLoading(true);
    setError(null);

    // Check if simulation is available
    if (!simulationPath) {
      setError(`Simulation not yet available for ${gender} ${crashSide} crash`);
      setIsLoading(false);
      return;
    }

    // Reset iframe when parameters change
    if (iframeRef.current) {
      iframeRef.current.src = simulationPath;
    }
  }, [gender, crashSide, simulationPath]);

  const handleIframeLoad = () => {
    setIsLoading(false);
  };

  const handleIframeError = () => {
    setError('Failed to load simulation');
    setIsLoading(false);
  };

  // If no simulation is available, show placeholder
  if (!simulationPath) {
    return (
      <div className="bg-safety-gray/30 border-2 border-safety-orange/50 rounded-lg p-8 h-[600px] flex items-center justify-center shadow-[0_0_15px_rgba(220,60,140,0.2),0_0_30px_rgba(160,80,200,0.15)] hover:shadow-[0_0_20px_rgba(220,60,140,0.3),0_0_40px_rgba(160,80,200,0.2)] transition-all duration-300">
        <div className="text-center">
          <div className="w-24 h-24 mx-auto mb-4 border-4 border-safety-orange/50 rounded-lg flex items-center justify-center">
            <svg
              className="w-12 h-12 text-safety-orange/50"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-bold mb-2 bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent">
            Simulation Not Available
          </h3>
          <p className="text-safety-orange/60 text-sm mb-2">
            {error || `No simulation for ${gender} ${crashSide} crash yet`}
          </p>
          <p className="text-safety-orange/40 text-xs">
            Available: Male (frontal, left, right)
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative bg-safety-gray/30 border-2 border-safety-orange/50 rounded-lg overflow-hidden h-[600px] shadow-[0_0_15px_rgba(220,60,140,0.2),0_0_30px_rgba(160,80,200,0.15)] hover:shadow-[0_0_20px_rgba(220,60,140,0.3),0_0_40px_rgba(160,80,200,0.2)] transition-all duration-300">
      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-safety-black/80 z-10 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-safety-orange/30 border-t-safety-orange mb-4"></div>
            <p className="text-safety-orange/70 text-sm">Loading simulation...</p>
          </div>
        </div>
      )}

      {/* Error Overlay */}
      {error && !isLoading && (
        <div className="absolute inset-0 bg-safety-black/80 z-10 flex items-center justify-center">
          <div className="text-center px-6">
            <div className="w-16 h-16 mx-auto mb-4 border-4 border-red-500/50 rounded-lg flex items-center justify-center">
              <svg
                className="w-8 h-8 text-red-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <p className="text-red-500/90 text-sm font-medium">{error}</p>
          </div>
        </div>
      )}

      {/* Unity Simulation Label */}
      <div className="absolute top-4 left-4 z-20 bg-safety-black/70 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-safety-orange/30">
        <p className="text-xs text-safety-orange/80 font-medium">
          {gender.charAt(0).toUpperCase() + gender.slice(1)} {crashSide.charAt(0).toUpperCase() + crashSide.slice(1)} Crash
        </p>
      </div>

      {/* Unity WebGL Iframe */}
      <iframe
        ref={iframeRef}
        src={simulationPath}
        title={`Unity Crash Simulation - ${gender} ${crashSide}`}
        className="w-full h-full border-0"
        onLoad={handleIframeLoad}
        onError={handleIframeError}
        allowFullScreen
        style={{
          display: isLoading ? 'none' : 'block'
        }}
      />
    </div>
  );
};

export default UnitySimulation;

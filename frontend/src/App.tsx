import { useState } from 'react';
import CrashInputForm from './components/CrashInputForm';
import ErrorModal from './components/ErrorModal';
import LoadingModal from './components/LoadingModal';
import ResultsDisplay from './components/ResultsDisplay';
import LandingPage from './components/LandingPage';
import HistoryPage from './components/HistoryPage';
import AccessibilitySettings from './components/AccessibilitySettings';
import { AccessibilityProvider } from './contexts/AccessibilityContext';
import { evaluateCrashRisk } from './api/crashRiskApi';
import type { CarData, DummyData, CrashRiskResponse } from './types';
import './App.css';

type PageView = 'home' | 'history';

function App() {
  const [showLanding, setShowLanding] = useState(true);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [currentPage, setCurrentPage] = useState<PageView>('home');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [results, setResults] = useState<CrashRiskResponse | null>(null);

  const validateInputs = (carData: CarData, dummyData: DummyData): string[] => {
    const errors: string[] = [];

    if (!carData.impact_speed_kmh || carData.impact_speed_kmh <= 0) {
      errors.push('Impact Speed is required');
    }
    if (!carData.vehicle_mass_kg || carData.vehicle_mass_kg <= 0) {
      errors.push('Vehicle Mass is required');
    }
    if (!carData.crash_side) {
      errors.push('Crash Side is required');
    }
    if (!dummyData.gender) {
      errors.push('Occupant Gender is required');
    }
    if (!dummyData.seat_position) {
      errors.push('Seat Position is required');
    }

    return errors;
  };

  const handleStart = () => {
    setIsTransitioning(true);
    setTimeout(() => {
      setShowLanding(false);
    }, 800); // Match animation duration
  };

  const handleBackToLanding = () => {
    setShowLanding(true);
    setIsTransitioning(false);
  };

  const handleSubmit = async (carData: CarData, dummyData: DummyData) => {
    // Validate inputs
    const validationErrors = validateInputs(carData, dummyData);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      setShowErrorModal(true);
      return;
    }

    // Clear previous results
    setResults(null);

    // Show loading
    setIsLoading(true);

    try {
      const response = await evaluateCrashRisk({
        car_data: carData,
        dummy_data: dummyData,
      });

      setResults(response);
    } catch (error) {
      setErrors([error instanceof Error ? error.message : 'An unknown error occurred']);
      setShowErrorModal(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AccessibilityProvider>
      {showLanding ? (
        <div
          className={`transition-all duration-700 ease-in-out ${
            isTransitioning ? 'opacity-0 -translate-y-12' : 'opacity-100 translate-y-0'
          }`}
        >
          <LandingPage onStart={handleStart} />
        </div>
      ) : (
        <div
          className="min-h-screen text-safety-orange animate-fadeIn flex flex-col"
          style={{
            background: 'radial-gradient(circle at center, rgba(26, 26, 26, 1) 0%, rgba(0, 0, 0, 1) 60%)'
          }}
        >
          {/* Header with Logo and Navigation */}
          <header className="backdrop-blur-sm sticky top-0 z-40" style={{ background: 'transparent' }}>
            <div className="container mx-auto px-6 py-4">
              <div className="flex items-center">
                {/* Logo and Title - Fixed position */}
                <div
                  onClick={handleBackToLanding}
                  className="flex items-center cursor-pointer transition-transform duration-200 hover:scale-105 flex-shrink-0"
                >
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

                {/* Navigation Tabs - Aligned to the right with fixed spacing */}
                <div className="ml-auto flex space-x-2">
                  <button
                    onClick={() => setCurrentPage('home')}
                    className={`px-6 py-2 rounded-lg transition-all duration-200 min-w-[100px] ${
                      currentPage === 'home'
                        ? 'bg-safety-orange/20 text-safety-orange border border-safety-orange/50'
                        : 'text-safety-orange/60 hover:text-safety-orange hover:bg-safety-orange/10'
                    }`}
                    style={{ fontFamily: 'Poppins, sans-serif' }}
                  >
                    Home
                  </button>
                  <button
                    onClick={() => setCurrentPage('history')}
                    className={`px-6 py-2 rounded-lg transition-all duration-200 min-w-[100px] ${
                      currentPage === 'history'
                        ? 'bg-safety-orange/20 text-safety-orange border border-safety-orange/50'
                        : 'text-safety-orange/60 hover:text-safety-orange hover:bg-safety-orange/10'
                    }`}
                    style={{ fontFamily: 'Poppins, sans-serif' }}
                  >
                    History
                  </button>
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="container mx-auto px-6 py-8 flex-1">
            {currentPage === 'home' ? (
              <>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Left: Unity Simulation Placeholder */}
                  <div className="order-2 lg:order-1">
                    <div className="bg-safety-gray/30 border-2 border-safety-orange/30 rounded-lg p-8 h-[600px] flex items-center justify-center">
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
                              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                        </div>
                        <h3 className="text-xl font-bold text-safety-orange mb-2">
                          Unity Simulation
                        </h3>
                        <p className="text-safety-orange/60 text-sm">
                          3D crash visualization will appear here
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Right: Input Form */}
                  <div className="order-1 lg:order-2">
                    <CrashInputForm onSubmit={handleSubmit} />
                  </div>
                </div>

                {/* Results Section */}
                <ResultsDisplay results={results} />
              </>
            ) : (
              <HistoryPage />
            )}
          </main>

          {/* Footer */}
          <footer className="border-t border-safety-orange/30 py-6 bg-safety-black/50 mt-auto">
            <div className="container mx-auto px-6 text-center text-safety-orange/60 text-sm">
              <p>&copy; 2026 Safety1st - Crash Risk Analysis Tool</p>
            </div>
          </footer>

          {/* Modals */}
          <ErrorModal
            isOpen={showErrorModal}
            onClose={() => setShowErrorModal(false)}
            errors={errors}
          />
          <LoadingModal isOpen={isLoading} />
        </div>
      )}

      {/* Accessibility Settings - Always Available */}
      {!showLanding && <AccessibilitySettings />}
    </AccessibilityProvider>
  );
}

export default App;

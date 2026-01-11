import React from 'react';

interface LoadingModalProps {
  isOpen: boolean;
}

const LoadingModal: React.FC<LoadingModalProps> = ({ isOpen }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Blurred background overlay */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal content */}
      <div className="relative bg-safety-gray border-2 border-safety-orange rounded-lg p-12 max-w-md w-full mx-4 shadow-2xl">
        <div className="text-center">
          {/* Spinning loader */}
          <div className="mx-auto mb-6">
            <div className="relative w-20 h-20 mx-auto">
              <div className="absolute top-0 left-0 w-full h-full border-4 border-safety-orange/20 rounded-full"></div>
              <div className="absolute top-0 left-0 w-full h-full border-4 border-safety-orange border-t-transparent rounded-full animate-spin"></div>
            </div>
          </div>

          <h3 className="text-2xl font-bold text-safety-orange mb-3">
            Analyzing Crash Scenario
          </h3>

          <p className="text-safety-orange/80 text-sm">
            Please wait while we calculate the risk score...
          </p>

          <div className="mt-6 flex justify-center space-x-1">
            <div className="w-2 h-2 bg-safety-orange rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-safety-orange rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-safety-orange rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingModal;

import React from 'react';

interface ErrorModalProps {
  isOpen: boolean;
  onClose: () => void;
  errors: string[];
}

const ErrorModal: React.FC<ErrorModalProps> = ({ isOpen, onClose, errors }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Blurred background overlay */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal content */}
      <div className="relative bg-safety-gray/30 border-2 border-safety-orange/50 rounded-lg p-8 max-w-md w-full mx-4 shadow-[0_0_15px_rgba(220,60,140,0.2),0_0_30px_rgba(160,80,200,0.15)] transition-all duration-300">
        <div className="text-center">
          {/* Error Icon */}
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-900/30 mb-4">
            <svg
              className="h-10 w-10 text-red-500"
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

          <h3 className="text-2xl font-bold mb-4 bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent">
            Missing Information
          </h3>

          <div className="text-left mb-6">
            <p className="text-safety-orange mb-3">
              Please fill in the following required fields:
            </p>
            <ul className="list-disc list-inside space-y-2 text-safety-orange/90">
              {errors.map((error, index) => (
                <li key={index} className="text-sm">
                  {error}
                </li>
              ))}
            </ul>
          </div>

          <button
            onClick={onClose}
            className="w-full py-4 px-6 text-lg font-bold rounded-2xl transition-all duration-300 hover:scale-105 backdrop-blur-md border border-safety-orange/30 glow-button"
            style={{
              background: 'radial-gradient(circle at center, rgba(220, 60, 140, 0.2) 0%, rgba(0, 0, 0, 0.8) 100%)',
              color: 'rgba(220, 60, 140, 0.95)'
            }}
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
};

export default ErrorModal;

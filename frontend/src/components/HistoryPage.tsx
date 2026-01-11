import React, { useEffect, useState } from 'react';
import type { CrashRiskResponse } from '../types';

interface HistoryPageProps {
  onViewSimulation?: (simulation: any) => void;
}

const HistoryPage: React.FC<HistoryPageProps> = ({ onViewSimulation }) => {
  const [simulations, setSimulations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5001/api/history');
      const data = await response.json();

      if (data.success) {
        setSimulations(data.simulations);
      } else {
        setError(data.error || 'Failed to load history');
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRiskColor = (score: number) => {
    if (score < 40) return 'text-green-400';
    if (score < 70) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getRiskLabel = (score: number) => {
    if (score < 40) return 'Low Risk';
    if (score < 70) return 'Moderate Risk';
    return 'High Risk';
  };

  const getRiskBoxStyle = (score: number) => {
    if (score < 40) {
      return 'border-2 text-green-500 shadow-[0_0_8px_rgba(0,255,0,0.3),0_0_15px_rgba(0,255,0,0.2)]';
    }
    if (score < 70) {
      return 'border-2 text-yellow-300 shadow-[0_0_8px_rgba(255,255,0,0.3),0_0_15px_rgba(255,255,0,0.2)]';
    }
    return 'border-2 text-red-500 shadow-[0_0_8px_rgba(255,0,0,0.3),0_0_15px_rgba(255,0,0,0.2)]';
  };

  if (loading) {
    return (
      <div className="container mx-auto px-6 py-12">
        <div className="text-center text-safety-orange text-xl">Loading history...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-6 py-12">
        <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-6 text-center">
          <p className="text-red-400 text-lg">{error}</p>
          <button
            onClick={fetchHistory}
            className="mt-4 px-6 py-2 bg-safety-orange text-safety-black rounded-lg hover:bg-safety-orange-dark transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (simulations.length === 0) {
    return (
      <div className="container mx-auto px-6 py-12">
        <div className="bg-safety-gray/30 border-2 border-safety-orange/50 rounded-lg p-12 text-center shadow-[0_0_15px_rgba(220,60,140,0.2),0_0_30px_rgba(160,80,200,0.15)] hover:shadow-[0_0_20px_rgba(220,60,140,0.3),0_0_40px_rgba(160,80,200,0.2)] transition-all duration-300">
          <h2 className="text-2xl font-semibold mb-4 bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent">No Simulations Yet</h2>
          <p className="text-safety-orange/70">
            Run your first crash simulation to see it appear here.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 py-8">
      <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent">Simulation History</h2>

      <div className="space-y-4">
        {simulations.map((sim) => {
          const finalRisk = sim.gemini_analysis?.risk_score || sim.baseline?.risk_score || 0;
          const confidence = sim.gemini_analysis?.confidence || 0;

          return (
            <div
              key={sim._id}
              className="bg-safety-gray/30 border border-safety-orange/30 rounded-lg p-6 hover:border-safety-orange/50 transition-all cursor-pointer"
              onClick={() => onViewSimulation && onViewSimulation(sim)}
            >
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Date and Basic Info */}
                <div className="md:col-span-1">
                  <div className="text-safety-orange/70 text-sm mb-1">
                    {formatDate(sim.timestamp)}
                  </div>
                  <div className="text-safety-orange font-medium">
                    {sim.crash_configuration || 'Unknown'} crash
                  </div>
                  <div className="text-safety-orange/80 text-sm">
                    {sim.occupant_gender === 'female' ? 'Female' : 'Male'} occupant
                    {sim.is_pregnant && ' (Pregnant)'}
                  </div>
                </div>

                {/* Risk Score */}
                <div className="md:col-span-1 flex items-center gap-4">
                  <div>
                    <div className="text-safety-orange/70 text-xs uppercase tracking-wider mb-1">
                      Risk Score
                    </div>
                    <div 
                      className="text-4xl font-bold"
                      style={{
                        background: 'linear-gradient(135deg, #FF9999 0%, #DC3C8C 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        filter: 'drop-shadow(0 0 4px rgba(255, 153, 153, 0.2)) drop-shadow(0 0 8px rgba(220, 60, 140, 0.15))'
                      }}
                    >
                      {finalRisk.toFixed(1)}
                    </div>
                  </div>
                  <div 
                    className={`px-4 py-1 rounded-full text-sm font-bold whitespace-nowrap mt-1 ml-2 ${getRiskBoxStyle(finalRisk)}`}
                    style={{
                      borderColor: finalRisk < 40 ? '#00FF00' : finalRisk < 70 ? '#FFFF00' : '#FF0000'
                    }}
                  >
                    {getRiskLabel(finalRisk)}
                  </div>
                </div>

                {/* Confidence */}
                {confidence > 0 && (
                  <div className="md:col-span-1 flex flex-col justify-center">
                    <div className="text-safety-orange/70 text-xs uppercase tracking-wider mb-1">
                      Confidence
                    </div>
                    <div className="text-2xl font-bold text-safety-orange">
                      {(confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                )}

                {/* Injury Criteria */}
                <div className="md:col-span-1">
                  <div className="text-safety-orange/70 text-xs uppercase tracking-wider mb-2">
                    Key Metrics
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-safety-orange/60">HIC15:</span>{' '}
                      <span className="text-gray-500 font-medium">
                        {sim.baseline?.HIC15?.toFixed(0) || 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-safety-orange/60">Nij:</span>{' '}
                      <span className="text-gray-500 font-medium">
                        {sim.baseline?.Nij?.toFixed(2) || 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-safety-orange/60">Chest:</span>{' '}
                      <span className="text-gray-500 font-medium">
                        {sim.baseline?.chest_A3ms_g?.toFixed(0) || 'N/A'}g
                      </span>
                    </div>
                    <div>
                      <span className="text-safety-orange/60">Femur:</span>{' '}
                      <span className="text-gray-500 font-medium">
                        {sim.baseline?.femur_load_kN?.toFixed(1) || 'N/A'}kN
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Explanation (if available) */}
              {sim.gemini_analysis?.explanation && (
                <div className="mt-4 pt-4 border-t border-safety-orange/20">
                  <p className="text-gray-500 text-sm line-clamp-2">
                    {sim.gemini_analysis.explanation}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Pagination could go here */}
      <div className="mt-8 text-center text-safety-orange/60 text-sm">
        Showing {simulations.length} simulation{simulations.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
};

export default HistoryPage;

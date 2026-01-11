import React, { useEffect, useRef } from 'react';
import type { CrashRiskResponse } from '../types';

interface ResultsDisplayProps {
  results: CrashRiskResponse | null;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results }) => {
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (results && resultsRef.current) {
      // Auto-scroll to results
      resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [results]);

  if (!results) return null;

  const getRiskColor = (score: number) => {
    if (score < 30) return 'text-green-500';
    if (score < 60) return 'text-yellow-300';
    return 'text-red-500';
  };

  const getRiskLabel = (score: number) => {
    if (score < 30) return 'Low Risk';
    if (score < 60) return 'Moderate Risk';
    return 'High Risk';
  };

  const getRiskBoxStyle = (score: number) => {
    if (score < 30) {
      return 'border-2 text-green-500 shadow-[0_0_15px_rgba(0,255,0,0.6),0_0_30px_rgba(0,255,0,0.4)]';
    }
    if (score < 60) {
      return 'border-2 text-yellow-300 shadow-[0_0_15px_rgba(255,255,0,0.6),0_0_30px_rgba(255,255,0,0.4)]';
    }
    return 'border-2 text-red-500 shadow-[0_0_15px_rgba(255,0,0,0.6),0_0_30px_rgba(255,0,0,0.4)]';
  };

  return (
    <div ref={resultsRef} className="mt-12 pb-12">
      <div className="border-2 border-safety-orange/50 rounded-lg p-8 bg-safety-gray/30 shadow-[0_0_15px_rgba(220,60,140,0.2),0_0_30px_rgba(160,80,200,0.15)] hover:shadow-[0_0_20px_rgba(220,60,140,0.3),0_0_40px_rgba(160,80,200,0.2)] transition-all duration-300">
        <h2 className="text-3xl font-bold mb-8 text-center bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent">
          Risk Assessment Results
        </h2>

        {/* Risk Score */}
        <div className="bg-safety-black/50 rounded-lg p-8 mb-6 text-center">
          <div className="text-safety-orange/70 text-sm uppercase tracking-wider mb-2">
            Overall Risk Score
          </div>
          <div 
            className="text-7xl font-bold mb-6"
            style={{
              background: 'linear-gradient(135deg, #FF9999 0%, #DC3C8C 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              filter: 'drop-shadow(0 0 8px rgba(255, 153, 153, 0.3)) drop-shadow(0 0 15px rgba(220, 60, 140, 0.2))'
            }}
          >
            {results.risk_score.toFixed(1)}
          </div>
          <div 
            className={`inline-block px-6 py-2 rounded-full text-xl font-bold mb-8 ${getRiskBoxStyle(results.risk_score)}`}
            style={{
              borderColor: results.risk_score < 30 ? '#00FF00' : results.risk_score < 60 ? '#FFFF00' : '#FF0000'
            }}
          >
            {getRiskLabel(results.risk_score)}
          </div>

          {/* Confidence */}
          <div className="pt-6 border-t border-safety-orange/30">
            <div className="text-safety-orange/70 text-sm uppercase tracking-wider mb-2">
              Confidence Level
            </div>
            <div className="text-3xl font-bold text-gray-600">
              {(results.confidence * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Explanation */}
        <div className="bg-safety-black/30 rounded-lg p-6 mb-6">
          <h3 className="text-xl font-bold mb-4 bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent">Analysis</h3>
          <p className="text-gray-500 leading-relaxed whitespace-pre-wrap">
            {results.explanation}
          </p>
        </div>

        {/* Gender Bias Insights */}
        {results.gender_bias_insights && results.gender_bias_insights.length > 0 && (
          <div className="bg-safety-black/30 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-bold mb-4 bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent">
              Gender-Specific Considerations
            </h3>
            <ul className="space-y-3">
              {results.gender_bias_insights.map((insight, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-safety-orange mr-3">•</span>
                  <span className="text-gray-500">{insight}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Baseline Injury Criteria */}
        {results.baseline && results.baseline.injury_criteria && (
        <div className="bg-safety-black/30 rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4 bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent">
            Injury Criteria (Baseline Physics)
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="text-center p-3 bg-safety-gray/50 rounded">
              <div className="text-safety-orange/70 text-xs mb-1">HIC15</div>
              <div className="text-gray-500 font-bold">
                {results.baseline.injury_criteria.HIC15?.toFixed(1) ?? 'N/A'}
              </div>
            </div>
            <div className="text-center p-3 bg-safety-gray/50 rounded">
              <div className="text-safety-orange/70 text-xs mb-1">Nij</div>
              <div className="text-gray-500 font-bold">
                {results.baseline.injury_criteria.Nij?.toFixed(3) ?? 'N/A'}
              </div>
            </div>
            <div className="text-center p-3 bg-safety-gray/50 rounded">
              <div className="text-safety-orange/70 text-xs mb-1">Chest (g)</div>
              <div className="text-gray-500 font-bold">
                {results.baseline.injury_criteria.chest_A3ms_g?.toFixed(1) ?? 'N/A'}
              </div>
            </div>
            <div className="text-center p-3 bg-safety-gray/50 rounded">
              <div className="text-safety-orange/70 text-xs mb-1">Thorax (mm)</div>
              <div className="text-gray-500 font-bold">
                {results.baseline.injury_criteria.thorax_irtracc_max_deflection_proxy_mm?.toFixed(1) ?? 'N/A'}
              </div>
            </div>
            <div className="text-center p-3 bg-safety-gray/50 rounded">
              <div className="text-safety-orange/70 text-xs mb-1">Femur (kN)</div>
              <div className="text-gray-500 font-bold">
                {results.baseline.injury_criteria.femur_load_kN?.toFixed(1) ?? 'N/A'}
              </div>
            </div>
          </div>
        </div>
        )}

        {/* Data Sources */}
        {results.data_sources && results.data_sources.length > 0 && (
          <div className="mt-6 pt-6 border-t border-safety-orange/30">
            <h4 className="text-sm font-bold text-safety-orange/70 mb-3 uppercase tracking-wider">
              Data Sources
            </h4>
            <div className="space-y-2">
              {results.data_sources.map((source, index) => (
                <a
                  key={index}
                  href={source}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-500 hover:text-safety-orange text-xs block truncate transition-colors"
                >
                  {source}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultsDisplay;

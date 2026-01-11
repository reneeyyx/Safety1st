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
    if (score < 30) return 'text-green-400';
    if (score < 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getRiskLabel = (score: number) => {
    if (score < 30) return 'Low Risk';
    if (score < 60) return 'Moderate Risk';
    return 'High Risk';
  };

  return (
    <div ref={resultsRef} className="mt-12 pb-12">
      <div className="border-2 border-safety-orange rounded-lg p-8 bg-safety-gray/50">
        <h2 className="text-3xl font-bold text-safety-orange mb-8 text-center">
          Risk Assessment Results
        </h2>

        {/* Risk Score */}
        <div className="bg-safety-black/50 rounded-lg p-8 mb-6 text-center">
          <div className="text-safety-orange/70 text-sm uppercase tracking-wider mb-2">
            Overall Risk Score
          </div>
          <div className={`text-7xl font-bold ${getRiskColor(results.risk_score)} mb-2`}>
            {results.risk_score.toFixed(1)}
          </div>
          <div className="text-2xl font-semibold text-safety-orange">
            {getRiskLabel(results.risk_score)}
          </div>

          {/* Confidence */}
          <div className="mt-6 pt-6 border-t border-safety-orange/30">
            <div className="text-safety-orange/70 text-sm uppercase tracking-wider mb-2">
              Confidence Level
            </div>
            <div className="text-3xl font-bold text-safety-orange">
              {(results.confidence * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Explanation */}
        <div className="bg-safety-black/30 rounded-lg p-6 mb-6">
          <h3 className="text-xl font-bold text-safety-orange mb-4">Analysis</h3>
          <p className="text-safety-orange/90 leading-relaxed whitespace-pre-wrap">
            {results.explanation}
          </p>
        </div>

        {/* Gender Bias Insights */}
        {results.gender_bias_insights && results.gender_bias_insights.length > 0 && (
          <div className="bg-safety-black/30 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-bold text-safety-orange mb-4">
              Gender-Specific Considerations
            </h3>
            <ul className="space-y-3">
              {results.gender_bias_insights.map((insight, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-safety-orange mr-3">•</span>
                  <span className="text-safety-orange/90">{insight}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Baseline Injury Criteria */}
        <div className="bg-safety-black/30 rounded-lg p-6">
          <h3 className="text-xl font-bold text-safety-orange mb-4">
            Injury Criteria (Baseline Physics)
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="text-center p-3 bg-safety-gray/50 rounded">
              <div className="text-safety-orange/70 text-xs mb-1">HIC15</div>
              <div className="text-safety-orange font-bold">
                {results.baseline.injury_criteria.HIC15.toFixed(1)}
              </div>
            </div>
            <div className="text-center p-3 bg-safety-gray/50 rounded">
              <div className="text-safety-orange/70 text-xs mb-1">Nij</div>
              <div className="text-safety-orange font-bold">
                {results.baseline.injury_criteria.Nij.toFixed(3)}
              </div>
            </div>
            <div className="text-center p-3 bg-safety-gray/50 rounded">
              <div className="text-safety-orange/70 text-xs mb-1">Chest (g)</div>
              <div className="text-safety-orange font-bold">
                {results.baseline.injury_criteria.chest_A3ms_g.toFixed(1)}
              </div>
            </div>
            <div className="text-center p-3 bg-safety-gray/50 rounded">
              <div className="text-safety-orange/70 text-xs mb-1">Thorax (mm)</div>
              <div className="text-safety-orange font-bold">
                {results.baseline.injury_criteria.thorax_irtracc_max_deflection_proxy_mm.toFixed(1)}
              </div>
            </div>
            <div className="text-center p-3 bg-safety-gray/50 rounded">
              <div className="text-safety-orange/70 text-xs mb-1">Femur (kN)</div>
              <div className="text-safety-orange font-bold">
                {results.baseline.injury_criteria.femur_load_kN.toFixed(1)}
              </div>
            </div>
          </div>
        </div>

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
                  className="text-safety-orange/60 hover:text-safety-orange text-xs block truncate transition-colors"
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

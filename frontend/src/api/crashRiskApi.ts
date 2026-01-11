import axios from 'axios';
import type { CrashRiskRequest, CrashRiskResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

export const evaluateCrashRisk = async (
  data: CrashRiskRequest
): Promise<CrashRiskResponse> => {
  try {
    const response = await axios.post<CrashRiskResponse>(
      `${API_BASE_URL}/api/evaluate-crash`,
      data,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.message || 'Failed to evaluate crash risk');
    }
    throw new Error('Network error. Please check your connection.');
  }
};

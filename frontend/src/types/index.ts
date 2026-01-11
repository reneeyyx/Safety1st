export interface CarData {
  impact_speed_kmh: number;
  crash_side: 'frontal' | 'side' | 'rear';
  vehicle_mass_kg: number;
  crumple_zone_length_m: number;
  cabin_rigidity: 'low' | 'medium' | 'high';
  intrusion_cm: number;
  seatbelt_used: boolean;
  seatbelt_pretensioner: boolean;
  seatbelt_load_limiter: boolean;
  front_airbag: boolean;
  side_airbag: boolean;
}

export interface DummyData {
  occupant_mass_kg: number;
  occupant_height_m: number;
  gender: 'male' | 'female';
  is_pregnant: boolean;
  seat_position: 'driver' | 'passenger';
  seat_distance_from_wheel_cm: number;
  seat_recline_angle_deg: number;
  seat_height_relative_to_dash_cm: number;
  neck_strength: 'weak' | 'average' | 'strong';
  pelvis_lap_belt_fit: 'poor' | 'average' | 'good';
}

export interface CrashRiskRequest {
  car_data: CarData;
  dummy_data: DummyData;
}

export interface CrashRiskResponse {
  success: boolean;
  risk_score: number;
  confidence: number;
  explanation: string;
  gender_bias_insights: string[];
  baseline: {
    risk_score: number;
    injury_criteria: {
      HIC15: number;
      Nij: number;
      chest_A3ms_g: number;
      thorax_irtracc_max_deflection_proxy_mm: number;
      femur_load_kN: number;
    };
  };
  data_sources: string[];
}

export interface FormErrors {
  [key: string]: string;
}

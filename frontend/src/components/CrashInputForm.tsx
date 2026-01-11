import React, { useState } from 'react';
import type { CarData, DummyData } from '../types';

interface CrashInputFormProps {
  onSubmit: (carData: CarData, dummyData: DummyData) => void;
}

// Default values based on gender
const getDefaultValues = (gender: 'male' | 'female', isPregnant: boolean) => {
  if (gender === 'female') {
    if (isPregnant) {
      return {
        occupant_mass_kg: 70, // Pregnant woman average
        occupant_height_m: 1.63, // Average female height
      };
    }
    return {
      occupant_mass_kg: 62, // 50th percentile female
      occupant_height_m: 1.63,
    };
  }
  return {
    occupant_mass_kg: 75, // 50th percentile male
    occupant_height_m: 1.75,
  };
};

const CrashInputForm: React.FC<CrashInputFormProps> = ({ onSubmit }) => {
  // Car parameters
  const [impactSpeed, setImpactSpeed] = useState<string>('50');
  const [crashSide, setCrashSide] = useState<'frontal' | 'left' | 'right'>('frontal');
  const [vehicleMass, setVehicleMass] = useState<string>('1500');
  const [crumpleZone, setCrumpleZone] = useState<string>('0.6');
  const [cabinRigidity, setCabinRigidity] = useState<'low' | 'medium' | 'high'>('medium');
  const [seatbeltPretensioner, setSeatbeltPretensioner] = useState<boolean>(true);
  const [seatbeltLoadLimiter, setSeatbeltLoadLimiter] = useState<boolean>(true);
  const [frontAirbags, setFrontAirbags] = useState<boolean>(true);
  const [sideAirbags, setSideAirbags] = useState<boolean>(false);
  const [frontAirbagSize, setFrontAirbagSize] = useState<string>('60'); // liters
  const [sideAirbagSize, setSideAirbagSize] = useState<string>('12'); // liters

  // Dummy parameters
  const [gender, setGender] = useState<'male' | 'female'>('female');
  const [seatPosition, setSeatPosition] = useState<'driver' | 'passenger'>('driver');
  const [isPregnant, setIsPregnant] = useState<boolean>(false);

  // Auto-populated based on gender
  const defaultValues = getDefaultValues(gender, isPregnant);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const carData: CarData = {
      impact_speed_kmh: parseFloat(impactSpeed) || 50,
      crash_side: crashSide,
      vehicle_mass_kg: parseFloat(vehicleMass) || 1500,
      crumple_zone_length_m: parseFloat(crumpleZone) || 0.6,
      cabin_rigidity: cabinRigidity,
      intrusion_cm: 0,
      seatbelt_used: true,
      seatbelt_pretensioner: seatbeltPretensioner,
      seatbelt_load_limiter: seatbeltLoadLimiter,
      front_airbag: frontAirbags,
      side_airbag: sideAirbags,
    };

    const dummyData: DummyData = {
      occupant_mass_kg: defaultValues.occupant_mass_kg,
      occupant_height_m: defaultValues.occupant_height_m,
      gender: gender,
      is_pregnant: isPregnant,
      seat_position: seatPosition,
      seat_distance_from_wheel_cm: 30,
      seat_recline_angle_deg: 25,
      seat_height_relative_to_dash_cm: 0,
      neck_strength: 'average',
      pelvis_lap_belt_fit: 'average',
    };

    onSubmit(carData, dummyData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Car Parameters Section */}
      <div className="bg-safety-gray/30 rounded-lg p-6 border-2 border-safety-orange/50 shadow-[0_0_15px_rgba(220,60,140,0.2),0_0_30px_rgba(160,80,200,0.15)] hover:shadow-[0_0_20px_rgba(220,60,140,0.3),0_0_40px_rgba(160,80,200,0.2)] transition-all duration-300">
        <h3 className="text-xl font-bold mb-4 pb-2 border-b border-safety-orange/30 bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent">
          Vehicle Parameters
        </h3>

        <div className="space-y-4">
          {/* Impact Speed */}
          <div>
            <label className="block text-gray-500 text-sm font-normal mb-2">
              Impact Speed (km/h) *
            </label>
            <input
              type="number"
              value={impactSpeed}
              onChange={(e) => setImpactSpeed(e.target.value)}
              className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
              required
              min="0"
              max="200"
            />
          </div>

          {/* Crash Side */}
          <div>
            <label className="block text-gray-500 text-sm font-normal mb-2">
              Crash Side *
            </label>
            <select
              value={crashSide}
              onChange={(e) => setCrashSide(e.target.value as 'frontal' | 'left' | 'right')}
              className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
              required
            >
              <option value="frontal">Frontal</option>
              <option value="left">Left</option>
              <option value="right">Right</option>
            </select>
          </div>

          {/* Vehicle Mass */}
          <div>
            <label className="block text-gray-500 text-sm font-normal mb-2">
              Vehicle Mass (kg) *
              <span className="text-safety-orange/60 font-normal text-xs ml-2">
                heavier → safer
              </span>
            </label>
            <input
              type="number"
              value={vehicleMass}
              onChange={(e) => setVehicleMass(e.target.value)}
              className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
              required
              min="500"
              max="5000"
            />
          </div>

          {/* Crumple Zone */}
          <div>
            <label className="block text-gray-500 text-sm font-normal mb-2">
              Crumple Zone Length (m)
              <span className="text-safety-orange/60 font-normal text-xs ml-2">
                longer → lower force
              </span>
            </label>
            <input
              type="number"
              step="0.1"
              value={crumpleZone}
              onChange={(e) => setCrumpleZone(e.target.value)}
              className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
              min="0.1"
              max="1.0"
            />
          </div>

          {/* Cabin Rigidity */}
          <div>
            <label className="block text-gray-500 text-sm font-normal mb-2">
              Cabin Rigidity
              <span className="text-safety-orange/60 font-normal text-xs ml-2">
                weak cabin hurts small bodies more
              </span>
            </label>
            <select
              value={cabinRigidity}
              onChange={(e) => setCabinRigidity(e.target.value as 'low' | 'medium' | 'high')}
              className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

          {/* Safety Features */}
          <div className="pt-4 border-t border-safety-orange/20">
            <div className="font-semibold mb-3 text-sm bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent">Safety Features</div>

            <div className="space-y-4">
              {/* Seatbelt Pretensioner */}
              <div>
                <label className="block text-gray-500 text-sm font-normal mb-2">
                  Seatbelt Pretensioner
                </label>
                <select
                  value={seatbeltPretensioner ? 'yes' : 'no'}
                  onChange={(e) => setSeatbeltPretensioner(e.target.value === 'yes')}
                  className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
                >
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </div>

              {/* Seatbelt Load Limiter */}
              <div>
                <label className="block text-gray-500 text-sm font-normal mb-2">
                  Seatbelt Load Limiter
                </label>
                <select
                  value={seatbeltLoadLimiter ? 'yes' : 'no'}
                  onChange={(e) => setSeatbeltLoadLimiter(e.target.value === 'yes')}
                  className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
                >
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </div>

              {/* Front Airbags */}
              <div>
                <label className="block text-gray-500 text-sm font-normal mb-2">
                  Front Airbags
                </label>
                <select
                  value={frontAirbags ? 'yes' : 'no'}
                  onChange={(e) => setFrontAirbags(e.target.value === 'yes')}
                  className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
                >
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
                
                {/* Front Airbag Size - Show when Yes */}
                {frontAirbags && (
                  <div className="mt-3 ml-4 pl-4 border-l-2 border-safety-orange/30">
                    <label className="block text-safety-orange/80 text-xs font-semibold mb-2">
                      Front Airbag Size (liters)
                    </label>
                    <input
                      type="number"
                      value={frontAirbagSize}
                      onChange={(e) => setFrontAirbagSize(e.target.value)}
                      className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
                      min="30"
                      max="100"
                      step="5"
                    />
                    <div className="text-safety-orange/60 text-xs mt-1">
                      Typical: 60-70L (driver), 50-60L (passenger)
                    </div>
                  </div>
                )}
              </div>

              {/* Side Airbags */}
              <div>
                <label className="block text-gray-500 text-sm font-normal mb-2">
                  Side Airbags
                </label>
                <select
                  value={sideAirbags ? 'yes' : 'no'}
                  onChange={(e) => setSideAirbags(e.target.value === 'yes')}
                  className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
                >
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
                
                {/* Side Airbag Size - Show when Yes */}
                {sideAirbags && (
                  <div className="mt-3 ml-4 pl-4 border-l-2 border-safety-orange/30">
                    <label className="block text-safety-orange/80 text-xs font-semibold mb-2">
                      Side Airbag Size (liters)
                    </label>
                    <input
                      type="number"
                      value={sideAirbagSize}
                      onChange={(e) => setSideAirbagSize(e.target.value)}
                      className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
                      min="8"
                      max="20"
                      step="1"
                    />
                    <div className="text-safety-orange/60 text-xs mt-1">
                      Typical: 10-15L (torso), 8-12L (head)
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dummy Parameters Section */}
      <div className="bg-safety-gray/30 rounded-lg p-6 border-2 border-safety-orange/50 shadow-[0_0_15px_rgba(220,60,140,0.2),0_0_30px_rgba(160,80,200,0.15)] hover:shadow-[0_0_20px_rgba(220,60,140,0.3),0_0_40px_rgba(160,80,200,0.2)] transition-all duration-300">
        <h3 className="text-xl font-bold mb-4 pb-2 border-b border-safety-orange/30 bg-gradient-to-r from-[rgba(220,60,140,0.7)] to-[rgba(160,80,200,0.7)] bg-clip-text text-transparent">
          Occupant Parameters
        </h3>

        <div className="space-y-4">
          {/* Gender */}
          <div>
            <label className="block text-gray-500 text-sm font-normal mb-2">
              Sex *
            </label>
            <select
              value={gender}
              onChange={(e) => {
                setGender(e.target.value as 'male' | 'female');
                if (e.target.value === 'male') setIsPregnant(false);
              }}
              className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
              required
            >
              <option value="female">Female</option>
              <option value="male">Male</option>
            </select>
          </div>

          {/* Seat Position */}
          <div>
            <label className="block text-gray-500 text-sm font-normal mb-2">
              Seat Position *
            </label>
            <select
              value={seatPosition}
              onChange={(e) => setSeatPosition(e.target.value as 'driver' | 'passenger')}
              className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
              required
            >
              <option value="driver">Driver</option>
              <option value="passenger">Passenger</option>
            </select>
          </div>

          {/* Pregnancy - Only show for females */}
          {gender === 'female' && (
            <div className="pt-4 border-t border-safety-orange/20">
              <label className="block text-gray-500 text-sm font-normal mb-2">
                Pregnant
              </label>
              <select
                value={isPregnant ? 'yes' : 'no'}
                onChange={(e) => setIsPregnant(e.target.value === 'yes')}
                className="w-full bg-safety-black border border-safety-orange/50 rounded px-4 py-2 text-gray-500 focus:outline-none focus:border-safety-orange"
              >
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </div>
          )}

          {/* Auto-populated values info */}
          <div className="pt-4 mt-4 border-t border-safety-orange/20 bg-safety-black/30 rounded p-4">
            <div className="text-safety-orange/60 text-sm mb-2">
              Auto-populated based on selection:
            </div>
            <div className="text-gray-500 text-sm space-y-1">
              <div>• Occupant Mass: {defaultValues.occupant_mass_kg} kg</div>
              <div>• Occupant Height: {defaultValues.occupant_height_m} m</div>
              <div>• Neck Strength: Average</div>
              <div>• Pelvis/Lap Belt Fit: Average</div>
            </div>
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        className="w-full py-4 px-6 text-lg font-bold rounded-2xl transition-all duration-300 hover:scale-105 backdrop-blur-md border border-safety-orange/30 glow-button"
        style={{
          background: 'radial-gradient(circle at center, rgba(220, 60, 140, 0.2) 0%, rgba(0, 0, 0, 0.8) 100%)',
          color: 'rgba(220, 60, 140, 0.95)'
        }}
      >
        Calculate Risk Score
      </button>
    </form>
  );
};

export default CrashInputForm;

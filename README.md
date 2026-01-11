# Safety1st - Gender-Focused Car Crash Risk Calculator

**"Car safety wasn't built for her."**

A sophisticated crash risk assessment tool that addresses the historical bias in automotive safety testing. Women are **17-73% more likely** to be seriously injured in the same crash due to vehicles being designed and tested primarily for male occupants. Safety1st provides physics-based biomechanical modeling with explicit attention to gender-specific vulnerabilities.

## Core Mission

- Use **female occupants as the default** (not an afterthought)
- Apply validated biomechanical models with gender-specific adjustments
- Educate manufacturers about gender disparities in crash safety
- Provide actionable insights for designing safer vehicles for all body types

## Key Features

- **Three-Layer Risk Assessment**: Physics baseline → Real-world research → AI synthesis
- **Gender-Specific Modeling**: 20% chest deflection penalty for females, seating position differences, pregnancy modeling
- **Interactive Unity Simulations**: Real-time 3D crash visualizations (male/female, frontal/left/right)
- **AI-Enhanced Analysis**: Google Gemini provides contextual risk adjustment with confidence scoring
- **Real-World Research**: Live web scraping from IIHS, WHO, and CDC for latest crash data
- **Accessibility First**: 5 accessibility modes (high contrast, colorblind safe, dyslexia-friendly, large text, reduced motion)
- **Simulation History**: MongoDB-backed history tracking for all past simulations

## Tech Stack

### Frontend
- **React 18.2 + TypeScript** - Type-safe UI development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Custom theme with magenta/purple gradient design
- **Axios** - HTTP client for API communication
- **Unity WebGL** - Embedded 3D crash simulations via iframe
- **Context API** - Accessibility settings management

### Backend
- **Python 3.x + Flask** - REST API server
- **MongoDB Atlas** - Cloud database for simulation history
- **Google Gemini API** - AI-enhanced risk analysis with confidence scoring
- **BeautifulSoup + httpx** - Web scraping for real-world crash data
- **Pydantic** - Type-safe data validation
- **NumPy** - Numerical calculations for biomechanical modeling

### Simulation
- **Unity** - 3D crash scene development
- **WebGL Build** - Browser-based rendering (no plugins required)
- **Available Simulations**:
  - Male: frontal, left, right
  - Female: frontal, left, right
  - Pregnant Female: frontal, left, right

## Project Structure

```
Safety1st/
├── frontend/                           # React web application
│   ├── src/
│   │   ├── components/
│   │   │   ├── LandingPage.tsx        # Landing page
│   │   │   ├── CrashInputForm.tsx     # Vehicle & occupant parameters
│   │   │   ├── UnitySimulation.tsx    # Unity iframe integration
│   │   │   ├── ResultsDisplay.tsx     # Risk score + AI explanation
│   │   │   ├── HistoryPage.tsx        # Past simulations viewer
│   │   │   ├── AccessibilitySettings.tsx  # 5 accessibility modes
│   │   │   ├── ErrorModal.tsx         # Error handling UI
│   │   │   └── LoadingModal.tsx       # Loading states
│   │   ├── contexts/
│   │   │   └── AccessibilityContext.tsx  # Accessibility state management
│   │   ├── api/
│   │   │   └── crashRiskApi.ts        # API client (Axios)
│   │   ├── types/
│   │   │   └── index.ts               # TypeScript interfaces
│   │   ├── App.tsx                    # Main app + routing
│   │   └── App.css                    # Accessibility mode styles
│   ├── public/
│   │   ├── front_man/                 # Male frontal Unity build
│   │   │   ├── Build/                 # WebGL assets
│   │   │   ├── TemplateData/
│   │   │   └── index.html
│   │   ├── left_man/                  # Male left Unity build
│   │   ├── right_man/                 # Male right Unity build
│   │   ├── front_woman/               # Female frontal Unity build
│   │   ├── left_woman/                # Female left Unity build
│   │   ├── right_woman/               # Female right Unity build
│   │   ├── front_pregnant_woman/      # Pregnant frontal Unity build
│   │   ├── left_pregnant_woman/       # Pregnant left Unity build
│   │   └── right_pregnant_woman/      # Pregnant right Unity build
│   ├── tailwind.config.js             # Custom theme (magenta/purple)
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                            # Python Flask API
│   ├── src/
│   │   ├── api/
│   │   │   └── routes.py              # API endpoints (839 lines)
│   │   ├── models/
│   │   │   ├── carDataModel.py        # Vehicle parameters (Pydantic)
│   │   │   ├── dummyDataModel.py      # Occupant parameters (Pydantic)
│   │   │   └── simulationModel.py     # MongoDB document schema
│   │   ├── modeling/
│   │   │   ├── calculator.py          # Physics-based biomechanical calculator (975 lines)
│   │   │   └── geminiAPI.py           # Gemini API integration (410 lines)
│   │   ├── scraper/
│   │   │   ├── scraper.py             # Main scraper orchestration
│   │   │   ├── search.py              # Query building (gender-aware)
│   │   │   ├── parse.py               # HTML text extraction
│   │   │   └── filter.py              # Relevance filtering (20 keywords)
│   │   ├── database/
│   │   │   ├── mongodb.py             # Singleton connection manager
│   │   │   └── __init__.py            # DB initialization + indexing
│   │   ├── config/
│   │   │   └── settings.py            # Configuration constants
│   │   └── main.py                    # Flask app initialization
│   ├── requirements.txt
│   └── .env                            # API keys, MongoDB URI
│
├── PHYSICS_CALCULATION_PRESENTATION.md # Technical documentation
├── .gitignore                          # Git configuration (includes Unity builds)
└── README.md
```

## Three-Layer Risk Assessment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT (React)                       │
│  • Vehicle params  • Occupant params  • Safety features     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              LAYER 1: BASELINE PHYSICS                      │
│                (calculator.py - 975 lines)                  │
│  • Crash dynamics (delta-v, crash pulse)                    │
│  • Injury criteria (HIC15, Nij, THOR-05F, KTH femur)       │
│  • Gender-specific adjustments (chest deflection +20%)      │
│  • Injury probability conversion (logistic curves)          │
│  → Baseline Risk Score (0-100)                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         LAYER 2: WEB SCRAPER (scraper/)                     │
│  • Gender-aware query building (20 keywords)                │
│  • IIHS, WHO, CDC data fetching                             │
│  • HTML parsing with BeautifulSoup                          │
│  • Relevance filtering (female, pregnant, small stature)    │
│  → Scraped Context (research snippets)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           LAYER 3: AI SYNTHESIS (geminiAPI.py)              │
│  • Baseline physics + scraped research                      │
│  • Risk adjustment (±5-15 points typical, ±20 max)          │
│  • Confidence score (0-100)                                 │
│  • Detailed explanation generation                          │
│  • Gender bias insights extraction                          │
│  → Final Risk Score + Explanation + Gender Considerations   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              MONGODB + USER DISPLAY                         │
│  • Save to history  • Return JSON  • React renders          │
└─────────────────────────────────────────────────────────────┘
```

## Gender-Specific Risk Factors

### 1. Anthropometric Differences
- **50th Percentile Male**: 75 kg, 1.75 m (historical crash test standard)
- **50th Percentile Female**: 62 kg, 1.63 m (used as default in this app)
- Body segment scaling: Head (6.3%), torso (46.7%), legs (13.3%)
- Pregnancy: Torso mass +15%, chest deflection +10%

### 2. Biomechanical Vulnerabilities
- **Chest Deflection**: Females experience **+20% more deflection** for same impact force
  - Reason: Smaller ribcage, less muscle mass, lower bone density
  - Pregnancy: Additional +10% deflection
- **Seating Position**: Females sit closer (avg 25cm vs 35cm from wheel)
  - <0.15m: +50% deflection (airbag deploying during impact)
  - 0.15-0.30m: +15% deflection (suboptimal airbag timing)
- **Neck Strength**: Weak (typical female) = 1.3× Nij value vs average
- **Pelvis Fit**: Poor fit (typical pregnant/short torso) = +25% femur force

### 3. Airbag Sizing Mismatch
- **Optimal Rule**: 0.85-0.95 liters per kg of occupant mass
- **60 kg female**: Standard 60L airbag is 11% oversized → +5% deflection
- **75 kg male**: Standard 60L airbag is 10% undersized → +5% deflection
- **90 kg male**: Standard 60L airbag is 26% undersized → +15% deflection

### 4. Injury Criteria (Validated Biomechanical Models)
- **HIC15**: Head Injury Criterion (15ms sliding window)
- **Nij**: Neck Injury Criterion (dynamic SDOF head-neck model)
- **THOR-05F Thorax**: Female-specific chest deflection (IRF injury risk function)
- **KTH Femur**: Femur load with pelvis fit adjustments
- **Correlation-Adjusted Combination**: `P(any injury) = 1 - [Π(1 - p_i)]^0.75`

## API Endpoints

### POST `/api/evaluate-crash`
**Primary endpoint**: Physics + Scraper + AI synthesis

Request:
```json
{
  "car_data": {
    "impact_speed_kmh": 50,
    "vehicle_mass_kg": 1500,
    "crash_side": "frontal",
    "crumple_zone_length_m": 0.7,
    "cabin_rigidity": "medium",
    "intrusion_cm": 10,
    "seatbelt_used": true,
    "seatbelt_pretensioner": true,
    "seatbelt_load_limiter": true,
    "front_airbag": true,
    "side_airbag": true,
    "airbag_capacity_liters": 60
  },
  "dummy_data": {
    "occupant_mass_kg": 62,
    "occupant_height_m": 1.63,
    "gender": "female",
    "is_pregnant": false,
    "seat_position": "driver",
    "seat_distance_from_wheel_cm": 25,
    "seat_recline_angle_deg": 22,
    "seat_height_relative_to_dash_cm": 2,
    "neck_strength": "average",
    "pelvis_lap_belt_fit": "average"
  }
}
```

Response:
```json
{
  "success": true,
  "risk_score": 42.5,
  "confidence": 87,
  "explanation": "Detailed multi-paragraph analysis...",
  "gender_bias_insights": [
    "Females sit closer to airbag (avg 25cm vs 35cm for males)...",
    "Standard airbags designed for 75kg male..."
  ],
  "baseline": {
    "risk_score": 38.2,
    "injury_criteria": {
      "HIC15": 485.3,
      "Nij": 0.62,
      "chest_A3ms_g": 48.7,
      "thorax_irtracc_max_deflection_proxy_mm": 38.4,
      "femur_load_kN": 3.8
    }
  },
  "data_sources": [
    "https://www.iihs.org/topics/fatality-statistics/detail/males-and-females",
    "https://www.iihs.org/topics/bibliography/ref/2331"
  ]
}
```

### POST `/api/crash-risk/calculate`
**Baseline physics only** (no scraper or AI)

### GET `/api/history`
**Retrieve all past simulations** for current session

### GET `/api/history/<id>`
**Get specific simulation** by ID

### DELETE `/api/history/<id>`
**Delete simulation** from history

## Setup Instructions

### Prerequisites
- **Python 3.8+**
- **Node.js 16+**
- **MongoDB Atlas account** (free tier works)
- **Google Gemini API key** (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
# Add the following:
GEMINI_API_KEY=your_gemini_api_key_here
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/safety1st
FLASK_ENV=development
PRODUCTION_SAFETY_THRESHOLD=40

# Run the server (port 5001)
python src/main.py
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
# Add the following:
VITE_API_URL=http://localhost:5001

# Run development server (port 5173)
npm run dev
```

### Unity Simulation Setup (Optional - Already Included)

Unity WebGL builds are already included in `frontend/public/`. To add new simulations:

1. Open Unity project
2. Create crash scene with car model and crash test dummy
3. Implement physics-based collision (spacebar to trigger, R to reset)
4. Build for WebGL: `File > Build Settings > WebGL`
5. Copy entire folder (including Build/) to `frontend/public/your_simulation_name/`
6. Update `getSimulationPath()` in [UnitySimulation.tsx](frontend/src/components/UnitySimulation.tsx) to add new simulation

**Note**: `.gitignore` is configured to include Unity Build folders in version control via exception: `!frontend/public/*/Build/`

## Running the Application

```bash
# Terminal 1 - Backend
cd backend
venv\Scripts\activate
python src/main.py
# Server running on http://localhost:5001

# Terminal 2 - Frontend
cd frontend
npm run dev
# App running on http://localhost:5173
```

Visit `http://localhost:5173` in your browser.

## Accessibility Features

Safety1st includes **5 accessibility modes** accessible via floating button:

1. **High Contrast**: Pure black/white, 3px borders
2. **Colorblind Safe**: Blue/orange color scheme (universal)
3. **Dyslexia Friendly**: OpenDyslexic font, extra letter spacing
4. **Large Text**: 18px base font, 1.2-2.5rem headings
5. **Reduced Motion**: 0.01ms animations, auto-scroll disabled

Settings persist in localStorage across sessions.

## Data Sources

The web scraper dynamically fetches research from:
- **IIHS** (Insurance Institute for Highway Safety) - Gender fatality statistics, crash test ratings
- **WHO** (World Health Organization) - Road traffic injury data
- **CDC** - Motor vehicle safety statistics

**Gender-Aware Query Keywords** (20 total):
`female`, `women`, `gender`, `male`, `pregnant`, `pregnancy`, `small`, `stature`, `size`, `percentile`, `dummy`, `anthropometric`, `body`, `occupant`, `injury`, `risk`, `crash`, `test`, `airbag`, `seatbelt`

## Scientific Basis

- NHTSA Advanced Airbag Research
- IIHS Small Overlap Front Crash Tests
- Euro NCAP Occupant Size Testing Protocols
- THOR-05F female crash test dummy specifications
- Published logistic regression models for injury probability (Mertz et al., Kleinberger et al.)
- Real-world NCAP crash test data for restraint effectiveness validation

## Design System

### Color Palette
- **Primary**: Muted magenta (#DC3C8C) - replaces "safety yellow" to signal focus on women's safety
- **Dark Magenta**: #B0307A
- **Background**: Radial gradient #1A1A1A → #000000
- **Risk Colors**: Green (<30), Yellow (30-60), Red (60+)

### Typography
- **Primary**: Poppins (sans-serif)
- **Accessibility**: OpenDyslexic (dyslexia-friendly mode)
- **Gradient Headings**: Linear gradient from pink (#FF0080) to purple (#A020F0)

### Visual Effects
- Neon-style glow effects with magenta/purple shadows
- Gradient text using background-clip technique
- Smooth animations (fadeIn, slideUpFadeIn)

## Key Technical Decisions

1. **Female-First Design**: Default to 50th percentile female (62kg, 1.63m) instead of male
2. **Correlation-Adjusted Risk**: `corr_factor=0.75` recognizes that injuries cluster (independence assumption overestimates)
3. **Three-Layer Architecture**: Physics provides baseline, AI adjusts based on real-world research
4. **Confidence Scoring**: AI acknowledges model uncertainty (typical 80-90%)
5. **Iframe Integration**: Simple Unity embedding (no react-unity-webgl library needed)

## Future Enhancements

- Continuous weight-based chest deflection factor (not just binary <70kg / ≥70kg)
- Side crash specific injury modeling (currently uses frontal model)
- Rear crash whiplash modeling
- Age factor (elderly have different injury thresholds)
- Real crash test data validation against NHTSA star ratings
- Child occupant modeling

## Environment Variables

### Backend `.env`
```env
GEMINI_API_KEY=your_gemini_api_key
MONGODB_URI=your_mongodb_uri
FLASK_ENV=development
PRODUCTION_SAFETY_THRESHOLD=40
```

### Frontend `.env`
```env
VITE_API_URL=http://localhost:5001
```

## Contributing

This project addresses a critical safety gap in automotive engineering. Contributions focusing on:
- Additional gender-specific biomechanical research
- Validation against real-world crash test data
- Enhanced Unity simulation physics
- Accessibility improvements

are especially welcome.

## License

MIT

## Acknowledgments

Built to address the systemic gender bias in automotive safety testing. Women deserve vehicles designed for their protection, not as an afterthought.

---

**"Women are 17-73% more likely to be seriously injured in the same crash. It's time to change that."**

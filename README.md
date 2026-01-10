# Safety1st - Pre-Production Crash Design Tool

A crash simulation and risk assessment tool for car manufacturers to evaluate vehicle safety designs before production.

## Overview

Safety1st allows car manufacturers to:
- Input vehicle design parameters (mass, crumple zone, safety features)
- Configure crash test dummy details (gender, position, pregnancy status)
- Run crash simulations in Unity
- Receive AI-powered risk scores with confidence levels and detailed explanations

## Tech Stack

### Frontend
- **React** - Web application UI
- **TypeScript** - Type-safe development
- **Unity WebGL** - Embedded crash simulation

### Backend
- **Python (Flask/FastAPI)** - REST API server
- **Google Gemini API** - AI-powered risk scoring
- **Beautiful Soup / Scrapy** - Web scraping for crash test data

### Simulation
- **Unity** - 3D crash simulation
- **WebGL Build** - Browser-based rendering

## Project Structure

```
Safety1st/
├── frontend/                 # React web application
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── CarForm.tsx   # Car parameters input
│   │   │   ├── DummyForm.tsx # Dummy details input
│   │   │   ├── Simulation.tsx # Unity WebGL embed
│   │   │   └── Results.tsx   # Risk score display
│   │   ├── types/            # TypeScript types
│   │   ├── api/              # API client
│   │   └── App.tsx           # Main app component
│   ├── public/
│   └── package.json
│
├── backend/                  # Python API server
│   ├── src/
│   │   ├── api/              # API routes
│   │   │   └── routes.py
│   │   ├── models/           # Data models
│   │   │   ├── car.py
│   │   │   └── dummy.py
│   │   ├── services/
│   │   │   ├── scraper.py    # Web scraping logic
│   │   │   ├── gemini.py     # Gemini API integration
│   │   │   └── calculator.py # Risk calculation
│   │   ├── config/
│   │   │   └── settings.py
│   │   └── main.py           # Flask/FastAPI app
│   ├── requirements.txt
│   └── .env.example
│
└── simulation/               # Unity project
    ├── Assets/
    ├── ProjectSettings/
    └── Build/                # WebGL builds
        └── webapp/
```

## Data Models

### Car Parameters (User Input)
- Crash test side: `frontal` | `left` | `right`
- Vehicle mass (kg): `number`
- Crumple zone length (m): `number`
- Cabin rigidity: `low` | `med` | `high`
- Seatbelt pretensioner: `boolean`
- Seatbelt load limiter: `boolean`
- Front airbags: `boolean`
- Side airbags: `boolean`

### Dummy Details (User Input + Auto-filled)
- Gender: `male` | `female`
- Seat position: `driver` | `passenger`
- Pregnant (females only): `boolean`

**Auto-filled based on gender/pregnancy:**
- Body mass (kg)
- Height (cm)
- Neck tension (N)
- Seat distance from airbag (cm)
- Seat height relative to dash (cm)
- Upright vs reclined angle (degrees)
- Torso length (cm)
- Pelvis vs lap belt fit (score)

### API Response
```json
{
  "riskScore": 0-100,
  "confidenceScore": 0-100,
  "explanation": {
    "factors": [
      {
        "name": "Vehicle Mass",
        "impact": "positive|negative",
        "description": "Higher mass reduces injury risk"
      }
    ],
    "summary": "Overall risk assessment..."
  },
  "simulationData": { }
}
```

## Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask flask-cors google-generativeai beautifulsoup4 requests python-dotenv

# Create .env file
cp .env.example .env
# Add your Gemini API key: GEMINI_API_KEY=your_key_here

# Run the server
python src/main.py
```

### 2. Frontend Setup

```bash
cd frontend

# Initialize React app (if not done)
npx create-react-app . --template typescript

# Install dependencies
npm install axios

# Run development server
npm start
```

### 3. Unity Simulation Setup

1. Open Unity Hub
2. Create new 3D project in `simulation/` directory
3. Build crash simulation scene
4. Build for WebGL: `File > Build Settings > WebGL`
5. Place build output in `simulation/Build/webapp/`

## Development Workflow

### Step 1: Implement Backend API

1. Create data models for car and dummy parameters
2. Set up Flask/FastAPI routes
3. Implement web scraper to gather crash test data
4. Integrate Gemini API for risk scoring
5. Create risk calculation logic

### Step 2: Build Frontend Forms

1. Create car parameters form component
2. Create dummy details form component
3. Implement auto-fill logic for dummy averages
4. Set up API client to communicate with backend

### Step 3: Unity Simulation

1. Create crash scene with car model and dummy
2. Implement physics-based collision
3. Add parameter controls (mass, crumple zone, etc.)
4. Build for WebGL

### Step 4: Integration

1. Embed Unity WebGL in React app
2. Pass parameters from forms to Unity
3. Trigger simulation on form submission
4. Display results from backend API

### Step 5: Polish

1. Add loading states
2. Error handling
3. Responsive design
4. Demo data presets

## API Endpoints

### POST /api/simulate
Request body:
```json
{
  "car": {
    "crashSide": "frontal",
    "vehicleMass": 1500,
    "crumpleZoneLength": 0.8,
    "cabinRigidity": "med",
    "seatbeltPretensioner": true,
    "seatbeltLoadLimiter": true,
    "frontAirbags": true,
    "sideAirbags": false
  },
  "dummy": {
    "gender": "female",
    "seatPosition": "driver",
    "pregnant": true
  }
}
```

Response:
```json
{
  "riskScore": 65,
  "confidenceScore": 82,
  "explanation": {
    "factors": [...],
    "summary": "..."
  }
}
```

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
GEMINI_API_KEY=your_gemini_api_key
FLASK_ENV=development
PORT=5000
```

## Running the Full Stack

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python src/main.py

# Terminal 2 - Frontend
cd frontend
npm start

# Unity simulation will be embedded in the React app
```

## Hackathon Priorities

1. **Core functionality first**: Form input → API call → Risk score display
2. **Unity simulation**: Can be simplified or mocked initially
3. **Web scraper**: Can use hardcoded data initially
4. **Gemini integration**: Focus on getting a working prompt/response
5. **Polish last**: UI/UX improvements at the end

## Git Workflow

```bash
# Commit frequently
git add .
git commit -m "Descriptive message"
git push origin main

# For team collaboration
git checkout -b feature/your-feature
# ... make changes ...
git push origin feature/your-feature
```

## Team Distribution

- **Frontend Dev**: React forms, Unity embedding, results display
- **Backend Dev**: API, Gemini integration, risk calculations
- **Unity Dev**: Crash simulation, WebGL build
- **Full-stack/Integration**: Connecting all pieces, testing

## Resources

- [Gemini API Docs](https://ai.google.dev/docs)
- [Unity WebGL Build](https://docs.unity3d.com/Manual/webgl-building.html)
- [React-Unity-WebGL](https://github.com/jeffreylanters/react-unity-webgl)
- [Flask CORS](https://flask-cors.readthedocs.io/)

## License

MIT

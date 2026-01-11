"""
Gemini API integration for crash risk analysis.
Combines baseline physics calculations with scraped safety data to produce
AI-enhanced risk scores, confidence levels, and detailed explanations.
"""

import google.generativeai as genai
from typing import Dict, Any, List
from config.settings import Config


# Configure Gemini API
if Config.GEMINI_API_KEY:
    genai.configure(api_key=Config.GEMINI_API_KEY)


class GeminiAnalysisResult:
    """Container for Gemini analysis results"""
    def __init__(self, risk_score: float, confidence: float, explanation: str,
                 gender_bias_insights: List[str] = None):
        self.risk_score = risk_score  # 0-100
        self.confidence = confidence  # 0-1
        self.explanation = explanation
        self.gender_bias_insights = gender_bias_insights or []


def build_gemini_prompt(
    baseline_results: Dict[str, Any],
    scraped_context: Dict[str, Any]
) -> str:
    """
    Build comprehensive prompt for Gemini combining baseline calculation
    and scraped safety data.

    Args:
        baseline_results: Output from calculate_baseline_risk()
        scraped_context: Output from scrape_safety_data() with keys:
            - summaryText: str
            - genderBiasNotes: List[str]
            - dataSources: List[str]

    Returns:
        Formatted prompt string for Gemini
    """

    # Extract key metrics
    hic15 = baseline_results.get('HIC15', 0)
    nij = baseline_results.get('Nij', 0)
    chest_a3ms = baseline_results.get('chest_A3ms_g', 0)
    chest_deflection_mm = baseline_results.get('thorax_irtracc_max_deflection_proxy_mm', 0)
    femur_load_kn = baseline_results.get('femur_load_kN', 0)
    baseline_risk = baseline_results.get('risk_score_0_100', 0)

    # Occupant details
    gender = baseline_results.get('occupant_gender', 'unknown')
    is_pregnant = baseline_results.get('is_pregnant', False)
    mass_kg = baseline_results.get('occupant_mass_kg', 0)
    height_m = baseline_results.get('occupant_height_m', 0)
    seat_position = baseline_results.get('seat_position', 'driver')
    pelvis_fit = baseline_results.get('pelvis_lap_belt_fit', 'average')

    # Crash details
    crash_type = baseline_results.get('crash_configuration', 'unknown')
    delta_v = baseline_results.get('delta_v_mps', 0)
    restraint = baseline_results.get('restraint_type', 'unknown')

    # Scraped context
    summary_text = scraped_context.get('summaryText', 'No external data available.')
    gender_bias_notes = scraped_context.get('genderBiasNotes', [])
    data_sources = scraped_context.get('dataSources', [])

    prompt = f"""You are an expert automotive safety analyst specializing in crash biomechanics and injury risk assessment.

Your task is to analyze crash test data and provide a comprehensive risk assessment with focus on gender-specific injury patterns.

## BASELINE PHYSICS CALCULATION

**Crash Configuration:**
- Type: {crash_type}
- Delta-V: {delta_v:.2f} m/s
- Restraint System: {restraint}

**Occupant Details:**
- Gender: {gender}
- Mass: {mass_kg} kg
- Height: {height_m} m
- Pregnant: {'Yes' if is_pregnant else 'No'}
- Seat Position: {seat_position}
- Pelvis/Lap Belt Fit: {pelvis_fit}

**Injury Criteria:**
- HIC15: {hic15:.1f} (head injury criterion)
- Nij: {nij:.3f} (neck injury criterion)
- Chest 3ms: {chest_a3ms:.1f} g (chest acceleration)
- Chest Deflection: {chest_deflection_mm:.1f} mm
- Femur Load: {femur_load_kn:.1f} kN

**Baseline Risk Score: {baseline_risk:.1f}/100**

## EXTERNAL SAFETY DATA

{summary_text}

**Gender-Specific Findings from Research:**
"""

    if gender_bias_notes:
        for i, note in enumerate(gender_bias_notes, 1):
            prompt += f"\n{i}. {note}"
    else:
        prompt += "\n(No specific gender-focused data found in external sources)"

    prompt += f"""

**Data Sources:**
"""

    if data_sources:
        for source in data_sources:
            prompt += f"\n- {source}"
    else:
        prompt += "\n(No external sources scraped)"

    prompt += f"""

## YOUR TASK

Analyze the above data and provide:

1. **Final Risk Score (0-100):**

   IMPORTANT: Start with the baseline risk score of **{baseline_risk:.1f}%** and make SMALL adjustments only.

   The baseline is physics-based and already accurate. Your adjustments should be:
   - **±5-15 points maximum** based on factors below
   - INCREASE risk if: research shows higher female vulnerability, pregnancy, poor restraint fit
   - DECREASE risk if: research shows better-than-expected outcomes, optimal restraints
   - DO NOT completely override the baseline - it's based on validated injury criteria

   Consider for adjustment:
   - Gender-specific vulnerabilities from research (typically +5-10% for females)
   - Pregnancy considerations (+5-15% for pregnant occupants)
   - Seat position and belt fit quality (±5%)
   - Research findings that contradict or support baseline assumptions

2. **Confidence Level (0-100):** Rate your confidence in this assessment based on:
   - Quality and relevance of external data
   - How well the occupant matches studied populations
   - Uncertainty in the baseline calculation assumptions
   - How typical the seat position and pelvis fit are for this demographic

3. **Detailed Explanation:** Provide a clear, evidence-based explanation that:
   - Lists the main injury risk factors
   - Explains how gender affects injury outcomes in this scenario
   - Highlights specific vulnerabilities (e.g., pregnant occupants, smaller stature, poor belt fit)
   - Addresses seat position differences (driver vs passenger crash dynamics)
   - Discusses pelvis/lap belt fit impact on lower body and abdominal injuries
   - References the external research where relevant
   - Mentions protective factors from safety equipment
   - Is written for a general audience (avoid excessive jargon)

4. **Gender Bias Insights:** Specific bullet points about how crash test gender bias affects this scenario

## OUTPUT FORMAT

Respond in this exact JSON format:

```json
{{
  "risk_score": <number 0-100>,
  "confidence": <number 0-100>,
  "explanation": "<multi-paragraph explanation>",
  "gender_bias_insights": [
    "<insight 1>",
    "<insight 2>",
    "<insight 3>"
  ]
}}
```

Be objective, evidence-based, and cite specific injury criteria values when explaining risk factors.
"""

    return prompt


def parse_gemini_response(response_text: str, baseline_risk: float = None) -> GeminiAnalysisResult:
    """
    Parse Gemini's JSON response into a structured result object.

    Args:
        response_text: Raw text from Gemini API
        baseline_risk: Optional baseline risk to validate against

    Returns:
        GeminiAnalysisResult object

    Raises:
        ValueError: If response cannot be parsed
    """
    import json
    import re

    # Try to extract JSON from response (handle markdown code blocks)
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to parse entire response as JSON
        json_str = response_text.strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Gemini response as JSON: {e}\nResponse: {response_text[:500]}")

    # Validate required fields
    if 'risk_score' not in data:
        raise ValueError("Gemini response missing 'risk_score' field")
    if 'confidence' not in data:
        raise ValueError("Gemini response missing 'confidence' field")
    if 'explanation' not in data:
        raise ValueError("Gemini response missing 'explanation' field")

    # Convert confidence to 0-1 scale if it's 0-100
    confidence = float(data['confidence'])
    if confidence > 1.0:
        confidence = confidence / 100.0

    risk_score = float(data['risk_score'])

    # Validate that Gemini didn't stray too far from baseline
    if baseline_risk is not None:
        max_deviation = 20.0  # Allow ±20 points max
        if abs(risk_score - baseline_risk) > max_deviation:
            print(f"WARNING: Gemini risk ({risk_score:.1f}) deviates >20 points from baseline ({baseline_risk:.1f})")
            print(f"Clamping to baseline ±{max_deviation} range")

            # Clamp to baseline ±20
            if risk_score < baseline_risk - max_deviation:
                risk_score = baseline_risk - max_deviation
            elif risk_score > baseline_risk + max_deviation:
                risk_score = baseline_risk + max_deviation

    return GeminiAnalysisResult(
        risk_score=risk_score,
        confidence=confidence,
        explanation=data['explanation'],
        gender_bias_insights=data.get('gender_bias_insights', [])
    )


async def analyze_with_gemini(
    baseline_results: Dict[str, Any],
    scraped_context: Dict[str, Any],
    model_name: str = None
) -> GeminiAnalysisResult:
    """
    Main function to analyze crash risk using Gemini AI.

    Args:
        baseline_results: Physics-based calculation results
        scraped_context: Web-scraped safety data context
        model_name: Gemini model to use (defaults to Config.GEMINI_MODEL)

    Returns:
        GeminiAnalysisResult with risk score, confidence, and explanation

    Raises:
        ValueError: If API key not configured or response invalid
        Exception: If API call fails after retries
    """
    if not Config.GEMINI_API_KEY:
        raise ValueError(
            "Gemini API key not configured. Set GEMINI_API_KEY environment variable."
        )

    # Build prompt
    prompt = build_gemini_prompt(baseline_results, scraped_context)

    # Select model
    if model_name is None:
        model_name = Config.GEMINI_MODEL

    # Initialize model
    model = genai.GenerativeModel(model_name)

    # Generate response with retry logic for quota errors
    import time
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            response_text = response.text
            break  # Success, exit retry loop

        except Exception as e:
            error_msg = str(e)

            # Check if it's a quota error
            if "quota" in error_msg.lower() or "429" in error_msg:
                if attempt < max_retries - 1:
                    # Wait with exponential backoff
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Quota exceeded, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed, return fallback analysis
                    print("Quota exceeded after all retries, using baseline analysis only")
                    return _create_fallback_analysis(baseline_results)
            else:
                # Non-quota error, fail immediately
                raise Exception(f"Gemini API call failed: {e}")

    # Parse response with baseline validation
    baseline_risk = baseline_results.get('risk_score_0_100', 50)
    result = parse_gemini_response(response_text, baseline_risk=baseline_risk)

    return result


def _create_fallback_analysis(baseline_results: Dict[str, Any]) -> GeminiAnalysisResult:
    """
    Create a fallback analysis when Gemini API is unavailable.
    Uses baseline risk score with generic but informative explanation.
    """
    baseline_risk = baseline_results.get('risk_score_0_100', 50)

    explanation = (
        f"This risk assessment is based on physics-based calculations using standard "
        f"injury criteria (HIC15, Nij, chest deflection, femur load). "
        f"The baseline risk score of {baseline_risk:.1f}% reflects the probability "
        f"of significant injury based on crash dynamics and occupant biomechanics. "
        f"AI-enhanced analysis temporarily unavailable due to API limits."
    )

    gender_bias_insights = [
        "Female occupants typically face higher injury risk due to smaller body size and different seating positions.",
        "Crash test standards have historically used average male dummies, potentially underestimating female risk.",
        "Pregnant occupants face additional risks to both maternal and fetal health during crashes."
    ]

    return GeminiAnalysisResult(
        risk_score=baseline_risk,
        confidence=0.70,  # Lower confidence without AI enhancement
        explanation=explanation,
        gender_bias_insights=gender_bias_insights
    )


def format_analysis_for_response(
    result: GeminiAnalysisResult,
    baseline_results: Dict[str, Any],
    scraped_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format Gemini analysis results for API response.

    Args:
        result: GeminiAnalysisResult from analyze_with_gemini()
        baseline_results: Original baseline calculation
        scraped_context: Original scraped data

    Returns:
        Dictionary ready for JSON response
    """
    risk_score = round(result.risk_score, 1)

    return {
        "success": True,

        # Final AI-enhanced results
        "risk_score": risk_score,
        "confidence": round(result.confidence, 4),
        "explanation": result.explanation,
        "gender_bias_insights": result.gender_bias_insights,

        # Production safety flag (based on AI-adjusted score)
        "safe_for_production": risk_score <= Config.PRODUCTION_SAFETY_THRESHOLD,
        "production_threshold": Config.PRODUCTION_SAFETY_THRESHOLD,

        # Baseline physics calculation (for transparency)
        "baseline": {
            "risk_score": baseline_results.get('risk_score_0_100'),
            "injury_criteria": {
                "HIC15": baseline_results.get('HIC15'),
                "Nij": baseline_results.get('Nij'),
                "chest_A3ms_g": baseline_results.get('chest_A3ms_g'),
                "thorax_irtracc_max_deflection_proxy_mm": baseline_results.get('thorax_irtracc_max_deflection_proxy_mm'),
                "femur_load_kN": baseline_results.get('femur_load_kN')
            },
            "injury_probabilities": {
                "P_head": baseline_results.get('P_head'),
                "P_neck": baseline_results.get('P_neck'),
                "P_chest": baseline_results.get('P_thorax_AIS3plus', baseline_results.get('P_chest', 0)),
                "P_femur": baseline_results.get('P_femur_AIS2plus_proxy', baseline_results.get('P_femur', 0)),
                "P_baseline": baseline_results.get('P_baseline')
            }
        },

        # External data sources (for citation)
        "data_sources": scraped_context.get('dataSources', []),

        # Full baseline results for advanced users
        "full_baseline_results": baseline_results
    }

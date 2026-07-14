# ai_agent.py
"""AI health report generation using Google Gemini (preferred) or OpenAI as fallback.
The function `generate_report` returns a markdown string suitable for display
and for inclusion in PDF reports.
"""
import os
import json
import streamlit as st

# Try to import Gemini client; if unavailable, fall back to OpenAI.
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None


def _get_gemini_client():
    """Initialize Gemini client using API key from Streamlit secrets or env.
    Returns a callable for chat generation or None if key missing.
    """
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    return model


def _get_openai_client():
    """Initialize OpenAI client using API key from secrets or env.
    Returns a function that calls chat completion.
    """
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    openai.api_key = api_key
    def chat(messages: list[dict]):
        response = openai.ChatCompletion.create(model="gpt-4o-mini", messages=messages)
        return response.choices[0].message.content
    return chat


def _build_prompt(patient_data: dict, prediction: dict) -> str:
    """Construct a detailed prompt for the LLM.
    `patient_data` contains the raw registration fields.
    `prediction` contains keys: prediction, risk_percentage, risk_category.
    """
    # Basic patient summary
    summary = (
        f"**Patient Name:** {patient_data.get('full_name')}\n"
        f"**Age:** {patient_data.get('age')}\n"
        f"**Gender:** {patient_data.get('gender')}\n"
        f"**Contact:** {patient_data.get('phone')} / {patient_data.get('email')}\n"
        f"**Visit Date:** {patient_data.get('visit_date')}\n"
    )
    # Medical measurements list
    measurements = (
        f"Pregnancies: {patient_data.get('pregnancies')}\n"
        f"Glucose: {patient_data.get('glucose')} mg/dL\n"
        f"Blood Pressure: {patient_data.get('blood_pressure')} mmHg\n"
        f"Skin Thickness: {patient_data.get('skin_thickness')} mm\n"
        f"Insulin: {patient_data.get('insulin')} µU/mL\n"
        f"BMI: {patient_data.get('bmi')}\n"
        f"Diabetes Pedigree Function: {patient_data.get('diabetes_pedigree')}\n"
    )
    # Prediction summary
    pred_summary = (
        f"**Prediction:** {prediction.get('prediction')}\n"
        f"**Risk Percentage:** {prediction.get('risk_percentage')}% ({prediction.get('risk_category')})\n"
    )
    # Prompt template
    prompt = (
        "You are a professional medical AI assistant. Using the patient information, "
        "medical measurements, and risk prediction below, write a concise, friendly health report. "
        "The report should include: patient summary, risk analysis, key contributing factors, "
        "personalised lifestyle and diet recommendations, exercise plan, suggested medical tests, "
        "follow‑up advice, and an urgent warning if the risk is high. Use markdown formatting.\n\n"
        f"---\nPatient Summary:\n{summary}\n---\nMeasurements:\n{measurements}\n---\nPrediction Summary:\n{pred_summary}\n---\nProvide the report now."
    )
    return prompt


def generate_report(patient_data: dict, prediction: dict) -> str:
    """Generate a markdown health report.
    Tries Gemini first; if unavailable, falls back to OpenAI. Returns the generated text.
    """
    # Build the prompt
    prompt = _build_prompt(patient_data, prediction)

    # Try Gemini
    if genai:
        model = _get_gemini_client()
        if model:
            try:
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                st.warning(f"Gemini generation failed: {e}. Falling back to OpenAI.")

    # Fallback to OpenAI
    openai_chat = _get_openai_client()
    if openai_chat:
        messages = [{"role": "user", "content": prompt}]
        try:
            return openai_chat(messages)
        except Exception as e:
            st.error(f"OpenAI generation failed: {e}")
            return "Unable to generate report at this time."
    else:
        st.error("No LLM API key configured. Please provide a Gemini or OpenAI key.")
        return "Report generation unavailable – missing API credentials."

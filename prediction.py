import streamlit as st
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from utils import validate_patient_input, get_current_timestamp, get_secret
from database import add_patient
from ai_agent import generate_report
from reports import download_pdf, download_csv
from alerts import evaluate_alerts

# Load model artifact (cached to avoid reloading on every run)
@st.cache_resource
def load_model_artifacts():
    """Load the pickled model from the repository root."""
    import joblib, os
    # Path to best_model.pkl located two directories up (Downloads folder)
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "best_model.pkl"))
    model = joblib.load(model_path)
    # Dummy scaler – identity transform
    class DummyScaler:
        def transform(self, X):
            return X
    # Feature order matching the form fields
    feature_order = [
        "Pregnancies",
        "Glucose",
        "BloodPressure",
        "SkinThickness",
        "Insulin",
        "BMI",
        "DiabetesPedigreeFunction",
        "Age",
    ]
    # Simple label map for binary classification
    label_map = {0: "Low", 1: "High"}
    return model, DummyScaler(), feature_order, label_map
        st.warning("Model files not found. Using dummy model for demonstration.")
        # Dummy model that returns equal probability for both classes
        class DummyModel:
            def predict_proba(self, X):
                # Return shape (n_samples, 2) with 0.5 each
                return np.full((X.shape[0], 2), 0.5)
        # Dummy scaler that returns input unchanged
        class DummyScaler:
            def transform(self, X):
                return X
        # Define feature order matching the form fields used in prediction
        feature_order = [
            "Pregnancies",
            "Glucose",
            "BloodPressure",
            "SkinThickness",
            "Insulin",
            "BMI",
            "DiabetesPedigreeFunction",
            "Age",
        ]
        label_map = {0: "Low", 1: "High"}
        return DummyModel(), DummyScaler(), feature_order, label_map

model, scaler, feature_order, label_map = load_model_artifacts()

def predict_risk(input_dict: dict) -> dict:
    """Run the scikit‑learn model on validated inputs.
    Returns prediction label, probability, and risk percentage.
    """
    # Arrange input according to feature_order
    X = np.array([input_dict[feat] for feat in feature_order], dtype=float).reshape(1, -1)
    X_scaled = scaler.transform(X)
    prob = model.predict_proba(X_scaled)[0]
    # Assuming binary classification with classes [0,1]
    pred_idx = np.argmax(prob)
    pred_label = label_map.get(pred_idx, str(pred_idx))
    risk_percentage = round(prob[pred_idx] * 100, 2)
    # Determine risk category
    if risk_percentage <= 30:
        risk_category = "Low"
    elif risk_percentage <= 70:
        risk_category = "Moderate"
    else:
        risk_category = "High"
    return {
        "prediction": pred_label,
        "probability": prob[pred_idx],
        "risk_percentage": risk_percentage,
        "risk_category": risk_category,
    }

def render_prediction_page():
    """Streamlit page for patient registration and diabetes prediction."""
    st.title(":pill: Register Patient & Predict Diabetes Risk")
    # ---- Patient info form ----
    with st.form("patient_form"):
        st.subheader("Patient Information")
        full_name = st.text_input("Full Name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        phone = st.text_input("Phone Number")
        email = st.text_input("Email")
        address = st.text_area("Address")
        visit_date = st.date_input("Date of Visit", value=pd.to_datetime('today'))
        st.subheader("Medical Measurements")
        pregnancies = st.number_input("Pregnancies", min_value=0, step=1)
        glucose = st.number_input("Glucose", min_value=0.0, step=0.1)
        blood_pressure = st.number_input("Blood Pressure", min_value=0.0, step=0.1)
        skin_thickness = st.number_input("Skin Thickness", min_value=0.0, step=0.1)
        insulin = st.number_input("Insulin", min_value=0.0, step=0.1)
        bmi = st.number_input("BMI", min_value=0.0, step=0.1)
        diabetes_pedigree = st.number_input("Diabetes Pedigree Function", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("Submit & Predict")

    if submitted:
        patient_data = {
            "full_name": full_name,
            "age": age,
            "gender": gender,
            "phone": phone,
            "email": email,
            "address": address,
            "visit_date": str(visit_date),
            "pregnancies": pregnancies,
            "glucose": glucose,
            "blood_pressure": blood_pressure,
            "skin_thickness": skin_thickness,
            "insulin": insulin,
            "bmi": bmi,
            "diabetes_pedigree": diabetes_pedigree,
        }
        valid, msg = validate_patient_input(patient_data)
        if not valid:
            st.error(msg)
            st.stop()
        # Prepare dict for model (feature keys must match feature_order list)
        model_input = {
            "Pregnancies": pregnancies,
            "Glucose": glucose,
            "BloodPressure": blood_pressure,
            "SkinThickness": skin_thickness,
            "Insulin": insulin,
            "BMI": bmi,
            "DiabetesPedigreeFunction": diabetes_pedigree,
            "Age": age,
        }
        with st.spinner("Running prediction..."):
            prediction = predict_risk(model_input)
        # Generate a unique patient ID (UUID4 short)
        import uuid
        patient_id = str(uuid.uuid4())[:8]
        # Store record in DB
        record = {
            "patient_id": patient_id,
            "name": full_name,
            "age": int(age),
            "gender": gender,
            "phone": phone,
            "email": email,
            "address": address,
            "visit_date": str(visit_date),
            "pregnancies": int(pregnancies),
            "glucose": float(glucose),
            "blood_pressure": float(blood_pressure),
            "skin_thickness": float(skin_thickness),
            "insulin": float(insulin),
            "bmi": float(bmi),
            "diabetes_pedigree": float(diabetes_pedigree),
            "prediction": prediction["prediction"],
            "risk_percentage": prediction["risk_percentage"],
            "recommendation": "",  # to be filled after AI report
            "created_at": get_current_timestamp(),
        }
        add_patient(record)
        # AI health report generation
        with st.spinner("Generating health report…"):
            report_text = generate_report(patient_data, prediction)
        # Update recommendation field in DB (simple update)
        from database import update_patient
        update_patient(patient_id, {"recommendation": report_text})
        # ---- Display results ----
        st.success("Prediction completed!")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Risk Category", value=prediction["risk_category"])
            st.metric(label="Risk %", value=f"{prediction['risk_percentage']}%")
        with col2:
            # Color badge based on risk
            if prediction["risk_category"] == "Low":
                color = "green"
            elif prediction["risk_category"] == "Moderate":
                color = "orange"
            else:
                color = "red"
            st.markdown(f"<h3 style='color:{color};'>🔴 {prediction['prediction']}</h3>", unsafe_allow_html=True)
        # Alerts
        alerts = evaluate_alerts(prediction, model_input)
        for al in alerts:
            if al["type"] == "error":
                st.error(al["message"])
            elif al["type"] == "warning":
                st.warning(al["message"])
            else:
                st.info(al["message"])
        # Show AI report (markdown)
        st.subheader("🩺 AI‑Generated Health Report")
        st.markdown(report_text)
        # Download options
        st.subheader("📥 Downloads")
        pdf_bytes = download_pdf(report_text, patient_id)
        st.download_button(label="Download PDF Report", data=pdf_bytes, file_name=f"{patient_id}_report.pdf", mime="application/pdf")
        csv_bytes = download_csv(patient_id)
        st.download_button(label="Download CSV Record", data=csv_bytes, file_name=f"{patient_id}_record.csv", mime="text/csv")

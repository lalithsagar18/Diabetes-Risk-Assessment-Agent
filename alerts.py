# alerts.py
# Helper functions to evaluate risk thresholds and generate UI alert messages.

def evaluate_alerts(prediction: dict, inputs: dict) -> list:
    """Return a list of alert dictionaries based on thresholds.

    Each alert dict contains:
        - type: "error", "warning", or "info"
        - message: string to display
    """
    alerts = []
    # High glucose threshold (example > 180 mg/dL)
    glucose = inputs.get("Glucose")
    if glucose is not None and glucose > 180:
        alerts.append({"type": "warning", "message": f"Glucose level {glucose} is higher than normal ( >180 ). Consider medical review."})
    # High BMI threshold (>30)
    bmi = inputs.get("BMI")
    if bmi is not None and bmi > 30:
        alerts.append({"type": "warning", "message": f"BMI {bmi:.1f} indicates obesity. Lifestyle changes recommended."})
    # High risk percentage (>70%)
    risk = prediction.get("risk_percentage")
    if risk is not None and risk > 70:
        alerts.append({"type": "error", "message": f"Predicted diabetes risk is {risk}%. Immediate medical attention advised!"})
    elif risk is not None and risk > 30:
        alerts.append({"type": "info", "message": f"Predicted risk is {risk}%. Monitor regularly and follow recommendations."})
    return alerts

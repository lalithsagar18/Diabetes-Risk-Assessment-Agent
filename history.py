# history.py
"""Patient history search and detail view.
Provides a UI where the user can look up patients by ID, name, or phone, see a list of matching records, and view the generated AI report.
"""
import streamlit as st
import pandas as pd
from database import search_patients, get_patient_by_id
from utils import init_session_state
from reports import download_pdf, download_csv


def render_history_page():
    """Render the History page with search and pagination."""
    init_session_state()
    st.title(":mag: Patient History")
    # Search form
    with st.form("search_form"):
        st.subheader("Search Patients")
        query = st.text_input("Enter Patient ID, Name, or Phone")
        submitted = st.form_submit_button("Search")
    if submitted:
        if not query:
            st.warning("Please enter a search term.")
            return
        results = search_patients(query)
        if not results:
            st.info("No matching patients found.")
            return
        df = pd.DataFrame(results)
        # Pagination
        items_per_page = 10
        page = st.number_input("Page", min_value=1, max_value=max(1, (len(df) - 1) // items_per_page + 1), value=1, step=1)
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_df = df.iloc[start_idx:end_idx]
        # Show table
        st.subheader(f"Results (page {page})")
        st.dataframe(page_df[["patient_id", "name", "age", "gender", "risk_percentage", "created_at"]])
        # Select a patient to view details
        selected_id = st.selectbox("Select Patient ID to view details", options=page_df["patient_id"].tolist())
        if selected_id:
            patient = get_patient_by_id(selected_id)
            if patient:
                st.subheader("Patient Details")
                for key in ["name", "age", "gender", "phone", "email", "address", "visit_date",
                            "pregnancies", "glucose", "blood_pressure", "skin_thickness",
                            "insulin", "bmi", "diabetes_pedigree", "prediction", "risk_percentage", "recommendation"]:
                    st.write(f"**{key.replace('_', ' ').title()}:** {patient.get(key, '')}")
                # Show AI report (stored in recommendation field)
                st.subheader("🩺 AI Health Report")
                report_md = patient.get("recommendation", "")
                if report_md:
                    st.markdown(report_md)
                else:
                    st.info("No report stored.")
                # Download options
                st.subheader("📥 Downloads")
                pdf_bytes = download_pdf(report_md, selected_id)
                st.download_button(label="Download PDF Report", data=pdf_bytes, file_name=f"{selected_id}_report.pdf", mime="application/pdf")
                csv_bytes = download_csv(selected_id)
                st.download_button(label="Download CSV Record", data=csv_bytes, file_name=f"{selected_id}_record.csv", mime="text/csv")
            else:
                st.error("Failed to retrieve patient details.")

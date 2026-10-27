"""
AI Farming Agent — Web Interface (app.py)
-----------------------------------------
A clean, responsive, agriculture-themed Streamlit web application.
Enables farmers and students to:
- Input crop type, location, growth stage, and observed symptoms.
- Upload crop-leaf photographs (JPG, JPEG, PNG).
- Receive comprehensive rule-based guidance and vision AI insights.
- Download structured reports as text files.
- Toggle between English and Marathi (prepared for regional deployment).
"""

import io
import os
from datetime import datetime
import streamlit as st
from PIL import Image

from agent import FarmingAgent
from tools import (
    SYMPTOM_DATABASE,
    CROP_INSIGHTS,
    get_ui_text,
    I18N_STRINGS,
)

# =====================================================================
# 1. STREAMLIT PAGE CONFIGURATION & THEME STYLING
# =====================================================================

st.set_page_config(
    page_title="AI Farming Agent",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Agriculture-Inspired CSS Theme
st.markdown(
    """
    <style>
    /* Main Background & Accent Colors */
    :root {
        --primary-green: #2d6a4f;
        --secondary-green: #40916c;
        --light-green: #e8f5e9;
        --accent-gold: #e9c46a;
        --alert-border: #b7e4c7;
    }

    .main-header {
        background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 60%, #40916c 100%);
        color: white !important;
        padding: 24px 28px;
        border-radius: 14px;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: 2.2rem;
        margin: 0;
        font-weight: 700;
    }
    .main-header p {
        color: #d8f3dc !important;
        font-size: 1.05rem;
        margin-top: 6px;
        margin-bottom: 0;
    }

    /* Card Containers */
    .farm-card {
        background-color: #ffffff;
        border: 1px solid #d8f3dc;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .farm-card-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1b4332;
        border-bottom: 2px solid #95d5b2;
        padding-bottom: 8px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Badges & Pills */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .badge-crop { background-color: #e8f5e9; color: #1b4332; border: 1px solid #a3b18a; }
    .badge-stage { background-color: #fefae0; color: #606c38; border: 1px solid #dda15e; }
    .badge-loc { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }

    /* Action Checklist Items */
    .step-item {
        background-color: #1a2e22 !important;
        color: #e8f5e9 !important;
        border-left: 4px solid #52b788;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .step-item b {
        color: #a7f3d0 !important;
    }

    .precaution-item {
        background-color: #2b1d0c !important;
        color: #fef3c7 !important;
        border-left: 4px solid #f59e0b;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .precaution-item b {
        color: #fcd34d !important;
    }

    /* Disclaimer Box */
    .disclaimer-card {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 10px;
        padding: 16px;
        margin-top: 20px;
        color: #991b1b;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================================
# 2. SIDEBAR CONFIGURATION & API STATUS
# =====================================================================

with st.sidebar:
    st.markdown("### 🌾 **AI Farming Agent**")
    st.caption("College Mini-Project Edition • v1.0")
    st.divider()

    # Language Switcher (Extensible for Marathi)
    lang_choice = st.selectbox(
        "🌐 Language / भाषा",
        options=["English", "मराठी (Marathi)"],
        index=0,
    )
    lang_code = "mr" if "Marathi" in lang_choice else "en"

    st.markdown("#### ⚙️ **API Configuration**")
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    has_api_key = bool(gemini_key and gemini_key != "your_gemini_api_key_here")

    if has_api_key:
        st.success("✅ Vision AI Connected (Gemini API)")
    else:
        st.warning("⚠️ Vision API Key Not Set (`.env`)")
        st.caption(
            "Rule-based assessment is fully active. "
            "To enable leaf image AI diagnosis, add `GEMINI_API_KEY` to your `.env` file."
        )

    st.divider()

    st.markdown("#### 📖 **How to Use:**")
    st.markdown(
        """
        1. **Select Crop & Stage** in the input form.
        2. **Enter Field Location** (optional).
        3. **Select Observed Symptoms** (yellowing, spots, wilt, etc.).
        4. **Upload a Leaf Photo** for visual inspection.
        5. Click **Analyze Crop** to view the report.
        6. **Download** the report as a text file.
        """
    )

    st.divider()
    if st.button("🔄 Reset / Clear Form", use_container_width=True):
        if "report_data" in st.session_state:
            del st.session_state["report_data"]
        st.rerun()


# =====================================================================
# 3. MAIN HEADER
# =====================================================================

header_title = get_ui_text("title", lang_code)
header_subtitle = get_ui_text("subtitle", lang_code)

st.markdown(
    f"""
    <div class="main-header">
        <h1>🌾 {header_title}</h1>
        <p>{header_subtitle}</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =====================================================================
# 4. FARMER INPUT SECTION
# =====================================================================

st.markdown("### 📋 1. Crop Information & Observed Symptoms")

col_left, col_right = st.columns([1.1, 0.9], gap="large")

with col_left:
    st.markdown("##### **Crop Profile**")

    crop_options = ["Tomato", "Potato", "Rice", "Wheat", "Cotton", "Other"]
    selected_crop = st.selectbox(
        get_ui_text("select_crop", lang_code),
        options=crop_options,
        index=0,
        help="Select the crop currently being cultivated.",
    )

    growth_stage_options = [
        "Seedling",
        "Vegetative",
        "Flowering",
        "Fruiting / Pod Development",
        "Harvesting / Maturity",
    ]
    selected_stage = st.selectbox(
        get_ui_text("growth_stage", lang_code),
        options=growth_stage_options,
        index=1,
        help="Select the current growth phase of your crop.",
    )

    location_input = st.text_input(
        get_ui_text("enter_location", lang_code),
        placeholder=get_ui_text("location_placeholder", lang_code),
        help="Optional: Enter your district, taluka, or village for location context.",
    )

    st.markdown("##### **Visible Crop Symptoms**")
    symptom_keys = list(SYMPTOM_DATABASE.keys())
    symptom_labels = {k: SYMPTOM_DATABASE[k]["label"] for k in symptom_keys}

    selected_symptom_keys = st.multiselect(
        get_ui_text("visible_symptoms", lang_code),
        options=symptom_keys,
        format_func=lambda k: symptom_labels[k],
        default=["yellow_leaves"],
        help="Select one or more symptoms observed on your crops.",
    )

with col_right:
    st.markdown("##### **Crop Leaf Photograph (Optional for AI Vision)**")
    uploaded_file = st.file_uploader(
        get_ui_text("upload_image", lang_code),
        type=["jpg", "jpeg", "png"],
        help="Upload a clear close-up photograph of the symptomatic crop leaf.",
    )

    if uploaded_file is not None:
        try:
            # Safely obtain image bytes without draining or locking the stream
            if hasattr(uploaded_file, "getvalue"):
                preview_bytes = uploaded_file.getvalue()
            else:
                if hasattr(uploaded_file, "seek"):
                    uploaded_file.seek(0)
                preview_bytes = uploaded_file.read()
                if hasattr(uploaded_file, "seek"):
                    uploaded_file.seek(0)

            preview_img = Image.open(io.BytesIO(preview_bytes))
            st.image(
                preview_img,
                caption=f"📷 Uploaded: {uploaded_file.name}",
                use_container_width=True,
            )
            # Ensure file pointer remains reset to start
            if hasattr(uploaded_file, "seek"):
                uploaded_file.seek(0)
        except Exception as e:
            st.error(f"Could not preview image file ({str(e)}). Please upload a valid JPG, JPEG, or PNG.")
    else:
        st.info("💡 Uploading a clear leaf photo enables AI Vision analysis alongside rule assessment.")


# =====================================================================
# 5. AGENT INVOCATION & WORKFLOW
# =====================================================================

st.write("")
analyze_clicked = st.button(
    get_ui_text("analyze_btn", lang_code),
    type="primary",
    use_container_width=True,
)

if analyze_clicked:
    agent = FarmingAgent(language=lang_code)

    with st.spinner(get_ui_text("loading_msg", lang_code)):
        result = agent.run(
            crop=selected_crop,
            growth_stage=selected_stage,
            symptoms=selected_symptom_keys,
            location=location_input,
            uploaded_image=uploaded_file,
        )

    if not result["success"]:
        for err in result["errors"]:
            st.error(f"❌ {err}")
    else:
        st.session_state["report_data"] = result
        st.success("✅ Analysis completed successfully!")


# =====================================================================
# 6. STRUCTURED FARMING REPORT DISPLAY
# =====================================================================

if "report_data" in st.session_state:
    report_bundle = st.session_state["report_data"]
    rep = report_bundle["report"]
    export_text = report_bundle["text_export"]
    rule = rep["rule_assessment"]
    synth = rep["combined_synthesis"]
    vision = rep["vision_assessment"]

    st.divider()
    st.markdown(f"## {get_ui_text('report_title', lang_code)}")

    # Display any input warnings (e.g., location or symptoms left blank)
    if rep.get("warnings"):
        for w in rep["warnings"]:
            st.warning(f"ℹ️ {w}")

    # Top Overview Chips
    st.markdown(
        f"""
        <div style="margin-bottom: 16px;">
            <span class="status-badge badge-crop">🌱 Crop: <b>{rep['crop']}</b></span>
            <span class="status-badge badge-stage">⏳ Stage: <b>{rep['growth_stage']}</b></span>
            <span class="status-badge badge-loc">📍 Location: <b>{rep['location']}</b></span>
            <span class="status-badge badge-crop">🕒 Generated: <b>{rep['timestamp']}</b></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Two column layout for details
    res_col1, res_col2 = st.columns([1, 1], gap="large")

    with res_col1:
        # Observed Symptoms Box
        st.markdown("#### 1. Observed Symptoms")
        if rep["symptoms_selected"]:
            for sym in rep["symptoms_selected"]:
                st.markdown(f"- 🌿 **{sym}**")
        else:
            st.info("No specific symptoms reported. Preventative maintenance profile active.")

        # Rule-Based Agronomic Guidance Box
        st.markdown("#### 2. Preliminary Agronomic Guidance")
        for g in rule.get("preliminary_guidance", []):
            st.markdown(f"- {g}")

        # Crop-Specific Agronomic Insights
        crop_notes = rule.get("crop_notes", {})
        if crop_notes:
            st.markdown(f"#### 3. Crop Notes for {rep['crop']}")
            st.caption(f"**Known Common Issues:** {crop_notes.get('common_issues', 'N/A')}")
            st.caption(f"**Key Scouting Check:** {crop_notes.get('key_check', 'N/A')}")

    with res_col2:
        # Potential Causes Box
        st.markdown("#### 4. Plausible Causes & Stress Factors")
        causes = synth.get("primary_causes", [])
        if causes:
            for c in causes:
                st.markdown(f"- 🔍 {c}")
        else:
            st.write("No severe anomalies detected from the provided inputs.")

        # AI Vision Analysis Section
        st.markdown("#### 5. AI Vision Image Assessment")
        if not rep["has_image"]:
            st.info("📷 *No image was uploaded. Visual leaf symptom inspection was skipped.*")
        else:
            if vision and vision.get("status") == "success" and vision.get("raw_text"):
                st.success("🤖 **AI Vision Model Findings:**")
                st.markdown(vision["raw_text"])
                st.caption(f"Evaluated via: `{vision.get('model_used', 'Gemini Vision')}`")
            elif vision and vision.get("status") == "missing_api_key":
                st.warning(f"⚠️ {vision.get('error')}")
                st.caption("Fell back to rule-based symptom assessment.")
            elif vision and vision.get("status") == "api_error":
                st.error(f"❌ {vision.get('error')}")
                st.caption("Fell back to rule-based symptom assessment.")

    st.divider()

    # Recommendations & Precautions Row
    rec_col1, rec_col2 = st.columns([1.1, 0.9], gap="large")

    with rec_col1:
        st.markdown("### 🛠️ Recommended Safe Next Steps")
        for step in synth.get("key_next_steps", []):
            st.markdown(
                f"""
                <div class="step-item">
                    ✅ <b>Action:</b> {step}
                </div>
                """,
                unsafe_allow_html=True,
            )

    with rec_col2:
        st.markdown("### ⚠️ Important Farm Precautions")
        for prec in synth.get("precautions", []):
            st.markdown(
                f"""
                <div class="precaution-item">
                    🛑 <b>Precaution:</b> {prec}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Disclaimer Card
    st.markdown(
        f"""
        <div class="disclaimer-card">
            <b>{get_ui_text('disclaimer_title', lang_code)}:</b><br/>
            {rep['disclaimer']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Download Report Button
    st.write("")
    timestamp_clean = datetime.now().strftime("%Y%m%d_%H%M%S")
    download_filename = f"Crop_Health_Report_{rep['crop']}_{timestamp_clean}.txt"

    st.download_button(
        label=get_ui_text("download_report", lang_code),
        data=export_text,
        file_name=download_filename,
        mime="text/plain",
        type="primary",
        use_container_width=True,
    )

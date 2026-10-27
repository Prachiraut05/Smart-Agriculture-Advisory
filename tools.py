"""
AI Farming Agent - Tools Module (tools.py)
------------------------------------------
Contains core functional tools:
1. Symptom-based rule engine for preliminary agronomic guidance.
2. Image validator for uploaded crop leaf photographs.
3. Vision-capable AI integration (Google Gemini) for leaf symptom visual analysis.
4. Multilingual text mappings (English with extensible Marathi support).
"""

import io
import os
import json
import base64
from typing import Dict, List, Tuple, Any, Optional
from PIL import Image
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Allowed image file extensions and limits
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


# =====================================================================
# 1. MULTILINGUAL SUPPORT (English default, ready for Marathi expansion)
# =====================================================================

I18N_STRINGS = {
    "en": {
        "title": "AI Farming Agent",
        "subtitle": "Your Smart Crop Health Assistant & Preliminary Care Advisor",
        "select_crop": "Select Crop",
        "enter_location": "Farm / Field Location",
        "location_placeholder": "e.g., Pune, Maharashtra / Nashik",
        "growth_stage": "Crop Growth Stage",
        "visible_symptoms": "Select Visible Crop Symptoms",
        "upload_image": "Upload Crop Leaf Photo (JPG, JPEG, PNG)",
        "analyze_btn": "🔍 Analyze Crop",
        "loading_msg": "Analyzing symptoms and evaluating crop health...",
        "report_title": "🌾 Preliminary Crop Health Report",
        "no_symptoms_warn": "No specific symptoms were selected. Providing general preventative crop management guidance.",
        "api_key_missing": "AI Vision API key is not configured. Running rule-based assessment only.",
        "download_report": "📥 Download Report (.txt)",
        "disclaimer_title": "⚠️ Important Disclaimer",
        "disclaimer_text": (
            "This report is a preliminary decision-support aid based on visible symptoms "
            "and AI vision analysis. It does NOT constitute a definitive laboratory diagnosis. "
            "Always inspect crops in person and consult your local Krishi Vigyan Kendra (KVK) "
            "or certified agricultural extension officer before applying chemical treatments."
        ),
    },
    "mr": {
        "title": "कृषी सल्लागार एआय (AI Farming Agent)",
        "subtitle": "तुमचा स्मार्ट पीक आरोग्य सहाय्यक आणि प्राथमिक सल्लागार",
        "select_crop": "पीक निवडा",
        "enter_location": "शेताचे / गावाचे ठिकाण",
        "location_placeholder": "उदा. पुणे, नाशिक, सातारा",
        "growth_stage": "पिकाची वाढीची अवस्था",
        "visible_symptoms": "पानावरील दिसणारी लक्षणे निवडा",
        "upload_image": "पिकाच्या पानाचा फोटो अपलोड करा (JPG, JPEG, PNG)",
        "analyze_btn": "🔍 पीक विश्लेषण करा",
        "loading_msg": "लक्षणे तपासून पीक आरोग्याचे विश्लेषण करत आहे...",
        "report_title": "🌾 प्राथमिक पीक आरोग्य अहवाल",
        "no_symptoms_warn": "कोणतीही विशिष्ट लक्षणे निवडलेली नाहीत. सामान्य पीक व्यवस्थापन सल्ला दिला जात आहे.",
        "api_key_missing": "एआय व्हिजन API की कॉन्फिगर केलेली नाही. केवळ नियम-आधारित मूल्यांकन सुरू आहे.",
        "download_report": "📥 अहवाल डाउनलोड करा (.txt)",
        "disclaimer_title": "⚠️ महत्त्वाची सूचना",
        "disclaimer_text": (
            "हा अहवाल केवळ प्राथमिक मार्गदर्शन आहे. ही कोणतीही अंतिम प्रयोगशाळा तपासणी नाही. "
            "रासायनिक फवारणी करण्यापूर्वी जवळच्या कृषी विज्ञान केंद्रातील (KVK) तज्ज्ञांचा सल्ला घ्या."
        ),
    },
}


def get_ui_text(key: str, lang: str = "en") -> str:
    """Retrieve UI string by key with fallback to English."""
    lang_dict = I18N_STRINGS.get(lang, I18N_STRINGS["en"])
    return lang_dict.get(key, I18N_STRINGS["en"].get(key, key))


# =====================================================================
# 2. RULE-BASED SYMPTOM KNOWLEDGE BASE
# =====================================================================

SYMPTOM_DATABASE: Dict[str, Dict[str, Any]] = {
    "yellow_leaves": {
        "label": "Yellow leaves (Chlorosis / Paling)",
        "preliminary_guidance": (
            "Examine soil moisture levels 2 inches below the surface. "
            "Observe whether yellowing starts from older (lower) leaves or younger (top) leaves. "
            "Check root zone for waterlogging or compaction restricting nutrient uptake."
        ),
        "possible_causes": [
            "Nitrogen deficiency (yellowing starting from older, lower leaves upwards)",
            "Iron or micronutrient deficiency (interveinal yellowing on young top leaves)",
            "Overwatering or poor soil drainage causing root suffocation",
            "Drought stress or underwatering causing premature leaf senescence",
        ],
        "suggested_next_steps": [
            "Test topsoil moisture before next irrigation; do not water if soil is already wet.",
            "If lower leaves are yellowing uniformly, consider side-dressing with well-decomposed organic compost or a balanced nitrogen source.",
            "Improve field aeration and drainage channels to prevent standing water.",
        ],
        "precautions": [
            "Do not over-apply synthetic chemical nitrogen, as it promotes succulent vegetative growth vulnerable to fungal attack.",
            "Avoid irrigating during peak midday heat.",
        ],
    },
    "brown_spots": {
        "label": "Brown spots (Necrotic lesions / Dark patches)",
        "preliminary_guidance": (
            "Inspect both the upper and lower surfaces of affected leaves using a hand lens. "
            "Check if the spots have concentric rings ('target board' pattern) or yellow surrounding halos. "
            "Monitor whether spots are spreading rapidly to neighboring leaves or stems."
        ),
        "possible_causes": [
            "Early blight (Alternaria solani) or Septoria leaf spot (fungal pathogen)",
            "Bacterial leaf spot or speck (often water-soaked with chlorotic halos)",
            "Cercospora or Helminthosporium leaf spot",
            "Foliar chemical burn from improper spray concentration",
        ],
        "suggested_next_steps": [
            "Prune and safely destroy heavily infected lower leaves using sanitized shears.",
            "Switch to drip or furrow irrigation to avoid wetting foliage directly.",
            "Maintain adequate spacing between crop rows to enhance air circulation and reduce humidity around the canopy.",
        ],
        "precautions": [
            "Avoid overhead sprinkler irrigation in late afternoon, as prolonged leaf wetness accelerates fungal spore germination.",
            "Do not compost diseased leaves; burn or bury them away from the field.",
        ],
    },
    "wilting": {
        "label": "Wilting (Drooping stems / Limp foliage)",
        "preliminary_guidance": (
            "Check root-zone moisture immediately. "
            "Observe whether the plant recovers turgidity during cool mornings/evenings or stays wilted continuously. "
            "Slice a lower wilted stem longitudinally to inspect for vascular browning."
        ),
        "possible_causes": [
            "Temporary drought stress due to inadequate soil moisture",
            "Root asphyxiation and root rot (Pythium / Phytophthora) from waterlogged soil",
            "Vascular fungal wilt (Fusarium oxysporum or Verticillium dahliae)",
            "Bacterial wilt (Ralstonia solanacearum) or nematode root damage",
        ],
        "suggested_next_steps": [
            "Perform a manual squeeze test of soil at root depth: if bone dry, apply gradual watering; if soggy and foul-smelling, stop watering immediately.",
            "Check root health of one symptomatic plant: healthy roots are creamy white; rotted roots are dark brown and mushy.",
            "Ensure proper drainage ditches are clear to drain stagnant rain or irrigation water.",
        ],
        "precautions": [
            "Do not flood a wilted crop immediately if the cause might be root rot; excessive moisture accelerates fungal decay.",
            "Never reuse irrigation runoff from fields infected with vascular wilt pathogens.",
        ],
    },
    "holes_in_leaves": {
        "label": "Holes in leaves (Chewed margins / Skeletonized foliage)",
        "preliminary_guidance": (
            "Scout the undersides of leaves, growing shoots, and leaf folds early in the morning. "
            "Look for visible caterpillars, beetles, larvae, or black fecal pellets (frass). "
            "Differentiate between shot-hole fungal lesions and active chewing insect bites."
        ),
        "possible_causes": [
            "Chewing caterpillars (e.g., Spodoptera / armyworms, loopers, cutworms)",
            "Flea beetles or leaf-eating beetles",
            "Snails or slugs in damp, heavily mulched conditions",
            "Grasshoppers or locust nymphs",
        ],
        "suggested_next_steps": [
            "Hand-pick and physically remove caterpillars or egg masses during morning scouting on small plots.",
            "Install yellow/blue sticky traps and pheromone traps to monitor pest incidence and flight patterns.",
            "Consider applying an organic neem-based formulation (Azadirachtin 1500 ppm or 5% NSKE) as an anti-feedant and repellent.",
        ],
        "precautions": [
            "Do not spray broad-spectrum synthetic chemical insecticides indiscriminately; they kill beneficial predators like ladybird beetles and spiders.",
            "Avoid spraying during flowering peak hours to protect honeybees and pollinators.",
        ],
    },
    "white_powder": {
        "label": "White powder (Powdery patches / Mildew)",
        "preliminary_guidance": (
            "Rub the white patch gently with a finger; powdery mildew rubs off easily like talc. "
            "Check both leaf surfaces and tender stem shoots. Note if older or shaded inner leaves are affected first."
        ),
        "possible_causes": [
            "Powdery mildew (fungal infection favored by high humidity, shade, and moderate temperatures)",
            "Downy mildew (often starts as pale angular spots on top, with whitish-gray felt underneath)",
            "Pesticide residue or hard water mineral residue (does not spread biologically)",
        ],
        "suggested_next_steps": [
            "Thin out dense foliage and prune redundant sucker branches to allow sunlight penetration and airflow.",
            "Avoid late afternoon or evening overhead watering.",
            "For mild initial patches, evaluate organic options like diluted cow milk spray (10%) or potassium bicarbonate / wettable sulfur as recommended by local extension.",
        ],
        "precautions": [
            "Do not apply sulfur-based sprays when temperatures exceed 32°C (90°F) to avoid phytotoxic foliar scorch.",
            "Do not over-fertilize with nitrogen, as tender new growth is highly susceptible to mildew colonization.",
        ],
    },
    "slow_growth": {
        "label": "Slow growth (Stunting / Poor vigor)",
        "preliminary_guidance": (
            "Assess environmental parameters: daily sunlight hours, soil compaction, and temperature extremes. "
            "Check soil pH if testing kit is available (most field crops prefer pH 6.0 - 7.5). "
            "Compare growth with neighboring healthy plants in the same plot."
        ),
        "possible_causes": [
            "Phosphorus or essential micronutrient deficiency (often accompanied by purplish or pale leaves)",
            "High soil salinity, alkalinity, or heavy soil compaction restricting root expansion",
            "Nematode attack on root system forming root-knots or galls",
            "Sub-optimal sunlight or extreme temperature stress during early stages",
        ],
        "suggested_next_steps": [
            "Gently loosen the soil around the root zone without damaging roots (light hoeing/intercultivation) to improve aeration.",
            "Conduct a standard soil health card test to determine soil pH, organic carbon, and N-P-K levels.",
            "Incorporate well-rotted farmyard manure (FYM) or vermicompost to improve soil biological activity and water retention.",
        ],
        "precautions": [
            "Do not guess fertilizer doses; uncalibrated chemical fertilizer application can lead to root burn or soil acidification.",
            "Ensure crops receive at least 6 to 8 hours of unfiltered sunlight per day.",
        ],
    },
}

# Crop-specific agronomic notes
CROP_INSIGHTS: Dict[str, Dict[str, str]] = {
    "Tomato": {
        "common_issues": "Early Blight, Late Blight, Tomato Leaf Curl Virus (transmitted by whitefly), Blossom End Rot (calcium/water fluctuation).",
        "key_check": "Inspect leaf underside for tiny whiteflies. Check fruit bottom for black sunken spots (calcium/watering imbalance).",
    },
    "Potato": {
        "common_issues": "Late Blight (Phytophthora infestans), Early Blight, Blackleg, Potato Tuber Moth.",
        "key_check": "Look for rapidly expanding dark water-soaked lesions on leaves during humid/rainy weather. Ensure earthing-up covers growing tubers.",
    },
    "Rice": {
        "common_issues": "Rice Blast (spindle-shaped lesions), Brown Spot, Bacterial Leaf Blight, Yellow Stem Borer (dead heart symptom).",
        "key_check": "Look for diamond-shaped eye spots on leaves. Check tiller bases for bore-holes and larval frass.",
    },
    "Wheat": {
        "common_issues": "Yellow/Brown/Black Rust, Powdery Mildew, Loose Smut, Aphid infestation.",
        "key_check": "Inspect leaves for linear pustules shedding yellow/orange/brown dust onto fingers. Check flag leaves during grain-fill stage.",
    },
    "Cotton": {
        "common_issues": "Cotton Leaf Curl Virus, Pink Bollworm, Bacterial Blight (angular leaf spot), Sucking pests (Jassids, Thrips, Whiteflies).",
        "key_check": "Check for upward/downward leaf curling and vein thickening. Inspect squares and tender bolls for entry pin-holes.",
    },
    "Other": {
        "common_issues": "General foliar fungal diseases, nutrient deficiencies, sucking and chewing insect complexes.",
        "key_check": "Compare healthy vs symptomatic plants in the field. Examine both soil moisture and leaf underside carefully.",
    },
}


# =====================================================================
# 3. RULE-BASED DECISION SYSTEM FUNCTION
# =====================================================================

def assess_symptoms(
    crop: str,
    growth_stage: str,
    symptoms: List[str],
    location: str = "",
) -> Dict[str, Any]:
    """
    Evaluates observed crop symptoms against agronomic rules.
    Provides preliminary guidance, possible causes, next steps, and precautions.
    """
    cleaned_location = location.strip() if location else "Unspecified location"
    
    # Handle scenario when no symptoms are selected
    if not symptoms:
        return {
            "has_symptoms": False,
            "crop": crop,
            "growth_stage": growth_stage,
            "location": cleaned_location,
            "symptoms_evaluated": [],
            "possible_causes": [
                "No visible symptoms selected. The crop may currently be in a healthy vegetative state, or symptoms are too subtle to categorize."
            ],
            "preliminary_guidance": [
                "Continue routine preventative crop monitoring at least twice a week.",
                "Maintain scheduled irrigation based on soil type and growth stage demands.",
                "Inspect under leaf surfaces and growing tips periodically for early pest arrivals.",
            ],
            "suggested_next_steps": [
                "Keep field borders clean of weeds that could host crop pests.",
                "Apply recommended organic mulch to conserve moisture and regulate soil temperature.",
                "Ensure balanced basal nutrition according to your local crop calendar.",
            ],
            "precautions": [
                "Do not apply preventative chemical fungicides or insecticides without visible economic threshold indications.",
                "Avoid excessive irrigation when topsoil remains damp.",
            ],
            "crop_notes": CROP_INSIGHTS.get(crop, CROP_INSIGHTS["Other"]),
            "disclaimer": get_ui_text("disclaimer_text"),
        }

    # Aggregate knowledge across all selected symptoms
    aggregated_guidance = []
    aggregated_causes = []
    aggregated_next_steps = []
    aggregated_precautions = []
    evaluated_labels = []

    for sym_key in symptoms:
        data = SYMPTOM_DATABASE.get(sym_key)
        if data:
            evaluated_labels.append(data["label"])
            aggregated_guidance.append(f"**{data['label']}**: {data['preliminary_guidance']}")
            for cause in data["possible_causes"]:
                if cause not in aggregated_causes:
                    aggregated_causes.append(cause)
            for step in data["suggested_next_steps"]:
                if step not in aggregated_next_steps:
                    aggregated_next_steps.append(step)
            for prec in data["precautions"]:
                if prec not in aggregated_precautions:
                    aggregated_precautions.append(prec)

    # Growth stage specific advice
    stage_advisories = {
        "Seedling": "Seedlings have tender root systems vulnerable to damping-off and fertilizer scorch. Maintain gentle moisture and light shading if sun is harsh.",
        "Vegetative": "Vegetative stage requires balanced nitrogen and phosphorus. Inspect canopy density and ensure adequate air circulation.",
        "Flowering": "Flowering stage is critical for pollination. Avoid heavy overhead spraying or water stress to prevent flower drop.",
        "Fruiting / Pod Development": "Fruit development requires high potassium and steady moisture. Protect developing fruit/bolls from boring pests and rot.",
        "Harvesting / Maturity": "Reduce irrigation gradually towards maturity to avoid fruit cracking, lodging, or harvest spoilage.",
    }
    stage_note = stage_advisories.get(growth_stage, "Maintain steady care suited to the current crop cycle.")

    return {
        "has_symptoms": True,
        "crop": crop,
        "growth_stage": growth_stage,
        "location": cleaned_location,
        "symptoms_evaluated": evaluated_labels,
        "stage_note": stage_note,
        "possible_causes": aggregated_causes,
        "preliminary_guidance": aggregated_guidance,
        "suggested_next_steps": aggregated_next_steps,
        "precautions": aggregated_precautions,
        "crop_notes": CROP_INSIGHTS.get(crop, CROP_INSIGHTS["Other"]),
        "disclaimer": get_ui_text("disclaimer_text"),
    }


# =====================================================================
# 4. IMAGE VALIDATOR
# =====================================================================

def validate_image(uploaded_file: Any) -> Tuple[bool, str, Optional[Image.Image]]:
    """
    Validates uploaded file format, size, and integrity.
    Returns: (is_valid, error_message, PIL_Image_or_None)
    """
    if uploaded_file is None:
        return False, "No image file was provided.", None

    # Check filename extension
    filename = getattr(uploaded_file, "name", "uploaded_image.jpg")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return (
            False,
            f"Invalid image format ('.{ext}'). Please upload a JPG, JPEG, or PNG image.",
            None,
        )

    # Check file size if available
    file_size = getattr(uploaded_file, "size", None)
    if file_size is not None and file_size > MAX_IMAGE_SIZE_BYTES:
        max_mb = MAX_IMAGE_SIZE_BYTES // (1024 * 1024)
        return (
            False,
            f"Image size exceeds {max_mb} MB limit. Please upload a smaller image file.",
            None,
        )

    # Read and verify image integrity with PIL
    try:
        if isinstance(uploaded_file, Image.Image):
            pil_image = uploaded_file.copy()
        else:
            # Extract raw image bytes safely from Streamlit UploadedFile, file-like object, or bytes
            if hasattr(uploaded_file, "getvalue"):
                image_bytes = uploaded_file.getvalue()
            elif hasattr(uploaded_file, "seek") and hasattr(uploaded_file, "read"):
                uploaded_file.seek(0)
                image_bytes = uploaded_file.read()
                uploaded_file.seek(0)
            elif hasattr(uploaded_file, "read"):
                image_bytes = uploaded_file.read()
            elif isinstance(uploaded_file, (bytes, bytearray)):
                image_bytes = bytes(uploaded_file)
            else:
                return False, "Unsupported file input type.", None

            # Check if bytes are empty
            if not image_bytes or len(image_bytes) == 0:
                return (
                    False,
                    "The uploaded image file is empty (0 bytes). Please upload a valid image.",
                    None,
                )

            # Verify image format and integrity
            test_buf = io.BytesIO(image_bytes)
            verifier = Image.open(test_buf)
            verifier.verify()

            # Open fresh image object for actual use
            pil_image = Image.open(io.BytesIO(image_bytes))

        # Auto-rotate smartphone photos based on EXIF orientation if present
        try:
            from PIL import ImageOps
            pil_image = ImageOps.exif_transpose(pil_image)
        except Exception:
            pass

        # Convert to RGB if palette or RGBA (JPEG safety)
        if pil_image.mode not in ("RGB", "L"):
            pil_image = pil_image.convert("RGB")

        return True, "", pil_image

    except Exception as e:
        return False, f"Could not read image file. It may be corrupted or unreadable. Error: {str(e)}", None


# =====================================================================
# 5. VISION-CAPABLE AI API INTEGRATION (Google Gemini)
# =====================================================================

def analyze_crop_image(
    image: Image.Image,
    crop: str,
    growth_stage: str,
    symptoms: List[str],
    location: str = "",
) -> Dict[str, Any]:
    """
    Sends crop leaf image and context to Google Gemini Vision AI.
    Strictly follows safety guidelines:
    - Describes visible leaf symptoms.
    - Suggests possible crop diseases or causes.
    - Explains reasoning in plain language.
    - Explicitly states uncertainty and notes preliminary nature.
    - Never claims confirmed diagnosis from image alone.
    - Gracefully handles missing API keys and service failures.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

    if not api_key or api_key == "your_gemini_api_key_here":
        return {
            "status": "missing_api_key",
            "error": "Google Gemini API key is missing. Set GEMINI_API_KEY in your .env file to enable vision analysis.",
            "visible_symptoms": "AI Image Vision analysis was not executed because no API key is configured.",
            "possible_causes": [],
            "reasoning": "Vision API skipped due to missing configuration.",
            "uncertainty_and_limitations": "Visual symptoms could not be inspected by AI vision model.",
            "further_checks": [
                "Inspect leaf upper and lower surfaces manually with a magnifying glass.",
                "Check soil moisture and root health in person.",
            ],
            "raw_text": None,
        }

    # Format symptom labels for context
    symptom_labels = [SYMPTOM_DATABASE.get(s, {}).get("label", s) for s in symptoms]
    symptoms_str = ", ".join(symptom_labels) if symptom_labels else "None reported by farmer"

    # Strict prompt ensuring agricultural safety and honest uncertainty
    prompt = f"""
You are an expert Agricultural Plant Pathology Assistant analyzing a crop photograph for a farmer.

CROP CONTEXT:
- Crop Type: {crop}
- Growth Stage: {growth_stage}
- Farm Location: {location if location else 'Unspecified'}
- Reported Farmer Symptoms: {symptoms_str}

TASK:
Analyze the uploaded crop leaf image carefully and provide an honest, safety-first assessment.

SAFETY RULES:
1. NEVER claim a confirmed diagnosis from an image alone. State clearly that image-based findings are preliminary observations.
2. Clearly describe visible leaf symptoms (e.g., chlorosis, lesion shape, necrotic spots, powdery growth, insect chewing, margins).
3. Suggest plausible candidate crop diseases, nutritional deficiencies, or abiotic stresses that fit these visual symptoms.
4. Explain your reasoning in simple, plain language that a beginner farmer or agriculture student can easily follow.
5. Highlight uncertainty: specify conditions that can look identical and explain what laboratory or field checks are needed.
6. DO NOT prescribe exact chemical pesticide or fertilizer doses. Focus on cultural, sanitation, and physical management practices.

Please structure your response with these clear section headings:
### 1. Visible Leaf Symptoms
(Detailed visual description of spots, discoloration, texture, or damage seen on the leaf)

### 2. Possible Causes & Candidate Conditions
(List 2-4 plausible diseases, deficiencies, or stress factors)

### 3. Reasoning & Visual Evidence
(Why these visual patterns match the candidate conditions)

### 4. Uncertainty & Necessary Field Checks
(Explain why an image alone cannot be 100% conclusive and list specific checks: e.g. stem cross-section, soil test, leaf underside check)

### 5. Recommended Safe Next Steps
(Actionable cultural practices, sanitation, and advice to consult local agricultural officers)
"""

    # First attempt: Try using official google.generativeai SDK if available
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        
        # Use configured model (defaults to gemini-1.5-flash)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([prompt, image])
        
        if response and response.text:
            return {
                "status": "success",
                "error": None,
                "raw_text": response.text.strip(),
                "model_used": model_name,
            }
        else:
            return {
                "status": "api_error",
                "error": "The AI model returned an empty response.",
                "raw_text": None,
            }

    except ImportError:
        # Fallback to direct Gemini REST API if google-generativeai is not installed
        return _call_gemini_rest_api(api_key, model_name, prompt, image)
    except Exception as e:
        # If SDK threw an error, attempt REST API or return structured error
        err_msg = str(e)
        # Attempt REST API fallback
        try:
            return _call_gemini_rest_api(api_key, model_name, prompt, image)
        except Exception:
            return {
                "status": "api_error",
                "error": f"AI Vision service encountered an error: {err_msg}",
                "raw_text": None,
            }


def _call_gemini_rest_api(
    api_key: str,
    model_name: str,
    prompt: str,
    image: Image.Image,
) -> Dict[str, Any]:
    """
    Fallback direct HTTP REST call to Google Gemini generateContent endpoint.
    Ensures zero dependency failures if SDK import fails.
    """
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    # Convert PIL Image to base64 JPEG
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": img_b64,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }

    try:
        response = requests.post(
            endpoint,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text_parts = [p.get("text", "") for p in parts if "text" in p]
                full_text = "\n".join(text_parts).strip()
                return {
                    "status": "success",
                    "error": None,
                    "raw_text": full_text,
                    "model_used": f"{model_name} (REST API)",
                }
            return {
                "status": "api_error",
                "error": "No response text candidate returned by Gemini API.",
                "raw_text": None,
            }
        else:
            err_data = response.json() if response.text else {}
            error_message = err_data.get("error", {}).get("message", response.text)
            return {
                "status": "api_error",
                "error": f"Gemini API HTTP {response.status_code}: {error_message}",
                "raw_text": None,
            }

    except Exception as e:
        return {
            "status": "api_error",
            "error": f"Failed to connect to Vision AI service: {str(e)}",
            "raw_text": None,
        }

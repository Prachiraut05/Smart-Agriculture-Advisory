"""
AI Farming Agent - Agent Orchestration (agent.py)
-------------------------------------------------
Coordinates the tool-using agent workflow:
1. Receives crop inputs, symptoms, and optional leaf image.
2. Validates user input and image integrity.
3. Executes rule-based symptom assessment.
4. Calls the vision-capable AI model if an image is provided.
5. Synthesizes evidence from rules and vision analysis.
6. Formulates a structured farming report and exportable plain-text summary.
7. Ensures agricultural safety principles and explicit uncertainty communication.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from PIL import Image

from tools import (
    assess_symptoms,
    validate_image,
    analyze_crop_image,
    get_ui_text,
    SYMPTOM_DATABASE,
    CROP_INSIGHTS,
)


class FarmingAgent:
    """
    Lightweight, deterministic agent orchestrating agronomic decision-making.
    Uses tools for symptom assessment and vision AI analysis.
    """

    def __init__(self, language: str = "en"):
        self.language = language

    def validate_inputs(
        self,
        crop: str,
        growth_stage: str,
        symptoms: List[str],
        location: str,
        uploaded_image: Any,
    ) -> Dict[str, Any]:
        """
        Validates farmer inputs and uploaded image file.
        Returns a dict with validation status and error messages if any.
        """
        errors: List[str] = []
        warnings: List[str] = []
        pil_image: Optional[Image.Image] = None

        # Validate crop
        if not crop or not crop.strip():
            errors.append("Please select a crop type.")

        # Validate growth stage
        if not growth_stage or not growth_stage.strip():
            errors.append("Please specify the crop growth stage.")

        # Location check: Empty location is allowed, but we note it
        cleaned_location = location.strip() if location else ""
        if not cleaned_location:
            warnings.append("Farm location not provided. Using general regional guidelines.")

        # Symptoms check: No symptoms selected is allowed, but we note it
        if not symptoms or len(symptoms) == 0:
            warnings.append("No specific symptoms selected. General preventative guidance will be provided.")

        # Validate image if provided
        if uploaded_image is not None:
            is_valid, img_err, img_obj = validate_image(uploaded_image)
            if not is_valid:
                errors.append(img_err)
            else:
                pil_image = img_obj

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "pil_image": pil_image,
            "cleaned_location": cleaned_location if cleaned_location else "Unspecified Field",
        }

    def run(
        self,
        crop: str,
        growth_stage: str,
        symptoms: List[str],
        location: str,
        uploaded_image: Any,
    ) -> Dict[str, Any]:
        """
        Main agent execution flow:
        1. Validate inputs.
        2. Execute rule-based symptom assessment tool.
        3. Execute vision AI image analysis tool (if image provided).
        4. Synthesize evidence from both sources.
        5. Generate comprehensive structured report and plain-text export.
        """
        # Step 1: Validate inputs
        validation = self.validate_inputs(
            crop=crop,
            growth_stage=growth_stage,
            symptoms=symptoms,
            location=location,
            uploaded_image=uploaded_image,
        )

        if not validation["is_valid"]:
            return {
                "success": False,
                "errors": validation["errors"],
                "warnings": validation["warnings"],
                "report": None,
                "text_export": None,
            }

        pil_image = validation["pil_image"]
        loc = validation["cleaned_location"]

        # Step 2: Run Rule-Based Symptom Assessment Tool
        rule_assessment = assess_symptoms(
            crop=crop,
            growth_stage=growth_stage,
            symptoms=symptoms,
            location=loc,
        )

        # Step 3: Run AI Image Vision Tool if image uploaded
        vision_assessment: Optional[Dict[str, Any]] = None
        if pil_image is not None:
            vision_assessment = analyze_crop_image(
                image=pil_image,
                crop=crop,
                growth_stage=growth_stage,
                symptoms=symptoms,
                location=loc,
            )

        # Step 4: Synthesize Evidence
        combined_synthesis = self._synthesize_evidence(
            crop=crop,
            growth_stage=growth_stage,
            symptoms=symptoms,
            rule_assessment=rule_assessment,
            vision_assessment=vision_assessment,
            has_image=(pil_image is not None),
        )

        # Step 5: Format Report
        structured_report = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "crop": crop,
            "growth_stage": growth_stage,
            "location": loc,
            "symptoms_selected": rule_assessment.get("symptoms_evaluated", []),
            "has_image": pil_image is not None,
            "pil_image": pil_image,
            "rule_assessment": rule_assessment,
            "vision_assessment": vision_assessment,
            "combined_synthesis": combined_synthesis,
            "warnings": validation["warnings"],
            "disclaimer": get_ui_text("disclaimer_text", self.language),
        }

        # Step 6: Generate Downloadable Plain-Text Report
        text_export = self._generate_text_export(structured_report)

        return {
            "success": True,
            "errors": [],
            "warnings": validation["warnings"],
            "report": structured_report,
            "text_export": text_export,
        }

    def _synthesize_evidence(
        self,
        crop: str,
        growth_stage: str,
        symptoms: List[str],
        rule_assessment: Dict[str, Any],
        vision_assessment: Optional[Dict[str, Any]],
        has_image: bool,
    ) -> Dict[str, Any]:
        """
        Combines rule-based conclusions with vision AI findings.
        Highlights areas of agreement, notes limitations, and builds prioritized recommendations.
        """
        primary_causes = list(rule_assessment.get("possible_causes", []))
        key_next_steps = list(rule_assessment.get("suggested_next_steps", []))
        precautions = list(rule_assessment.get("precautions", []))

        # Check vision status
        vision_status = "not_provided"
        vision_note = "No crop leaf photograph was provided for visual inspection."

        if has_image:
            if vision_assessment is None:
                vision_status = "skipped"
                vision_note = "Image processing was not initiated."
            elif vision_assessment.get("status") == "success":
                vision_status = "completed"
                vision_note = (
                    "AI Vision successfully examined the leaf image. "
                    "Findings combine visual patterns with your reported symptoms."
                )
            elif vision_assessment.get("status") == "missing_api_key":
                vision_status = "missing_api_key"
                vision_note = (
                    "Image provided, but Gemini Vision API key is not configured in .env. "
                    "Farming agent evaluated the case using agronomic rule-based logic."
                )
            else:
                vision_status = "error"
                vision_note = (
                    f"Vision analysis encountered an issue: {vision_assessment.get('error', 'Unknown')}. "
                    "Farming agent fell back to the rule-based assessment."
                )

        # Standard precautions for farm safety
        if "Always wear protective equipment (gloves, mask) if handling diseased foliage." not in precautions:
            precautions.append("Always wear protective equipment (gloves, mask) if handling diseased foliage.")
        if "Avoid spraying during noon heat or windy weather." not in precautions:
            precautions.append("Avoid foliar sprays during high midday temperatures or strong wind conditions.")

        return {
            "vision_status": vision_status,
            "vision_note": vision_note,
            "primary_causes": primary_causes,
            "key_next_steps": key_next_steps,
            "precautions": precautions,
            "agronomic_advisory": (
                f"For {crop} in the {growth_stage} stage, timely visual scouting and "
                "proper moisture management prevent minor stress from developing into severe crop loss."
            ),
        }

    def _generate_text_export(self, report: Dict[str, Any]) -> str:
        """
        Generates a clean, human-readable plain-text farming report for download.
        """
        crop = report.get("crop", "Unknown")
        stage = report.get("growth_stage", "Unknown")
        loc = report.get("location", "Unspecified")
        timestamp = report.get("timestamp", "")
        symptoms = report.get("symptoms_selected", [])
        synth = report.get("combined_synthesis", {})
        vision = report.get("vision_assessment")
        rule = report.get("rule_assessment", {})
        disclaimer = report.get("disclaimer", "")

        lines = [
            "=" * 68,
            "               AI FARMING AGENT — CROP HEALTH REPORT            ",
            "=" * 68,
            f"Generated on : {timestamp}",
            f"Crop Type    : {crop}",
            f"Growth Stage : {stage}",
            f"Farm Location: {loc}",
            "-" * 68,
            "",
            "1. REPORTED SYMPTOMS",
        ]

        if symptoms:
            for s in symptoms:
                lines.append(f"  • {s}")
        else:
            lines.append("  • None specified (General preventative advisory)")

        lines.extend([
            "",
            "2. RULE-BASED AGRONOMIC GUIDANCE",
        ])
        for g in rule.get("preliminary_guidance", []):
            # Clean markdown bold markers
            clean_g = g.replace("**", "")
            lines.append(f"  • {clean_g}")

        lines.extend([
            "",
            "3. POTENTIAL CAUSES & CONDITIONS",
        ])
        for c in synth.get("primary_causes", []):
            lines.append(f"  • {c}")

        lines.extend([
            "",
            "4. AI VISION IMAGE ANALYSIS",
            f"  Status: {synth.get('vision_note', '')}",
        ])

        if vision and vision.get("status") == "success" and vision.get("raw_text"):
            lines.append("")
            lines.append("  AI Vision Model Observations:")
            for v_line in vision["raw_text"].split("\n"):
                lines.append(f"    {v_line}")

        lines.extend([
            "",
            "5. RECOMMENDED NEXT STEPS",
        ])
        for step in synth.get("key_next_steps", []):
            lines.append(f"  [✓] {step}")

        lines.extend([
            "",
            "6. IMPORTANT PRECAUTIONS",
        ])
        for prec in synth.get("precautions", []):
            lines.append(f"  [!] {prec}")

        lines.extend([
            "",
            "7. CROP-SPECIFIC EXPERT NOTES",
            f"  Common Issues: {rule.get('crop_notes', {}).get('common_issues', 'N/A')}",
            f"  Field Check  : {rule.get('crop_notes', {}).get('key_check', 'N/A')}",
            "",
            "=" * 68,
            "DISCLAIMER & LIMITATIONS:",
            disclaimer,
            "=" * 68,
        ])

        return "\n".join(lines)

"""
AI Farming Agent — Automated Test Suite (test_agent.py)
-------------------------------------------------------
Verifies all 8 required test cases:
1. Normal symptom assessment
2. No symptoms selected
3. Image uploaded successfully
4. Invalid image format
5. Missing API key
6. API failure handling
7. Empty location handling
8. Report download generation
"""

import io
import os
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image

from tools import (
    assess_symptoms,
    validate_image,
    analyze_crop_image,
    SYMPTOM_DATABASE,
)
from agent import FarmingAgent


class MockUploadedFile:
    """Helper class mocking a Streamlit UploadedFile object."""
    def __init__(self, name: str, data: bytes):
        self.name = name
        self.size = len(data)
        self._data = data
        self._buffer = io.BytesIO(data)

    def read(self) -> bytes:
        return self._buffer.read()

    def getvalue(self) -> bytes:
        return self._data

    def seek(self, offset: int):
        self._buffer.seek(offset)


class TestFarmingAgent(unittest.TestCase):

    def setUp(self):
        """Create a sample valid PIL image in memory for testing."""
        self.agent = FarmingAgent()
        
        # Create a small 100x100 green image (simulating a leaf)
        img = Image.new("RGB", (100, 100), color=(34, 139, 34))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        self.sample_jpg_bytes = buf.getvalue()
        self.valid_upload = MockUploadedFile("leaf.jpg", self.sample_jpg_bytes)

    # -------------------------------------------------------------
    # 1. Normal Symptom Assessment
    # -------------------------------------------------------------
    def test_normal_symptom_assessment(self):
        """Verify normal symptom assessment produces guidance, causes, and next steps."""
        symptoms = ["yellow_leaves", "brown_spots"]
        result = assess_symptoms(
            crop="Tomato",
            growth_stage="Vegetative",
            symptoms=symptoms,
            location="Nashik",
        )

        self.assertTrue(result["has_symptoms"])
        self.assertEqual(result["crop"], "Tomato")
        self.assertEqual(len(result["symptoms_evaluated"]), 2)
        self.assertGreater(len(result["possible_causes"]), 0)
        self.assertGreater(len(result["preliminary_guidance"]), 0)
        self.assertGreater(len(result["suggested_next_steps"]), 0)
        self.assertGreater(len(result["precautions"]), 0)

        # Full agent run test
        agent_res = self.agent.run(
            crop="Tomato",
            growth_stage="Vegetative",
            symptoms=symptoms,
            location="Nashik",
            uploaded_image=None,
        )
        self.assertTrue(agent_res["success"])
        self.assertIsNotNone(agent_res["report"])

    # -------------------------------------------------------------
    # 2. No Symptoms Selected
    # -------------------------------------------------------------
    def test_no_symptoms_selected(self):
        """Verify workflow handles empty symptom selection with preventative guidance."""
        result = assess_symptoms(
            crop="Rice",
            growth_stage="Seedling",
            symptoms=[],
            location="Punjab",
        )

        self.assertFalse(result["has_symptoms"])
        self.assertEqual(len(result["symptoms_evaluated"]), 0)
        # Should contain preventative guidance
        self.assertGreater(len(result["preliminary_guidance"]), 0)
        self.assertTrue(any("preventative" in g.lower() for g in result["preliminary_guidance"]))

        # Full agent run test
        agent_res = self.agent.run(
            crop="Rice",
            growth_stage="Seedling",
            symptoms=[],
            location="Punjab",
            uploaded_image=None,
        )
        self.assertTrue(agent_res["success"])
        self.assertTrue(any("No specific symptoms" in w for w in agent_res["warnings"]))

    # -------------------------------------------------------------
    # 3. Image Uploaded Successfully
    # -------------------------------------------------------------
    def test_image_uploaded_successfully(self):
        """Verify a valid JPG image is parsed and validated successfully."""
        is_valid, err_msg, pil_img = validate_image(self.valid_upload)
        self.assertTrue(is_valid)
        self.assertEqual(err_msg, "")
        self.assertIsNotNone(pil_img)
        self.assertEqual(pil_img.size, (100, 100))

    def test_image_with_pre_read_stream(self):
        """Verify an uploaded file that was already read to EOF by preview can still be validated."""
        # Simulate preview read exhausting buffer
        self.valid_upload._buffer.read()
        self.assertEqual(self.valid_upload._buffer.tell(), len(self.sample_jpg_bytes))
        
        is_valid, err_msg, pil_img = validate_image(self.valid_upload)
        self.assertTrue(is_valid)
        self.assertEqual(err_msg, "")
        self.assertIsNotNone(pil_img)

    # -------------------------------------------------------------
    # 4. Invalid Image Format
    # -------------------------------------------------------------
    def test_invalid_image_format(self):
        """Verify invalid file extension (e.g., .pdf) is rejected with clear error."""
        invalid_upload = MockUploadedFile("document.pdf", b"%PDF-1.4...")
        is_valid, err_msg, pil_img = validate_image(invalid_upload)
        self.assertFalse(is_valid)
        self.assertIn("Invalid image format", err_msg)
        self.assertIsNone(pil_img)

        # Corrupted image bytes with .jpg extension
        corrupt_upload = MockUploadedFile("corrupted.jpg", b"NOT_AN_IMAGE_DATA")
        is_valid_c, err_c, pil_c = validate_image(corrupt_upload)
        self.assertFalse(is_valid_c)
        self.assertIn("Could not read image", err_c)

    # -------------------------------------------------------------
    # 5. Missing API Key
    # -------------------------------------------------------------
    def test_missing_api_key(self):
        """Verify missing GEMINI_API_KEY triggers graceful fallback without crashing."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            img = Image.new("RGB", (50, 50))
            result = analyze_crop_image(
                image=img,
                crop="Cotton",
                growth_stage="Flowering",
                symptoms=["wilting"],
                location="Wardha",
            )
            self.assertEqual(result["status"], "missing_api_key")
            self.assertIn("API key is missing", result["error"])

    # -------------------------------------------------------------
    # 6. API Failure Handling
    # -------------------------------------------------------------
    def test_api_failure_handling(self):
        """Verify API HTTP errors or network timeouts are caught and reported cleanly."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_test_key"}):
            # Mock requests.post to simulate server failure
            with patch("requests.post") as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.text = '{"error": {"message": "Internal Server Error"}}'
                mock_response.json.return_value = {"error": {"message": "Internal Server Error"}}
                mock_post.return_value = mock_response

                img = Image.new("RGB", (50, 50))
                result = analyze_crop_image(
                    image=img,
                    crop="Potato",
                    growth_stage="Vegetative",
                    symptoms=["brown_spots"],
                )
                self.assertEqual(result["status"], "api_error")
                self.assertIn("Internal Server Error", result["error"])

    # -------------------------------------------------------------
    # 7. Empty Location Handling
    # -------------------------------------------------------------
    def test_empty_location_handling(self):
        """Verify empty or whitespace-only location defaults gracefully without failure."""
        for empty_val in ["", "   ", None]:
            agent_res = self.agent.run(
                crop="Wheat",
                growth_stage="Vegetative",
                symptoms=["yellow_leaves"],
                location=empty_val,
                uploaded_image=None,
            )
            self.assertTrue(agent_res["success"])
            self.assertEqual(agent_res["report"]["location"], "Unspecified Field")
            self.assertTrue(any("location not provided" in w.lower() for w in agent_res["warnings"]))

    # -------------------------------------------------------------
    # 8. Report Download Generation
    # -------------------------------------------------------------
    def test_report_download_generation(self):
        """Verify the downloadable text report contains all required headers and sections."""
        agent_res = self.agent.run(
            crop="Tomato",
            growth_stage="Fruiting / Pod Development",
            symptoms=["yellow_leaves", "holes_in_leaves"],
            location="Kolhapur",
            uploaded_image=self.valid_upload,
        )

        self.assertTrue(agent_res["success"])
        text_export = agent_res["text_export"]
        self.assertIsNotNone(text_export)
        self.assertIsInstance(text_export, str)

        # Check required sections in exported text
        self.assertIn("AI FARMING AGENT — CROP HEALTH REPORT", text_export)
        self.assertIn("Crop Type    : Tomato", text_export)
        self.assertIn("Farm Location: Kolhapur", text_export)
        self.assertIn("1. REPORTED SYMPTOMS", text_export)
        self.assertIn("2. RULE-BASED AGRONOMIC GUIDANCE", text_export)
        self.assertIn("3. POTENTIAL CAUSES & CONDITIONS", text_export)
        self.assertIn("4. AI VISION IMAGE ANALYSIS", text_export)
        self.assertIn("5. RECOMMENDED NEXT STEPS", text_export)
        self.assertIn("6. IMPORTANT PRECAUTIONS", text_export)
        self.assertIn("DISCLAIMER & LIMITATIONS:", text_export)


if __name__ == "__main__":
    unittest.main()

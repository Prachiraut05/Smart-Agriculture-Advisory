# 🌾 AI Farming Agent — Basic Model

An intelligent, beginner-friendly, and practical AI-powered farming assistant built with **Python**, **Streamlit**, and **Google Gemini Vision**.

Designed specifically for **college mini-projects**, agriculture students, and rural decision-support, this application evaluates visible crop symptoms, inspects uploaded crop-leaf photographs, and produces structured, actionable preliminary health reports.

---

## 📌 1. Project Overview

Farmers often struggle with identifying early crop distress, fungal infections, pest attacks, and nutritional deficiencies. The **AI Farming Agent** bridges this gap by combining:

1. **Rule-Based Agronomic Knowledge Engine**: Evaluates selected crop symptoms (yellow leaves, brown spots, wilting, holes, white powder, slow growth) using established agricultural science rules.
2. **Vision-Capable AI (Google Gemini Vision)**: Inspects uploaded leaf photographs, describes visible lesions or chlorosis, suggests candidate causes, and highlights necessary field verifications.
3. **Safety-First Agricultural Logic**:
   - Never makes a definitive diagnosis from a photo alone.
   - Communicates uncertainty honestly.
   - Refrains from prescribing hazardous chemical doses without local soil context.
   - Encourages consulting local Krishi Vigyan Kendra (KVK) or extension officers.
4. **Exportable Reports**: Enables farmers and extension workers to download complete reports as `.txt` files for field records.

---

## 🏗️ 2. Project Architecture & File Structure

```text
AI-Farming-Agent/
├── app.py             # Streamlit web interface, themed UI, and report display
├── agent.py           # Agent orchestration, decision workflow, and text synthesis
├── tools.py           # Symptom rule engine, image validator, Gemini Vision API, & i18n
├── test_agent.py      # Automated test suite covering all 8 core test cases
├── requirements.txt   # Project dependencies (Streamlit, Pillow, Requests, Dotenv)
├── .env.example       # Template for Google Gemini API key configuration
├── .gitignore         # Excludes virtual environment, secret keys, and cache files
└── README.md          # Complete setup, testing, and college presentation guide
```

### Module Responsibilities

| File | Responsibility |
| :--- | :--- |
| **`app.py`** | Streamlit UI with agriculture-inspired green theme, input form, image preview, results cards, and download button. |
| **`agent.py`** | Orchestrates the decision process: validates inputs, triggers tools, synthesizes evidence, and structures final report. |
| **`tools.py`** | Contains `assess_symptoms()`, `validate_image()`, and `analyze_crop_image()` with direct REST fallback to Gemini Vision. |
| **`test_agent.py`** | Automated testing verifying normal symptoms, empty inputs, image handling, missing keys, and report generation. |
| **`requirements.txt`**| Lists lightweight, compatible dependencies. |
| **`.env.example`** | Safe template showing where to insert your `GEMINI_API_KEY`. |

---

## 🚀 3. Installation & Setup (Windows PowerShell)

Follow these simple steps in **VS Code** on Windows:

### Step 1: Open the Project in VS Code
1. Open VS Code.
2. Go to **File → Open Folder...** and select the `AI-Farming-Agent` folder.
3. Open a new PowerShell terminal by pressing `Ctrl + ` ` ` (tilde) or via **Terminal → New Terminal**.

### Step 2: Create a Python Virtual Environment
Run the following command in PowerShell:
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

> **Note for Windows Users**: If you see an error saying `Script execution is disabled on this system`, run this one-time command in PowerShell and press `Y`:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then re-run `.\venv\Scripts\Activate.ps1`.

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 🔑 4. Configuring the Gemini Vision API Key

The application works completely with rule-based assessment even without an API key. To enable the AI Vision analysis for leaf photos, get a free Google Gemini key:

1. Visit **[Google AI Studio](https://aistudio.google.com/)** and log in with your Google account.
2. Click **"Get API key"** and then **"Create API key"** (completely free, no credit card required).
3. In your project folder in VS Code, create a file named `.env` (or copy `.env.example` to `.env`).
4. Add your API key inside `.env`:
   ```env
   GEMINI_API_KEY=AIzaSyYourActualKeyHere
   GEMINI_MODEL=gemini-1.5-flash
   ```
5. Save the file. (The `.gitignore` file ensures your key is never committed to GitHub).

---

## ▶️ 5. Running the Application

With your virtual environment activated, launch the Streamlit app:

```powershell
streamlit run app.py
```

Your default browser will automatically open:
```text
Local URL: http://localhost:8501
```

---

## 🧪 6. Running the Automated Tests

The project includes an automated test suite verifying all 8 required test cases:

```powershell
python test_agent.py
```

### Verified Test Cases:
1. **Normal Symptom Assessment**: Verifies correct rules trigger for symptoms like yellowing and brown spots.
2. **No Symptoms Selected**: Verifies the agent defaults gracefully to preventative crop maintenance without crashing.
3. **Image Uploaded Successfully**: Tests that a valid JPG/PNG is parsed and validated.
4. **Invalid Image Format**: Tests rejection of non-image files (e.g. `.pdf`) or corrupted files.
5. **Missing API Key**: Confirms that when `GEMINI_API_KEY` is missing, the agent clearly informs the user and falls back to rule-based analysis.
6. **API Failure Handling**: Simulates network/server errors and confirms clean fallback.
7. **Empty Location Handling**: Verifies empty farm location defaults to `"Unspecified Field"` with a friendly notice.
8. **Report Download**: Verifies the exported text report contains all required sections and formatting.

---

## 🎓 7. College Demonstration Guide (Demo Flow for Teachers)

Here is a step-by-step walkthrough you can follow when demonstrating this project to your college professor or examiner:

### Step-by-Step Demo Flow:

#### Scenario A: Rule-Based Assessment Only (Baseline Demonstration)
1. **Explain the objective**: *"Respected Teacher, this project is an AI Farming Agent built to assist farmers in preliminary crop-health screening."*
2. **Select Crop**: Choose **Tomato**, Growth Stage **Vegetative**, and Location **Pune**.
3. **Select Symptoms**: Check **Yellow leaves** and **Brown spots**.
4. **Leave Image Empty** for the first run.
5. Click **🔍 Analyze Crop**.
6. **Show the output**:
   - Point out the **Rule-Based Preliminary Guidance** (e.g., checking lower leaf nitrogen vs upper leaf chlorosis).
   - Point out the **Candidate Causes** (Early blight, Septoria, Nitrogen deficiency).
   - Point out the **Recommended Next Steps** (switch to drip irrigation, sanitize shears) and **Farm Precautions** (avoid late overhead watering).
   - Point out the **Important Disclaimer**: Explain why ethical AI in agriculture must never guarantee 100% diagnosis without laboratory checks.

#### Scenario B: Leaf Image Upload & AI Vision Analysis
1. Upload a sample crop leaf picture (e.g., a tomato leaf with spots).
2. Click **🔍 Analyze Crop**.
3. **Show the AI Vision Card**:
   - The vision model describes the visual shape, color, and margins of the spots.
   - Shows candidate conditions based on image features.
   - Point out that the agent merges **both** the user symptoms and the AI vision observations into a unified report.

#### Scenario C: Resilient Fallback (Error Handling)
1. In `.env`, temporarily put an invalid key or leave it blank.
2. Click **🔍 Analyze Crop** with an image.
3. **Highlight to the examiner**: Notice how the application **does not crash**; instead, it displays an informative banner and seamlessly provides the rule-based assessment as a reliable fallback.

#### Scenario D: Downloading the Report
1. Click the **📥 Download Report (.txt)** button.
2. Open the downloaded text file to show the neat, structured summary formatted for farmers' records.

#### Scenario E: Multilingual Extensibility (Marathi Support)
1. In the sidebar, switch the language dropdown to **मराठी (Marathi)**.
2. Show that all UI titles, button texts, and disclaimers adapt smoothly, explaining that the architecture is prepared for regional Indian languages.

---

## 🔧 8. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | Windows PowerShell execution policy restriction. | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell. |
| `ModuleNotFoundError: No module named 'streamlit'` | Virtual environment is not activated. | Run `.\venv\Scripts\Activate.ps1` before starting the app. |
| `Vision API Key Not Set` warning in sidebar | `GEMINI_API_KEY` is not present in `.env`. | Create `.env` from `.env.example` and insert your Gemini API key. |
| Port 8501 is already in use | Another Streamlit process is running. | Run `streamlit run app.py --server.port 8502` to use an alternate port. |

---

## 🛡️ 9. Safety & Agronomic Ethics

1. **No Prescriptions Without Soil Data**: The agent explicitly avoids giving hazardous chemical pesticide dosages or chemical fertilizer quantities without a soil test card.
2. **Preliminary Nature**: Image analysis is treated as an advisory screening tool, not a replacement for plant pathology lab testing.
3. **Expert Consultation**: Every report reminds farmers to verify severe symptoms with local agricultural university officers or Krishi Vigyan Kendra (KVK).

---

## 📄 10. License & Credits

- Developed for College Mini-Project in Python & Applied AI.
- Free and open-source for educational and research purposes.

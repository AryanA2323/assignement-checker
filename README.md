# HandwriteAI — Automated Assignment Checker & Confidence Evaluator

> **Problem Statement Solved:**
> *"Manual evaluation of handwritten assignments is time-consuming, inconsistent, and difficult to scale for large numbers of students. Teachers need to spend significant time reading answers and checking whether they are correct and relevant."*

**HandwriteAI** is a minimal, portable, and fast solution designed to automate the checking of student handwritten assignments against an official master solution key. It transcribes handwritten answers, scores each question semantically against the master rubric, computes an **Accuracy Confidence Score (0–100%)**, and automatically flags low-confidence or illegible submissions for teacher review.

---

## 🌟 Key Features

- **End-to-End Multimodal Vision Evaluation**: Utilizes `gemini-2.5-flash` for OCR and semantic grading in a single pass (< 2 seconds per paper).
- **Minimal Dependencies & 100% Portability**: Uses only lightweight Python libraries (`Flask`, `google-genai`, `Pillow`, `pydantic`). No heavy CUDA/PyTorch or external C++ OCR binaries required.
- **Accurate Confidence Scoring**: Aggregates handwriting legibility, transcription certainty, and rubric alignment into an overall confidence metric (0–100%).
- **Teacher Review Flagging**: Submissions with confidence below threshold (default: 70%) or poor legibility (< 55%) are flagged with explicit audit reasons.
- **Demo Dataset Built-In**:
  - **Master Solution**: 4 multi-part questions on Artificial Intelligence and Machine Learning with scoring rubrics and key concepts.
  - **Student 1 (Alice Johnson)**: High score (~94%), neat handwriting, high confidence (95%).
  - **Student 2 (Bob Martinez)**: Average score (~74%), casual handwriting, moderate confidence (87%).
  - **Student 3 (Charlie Davis)**: Low score (~40%), messy/irregular handwriting, low confidence (61%) & flagged for teacher review.
- **Works with Real-World Data**: Supports any phone camera photo (`.jpg`, `.png`, `.webp`) and multi-page student `.pdf` documents.
- **Dual Interface**:
  - **Modern Web Dashboard**: Glassmorphic UI with real-time circular confidence gauges, side-by-side student work vs. transcription, and CSV/JSON export.
  - **Headless CLI Tool**: For batch scripts and headless workflows.
- **Offline / Mock Engine**: Instant out-of-the-box demonstration and 100% unit-tested even without an API key.

---

## 🚀 Quickstart

### 1. Requirements & Installation
Ensure you have Python (3.10+) installed. Then install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure Gemini API Key (Optional for live AI)
If you have a Gemini API key:
- Either copy `.env.example` to `.env` and set:
  ```env
  GEMINI_API_KEY=your_gemini_api_key_here
  GEMINI_MODEL=gemini-3.5-flash-lite
  DEFAULT_STRICTNESS=standard
  MANUAL_REVIEW_THRESHOLD=70
  ```
- Or enter it directly in the **Settings modal** within the Web Dashboard!

*(Note: If no API key is provided, the system automatically runs in Mock Simulator Mode for instant offline demonstration).*

---

## 🖥️ Running the Application

### Option A: Interactive Web Dashboard
Run:
```bash
python app.py
```
Open your browser at: **`http://127.0.0.1:5050`**

From the dashboard you can:
1. **Choose your evaluation mode**:
   - **Upload File / Paste Text**: Provide an answer key (PDF, JSON, or text) to grade strictly against.
   - **✨ Check with AI**: **No master solution required!** Gemini reads the handwritten answers and evaluates factual correctness directly against authoritative real-world Google data & academic consensus.
2. Upload multi-page student handwritten PDFs or images (e.g. from `ass_1/`).
3. Select grading strictness (`Lenient`, `Standard`, `Strict`).
4. Click **"Run AI Assignment Checking"** or **"✨ Run Direct AI Evaluation"**.
5. View real-time scores, circular confidence gauges, transcribed answers, and export results to CSV or JSON!

### Option B: Command Line Interface (CLI)
Run batch evaluation directly from your terminal:
```bash
# 1. Autonomous Direct AI evaluation (NO MASTER SOLUTION NEEDED - checked directly with Google data):
python cli.py --ai-direct --students ass_1

# With optional subject context hint:
python cli.py --ai-direct --students ass_1 --subject "Distributed Systems"

# 2. Evaluate with master solution key:
python cli.py --master ass_1/master_solution.pdf --students ass_1

# 3. Evaluate demo students with demo master:
python cli.py

# 4. Offline mock simulator mode:
python cli.py --ai-direct --students ass_1 --mock
```

---

## 📚 Real-World College Dataset: `ass_1`

The `ass_1/` directory contains an authentic, rigorous college-level assignment (*CS 545: Advanced Distributed Systems - 50 Marks*):
- **`ass_1/master_solution.pdf`**: Official 4-page reference answer key and grading rubric generated with ReportLab covering Raft/Paxos consensus, 2PL/MVCC concurrency, Consistent Hashing quorums, and Chandra-Toueg failure detectors / PBFT bounds. (Also provided as `.json` and `.txt`).
- **`ass_1/student_1_alex_chen.pdf`**: 3-page handwritten submission in royal blue ink (`segoepr.ttf`), neat handwriting, rigorous proofs (~94% score, high confidence).
- **`ass_1/student_2_priya_sharma.pdf`**: 3-page handwritten submission in black ballpoint (`Inkfree.ttf`), realistic college handwriting with typical student mix-ups (~68% score, medium confidence).
- **`ass_1/student_3_marcus_vance.pdf`**: 3-page handwritten submission in dark gel ink (`segoesc.ttf`), rushed/tilted handwriting, crossed-out notes, quorum inversion (~34% score, flagged for teacher manual review).

---

## 🧪 Automated Testing

Run the full automated test suite (15 unit and integration tests):
```bash
python -m pytest -v
```
All tests validate models, image optimization, confidence heuristics, batch evaluation, CLI execution, and Flask API endpoints.

---

## 📁 Project Architecture

```
assignement checker/
├── ass_1/                     # Realistic college assignment dataset
│   ├── master_solution.pdf    # Master answer key & rubric (PDF)
│   ├── master_solution.json   # Structured JSON version
│   ├── master_solution.txt    # Plaintext version
│   ├── student_1_alex_chen.pdf# Multi-page neat handwriting (94%)
│   ├── student_2_priya_sharma.pdf # Multi-page realistic handwriting (68%)
│   └── student_3_marcus_vance.pdf # Multi-page messy/flagged handwriting (34%)
├── app.py                     # Flask web server & REST API
├── cli.py                     # Terminal CLI runner
├── requirements.txt           # Minimal dependencies
├── .env                       # Active environment configuration
├── core/
│   ├── config.py              # Settings & API key management
│   ├── models.py              # Pydantic schemas (MasterSolution, StudentEvaluation)
│   ├── confidence.py          # Confidence calculation heuristics & review thresholds
│   ├── evaluator.py           # Gemini multimodal vision evaluator & mock fallback
│   └── utils.py               # Image optimization, multi-page PDF stitching & CSV export
├── demo_data/                 # Quick lightweight demo dataset
├── scripts/
│   ├── generate_ass1_dataset.py # Generator for the authentic ass_1 dataset
│   └── generate_demo_data.py  # Lightweight generator
├── templates/
│   └── index.html             # Clean, minimal web dashboard
├── static/
│   ├── css/style.css          # Glassmorphic responsive dark theme
│   └── js/app.js              # Client dashboard interactivity & gauges
└── tests/                     # 15 automated test cases
```

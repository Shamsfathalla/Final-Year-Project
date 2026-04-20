# 3arabeetak 🚗
### Multimodal Car Valuation & Analysis Platform — Egyptian Automotive Market

> **Final Year Project** — The Knowledge Hub Universities, partnered with Coventry University
> **Author:** Shams Fathalla Mohamed Abdelaziz | **Student ID:** SA2200965
> **Supervisors:** Dr. Batoul Haidar & Eng. Mostafa Badr

---

## Table of Contents

- [Overview](#overview)
- [Research Background](#research-background)
- [System Architecture](#system-architecture)
- [Model Performance](#model-performance)
- [Tech Stack](#tech-stack)
- [Datasets](#datasets)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Step 1: Download Assets](#step-1-download-assets)
  - [Step 2: Python Environment](#step-2-python-environment)
  - [Step 3: Node.js & Database Setup](#step-3-nodejs--database-setup)
  - [Step 4: Multimodal Valuation Engine](#step-4-multimodal-valuation-engine-cv--ml-backend)
  - [Step 5: Chatbot Backend](#step-5-chatbot-backend)
  - [Step 6: Local Models with Ollama](#step-6-local-models-with-ollama-optional)
- [License](#license)

---

## Overview

**3arabeetak** is an end-to-end AI platform built for the Egyptian automotive market. It automates car valuation, assesses physical vehicle condition through computer vision, and provides intelligent conversational search — all priced in **Egyptian Pounds (EGP)**.

The Egyptian used car market suffers from large pricing inconsistencies, subjective seller assessments, and the lack of intelligent search or recommendation services. Existing approaches either handle structured data price prediction *or* computer vision-based damage detection — but never unify both into a coherent valuation framework. 3arabeetak fills that gap by fusing structured listing data with real-time image analysis to deliver highly accurate, condition-adjusted valuations that mirror real-world depreciation.

> **Models, datasets, and static assets** are hosted externally due to file size constraints.
> 📁 [Download from Google Drive](https://drive.google.com/drive/folders/1Gy8jDVzXYJPaXkJTE_txGqaONGUJPQte?usp=sharing)

---

## Research Background

### Problem Statement

The Egyptian used car market has ongoing issues: unclear pricing, inconsistent vehicle condition reporting, and scattered access to critical market information. Current platforms do not account for the visual condition of a vehicle — a major driver of resale value — and provide limited support for assessing price fairness or comparing listings across platforms.

### Research Objectives

- Develop a multi-modal valuation model that combines structured vehicle attributes with CNN-derived visual embeddings to generate condition-aware price predictions
- Construct a computer vision pipeline capable of distinguishing damaged from undamaged vehicles using diverse image datasets including CarDD, Kaggle samples, and scraped Egyptian market images
- Design an NLP-powered API search agent that interprets natural language queries and retrieves relevant Egyptian marketplace listings in real time
- Implement a recommendation system integrating content-based similarity, behavioral patterns, and price fairness metrics
- Develop supporting analytical modules including an import cost calculator and market analytics dashboard
- Evaluate all system components using established metrics: RMSE, Accuracy, F1-score, ROC AUC

---

## System Architecture

### 1. Data Collection & Scraping

A parallelized web scraping pipeline aggregates structured vehicle listings from major Egyptian automotive platforms.

- **Framework:** Playwright Stealth with 5 parallel workers, configured to bypass anti-bot systems
- **Sources:** Contactcars, Hatla2ee, Bidex, Dubizzle, YallaMotors
- **Scale:** Thousands of new and used car listings aggregated into a PostgreSQL database
- **Preprocessing:** Over 21,000 unspecified trims standardized; engineered features include `Car Age` and `Miles Per Year` to distinguish city vs. highway wear
- **Outlier Filtering:** A "Brand Tier" system (Economy → Premium → Luxury → Exotic) dynamically removes extreme price anomalies and invalid age-to-mileage ratios while preserving legitimate high-value data

---

### 2. Computer Vision: Condition Assessment

Physical vehicle condition is evaluated through a **4-stage image classification pipeline** powered by an Ensemble Voting Mechanism.

> **Key design decision:** Initial attempts using YOLOv8 with bounding boxes achieved only ~50% accuracy due to hallucinations caused by overlapping damage types. The methodology was shifted to holistic image classification, which yielded significantly better results. For stages with weaker individual models, an ensemble voting structure is used — multiple models vote and the most common classification wins.

| Stage | Purpose | Models Used |
|---|---|---|
| Stage 1 — Exterior Detection | Filters out interior images to prevent misclassification | ViT, EfficientNet, MLP, YOLOv8, SVM |
| Stage 2 — Damage Detection | Classifies as Undamaged or identifies specific damage type (bumper, door, glass, Total Loss, etc.) | ViT, YOLOv8, MLP, EfficientNet, SVM |
| Stage 3a — Severity Grading | If damage present, grades as Minor / Moderate / Severe | ViT, SVM, MLP, YOLOv8, EfficientNet |
| Stage 3b — Undamaged Condition Scoring | Scores overall physical state on a 0–10 scale | ViT, SVM, EfficientNet, YOLOv8, MLP |

**Condition Score Scale (Stage 3b):**

| Score Range | Label |
|---|---|
| 0 – 2.9 | Poor |
| 3 – 4.9 | Fair |
| 5 – 6.9 | Good |
| 7 – 8.4 | Very Good |
| 8.5 – 10 | Excellent |

---

### 3. Machine Learning: Price Prediction

Structured tabular data and computer vision outputs are fused to predict realistic market values.

- **Feature Engineering:** Mileage, age, brand, engine size, transmission, and generated CV Condition Score merged into a unified feature set
- **Model Selection:** LightGBM, CatBoost, Random Forest, XGBoost, and MLP were all evaluated. **LightGBM** was selected for production, achieving the lowest RMSE and an **R² of 0.955**
- **Key Finding:** Exotic/super-luxury vehicles caused outsized RMSE impact. Splitting the dataset by brand tier improved standard classes but degraded exotic car accuracy — a unified dataset with rigorous dynamic outlier filtering proved the most robust approach
- **Multimodal Adjustment:** The baseline LightGBM price is penalized for detected damage or rewarded for excellent physical condition, yielding a final condition-aware estimate

---

### 4. NLP Semantic Search Agent

An LLM-powered retrieval system that interprets natural language queries and converts them into SQL against the live PostgreSQL database.

- **Intent routing:** Queries starting with "compare" → comparison agent; "recommend" → recommendation agent; all others → search agent
- **Pipeline:** Natural language → LLM extracts structured JSON → backend converts to optimized SQL → results ranked by TF-IDF and cosine similarity → deduplicated top 100 returned
- **Model decision:** Local models (Ollama/Gemma3) were tested but suffered from hallucinations during SQL generation due to hardware constraints. The production system uses the **cloud-hosted Gemini API** for accurate intent parsing and reliable query generation
- **Capabilities:** Search, vehicle comparison (side-by-side with AI-generated verdict), and personalized recommendations

---

### 5. Core Features

**🧮 Import Cost Calculator**
Dynamically estimates the total landed cost of importing a vehicle into Egypt:
- 0% customs for EU-manufactured or fully electric vehicles
- ~40% customs for non-EU engines ≤1600cc; ~135% for engines >1600cc
- Standard 14% VAT applied universally
- Shipping from major global markets: Europe ($1,200–$1,400), USA ($2,000), Japan/South Korea ($2,700), UAE ($900)
- Container vs. RORO shipping (RORO applies a 20% discount)
- Port fee scaling: Alexandria (baseline), Port Said (+4%), Sokhna (+6%), Damietta (+8%)
- Fixed fees for port clearance and customs brokerage included in final estimate

**📊 Market Analytics Dashboard**
Visualizes historical price trends and market fluctuations for specific vehicle models over configurable time ranges (1Y, 2Y, 3Y, 5Y, All).

**🔐 User Accounts & History**
Firebase authentication with persistent PostgreSQL storage of saved chat sessions, favorite vehicles, and past comparisons — used to continuously refine the recommendation engine.

---

## Model Performance

### Structured Price Prediction

| Model | RMSE | MAE | R² |
|---|---|---|---|
| **LightGBM** | **328,781** | **124,515** | **0.955** |
| CatBoost | 337,372 | 131,547 | 0.952 |
| RandomForest | 344,638 | 120,508 | 0.950 |
| XGBoost | 380,755 | 128,635 | 0.940 |
| MLP | 450,759 | 167,864 | 0.916 |

### Computer Vision Pipeline

**Stage 1 — Exterior vs. Interior Detection**

| Model | Accuracy | F1-score | ROC AUC |
|---|---|---|---|
| ViT | 1.000 | 1.000 | 1.000 |
| EfficientNet | 0.998 | 0.998 | 0.998 |
| MLP | 0.997 | 0.997 | 0.999 |
| YOLOv8 | 0.997 | 0.997 | 0.999 |
| SVM | 0.992 | 0.992 | 0.999 |

**Stage 2 — Damage Detection & Classification**

| Model | Accuracy | F1-score | ROC AUC |
|---|---|---|---|
| **ViT** | **0.886** | **0.881** | **0.994** |
| YOLOv8 | 0.877 | 0.873 | 0.992 |
| MLP | 0.829 | 0.815 | 0.976 |
| EfficientNet | 0.811 | 0.806 | 0.980 |
| SVM | 0.781 | 0.769 | 0.978 |

**Stage 3a — Damage Severity Classification**

| Model | Accuracy | F1-score | ROC AUC |
|---|---|---|---|
| **ViT** | **0.742** | **0.731** | **0.895** |
| SVM | 0.738 | 0.733 | 0.867 |
| MLP | 0.702 | 0.686 | 0.848 |
| YOLOv8 | 0.694 | 0.699 | 0.860 |
| EfficientNet | 0.669 | 0.662 | 0.812 |

**Stage 3b — Undamaged Condition Scoring**

| Model | Accuracy | F1-score | ROC AUC |
|---|---|---|---|
| **ViT** | **0.846** | **0.846** | **0.971** |
| SVM | 0.787 | 0.788 | 0.944 |
| EfficientNet | 0.777 | 0.778 | 0.949 |
| YOLOv8 | 0.771 | 0.774 | 0.953 |
| MLP | 0.707 | 0.712 | 0.935 |

> The Vision Transformer (ViT) consistently outperformed all other architectures across every CV stage. Damage severity estimation (Stage 3a) proved the most challenging visual task across all models.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Scraping | Python, Playwright Stealth |
| Computer Vision | PyTorch, YOLOv8, ViT, EfficientNet, OpenCV |
| Machine Learning | Scikit-Learn, LightGBM, CatBoost, XGBoost |
| NLP / AI | Gemini API, LangChain, Ollama |
| Backend | Node.js, Express, Flask |
| Database | PostgreSQL |
| Authentication | Firebase |

---

## Datasets

Image datasets used to train the computer vision pipeline:

| Dataset | Source |
|---|---|
| Car Damage Severity Dataset | [Kaggle](https://www.kaggle.com/datasets/prajwalbhamere/car-damage-severity-dataset) |
| Car Damage Assessment | [Kaggle](https://www.kaggle.com/datasets/hamzamanssor/car-damage-assessment) |
| The Car Connection Picture Dataset | [Kaggle](https://www.kaggle.com/datasets/prondeau/the-car-connection-picture-dataset) |
| Car Parts and Car Damages | [Kaggle](https://www.kaggle.com/datasets/humansintheloop/car-parts-and-car-damages) |
| Vehide Dataset — Automatic Vehicle Damage Detection | [Kaggle](https://www.kaggle.com/datasets/hendrichscullen/vehide-dataset-automatic-vehicle-damagedetection) |
| Car Damage Dataset | [Kaggle](https://www.kaggle.com/datasets/vinayjose/car-damage-dataset) |
| Ripik Hackfest | [Kaggle](https://www.kaggle.com/datasets/sudhanshu2198/ripik-hackfest) |
| Comprehensive Car Damage Detection | [Kaggle](https://www.kaggle.com/datasets/samwash94/comprehensive-car-damage-detection) |
| Persian Car Interior Design | [Kaggle](https://www.kaggle.com/datasets/behnamhasanbeygi/persian-car-interior-design) |
| Car Engine Bay Pictures | [Kaggle](https://www.kaggle.com/datasets/khaledchawa/car-engine-bay-pictures) |
| CAWDEC | [Kaggle](https://www.kaggle.com/datasets/adamnovozmsk/cawdec) |
| Car Damage Detection (Roboflow) | [Roboflow](https://universe.roboflow.com/college-gxdrt/car-damage-detection-ha5mm/dataset/1) |
| Car Damage Detection — Finance (Roboflow) | [Roboflow](https://universe.roboflow.com/finance-insitut/car-damage-detection-ku5hj/dataset/1) |
| Car Interior (Roboflow) | [Roboflow](https://universe.roboflow.com/exterior-glass/car-interior-orwin) |
| CarDD Dataset | [cardd-ustc.github.io](https://cardd-ustc.github.io/) |

Structured listing data scraped from: [Contactcars](https://www.contactcars.com/en), [Biddex](https://biddex.com/en), [Dubizzle Egypt](https://www.dubizzle.com.eg/en/motors/), [Hatla2ee](https://eg.hatla2ee.com/en), [YallaMotor Egypt](https://egypt.yallamotor.com/)

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- [Ollama](https://ollama.com/) *(optional — for local model inference)*

---

### Step 1: Download Assets

Before running anything, download the required models and datasets from the [Google Drive link](https://drive.google.com/drive/folders/1Gy8jDVzXYJPaXkJTE_txGqaONGUJPQte?usp=sharing).

- **For Notebooks:** Place image dataset folders directly into their corresponding directories under `Notebooks/`
  - Example: place the *Undamaged Condition* dataset inside `Notebooks/Undamaged Condition/`
- **For the Website Backend:** Place trained `.pt`, `.h5`, or `.pkl` model files in their respective backend directories
  - Example: model files go inside the `Price/` folder; test images go in `Price/static/uploads/`

---

### Step 2: Python Environment

All Python dependencies are consolidated into a single `requirements.txt`. A virtual environment is recommended.

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (only required if running the scrapers)
playwright install
```

---

### Step 3: Node.js & Database Setup

The main web interface and API routing depend on Node.js and PostgreSQL.

**Install Node modules:**
```bash
npm install
```

**Configure environment variables:**

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgres://username:password@localhost:5432/your_database_name
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your_auth_domain
FIREBASE_PROJECT_ID=arabeetak-892f2
FIREBASE_STORAGE_BUCKET=your_storage_bucket
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
```

**Firebase Service Account:**

Place your `firebase-service-account.json` file in the root directory alongside `server.js`.

**PostgreSQL:**

Ensure PostgreSQL is installed and running. Create a new empty database matching the name in `DATABASE_URL`. The `server.js` script automatically initializes all required tables (`users`, `chat_sessions`, `favorites`, `saved_comparisons`) on first run.

**Start the application:**
```bash
node server.js
```

---

### Step 4: Multimodal Valuation Engine (CV & ML Backend)

The core inference engine handles both image processing (CV) and structured tabular data (ML) to generate final valuations.

```bash
cd Price/
python app.py
```

> Ensure model files are in place as described in [Step 1](#step-1-download-assets). The server starts on `http://localhost:5000` by default.

---

### Step 5: Chatbot Backend

The conversational AI agent runs on the cloud-hosted Gemini API.

```bash
cd Chatbot/
python app.py
```

> Ensure your Gemini API key is set in your environment variables before starting.

---

### Step 6: Local Models with Ollama (Optional)

For offline testing or air-gapped environments. Note: local models performed worse than the Gemini API for complex NLP-to-SQL tasks due to hardware constraints on smaller model sizes.

**Install Ollama** from [ollama.com](https://ollama.com/).

```bash
# Terminal 1 — start the server
ollama serve

# Terminal 2 — pull and run a model
ollama run gemma3:4b

# Vision-capable model (for multimodal use)
ollama run llava
```

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 Shams Fathalla Mohamed Abdelaziz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

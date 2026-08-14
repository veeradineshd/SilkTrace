# 🧵 SilkTrace – AI-Powered Smart Textile Manufacturing Intelligence Platform

> **An enterprise AI platform for textile manufacturing units and handloom/power-loom micro-clusters that predicts worker productivity, forecasts industrial energy consumption, and classifies fabric defects using Machine Learning, Deep Learning, and Google Cloud OIDC Authentication.**

---

## 📌 Executive Overview

**SilkTrace** is an artificial intelligence-driven decision-support system engineered to modernize textile manufacturing operations. The platform unifies **Machine Learning (Random Forest)** for workforce productivity and energy consumption forecasting with **Deep Learning (MobileNetV2)** for automated fabric quality control, accessible through a glassmorphic industrial **Streamlit** dashboard.

SilkTrace equips plant managers, quality control engineers, and analysts with real-time operational insights, automated PDF/CSV reporting, executive KPI dashboards, and Google Cloud OpenID Connect (OIDC) authentication with Role-Based Access Control (RBAC).

---

## 🎯 Industry Problem Statement

Textile manufacturing units frequently rely on manual logs and fragmented monitoring for:
* **Worker Productivity**: Difficulty anticipating line delays, SMV discrepancies, or style change bottlenecks.
* **Energy Consumption**: Unplanned electricity cost spikes driven by inductive equipment operating during peak billing hours.
* **Fabric Quality Assurance**: Slow manual inspection of fabric reels leading to unflagged defects (holes, horizontal/vertical streaks) and high scrap rates.

---

## 💡 The SilkTrace Solution

SilkTrace addresses these manufacturing challenges by deploying:
1. **👷 Worker Productivity Prediction**: Random Forest Regressor predicting line actual productivity based on 14 production and workforce parameters.
2. **⚡ Energy Consumption Forecasting**: Random Forest Regressor predicting factory electrical usage in kWh based on reactive power, power factor, and load types.
3. **🧵 Automated Fabric Defect Detection**: MobileNetV2 Deep Learning classifier processing 224x224 fabric photos to identify structural defects (`Hole`, `Horizontal`, `Vertical`).
4. **🔒 Google Cloud OIDC Authentication**: Enterprise authentication with OAuth 2.0 / OpenID Connect, session security (`st.stop()`), and role-based permissions (`ADMIN`, `ANALYST`, `OPERATOR`, `VIEWER`).
5. **📊 Executive Analytics & Alert Center**: Data-driven KPI dashboards and automated rule-based alert engines flagging operational anomalies.
6. **📄 Automated PDF & CSV Reporting**: Cross-platform ReportLab PDF report generation with operator attribution and recommended actions.

---

## 🏗 System Architecture

```
User (Browser)
    │
    ▼
Google Cloud OIDC Authentication (OAuth 2.0 / OpenID Connect)
    │
    ▼
SilkTrace Streamlit Web Application (dashboard/app.py)
    ├── 👷 Productivity Prediction (Random Forest)
    ├── ⚡ Energy Forecasting (Random Forest)
    ├── 🧵 Fabric Quality Inspection (MobileNetV2)
    ├── 📊 Executive Analytics & Alert Engine
    └── 🩺 System Health Diagnostics
    │
    ▼
Output Engines: Plotly Visualizations | ReportLab PDF Reports | CSV History Logs
```

For full details, see [docs/architecture.md](docs/architecture.md).

---

## 🛠 Technology Stack

| Domain | Technology / Library |
| :--- | :--- |
| **Language** | Python 3.12 |
| **Web Framework** | Streamlit 1.59.2, Streamlit Option Menu |
| **Machine Learning** | Scikit-learn, Joblib |
| **Deep Learning** | TensorFlow / Keras (MobileNetV2 Architecture) |
| **Data Processing** | Pandas, NumPy |
| **Visualizations** | Plotly Express & Graph Objects |
| **Reporting & Export** | ReportLab PDF Engine, CSV Data Exporter |
| **Security & Auth** | Google OpenID Connect (OIDC), OAuth 2.0, Requests |
| **Deployment** | Render Web Service (Gunicorn / Streamlit Headless Server) |

---

## 📂 Project Structure

```
SilkTrace_Project/
├── .streamlit/
│   ├── config.toml                # Streamlit UI & theme configuration
│   └── secrets.toml.example       # OIDC auth template (DO NOT commit real secrets)
├── assets/                        # Static branding assets
├── dashboard/
│   ├── app.py                     # Main Streamlit application entrypoint
│   └── silktrace_logo.png         # SilkTrace logo
├── datasets/
│   ├── energy/                    # Steel Industry Energy Consumption dataset
│   ├── fabric_defect/             # Fabric defect images (Hole, Horizontal, Vertical)
│   ├── productivity/              # Garments Worker Productivity dataset
│   └── yarn_price/                # Historical yarn price dataset
├── docs/
│   └── architecture.md            # Comprehensive system & data-flow architecture
├── history/                       # Persistent prediction & inspection CSV logs
├── models/
│   ├── date_encoder.pkl           # Date feature encoder
│   ├── quarter_encoder.pkl        # Quarter feature encoder
│   ├── department_encoder.pkl     # Department feature encoder
│   ├── day_encoder.pkl            # Day feature encoder
│   ├── productivity_model.pkl     # Random Forest Productivity Model (~7.8 MB)
│   ├── energy_model.pkl           # Random Forest Energy Model (GitHub Release download)
│   └── fabric_defect_model.keras  # MobileNetV2 Fabric Model (GitHub Release download)
├── reports/                       # Generated ReportLab PDF inspection reports
├── src/
│   ├── analytics.py               # KPI calculation & Plotly chart builders
│   ├── auth.py                    # Google OIDC auth & RBAC permission gate
│   ├── config.py                  # Centralized paths, model release URLs & metadata
│   ├── history.py                 # Persistent prediction CSV loggers
│   ├── models.py                  # Model loaders & inference wrappers
│   ├── prediction.py              # Legacy API compatibility bridge
│   └── reports.py                 # ReportLab PDF report generator
├── tests/
│   └── test_app.py                # Automated unit test suite
├── .gitignore                     # Git tracking exclusions
├── .python-version                # Python runtime definition (3.12.10)
├── README.md                      # Project documentation
├── render.yaml                    # Render production service deployment config
└── requirements.txt               # Pinned Python dependencies
```

---

## 🔒 Google Cloud Authentication Setup

SilkTrace uses **Google OpenID Connect (OIDC)** for user authentication.

### 1. Google Cloud Console Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a Google Cloud Project.
3. Configure the **OAuth Consent Screen**:
   - Application Name: `SilkTrace`
   - Scopes: `openid`, `email`, `profile`
4. Create **OAuth 2.0 Client Credentials**:
   - Application Type: `Web Application`
   - Authorized Redirect URIs:
     - **Local Development**: `http://localhost:8501/oauth2callback`
     - **Production (Render)**: `https://<YOUR-RENDER-SERVICE-NAME>.onrender.com/oauth2callback`

### 2. Secrets Configuration
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`:
```toml
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
GOOGLE_REDIRECT_URI = "http://localhost:8501/oauth2callback"
```
> ⚠️ **SECURITY NOTICE**: Never commit `.streamlit/secrets.toml` to Git. It is listed in `.gitignore`.

---

## 🚀 Local Installation & Running

### Prerequisites
- Python 3.12 installed
- Git

### Quickstart
```bash
# 1. Clone repository
git clone https://github.com/veeradineshd/SilkTrace.git
cd SilkTrace_Project

# 2. Create & activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run automated test suite
python -m unittest discover -s tests

# 5. Launch Streamlit application
streamlit run dashboard/app.py
```

Open your browser at `http://localhost:8501`.

---

## ☁️ Render Deployment Guide

SilkTrace includes a pre-configured `render.yaml` manifest.

### Deployment Steps
1. Push your repository to GitHub.
2. Log into [Render](https://render.com/).
3. Click **New +** -> **Blueprint** and connect your `SilkTrace` repository.
4. Render will parse `render.yaml` automatically:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`
5. In the Render Dashboard under **Environment Variables**, add:
   - `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID
   - `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret
   - `GOOGLE_REDIRECT_URI`: `https://<YOUR-RENDER-SERVICE-NAME>.onrender.com/oauth2callback`
6. Deploy the service.

---

## 👨‍💻 Resume / Portfolio Summary

**SilkTrace — AI-Powered Textile Manufacturing Analytics Platform**
- Architected and built an industrial AI analytics platform using **Python**, **Streamlit**, **Scikit-learn**, and **TensorFlow (MobileNetV2)**.
- Implemented machine-learning models predicting worker productivity (Random Forest, 14 features) and forecasting industrial energy usage (Random Forest, 10 features).
- Developed a computer-vision fabric defect classifier processing 224x224 pixel photos to detect structural defects (Hole, Horizontal, Vertical).
- Integrated enterprise **Google Cloud OpenID Connect (OIDC)** authentication with Role-Based Access Control (`ADMIN`, `ANALYST`, `OPERATOR`, `VIEWER`).
- Implemented real-time executive KPI dashboards, automated operational alert engines, cross-platform **ReportLab PDF report generation**, and CSV export capabilities.
- Prepared production deployment via **Render** with automated `unittest` verification and secret protection.

---

## 👤 Developer Information

- **Developer**: Veera Dinesh D
- **Institution**: Sri Eshwar College of Engineering
- **Version**: `v1.0.0`
- **License**: MIT

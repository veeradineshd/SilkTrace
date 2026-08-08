# 🧵 SilkTrace – AI-Powered Smart Textile Monitoring & Prediction System

> **An intelligent AI-powered platform for textile manufacturing that predicts worker productivity, forecasts energy consumption, and detects fabric defects using Machine Learning and Deep Learning.**

---

## 📌 Overview

**SilkTrace** is an AI-powered decision-support system designed for the textile manufacturing industry.

The platform combines **Machine Learning, Deep Learning, Data Analytics, and an interactive Streamlit dashboard** to help textile industries monitor production performance, optimize energy consumption, and automate fabric quality inspection.

SilkTrace brings multiple AI capabilities together into a single application, providing actionable insights through an easy-to-use dashboard.

---

## 🎯 Problem Statement

Textile manufacturing units often depend on manual records and traditional methods to monitor:

* Worker productivity
* Energy consumption
* Production performance
* Fabric quality
* Manufacturing defects

These approaches can be time-consuming, error-prone, and difficult to analyze.

SilkTrace addresses these challenges by applying **Artificial Intelligence and Data Analytics** to automate prediction, monitoring, and quality inspection.

---

## 💡 Proposed Solution

SilkTrace provides an integrated AI platform that can:

* 👷 Predict worker productivity
* ⚡ Predict energy consumption
* 🧵 Detect fabric defects automatically
* 📊 Analyze manufacturing data
* 📈 Visualize production and energy insights
* 📄 Generate inspection reports
* 📁 Maintain prediction history

---

# 🤖 AI Modules

## 👷 1. Worker Productivity Prediction

Predicts worker productivity using historical garment manufacturing data.

**Model:** Random Forest Regressor

**Dataset:** Garments Worker Productivity Dataset

### Input Features

* Date
* Quarter
* Department
* Day
* Team
* Targeted Productivity
* SMV
* WIP
* Overtime
* Incentive
* Idle Time
* Idle Men
* Style Changes
* Number of Workers

### Output

The system predicts the expected **actual productivity**.

---

## ⚡ 2. Energy Consumption Prediction

Predicts industrial energy consumption using historical energy usage data.

**Model:** Random Forest Regressor

**Dataset:** Steel Industry Energy Consumption Dataset

The model considers electrical and operational parameters such as:

* Reactive power
* Power factor
* CO₂ emissions
* NSM
* Week status
* Day of the week
* Load type

### Output

The system predicts **energy consumption in kWh**.

---

## 🧵 3. Fabric Defect Detection

SilkTrace uses Deep Learning to automatically identify fabric defects from images.

**Model:** MobileNetV2

**Framework:** TensorFlow / Keras

### Supported Defect Classes

| Class         | Description                       |
| ------------- | --------------------------------- |
| 🕳️ Hole      | Hole or missing portion in fabric |
| ↔️ Horizontal | Horizontal fabric defect          |
| ↕️ Vertical   | Vertical fabric defect            |

The system provides an AI-based classification of the uploaded fabric image.

---

# 📊 Dashboard Modules

The SilkTrace Streamlit dashboard contains:

### 🏠 Home

Provides an overview of the SilkTrace platform and its major AI capabilities.

### ⚡ Energy Prediction

Allows users to enter industrial parameters and obtain an AI-based energy consumption prediction.

### 👷 Productivity Prediction

Predicts worker productivity using manufacturing parameters.

### 🧵 Fabric Defect Detection

Allows users to upload fabric images and automatically classify defects.

### 📊 Analytics

Provides interactive visualizations and insights from the available datasets.

### 📖 About SilkTrace

Provides information about the project, technologies, and system capabilities.

---

# 🖼️ Dashboard Screenshots

## 🏠 Home

![SilkTrace Home](screenshots/homepage_1.png)

![SilkTrace Home](screenshots/homepage_2.png)

---

## ⚡ Energy Prediction

![Energy Prediction](screenshots/energy_prediction_1.png)

![Energy Prediction](screenshots/energy_prediction_2.png)

![Energy Prediction](screenshots/energy_prediction_3.png)

![Energy Prediction](screenshots/energy_prediction_4.png)

---

## 👷 Productivity Prediction

![Productivity Prediction](screenshots/productivity_prediction_1.png)

![Productivity Prediction](screenshots/productivity_prediction_2.png)

![Productivity Prediction](screenshots/productivity_prediction_3.png)

![Productivity Prediction](screenshots/productivity_prediction_4.png)

---

## 🧵 Fabric Defect Detection

![Fabric Defect Detection](screenshots/fabric_defect_detection_1.png)

![Fabric Defect Detection](screenshots/fabric_defect_detection_2.png)

![Fabric Defect Detection](screenshots/fabric_defect_detection_3.png)

![Fabric Defect Detection](screenshots/fabric_defect_detection_4.png)

![Fabric Defect Detection](screenshots/fabric_defect_detection_5.png)

![Fabric Defect Detection](screenshots/fabric_defect_detection_6.png)

---

## 📊 Analytics

![Analytics Dashboard](screenshots/analytics_page_1.png)

![Analytics Dashboard](screenshots/analytics_page_2.png)

![Analytics Dashboard](screenshots/analytics_page_3.png)

![Analytics Dashboard](screenshots/analytics_page_4.png)

![Analytics Dashboard](screenshots/analytics_page_5.png)

![Analytics Dashboard](screenshots/analytics_page_6.png)

---

## 📖 About SilkTrace

![About SilkTrace](screenshots/about_silktrace_1.png)

![About SilkTrace](screenshots/about_silktrace_2.png)

---

# 🛠️ Technology Stack

| Technology            | Purpose                   |
| --------------------- | ------------------------- |
| 🐍 Python             | Core programming language |
| 🐼 Pandas             | Data processing           |
| 🔢 NumPy              | Numerical computation     |
| 🤖 Scikit-learn       | Machine Learning          |
| 🧠 TensorFlow / Keras | Deep Learning             |
| 🎨 Streamlit          | Interactive web dashboard |
| 📊 Plotly             | Data visualization        |
| 🖼️ Pillow            | Image processing          |
| 💾 Joblib             | Model serialization       |
| 📄 ReportLab          | PDF report generation     |

---

# ✨ Key Features

* 👷 AI-based worker productivity prediction
* ⚡ Industrial energy consumption prediction
* 🧵 Deep Learning-based fabric defect detection
* 📊 Interactive analytics dashboard
* 📈 Data visualization
* 📄 Automatic PDF inspection reports
* 📁 Prediction history using CSV files
* 🚀 Real-time prediction interface
* 🎯 Multi-model AI integration
* 🖥️ User-friendly Streamlit interface

---

# 📁 Project Structure

```text
SilkTrace_Project/
│
├── dashboard/
│   └── app.py
│
├── datasets/
│   ├── energy/
│   └── productivity/
│
├── history/
│   ├── energy_history.csv
│   └── productivity_history.csv
│
├── models/
│   ├── energy_model.pkl
│   ├── productivity_model.pkl
│   └── fabric_defect_model.keras
│
├── notebooks/
│
├── reports/
│
├── screenshots/
│   ├── homepage_*.png
│   ├── energy_prediction_*.png
│   ├── productivity_prediction_*.png
│   ├── fabric_defect_detection_*.png
│   ├── analytics_page_*.png
│   └── about_silktrace_*.png
│
├── src/
│
├── README.md
└── requirements.txt
```

---

# 🚀 How to Run

## 1. Clone the Repository

```bash
git clone https://github.com/veeradineshd/SilkTrace.git
cd SilkTrace
```

## 2. Create a Virtual Environment

```bash
python -m venv .venv312
```

Activate it on Windows:

```bash
.venv312\Scripts\activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Run the Streamlit Dashboard

```bash
streamlit run dashboard/app.py
```

The application will open in your browser.

---

# 📈 Project Outcome

SilkTrace demonstrates how Artificial Intelligence can be applied to textile manufacturing to support:

* Improved worker productivity
* Better energy management
* Automated fabric quality inspection
* Data-driven decision making
* Manufacturing process monitoring
* Reduced dependence on manual inspection

---

# 🌍 Industrial Impact

SilkTrace can support textile manufacturing units by combining operational data and AI predictions into a single decision-support platform.

The system demonstrates the potential of AI to improve **production efficiency, energy awareness, and quality inspection** in textile manufacturing environments.

---

# 🔮 Future Enhancements

* 📡 IoT sensor integration
* 🏭 Live factory monitoring
* ☁️ Cloud deployment
* 📧 Automated email alerts
* 🤖 AI-powered chat assistant
* 📱 Mobile application
* 📊 Advanced predictive analytics
* 🔔 Real-time anomaly detection

---

# 📄 License

This project is developed for **academic and educational purposes**.

---

# 👨‍💻 Developer

**Veera Dinesh D**

**B.Tech – Artificial Intelligence & Data Science**

**Sri Eshwar College of Engineering**

---

⭐ **If you find this project interesting, consider giving the repository a star!**

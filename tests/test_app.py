# SilkTrace — Automated Test Suite
import unittest
import os
import sys
from pathlib import Path
import pandas as pd

# Add workspace root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config import (
    APP_NAME,
    APP_VERSION,
    PRODUCTIVITY_MODEL_PATH,
    DATE_ENCODER_PATH,
    QUARTER_ENCODER_PATH,
    DEPARTMENT_ENCODER_PATH,
    DAY_ENCODER_PATH,
    PRODUCTIVITY_DATASET_PATH,
    ENERGY_DATASET_PATH,
    REPORTS_DIR,
)

class TestSilkTraceSystem(unittest.TestCase):

    def test_01_config_and_paths(self):
        """Test configuration constants and core directory paths."""
        self.assertEqual(APP_NAME, "SilkTrace")
        self.assertEqual(APP_VERSION, "v1.0.0")
        self.assertTrue(BASE_DIR.exists())
        self.assertTrue(PRODUCTIVITY_DATASET_PATH.exists())
        self.assertTrue(ENERGY_DATASET_PATH.exists())

    def test_02_encoder_loading(self):
        """Test loading categorical feature encoders."""
        from src.models import load_encoders
        encoders = load_encoders()
        self.assertIn("date", encoders)
        self.assertIn("quarter", encoders)
        self.assertIn("department", encoders)
        self.assertIn("day", encoders)

    def test_03_productivity_model_loading(self):
        """Test productivity model file existence and loading."""
        self.assertTrue(PRODUCTIVITY_MODEL_PATH.exists())
        from src.models import load_productivity_model
        model = load_productivity_model()
        self.assertIsNotNone(model)

    def test_04_productivity_prediction(self):
        """Test worker productivity prediction function."""
        from src.models import load_encoders, predict_productivity
        encoders = load_encoders()
        
        sample_input = {
            "date": encoders["date"].transform([encoders["date"].classes_[0]])[0],
            "quarter": encoders["quarter"].transform([encoders["quarter"].classes_[0]])[0],
            "department": encoders["department"].transform([encoders["department"].classes_[0]])[0],
            "day": encoders["day"].transform([encoders["day"].classes_[0]])[0],
            "team": 1,
            "targeted_productivity": 0.80,
            "smv": 20.0,
            "wip": 100.0,
            "over_time": 0,
            "incentive": 50,
            "idle_time": 0.0,
            "idle_men": 0,
            "no_of_style_change": 0,
            "no_of_workers": 50
        }

        pred, elapsed, status = predict_productivity(sample_input)
        self.assertIsInstance(pred, float)
        self.assertGreaterEqual(pred, 0.0)
        self.assertLessEqual(pred, 1.5)
        self.assertGreater(elapsed, 0.0)
        self.assertIsInstance(status, str)

    def test_05_legacy_prediction_api(self):
        """Test backwards compatibility of src.prediction module."""
        from src.prediction import predict_productivity as legacy_predict_prod
        from src.models import load_encoders
        encoders = load_encoders()
        
        sample_input = {
            "date": encoders["date"].transform([encoders["date"].classes_[0]])[0],
            "quarter": encoders["quarter"].transform([encoders["quarter"].classes_[0]])[0],
            "department": encoders["department"].transform([encoders["department"].classes_[0]])[0],
            "day": encoders["day"].transform([encoders["day"].classes_[0]])[0],
            "team": 1,
            "targeted_productivity": 0.80,
            "smv": 20.0,
            "wip": 100.0,
            "over_time": 0,
            "incentive": 50,
            "idle_time": 0.0,
            "idle_men": 0,
            "no_of_style_change": 0,
            "no_of_workers": 50
        }
        val = legacy_predict_prod(sample_input)
        self.assertIsInstance(val, (float, int))

    def test_06_pdf_report_generation(self):
        """Test PDF report generation using ReportLab."""
        from src.reports import create_pdf_report
        summary_df = pd.DataFrame({
            "Attribute": ["Test Defect", "Confidence"],
            "Value": ["Horizontal", "95.5%"]
        })
        pdf_path = create_pdf_report(
            summary_df,
            predicted_class="Horizontal",
            confidence=95.5,
            inspection_time="2026-08-14 12:00:00",
            user_name="Test Operator",
            user_email="test@silktrace.ai"
        )
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 0)

    def test_07_analytics_kpi_computation(self):
        """Test Analytics KPI computation and alert engine."""
        from src.analytics import load_analytics_datasets, compute_executive_kpis, generate_operational_alerts
        prod_df, eng_df = load_analytics_datasets()
        self.assertFalse(prod_df.empty)
        self.assertFalse(eng_df.empty)

        empty_df = pd.DataFrame()
        kpis = compute_executive_kpis(prod_df, eng_df, empty_df, empty_df, empty_df)
        self.assertIn("avg_actual_prod", kpis)
        self.assertIn("total_predictions", kpis)

        alerts = generate_operational_alerts(prod_df, eng_df)
        self.assertIsInstance(alerts, list)

if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile

import numpy as np
import pytest

from app.ai import (
    ControlRoomAssistant,
    CrowdPredictor,
    DelayPredictor,
    DemandPredictor,
    ETAPredictor,
    IncidentPredictor,
)
from app.ai.base import BasePredictor
from app.ai.inference import InferenceEngine
from app.ai.train import train_all


class MockPredictor(BasePredictor):
    def _build_model(self):
        from sklearn.linear_model import LinearRegression

        return LinearRegression()

    def _prepare_features(self, data):
        import numpy as np

        rows = [[float(v) for v in row.values()] for row in data]
        return np.array(rows, dtype=np.float64)

    def _predict_impl(self, data):
        if isinstance(data, np.ndarray):
            return self.model.predict(data)
        return self.model.predict(self._prepare_features(data))

    def train(self, data, target_col="target"):
        import numpy as np
        from sklearn.model_selection import train_test_split

        X = np.random.randn(len(data), 2)
        y = np.random.randn(len(data))
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model = self._build_model()
        self.model.fit(X_tr, y_tr)
        self._is_trained = True
        return {"mae": 0.5, "r2": 0.8}


class TestBasePredictor:
    def test_save_and_load(self):
        pred = MockPredictor()
        data = [{"a": 1.0, "b": 2.0}] * 10
        pred.train(data)
        with tempfile.TemporaryDirectory() as tmp:
            pred.save("test_model")
            loaded = MockPredictor(model_dir=tmp)
            loaded.model = pred.model
            loaded._is_trained = True
            assert loaded.is_trained
            result = loaded.predict([{"a": 1.0, "b": 2.0}])
            assert len(result) > 0

    def test_not_trained_raises(self):
        pred = MockPredictor()
        with pytest.raises(RuntimeError, match="not trained"):
            pred.predict([{"a": 1.0}])


class TestDelayPredictor:
    def test_build_model(self):
        pred = DelayPredictor()
        model = pred._build_model()
        assert model is not None

    def test_prepare_features(self):
        pred = DelayPredictor()
        data = pred.generate_synthetic_data(10)
        X = pred._prepare_features(data)
        assert X.shape[0] == 10
        assert X.shape[1] == len(pred._feature_names)

    def test_train_and_predict(self):
        pred = DelayPredictor()
        data = pred.generate_synthetic_data(500)
        metrics = pred.train(data)
        assert "mae" in metrics
        assert "r2" in metrics
        assert pred.is_trained
        pred_data = pred.generate_synthetic_data(5)
        result = pred.predict(pred_data)
        assert len(result) == 5
        assert all(r >= 0 for r in result)

    def test_save_load(self, tmp_path):
        pred = DelayPredictor(str(tmp_path))
        data = pred.generate_synthetic_data(500)
        pred.train(data)
        pred.save("delay_test")
        loaded = DelayPredictor(str(tmp_path))
        loaded.load("delay_test")
        assert loaded.is_trained
        test_data = pred.generate_synthetic_data(3)
        orig = pred.predict(test_data)
        reloaded = loaded.predict(test_data)
        assert np.allclose(orig, reloaded)


class TestCrowdPredictor:
    def test_train_and_predict(self):
        pred = CrowdPredictor()
        data = pred.generate_synthetic_data(500)
        metrics = pred.train(data)
        assert "mae" in metrics
        assert pred.is_trained
        test_data = pred.generate_synthetic_data(5)
        result = pred.predict(test_data)
        assert len(result) == 5

    def test_predict_station(self):
        pred = CrowdPredictor()
        data = pred.generate_synthetic_data(500)
        pred.train(data)
        pct = pred.predict_station("CST", "RD", 9, 0, 3)
        assert 0 <= pct <= 100


class TestDemandPredictor:
    def test_train_and_predict(self):
        pred = DemandPredictor()
        data = pred.generate_synthetic_data(500)
        metrics = pred.train(data)
        assert "mae" in metrics
        assert pred.is_trained
        test_data = pred.generate_synthetic_data(5)
        result = pred.predict(test_data)
        assert len(result) == 5

    def test_predict_od(self):
        pred = DemandPredictor()
        data = pred.generate_synthetic_data(500)
        pred.train(data)
        count = pred.predict_od("STA", "STB", "RD", "RD", 9, 0)
        assert count >= 0

    def test_top_od_pairs(self):
        pred = DemandPredictor()
        data = pred.generate_synthetic_data(500)
        pred.train(data)
        top = pred.get_top_od_pairs(3)
        assert len(top) <= 3
        for pair in top:
            assert "origin_dest" in pair
            assert "passenger_count" in pair


class TestETAPredictor:
    def test_train_and_predict(self):
        pred = ETAPredictor()
        data = pred.generate_synthetic_data(500)
        metrics = pred.train(data)
        assert "mae" in metrics
        assert pred.is_trained
        test_data = pred.generate_synthetic_data(5)
        result = pred.predict(test_data)
        assert len(result) == 5
        assert all(r >= 30 for r in result)

    def test_predict_eta(self):
        pred = ETAPredictor()
        data = pred.generate_synthetic_data(500)
        pred.train(data)
        eta = pred.predict_eta("STA", "STD", "RD", 9, 0)
        assert eta >= 30


class TestIncidentPredictor:
    def test_train_and_predict(self):
        pred = IncidentPredictor()
        data = pred.generate_synthetic_data(500)
        metrics = pred.train(data)
        assert "accuracy" in metrics
        assert pred.is_trained
        test_data = pred.generate_synthetic_data(10)
        result = pred.predict(test_data)
        assert len(result) == 10
        assert all(r in (0, 1) for r in result)

    def test_predict_proba(self):
        pred = IncidentPredictor()
        data = pred.generate_synthetic_data(500)
        pred.train(data)
        test_data = pred.generate_synthetic_data(3)
        proba = pred.predict_proba(test_data)
        assert proba.shape == (3, 2)
        assert all(0 <= p <= 1 for p in proba[:, 1])

    def test_predict_risk(self):
        pred = IncidentPredictor()
        data = pred.generate_synthetic_data(500)
        pred.train(data)
        risk = pred.predict_risk("RD", 5, 9, 0)
        assert "risk_probability_pct" in risk
        assert "risk_level" in risk
        assert risk["risk_level"] in ("low", "medium", "high")


class TestControlRoomAssistant:
    def test_intent_classification(self):
        asst = ControlRoomAssistant()
        result = asst.process_query("How delayed is the red line?")
        assert result["intent"] == "delay_query"
        assert result["confidence"] > 0

    def test_crowd_intent(self):
        asst = ControlRoomAssistant()
        result = asst.process_query("How crowded is Central Secretariat?")
        assert result["intent"] == "crowd_query"

    def test_eta_intent(self):
        asst = ControlRoomAssistant()
        result = asst.process_query("What is the ETA from Kashmere Gate to Hauz Khas?")
        assert result["intent"] == "eta_query"

    def test_incident_intent(self):
        asst = ControlRoomAssistant()
        result = asst.process_query("Any incidents on the yellow line?")
        assert result["intent"] == "incident_query"

    def test_demand_intent(self):
        asst = ControlRoomAssistant()
        result = asst.process_query("What are the busiest routes by passenger demand?")
        assert result["intent"] == "demand_query"

    def test_summary_intent(self):
        asst = ControlRoomAssistant()
        result = asst.process_query("Give me a system summary")
        assert result["intent"] == "summary_query"

    def test_help_intent(self):
        asst = ControlRoomAssistant()
        result = asst.process_query("What can you do?")
        assert result["intent"] == "help_query"

    def test_unknown_intent(self):
        asst = ControlRoomAssistant()
        result = asst.process_query("What is the weather like?")
        assert result["intent"] == "unknown"

    def test_response_has_text(self):
        asst = ControlRoomAssistant()
        result = asst.process_query("How delayed is the red line?")
        assert "text" in result
        assert len(result["text"]) > 0

    def test_register_predictors(self):
        asst = ControlRoomAssistant()
        preds = {"delay": DelayPredictor(), "crowd": CrowdPredictor()}
        data = DelayPredictor().generate_synthetic_data(200)
        preds["delay"].train(data)
        asst.register_predictors(preds)
        result = asst.process_query("How delayed is the red line?")
        assert "delay_minutes" in result

    def test_context_tracking(self):
        asst = ControlRoomAssistant()
        asst.process_query("How delayed?")
        asst.process_query("Any incidents?")
        ctx = asst.get_context()
        assert ctx["query_count"] == 2
        assert len(ctx["last_query"]) > 0

    def test_reset_context(self):
        asst = ControlRoomAssistant()
        asst.process_query("How delayed?")
        asst.reset_context()
        ctx = asst.get_context()
        assert ctx["query_count"] == 0


class TestInferenceEngine:
    def test_engine_creation(self):
        engine = InferenceEngine()
        assert "delay" in engine.predictors
        assert "incident" in engine.predictors

    def test_load_all(self):
        engine = InferenceEngine()
        results = engine.load_all()
        assert isinstance(results, dict)

    def test_is_ready(self):
        engine = InferenceEngine()
        ready = engine.is_ready()
        assert isinstance(ready, dict)


class TestTrainingPipeline:
    def test_train_all(self, tmp_path):
        results = train_all(str(tmp_path), n_samples=200, verbose=False)
        assert "delay" in results
        assert "crowd" in results
        assert "demand" in results
        assert "eta" in results
        assert "incident" in results
        for name, metrics in results.items():
            assert len(metrics) > 0
            model_path = tmp_path / f"{name}.joblib"
            meta_path = tmp_path / f"{name}_meta.json"
            assert model_path.exists(), f"Model file missing: {model_path}"
            assert meta_path.exists(), f"Meta file missing: {meta_path}"

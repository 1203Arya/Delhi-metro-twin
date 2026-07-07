from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import numpy as np


class IntentClassifier:
    def __init__(self) -> None:
        self.intents: dict[str, list[str]] = {
            "delay_query": [
                r"delay",
                r"late",
                r"behind schedule",
                r"on time",
                r"running (late|slow)",
                r"what.?s the (status|delay)",
                r"how (late|delayed)",
            ],
            "crowd_query": [
                r"crowd",
                r"busy",
                r"packed",
                r"congestion",
                r"how full",
                r"occupancy",
                r"platform (crowd|density)",
                r"rush",
            ],
            "eta_query": [
                r"eta",
                r"arrival",
                r"how long",
                r"travel time",
                r"reach",
                r"when (will|does|is|would).*(arrive|reach|come|get)",
                r"time to reach",
                r"minutes (to|from)",
            ],
            "incident_query": [
                r"incident",
                r"accident",
                r"problem",
                r"issue",
                r"disruption",
                r"breakdown",
                r"signal (fail|problem)",
                r"track (block|close|problem)",
                r"emergency",
                r"what happened",
            ],
            "demand_query": [
                r"demand",
                r"passenger (flow|count|volume|traffic)",
                r"how many passenger",
                r"busiest",
                r"crowded (station|line)",
                r"ridership",
                r"top station",
            ],
            "summary_query": [
                r"summary",
                r"overview",
                r"status",
                r"how is (everything|the metro)",
                r"report",
                r"dashboard",
            ],
            "help_query": [
                r"help",
                r"what can you do",
                r"capabilities",
                r"commands",
                r"how (can you|do you) help",
            ],
        }
        self._compiled: dict[str, list[re.Pattern]] = {}
        for intent, patterns in self.intents.items():
            self._compiled[intent] = [re.compile(p, re.IGNORECASE) for p in patterns]

    def classify(self, text: str) -> tuple[str, float]:
        text = text.strip().lower()
        if not text:
            return "unknown", 0.0
        scores: list[tuple[str, int]] = []
        for intent, patterns in self._compiled.items():
            count = sum(1 for p in patterns if p.search(text))
            if count > 0:
                scores.append((intent, count))
        if not scores:
            return "unknown", 0.0
        scores.sort(key=lambda x: x[1], reverse=True)
        max_count = scores[0][1]
        matching = [s for s in scores if s[1] == max_count]
        return matching[0][0], max_count / len(self._compiled[matching[0][0]])


class ControlRoomAssistant:
    def __init__(self) -> None:
        self.intent_classifier = IntentClassifier()
        self._context: dict[str, Any] = {
            "last_query": "",
            "last_response": "",
            "query_count": 0,
        }
        self.predictors: dict[str, Any] = {}

    def register_predictors(self, predictors: dict[str, Any]) -> None:
        self.predictors.update(predictors)

    def process_query(self, query: str) -> dict[str, Any]:
        self._context["last_query"] = query
        self._context["query_count"] += 1
        intent, confidence = self.intent_classifier.classify(query)
        handler = getattr(self, f"_handle_{intent}", self._handle_unknown)
        response = handler(query)
        response["intent"] = intent
        response["confidence"] = round(confidence, 3)
        response["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._context["last_response"] = response.get("text", "")
        return response

    def _handle_delay_query(self, query: str) -> dict[str, Any]:
        line, station = self._extract_line_station(query)
        predictor = self.predictors.get("delay")
        if predictor and predictor.is_trained:
            data = self._build_delay_features(line, station)
            pred = predictor.predict(data)
            avg_delay = float(np.mean(pred))
        else:
            avg_delay = 0.0
        status = "on time" if avg_delay < 1.0 else f"delayed by ~{avg_delay:.1f} min"
        text = f"Current delays on {line or 'all lines'}: trains are {status}."
        if station:
            text += f" At {station}, average delay is ~{avg_delay:.1f} minutes."
        return {
            "text": text,
            "delay_minutes": round(avg_delay, 2),
            "line": line or "all",
            "station": station or "all",
        }

    def _handle_crowd_query(self, query: str) -> dict[str, Any]:
        line, station = self._extract_line_station(query)
        predictor = self.predictors.get("crowd")
        if predictor and predictor.is_trained:
            data = self._build_crowd_features(line, station)
            pred = predictor.predict(data)
            crowd_pct = float(np.mean(pred))
        else:
            crowd_pct = 45.0
        level = (
            "low"
            if crowd_pct < 30
            else (
                "moderate"
                if crowd_pct < 60
                else ("high" if crowd_pct < 85 else "critical")
            )
        )
        text = f"Crowd level at {station or 'stations on ' + (line or 'all lines')}: {level} ({crowd_pct:.0f}% capacity)."
        return {
            "text": text,
            "crowding_pct": round(crowd_pct, 1),
            "level": level,
            "line": line or "all",
            "station": station or "all",
        }

    def _handle_eta_query(self, query: str) -> dict[str, Any]:
        stations = self._extract_station_pair(query)
        predictor = self.predictors.get("eta")
        if predictor and predictor.is_trained and stations:
            eta_s = predictor.predict_eta(stations[0], stations[1])
        else:
            eta_s = 300.0
        eta_min = eta_s / 60.0
        if stations:
            text = f"Estimated travel time from {stations[0]} to {stations[1]}: ~{eta_min:.1f} minutes."
        else:
            text = f"Estimated travel time: ~{eta_min:.1f} minutes."
        return {
            "text": text,
            "eta_seconds": round(eta_s, 1),
            "eta_minutes": round(eta_min, 1),
        }

    def _handle_incident_query(self, query: str) -> dict[str, Any]:
        line, station = self._extract_line_station(query)
        predictor = self.predictors.get("incident")
        if predictor and predictor.is_trained:
            data = self._build_incident_features(line, station)
            predictor.predict(data)
            proba = predictor.predict_proba(data)
            risk_pct = float(np.mean(proba[:, 1]) * 100) if proba.shape[1] > 1 else 0.0
        else:
            risk_pct = 5.0
        level = "low" if risk_pct < 20 else ("medium" if risk_pct < 50 else "high")
        text = f"Incident risk on {line or 'all lines'}: {level} ({risk_pct:.1f}% probability)."
        if risk_pct >= 50:
            text += " Monitoring advised."
        return {
            "text": text,
            "risk_pct": round(risk_pct, 1),
            "level": level,
            "line": line or "all",
        }

    def _handle_demand_query(self, query: str) -> dict[str, Any]:
        predictor = self.predictors.get("demand")
        if predictor and predictor.is_trained:
            top = predictor.get_top_od_pairs(5)
            pairs_text = "; ".join(
                [f"{p['origin_dest']}: {p['passenger_count']}" for p in top]
            )
            text = f"Top origin-destination pairs: {pairs_text}."
        else:
            text = (
                "Passenger demand data not available yet. Train the demand model first."
            )
        return {
            "text": text,
            "top_od_pairs": top if predictor and predictor.is_trained else [],
        }

    def _handle_summary_query(self, query: str) -> dict[str, Any]:
        parts = []
        for name, pred in self.predictors.items():
            if pred.is_trained:
                m = pred.get_metrics()
                parts.append(
                    f"{name}: trained (r2={m.get('r2', 0):.3f})"
                    if "r2" in m
                    else f"{name}: trained"
                )
            else:
                parts.append(f"{name}: not trained")
        text = "Metro Operations Summary: " + "; ".join(parts) + "."
        return {"text": text, "models": list(self.predictors.keys())}

    def _handle_help_query(self, query: str) -> dict[str, Any]:
        text = (
            "I can help with:\n"
            "- Delay queries: 'How delayed is the red line?'\n"
            "- Crowd queries: 'How crowded is Central Secretariat?'\n"
            "- ETA queries: 'ETA from Kashmere Gate to Hauz Khas?'\n"
            "- Incident queries: 'Any incidents on the yellow line?'\n"
            "- Demand queries: 'What are the busiest routes?'\n"
            "- Summary: 'Give me a system summary'"
        )
        return {"text": text}

    def _handle_unknown(self, query: str) -> dict[str, Any]:
        return {
            "text": "I'm not sure how to answer that. Try asking about delays, crowding, ETA, incidents, or demand.",
            "suggestions": ["delay", "crowd", "ETA", "incident", "demand", "summary"],
        }

    def _extract_line_station(self, query: str) -> tuple[str, str]:
        line_codes = [
            "RD",
            "YL",
            "BL",
            "BR",
            "GR",
            "GB",
            "VL",
            "PK",
            "MG",
            "GY",
            "OR",
            "RM",
        ]
        line_names = {
            "red": "RD",
            "yellow": "YL",
            "blue": "BL",
            "green": "GR",
            "orange": "OR",
            "pink": "PK",
            "magenta": "MG",
            "grey": "GY",
            "violet": "VL",
            "rapid": "RM",
        }
        line = ""
        for full, code in line_names.items():
            if full in query.lower():
                line = code
                break
        for code in line_codes:
            if code.lower() in query.lower():
                line = code
                break
        station = ""
        station_match = re.search(
            r"(?:at|from|to|near|station\s+is|in\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            query,
        )
        if station_match:
            station = station_match.group(1)
        return line, station

    def _extract_station_pair(self, query: str) -> list[str]:
        stations = re.findall(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", query)
        return stations[:2] if len(stations) >= 2 else ["Station A", "Station B"]

    def _build_delay_features(self, line: str, station: str) -> list[dict[str, Any]]:
        now = datetime.now()
        row = {
            "hour": now.hour,
            "day_of_week": now.weekday(),
            "month": now.month,
            "is_peak_hour": 1 if (7 <= now.hour <= 10) or (17 <= now.hour <= 20) else 0,
            "is_weekend": 1 if now.weekday() >= 5 else 0,
            "line_code": line or "RD",
            "station_sequence": 5,
            "num_stations_remaining": 10,
            "prev_delay_minutes": 0.0,
            "headway_s": 120.0,
            "dwell_time_s": 20.0,
            "train_occupancy_pct": 0.5,
            "is_terminus": 0,
            "has_junction": 0,
            "num_platforms": 2,
            "track_length_km": 1.5,
            "speed_limit_kmh": 80.0,
            "is_curve": 0,
        }
        return [row]

    def _build_crowd_features(self, line: str, station: str) -> list[dict[str, Any]]:
        now = datetime.now()
        return [
            {
                "hour": now.hour,
                "day_of_week": now.weekday(),
                "month": now.month,
                "is_peak_hour": 1
                if (7 <= now.hour <= 10) or (17 <= now.hour <= 20)
                else 0,
                "is_weekend": 1 if now.weekday() >= 5 else 0,
                "line_code": line or "RD",
                "station_sequence": 5,
                "is_terminus": 0,
                "has_junction": 0,
                "is_interchange": 1,
                "num_platforms": 2,
                "num_lines_at_station": 2,
                "nearby_offices": 5,
                "nearby_residential": 3,
                "temperature_c": 25.0,
                "is_holiday": 0,
            }
        ]

    def _build_incident_features(self, line: str, station: str) -> list[dict[str, Any]]:
        now = datetime.now()
        return [
            {
                "hour": now.hour,
                "day_of_week": now.weekday(),
                "month": now.month,
                "is_peak_hour": 1
                if (7 <= now.hour <= 10) or (17 <= now.hour <= 20)
                else 0,
                "is_weekend": 1 if now.weekday() >= 5 else 0,
                "line_code": line or "RD",
                "station_sequence": 5,
                "num_trains_active": 15,
                "avg_headway_s": 120.0,
                "avg_speed_kmh": 45.0,
                "avg_occupancy_pct": 60.0,
                "is_terminus": 0,
                "has_junction": 0,
                "num_platforms": 2,
                "track_length_km": 1.5,
                "speed_limit_kmh": 80.0,
                "is_curve": 0,
                "max_gradient_pct": 1.0,
                "days_since_last_incident": 30.0,
                "prev_incidents_24h": 0,
            }
        ]

    def get_context(self) -> dict[str, Any]:
        return dict(self._context)

    def reset_context(self) -> None:
        self._context = {"last_query": "", "last_response": "", "query_count": 0}


assistant = ControlRoomAssistant()

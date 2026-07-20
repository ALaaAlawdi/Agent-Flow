"""Superhuman Prediction - See the future better than humans.

Features:
- Trend analysis and forecasting
- Pattern-based prediction
- Monte Carlo simulation
- Bayesian inference for uncertainty
- Scenario planning
- Early warning systems
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict


class Trend:
    """A detected trend in data."""
    
    def __init__(
        self,
        name: str,
        direction: str,  # "rising", "falling", "cyclical", "stable"
        strength: float,  # 0-1
        confidence: float,
        duration: str,  # "short", "medium", "long"
    ):
        self.name = name
        self.direction = direction
        self.strength = strength
        self.confidence = confidence
        self.duration = duration
        self.detected_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "direction": self.direction,
            "strength": self.strength,
            "confidence": self.confidence,
            "duration": self.duration,
        }


class Forecast:
    """A forecast of future states."""
    
    def __init__(
        self,
        forecast_id: str,
        target: str,
        horizon: str,  # "1h", "1d", "1w", "1m", "1y"
        prediction: Any,
        confidence: float,
        scenarios: list[dict] = None,
    ):
        self.forecast_id = forecast_id
        self.target = target
        self.horizon = horizon
        self.prediction = prediction
        self.confidence = confidence
        self.scenarios = scenarios or []
        self.created_at = datetime.now().isoformat()


class BayesianInference:
    """Bayesian inference for updating beliefs."""
    
    def __init__(self):
        self.priors: dict[str, float] = {}
        self.posteriors: dict[str, float] = {}
        self.evidence: list[dict] = []
    
    def set_prior(self, hypothesis: str, probability: float):
        """Set prior probability."""
        self.priors[hypothesis] = max(0, min(1, probability))
        self.posteriors[hypothesis] = self.priors[hypothesis]
    
    def update(self, hypothesis: str, likelihood: float, evidence_weight: float = 1.0):
        """Update belief using Bayes' theorem.
        
        P(H|E) = P(E|H) * P(H) / P(E)
        """
        prior = self.posteriors.get(hypothesis, self.priors.get(hypothesis, 0.5))
        
        # Simplified Bayesian update
        posterior = (likelihood * prior * evidence_weight) / (
            (likelihood * prior) + ((1 - likelihood) * (1 - prior))
        )
        
        self.posteriors[hypothesis] = max(0, min(1, posterior))
        
        self.evidence.append({
            "hypothesis": hypothesis,
            "likelihood": likelihood,
            "weight": evidence_weight,
            "old": prior,
            "new": self.posteriors[hypothesis],
            "timestamp": datetime.now().isoformat(),
        })
        
        return self.posteriors[hypothesis]
    
    def get_belief(self, hypothesis: str) -> float:
        """Get current belief."""
        return self.posteriors.get(hypothesis, self.priors.get(hypothesis, 0.5))


class MonteCarloSimulator:
    """Monte Carlo simulation for predicting outcomes."""
    
    def __init__(self, num_simulations: int = 1000):
        self.num_simulations = num_simulations
        self.results: list[Any] = []
    
    def simulate(
        self,
        model: callable,
        parameters: dict,
    ) -> dict:
        """Run Monte Carlo simulation."""
        outcomes = []
        
        for _ in range(self.num_simulations):
            # Sample parameters with uncertainty
            sampled_params = {}
            for key, value in parameters.items():
                if isinstance(value, (int, float)):
                    # Add 10% noise
                    noise = value * 0.1 * (2 * random.random() - 1)
                    sampled_params[key] = value + noise
                else:
                    sampled_params[key] = value
            
            # Run model
            outcome = model(**sampled_params)
            outcomes.append(outcome)
        
        # Analyze outcomes
        avg = sum(outcomes) / len(outcomes) if outcomes else 0
        min_val = min(outcomes) if outcomes else 0
        max_val = max(outcomes) if outcomes else 0
        
        # Calculate percentiles
        sorted_outcomes = sorted(outcomes)
        p10 = sorted_outcomes[len(sorted_outcomes) // 10] if sorted_outcomes else 0
        p90 = sorted_outcomes[(len(sorted_outcomes) * 9) // 10] if sorted_outcomes else 0
        
        return {
            "mean": avg,
            "min": min_val,
            "max": max_val,
            "p10": p10,
            "p90": p90,
            "simulations": self.num_simulations,
            "distribution": outcomes[:100],  # Sample
        }


class EarlyWarningSystem:
    """Detect problems before they happen."""
    
    def __init__(self):
        self.warning_signals: list[dict] = []
        self.anomaly_threshold = 0.7
    
    def monitor(
        self,
        metric_name: str,
        current_value: float,
        expected_range: tuple[float, float],
    ) -> Optional[dict]:
        """Monitor a metric and emit warnings."""
        min_expected, max_expected = expected_range
        
        if current_value < min_expected or current_value > max_expected:
            severity = "high" if abs(current_value - sum(expected_range) / 2) > (
                max_expected - min_expected
            ) else "medium"
            
            warning = {
                "metric": metric_name,
                "current": current_value,
                "expected": expected_range,
                "severity": severity,
                "anomaly_score": abs(current_value - sum(expected_range) / 2) / (
                    max_expected - min_expected
                ),
                "detected_at": datetime.now().isoformat(),
            }
            
            self.warning_signals.append(warning)
            return warning
        
        return None
    
    def get_warnings(self, severity: Optional[str] = None) -> list[dict]:
        """Get warnings filtered by severity."""
        if severity:
            return [w for w in self.warning_signals if w["severity"] == severity]
        return self.warning_signals


class Oracle:
    """Superhuman prediction engine.
    
    Predicts:
    - Future trends
    - Likely outcomes
    - Anomalies and risks
    - Optimal timing
    """
    
    def __init__(self):
        self.trends: list[Trend] = []
        self.forecasts: list[Forecast] = []
        self.bayesian = BayesianInference()
        self.monte_carlo = MonteCarloSimulator()
        self.warning_system = EarlyWarningSystem()
    
    def detect_trends(self, data: list[float]) -> list[Trend]:
        """Detect trends in time series data."""
        if len(data) < 3:
            return []
        
        trends = []
        
        # Calculate slope
        first_half_avg = sum(data[:len(data)//2]) / (len(data)//2)
        second_half_avg = sum(data[len(data)//2:]) / (len(data) - len(data)//2)
        
        if second_half_avg > first_half_avg * 1.1:
            direction = "rising"
        elif second_half_avg < first_half_avg * 0.9:
            direction = "falling"
        else:
            direction = "stable"
        
        strength = abs(second_half_avg - first_half_avg) / max(abs(first_half_avg), 1)
        
        trend = Trend(
            name="trend",
            direction=direction,
            strength=min(1.0, strength),
            confidence=min(1.0, len(data) / 100),
            duration="medium",
        )
        trends.append(trend)
        self.trends.append(trend)
        
        return trends
    
    def forecast(
        self,
        target: str,
        current_value: float,
        trend: Trend,
        horizon: str = "1w",
    ) -> Forecast:
        """Forecast future value."""
        
        # Project based on trend
        horizon_days = {
            "1h": 1/24, "1d": 1, "1w": 7, "1m": 30, "1y": 365,
        }.get(horizon, 7)
        
        # Simple projection
        if trend.direction == "rising":
            projected = current_value * (1 + trend.strength * horizon_days / 30)
        elif trend.direction == "falling":
            projected = current_value * (1 - trend.strength * horizon_days / 30)
        else:
            projected = current_value
        
        forecast_id = f"forecast_{len(self.forecasts)}"
        forecast = Forecast(
            forecast_id=forecast_id,
            target=target,
            horizon=horizon,
            prediction=projected,
            confidence=trend.confidence * 0.8,
            scenarios=[
                {"scenario": "best_case", "value": projected * 1.2},
                {"scenario": "expected", "value": projected},
                {"scenario": "worst_case", "value": projected * 0.8},
            ],
        )
        
        self.forecasts.append(forecast)
        return forecast
    
    def predict_outcome(
        self,
        situation: dict,
        num_simulations: int = 1000,
    ) -> dict:
        """Predict outcome using Monte Carlo simulation."""
        
        # Define model
        def outcome_model(**kwargs):
            # Simple linear model with randomness
            base = sum(kwargs.values()) if kwargs else 0
            return base + random.gauss(0, 1)
        
        self.monte_carlo.num_simulations = num_simulations
        result = self.monte_carlo.simulate(outcome_model, situation)
        
        return result
    
    def predict_anomaly(
        self,
        metric_name: str,
        current_value: float,
        historical_avg: float,
        historical_std: float,
    ) -> dict:
        """Predict if current value is anomalous."""
        
        # Z-score
        if historical_std == 0:
            z_score = 0
        else:
            z_score = abs(current_value - historical_avg) / historical_std
        
        is_anomaly = z_score > 2.0  # > 2 standard deviations
        
        return {
            "metric": metric_name,
            "current": current_value,
            "z_score": z_score,
            "is_anomaly": is_anomaly,
            "severity": "high" if z_score > 3 else "medium" if z_score > 2 else "low",
            "prediction": "anomaly_detected" if is_anomaly else "normal",
        }
    
    def set_belief(self, hypothesis: str, probability: float):
        """Set prior belief."""
        self.bayesian.set_prior(hypothesis, probability)
    
    def update_belief(self, hypothesis: str, evidence: float):
        """Update belief with new evidence."""
        return self.bayesian.update(hypothesis, evidence)
    
    def get_oracle_report(self) -> dict:
        """Get comprehensive oracle report."""
        return {
            "trends_detected": len(self.trends),
            "forecasts_made": len(self.forecasts),
            "current_beliefs": dict(self.bayesian.posteriors),
            "warnings_issued": len(self.warning_system.warning_signals),
        }
"""Price anomaly detection. CPU z-score baseline (no heavy deps); an autoencoder
(torch) variant can be added later for multivariate signals."""

import statistics


class AnomalyDetector:
    def detect(self, history: list[float], value: float, z_threshold: float = 3.0) -> dict:
        if len(history) < 5:
            return {"is_anomaly": False, "score": 0.0, "reason": "insufficient_history"}
        mean = statistics.fmean(history)
        stdev = statistics.pstdev(history) or 1e-9
        z = (value - mean) / stdev
        return {
            "is_anomaly": abs(z) >= z_threshold,
            "score": round(abs(z), 3),
            "z": round(z, 3),
            "mean": round(mean, 2),
        }

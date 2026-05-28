"""Regional surplus/deficit classifier. CPU heuristic baseline (stock vs demand);
a learned classifier can replace this when stock/demand history is available."""


class SurplusDeficitClassifier:
    def classify(self, stock: float, demand: float) -> dict:
        if demand <= 0:
            return {"label": "unknown", "ratio": None}
        ratio = stock / demand
        if ratio >= 1.2:
            label = "surplus"
        elif ratio <= 0.8:
            label = "deficit"
        else:
            label = "balanced"
        return {"label": label, "ratio": round(ratio, 3)}

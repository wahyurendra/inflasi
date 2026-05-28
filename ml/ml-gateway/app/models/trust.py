"""Contributor trust score (0..1) from simple behavioural features. CPU heuristic;
can be swapped for a learned model once enough labelled history exists."""


class TrustScorer:
    def score(self, approved: int = 0, total: int = 0, account_age_days: int = 0, flagged: int = 0) -> dict:
        base = (approved / total) if total > 0 else 0.5
        age_bonus = min(account_age_days / 365, 1.0) * 0.1
        flag_penalty = min(flagged * 0.05, 0.3)
        score = max(0.0, min(1.0, base + age_bonus - flag_penalty))
        return {"trust": round(score, 3), "approved": approved, "total": total}

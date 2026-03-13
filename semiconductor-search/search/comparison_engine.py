from config.ranking_weights import RANKING_CONFIG


def apply_rules_and_rank(base: dict, candidates: list[dict], top_n: int) -> list[dict]:
    category = (base.get("category") or "").lower()
    cfg = RANKING_CONFIG.get(category, RANKING_CONFIG["default"])
    weights = cfg["weights"]
    rules = cfg["rules"]

    ranked = []
    for candidate in candidates:
        if not _passes_rules(base, candidate, rules):
            continue
        score = _score(base, candidate, weights)
        item = dict(candidate)
        item["rule_score"] = round(score, 4)
        ranked.append(item)

    return sorted(ranked, key=lambda x: x["rule_score"], reverse=True)[:top_n]


def _passes_rules(base: dict, candidate: dict, rules: dict) -> bool:
    for field, mode in rules.items():
        b = base.get(field)
        c = candidate.get(field)
        if b is None or c is None:
            continue
        if mode == "gte" and c < b:
            return False
        if mode == "lte" and c > b:
            return False
    return True


def _score(base: dict, candidate: dict, weights: dict) -> float:
    total = sum(weights.values()) or 1
    score = 0.0
    for field, weight in weights.items():
        b = base.get(field)
        c = candidate.get(field)
        if b is None or c is None:
            continue
        if isinstance(b, (int, float)) and isinstance(c, (int, float)) and max(abs(b), abs(c)) > 0:
            closeness = min(abs(b), abs(c)) / max(abs(b), abs(c))
            score += closeness * weight
        else:
            if str(b).lower() == str(c).lower():
                score += weight
    return score / total

"""Deterministic fictional data helpers for the public portfolio demos."""

import math


# Fictional catalogue and hand-authored toy descriptors. These values are not
# trained on transactions and must not be presented as model outputs.
ILLUSTRATIVE_CATALOGUE = {
    "Comet Trail Mug": (1.0, 1.0, 1.0, 0.0, 0.0, 0.0),
    "Orbit Flask": (1.0, 1.0, 1.0, 0.0, 0.0, 0.0),
    "Harbor Lunch Tin": (0.9, 0.8, 1.0, 0.0, 0.0, 0.2),
    "Paperleaf Notebook": (0.0, 0.0, 0.2, 1.0, 1.0, 0.2),
    "Desk Nest Organizer": (0.0, 0.0, 0.3, 1.0, 0.6, 1.0),
    "Tideway Carryall": (0.8, 0.1, 0.8, 0.0, 0.0, 1.0),
}


def illustrative_recommendations(basket, limit=4):
    """Rank fictional products by cosine similarity to a fictional basket."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= len(ILLUSTRATIVE_CATALOGUE) - 1:
        raise ValueError("limit must be an integer from 1 to 5")
    if isinstance(basket, str):
        raise ValueError("basket must be a collection of fictional catalogue items")
    selected = list(basket)
    if len(selected) != len(set(selected)):
        raise ValueError("basket items must be unique")
    if any(item not in ILLUSTRATIVE_CATALOGUE for item in selected):
        raise ValueError("basket contains an item outside the fictional catalogue")
    if not selected:
        return []

    def cosine(left, right):
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0

    candidates = []
    for name, vector in ILLUSTRATIVE_CATALOGUE.items():
        if name in selected:
            continue
        score = sum(cosine(vector, ILLUSTRATIVE_CATALOGUE[item]) for item in selected) / len(selected)
        candidates.append({"product": name, "illustrative_similarity": score})
    return sorted(candidates, key=lambda item: (-item["illustrative_similarity"], item["product"]))[:limit]


def illustrative_threshold_met(hypothetical_baskets, visitor_selected_threshold):
    """Evaluate a visitor-chosen toy rule; this does not predict future behavior."""
    for value, label, minimum in (
        (hypothetical_baskets, "hypothetical_baskets", 0),
        (visitor_selected_threshold, "visitor_selected_threshold", 1),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum or value > 12:
            raise ValueError(f"{label} must be an integer from {minimum} to 12")
    return hypothetical_baskets >= visitor_selected_threshold

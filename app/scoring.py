import logging

logger = logging.getLogger("scoring")


def calculate_score(activity: dict) -> tuple[float, str]:
    """
    Calculates a 0-100 risk score from a wallet's recent activity summary.
    Returns the score plus a plain-language explanation of what drove it.

    This is a simple, transparent heuristic model (not ML) by design:
    every score is fully explainable, which matters more for a portfolio
    project than marginal accuracy gains from a black-box model.
    """
    tx_count = activity["tx_count"]
    total_value_eth = activity["total_value_eth"]
    contract_interactions = activity["contract_interactions"]

    score = 0.0
    reasons = []

    # High transaction frequency in a short window can indicate bot/exploit activity
    if tx_count >= 50:
        score += 30
        reasons.append(f"very high transaction frequency ({tx_count} txs in the observed window)")
    elif tx_count >= 15:
        score += 15
        reasons.append(f"elevated transaction frequency ({tx_count} txs)")

    # Large volume moved is inherently higher-stakes, regardless of intent
    if total_value_eth >= 100:
        score += 30
        reasons.append(f"large volume moved ({total_value_eth:.2f} ETH)")
    elif total_value_eth >= 20:
        score += 15
        reasons.append(f"moderate volume moved ({total_value_eth:.2f} ETH)")

    # Heavy contract interaction can indicate automated/programmatic behavior
    if tx_count > 0:
        contract_ratio = contract_interactions / tx_count
        if contract_ratio >= 0.8:
            score += 25
            reasons.append(f"{contract_ratio:.0%} of transactions were contract interactions")
        elif contract_ratio >= 0.4:
            score += 10
            reasons.append(f"{contract_ratio:.0%} of transactions were contract interactions")

    score = min(100.0, score)

    if not reasons:
        reasoning = "No notable activity patterns detected in the observed window."
    else:
        reasoning = "Score driven by: " + "; ".join(reasons) + "."

    return score, reasoning

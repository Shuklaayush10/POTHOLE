def get_recommendation(severity):
    recommendations = {
        "MINOR": {
            "action": "Cold patch repair",
            "risk": "Low risk. Monitor for further degradation.",
            "urgency_days": "Within 30 days"
        },
        "MODERATE": {
            "action": "Asphalt patching / Milling",
            "risk": "Medium risk. Can cause vehicle damage.",
            "urgency_days": "Within 7-14 days"
        },
        "SEVERE": {
            "action": "Full-depth reconstruction",
            "risk": "High risk. Immediate safety hazard.",
            "urgency_days": "Immediate (24-48 hours)"
        }
    }
    return recommendations.get(severity, recommendations["MINOR"])

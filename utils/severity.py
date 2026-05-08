def estimate_severity(area, depth_proxy):
    # depth_proxy is average intensity (0-255). Darker is deeper.
    # Lower depth_proxy means darker (deeper)
    
    severity_score = 0
    if area < 5000:
        severity_score += 1
    elif area < 15000:
        severity_score += 2
    else:
        severity_score += 3
        
    if depth_proxy > 150: # Light
        severity_score += 1
    elif depth_proxy > 80: # Medium
        severity_score += 2
    else: # Dark/Deep
        severity_score += 3
        
    if severity_score <= 3:
        severity = "MINOR"
        confidence = 0.85
        urgency = "Low"
    elif severity_score <= 5:
        severity = "MODERATE"
        confidence = 0.90
        urgency = "Medium"
    else:
        severity = "SEVERE"
        confidence = 0.95
        urgency = "High"
        
    return {
        "severity": severity,
        "confidence": confidence,
        "urgency": urgency
    }

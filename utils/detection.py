import cv2
import numpy as np
import os
import uuid

def process_image(image_path, processed_dir):
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        return None
        
    original_img = img.copy()
    
    # Grayscale conversion
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Edge detection
    edges = cv2.Canny(blurred, 50, 150)
    
    # Morphological operations (dilate, erode) to close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    # Contour detection
    contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    potholes = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # Region filtering based on area
        if area > 1000 and area < 50000:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            
            # Potholes are usually somewhat circular or oval, not long lines
            if 0.2 < aspect_ratio < 5.0:
                # Mask to get the intensity inside the pothole
                mask = np.zeros_like(gray)
                cv2.drawContours(mask, [contour], -1, 255, -1)
                mean_val = cv2.mean(gray, mask=mask)[0]
                
                # Darker areas are typically potholes (mean_val < 180)
                if mean_val < 180:
                    potholes.append({
                        "x": x, "y": y, "w": w, "h": h,
                        "area": area,
                        "depth_proxy": mean_val, # lower is darker/deeper
                        "contour": contour
                    })
                    
                    # Draw bounding box and contour
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.drawContours(img, [contour], -1, (0, 255, 0), 2)
                    cv2.putText(img, "Pothole", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    if len(potholes) == 0:
        return None
        
    # We'll just analyze the largest pothole for the report
    largest_pothole = max(potholes, key=lambda p: p['area'])
    
    filename = f"processed_{uuid.uuid4().hex}.jpg"
    processed_path = os.path.join(processed_dir, filename)
    
    cv2.imwrite(processed_path, img)
    
    return {
        "filename": filename,
        "width": largest_pothole['w'],
        "height": largest_pothole['h'],
        "area": largest_pothole['area'],
        "depth_proxy": largest_pothole['depth_proxy'],
        "total_detected": len(potholes)
    }

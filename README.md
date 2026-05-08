# AI-Powered Pothole Detection System

A complete web application that uses OpenCV to detect potholes from uploaded images, estimates severity, and provides repair recommendations.

## Features
- Upload road images for AI analysis
- OpenCV-based computer vision detection
- Severity estimation (Minor, Moderate, Severe)
- Smart dashboards and geolocation mapping
- PDF report generation
- REST API integration

## Run Locally

1. Install dependencies:
`pip install -r requirements.txt`

2. Run the Flask application:
`python app.py`

3. Open `http://localhost:5000` in your browser.

## Run with Docker

1. Build image:
`docker build -t pothole-app .`

2. Run container:
`docker run -p 5000:5000 pothole-app`

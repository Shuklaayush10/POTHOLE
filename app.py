import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

from utils.detection import process_image
from utils.severity import estimate_severity
from utils.recommendations import get_recommendation
from utils.pdf_generator import generate_pdf

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-pothole'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/pothole.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max upload

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database'), exist_ok=True)

db = SQLAlchemy(app)

class PotholeReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_image = db.Column(db.String(255), nullable=False)
    processed_image = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    severity = db.Column(db.String(50), nullable=False)
    area = db.Column(db.Float, nullable=False)
    depth_proxy = db.Column(db.Float, nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/dashboard')
def dashboard():
    reports = PotholeReport.query.order_by(PotholeReport.timestamp.desc()).limit(1).all()
    latest_report = reports[0] if reports else None
    return render_template('dashboard.html', report=latest_report)

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/admin')
def admin():
    reports = PotholeReport.query.order_by(PotholeReport.timestamp.desc()).all()
    return render_template('admin.html', reports=reports)

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add uuid to avoid collisions
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Get coordinates if provided
        lat = request.form.get('latitude', type=float)
        lng = request.form.get('longitude', type=float)
        
        # Process image
        result = process_image(filepath, app.config['PROCESSED_FOLDER'])
        
        if result is None:
            return jsonify({'error': 'No potholes detected or invalid image'}), 400
            
        # Estimate Severity
        severity_data = estimate_severity(result['area'], result['depth_proxy'])
        
        # Get Recommendation
        rec_data = get_recommendation(severity_data['severity'])
        
        # Save to DB
        report = PotholeReport(
            original_image=unique_filename,
            processed_image=result['filename'],
            latitude=lat,
            longitude=lng,
            severity=severity_data['severity'],
            area=result['area'],
            depth_proxy=result['depth_proxy'],
            recommendation=rec_data['action']
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'report_id': report.id,
            'original_image': f'/uploads/{unique_filename}',
            'processed_image': f'/processed/{result["filename"]}',
            'severity': severity_data['severity'],
            'confidence': severity_data['confidence'],
            'urgency': severity_data['urgency'],
            'area': result['area'],
            'recommendation': rec_data['action'],
            'risk': rec_data['risk'],
            'total_detected': result['total_detected']
        })
        
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/results/<int:report_id>')
def get_result(report_id):
    report = PotholeReport.query.get_or_404(report_id)
    return jsonify({
        'id': report.id,
        'original_image': f'/uploads/{report.original_image}',
        'processed_image': f'/processed/{report.processed_image}',
        'latitude': report.latitude,
        'longitude': report.longitude,
        'severity': report.severity,
        'area': report.area,
        'recommendation': report.recommendation,
        'timestamp': report.timestamp.isoformat()
    })

@app.route('/api/history')
def get_history():
    reports = PotholeReport.query.order_by(PotholeReport.timestamp.desc()).all()
    data = []
    for r in reports:
        data.append({
            'id': r.id,
            'severity': r.severity,
            'timestamp': r.timestamp.isoformat(),
            'latitude': r.latitude,
            'longitude': r.longitude
        })
    return jsonify(data)

@app.route('/api/heatmap-data')
def get_heatmap_data():
    reports = PotholeReport.query.filter(PotholeReport.latitude.isnot(None)).all()
    data = []
    for r in reports:
        # Give higher weight to severe
        intensity = 1.0 if r.severity == 'SEVERE' else (0.6 if r.severity == 'MODERATE' else 0.3)
        data.append([r.latitude, r.longitude, intensity])
    return jsonify(data)

@app.route('/download_report/<int:report_id>')
def download_report(report_id):
    report = PotholeReport.query.get_or_404(report_id)
    pdf_filename = f"report_{report.id}.pdf"
    pdf_path = os.path.join(app.config['PROCESSED_FOLDER'], pdf_filename)
    
    generate_pdf(report, pdf_path, current_app)
    
    return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_file(os.path.join(app.config['PROCESSED_FOLDER'], filename))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

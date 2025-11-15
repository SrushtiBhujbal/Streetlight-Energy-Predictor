from flask import Flask, request, jsonify, render_template
import joblib
import pandas as pd
import numpy as np
import os
import json
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load model and metadata
try:
    model = joblib.load('models/final_streetlight_model.pkl')
    feature_columns = joblib.load('models/final_feature_columns.pkl')
    target_column = joblib.load('models/target_column.pkl')
    
    with open('models/model_info.json', 'r') as f:
        model_info = json.load(f)
    
    print("✅ Professional model loaded successfully")
    print(f"📊 Model Info: {model_info['training_samples']:,} samples, {model_info['cv_accuracy_percentage']:.1f}% accuracy")
    
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None
    feature_columns = []
    model_info = {}

@app.route('/')
def home():
    return render_template('professional_index.html', model_info=model_info)

@app.route('/api/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model not available'}), 500
        
    try:
        data = request.get_json()
        
        # Create input array with proper feature order and names
        input_data = []
        for col in feature_columns:
            value = data.get(col, 0)
            input_data.append(float(value))
            
        # Convert to DataFrame with proper feature names to avoid warnings
        features_df = pd.DataFrame([input_data], columns=feature_columns)
        
        # Get prediction
        prediction = model.predict(features_df)[0]
        probability = model.predict_proba(features_df)[0]
        confidence = max(probability)
        
        # Generate detailed explanation
        hour = data.get('hour', 12)
        month = data.get('month', 6)
        cloud = data.get('cloud', 0)
        precipitation = data.get('precipitation_mm', 0)
        visibility = data.get('visibility_km', 10)
        temperature = data.get('temperature_final', 25)
        
        explanation, details = generate_detailed_explanation(prediction, hour, month, cloud, precipitation, visibility, temperature, confidence)
        
        # Energy savings calculation
        power_watts = data.get('power_consumption_watts', 150)
        hourly_savings = power_watts if prediction == 0 else 0
        daily_savings = hourly_savings * 12  # Assume 12 hours potential savings
        monthly_savings = daily_savings * 30
        co2_savings = hourly_savings * 0.0005  # kg CO2 per watt-hour
        
        result = {
            'success': True,
            'prediction': int(prediction),
            'status': 'ON' if prediction == 1 else 'OFF',
            'confidence': float(confidence),
            'explanation': explanation,
            'details': details,
            'energy_savings': {
                'hourly': hourly_savings,
                'daily': daily_savings,
                'monthly': monthly_savings,
                'co2': round(co2_savings, 4)
            },
            'timestamp': datetime.now().isoformat(),
            'features_used': len(feature_columns),
            'conditions': {
                'hour': hour,
                'month': month,
                'cloud': cloud,
                'precipitation': precipitation,
                'visibility': visibility,
                'temperature': temperature
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

def generate_detailed_explanation(prediction, hour, month, cloud, precipitation, visibility, temperature, confidence):
    """Generate human-readable explanation for the prediction"""
    
    details = []
    
    # Time analysis
    if hour >= 19 or hour <= 6:
        details.append({"icon": "🌙", "text": f"Night time ({hour:02d}:00)", "type": "time"})
    elif 6 < hour < 12:
        details.append({"icon": "🌅", "text": f"Morning ({hour:02d}:00)", "type": "time"})
    elif 12 <= hour < 17:
        details.append({"icon": "☀️", "text": f"Afternoon ({hour:02d}:00)", "type": "time"})
    else:
        details.append({"icon": "🌆", "text": f"Evening ({hour:02d}:00)", "type": "time"})
    
    # Weather analysis
    if cloud < 20:
        details.append({"icon": "☀️", "text": f"Clear sky ({cloud}% clouds)", "type": "weather"})
    elif cloud < 50:
        details.append({"icon": "🌤️", "text": f"Partly cloudy ({cloud}% clouds)", "type": "weather"})
    elif cloud < 80:
        details.append({"icon": "☁️", "text": f"Cloudy ({cloud}% clouds)", "type": "weather"})
    else:
        details.append({"icon": "🌫️", "text": f"Heavy clouds ({cloud}% clouds)", "type": "weather"})
    
    # Precipitation analysis
    if precipitation > 1.0:
        details.append({"icon": "🌧️", "text": f"Heavy rain ({precipitation}mm)", "type": "precipitation"})
    elif precipitation > 0.3:
        details.append({"icon": "🌦️", "text": f"Light rain ({precipitation}mm)", "type": "precipitation"})
    elif precipitation > 0:
        details.append({"icon": "💧", "text": f"Drizzle ({precipitation}mm)", "type": "precipitation"})
    else:
        details.append({"icon": "✅", "text": "No precipitation", "type": "precipitation"})
    
    # Visibility analysis
    if visibility < 5:
        details.append({"icon": "🌫️", "text": f"Poor visibility ({visibility}km)", "type": "visibility"})
    elif visibility < 10:
        details.append({"icon": "👁️", "text": f"Moderate visibility ({visibility}km)", "type": "visibility"})
    else:
        details.append({"icon": "🔭", "text": f"Good visibility ({visibility}km)", "type": "visibility"})
    
    # Temperature analysis
    if temperature < 0:
        details.append({"icon": "❄️", "text": f"Freezing ({temperature}°C)", "type": "temperature"})
    elif temperature < 10:
        details.append({"icon": "🥶", "text": f"Cold ({temperature}°C)", "type": "temperature"})
    elif temperature < 25:
        details.append({"icon": "😊", "text": f"Moderate ({temperature}°C)", "type": "temperature"})
    else:
        details.append({"icon": "🔥", "text": f"Warm ({temperature}°C)", "type": "temperature"})
    
    if prediction == 1:
        main_reason = "Safety and visibility requirements"
        if hour >= 19 or hour <= 6:
            main_reason = "Night time lighting essential"
        elif cloud > 80:
            main_reason = "Heavy cloud coverage requires illumination"
        elif precipitation > 0.5:
            main_reason = "Rainy conditions need enhanced visibility"
        elif visibility < 5:
            main_reason = "Poor visibility requires safety lighting"
        
        explanation = f"🔦 {main_reason}"
    else:
        reasons = []
        if 7 <= hour <= 18:
            reasons.append("daylight hours")
        if cloud < 50:
            reasons.append("clear weather conditions")
        if precipitation == 0:
            reasons.append("no precipitation")
        if visibility > 8:
            reasons.append("good visibility")
            
        if reasons:
            explanation = f"💡 Energy saving mode activated - " + ", ".join(reasons)
        else:
            explanation = "✅ Conditions allow energy optimization"
    
    return explanation, details

@app.route('/api/model-info')
def get_model_info():
    return jsonify(model_info)

@app.route('/api/features')
def get_features():
    return jsonify({'features': feature_columns})

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'model_loaded': model is not None,
        'accuracy': model_info.get('cv_accuracy_percentage', 99.2),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)

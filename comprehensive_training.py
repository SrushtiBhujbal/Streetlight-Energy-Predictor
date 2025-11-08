import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
import json

print("🚀 COMPREHENSIVE STREETLIGHT MODEL TRAINING")
print("=" * 50)

# Load dataset
df = pd.read_csv('/Users/srushtibhujbal/streetlight-energy-ai/data/final_processeddataset_streetlight_energy_data.csv')
print(f"✅ Dataset loaded: {df.shape}")

# Comprehensive data analysis
print(f"\n📊 DATA ANALYSIS:")
print(f"Total records: {len(df):,}")
print(f"Columns: {len(df.columns)}")

# Show column types and basic info
print(f"\n📋 COLUMN TYPES:")
print(df.dtypes.value_counts())

# Analyze all potential target variables
print(f"\n🎯 TARGET VARIABLE ANALYSIS:")
target_columns = ['should_light_be_on', 'optimal_lighting_adjusted', 'fault_type']
for col in target_columns:
    if col in df.columns:
        counts = df[col].value_counts()
        print(f"{col}: {counts.to_dict()}")

# Create SMART target based on comprehensive logic
def create_comprehensive_target(row):
    try:
        hour = row['hour']
        month = row.get('month', 6)
        cloud = row.get('cloud', 0)
        precipitation = row.get('precipitation_mm', 0)
        visibility = row.get('visibility_km', 10)
        
        # Season-based lighting hours
        if month in [12, 1, 2]:  # Winter - longer nights
            night_start, night_end = 17, 7
        elif month in [6, 7, 8]:  # Summer - shorter nights
            night_start, night_end = 21, 5
        else:  # Spring/Fall
            night_start, night_end = 19, 6
        
        # Base night time logic
        is_night_time = hour >= night_start or hour <= night_end
        
        # Weather conditions that require lighting
        poor_visibility = visibility < 8
        heavy_cloud = cloud > 85
        rainy = precipitation > 0.3
        
        # Decision logic
        if is_night_time:
            return 1  # Lights ON at night
        elif poor_visibility or heavy_cloud or rainy:
            return 1  # Lights ON due to poor conditions
        else:
            return 0  # Lights OFF to save energy
            
    except Exception as e:
        # Fallback to original logic
        hour = row.get('hour', 12)
        return 1 if hour >= 19 or hour <= 6 else 0

# Apply smart target
df['smart_lighting_target'] = df.apply(create_comprehensive_target, axis=1)

print(f"\n🎯 SMART TARGET DISTRIBUTION:")
lights_on = (df['smart_lighting_target'] == 1).sum()
lights_off = (df['smart_lighting_target'] == 0).sum()
print(f"Lights ON: {lights_on:,} ({lights_on/len(df)*100:.1f}%)")
print(f"Lights OFF: {lights_off:,} ({lights_off/len(df)*100:.1f}%)")

# Feature selection - comprehensive set
all_numeric_features = df.select_dtypes(include=[np.number]).columns.tolist()
# Remove targets and identifiers
exclude_features = ['smart_lighting_target', 'should_light_be_on', 'optimal_lighting_adjusted', 
                   'fault_type', 'bulb_number', 'latitude', 'longitude']

feature_columns = [col for col in all_numeric_features if col not in exclude_features]
target_column = 'smart_lighting_target'

print(f"\n📊 SELECTED {len(feature_columns)} FEATURES:")
for i, feature in enumerate(feature_columns[:15]):  # Show first 15 features
    print(f"  {i+1:2d}. {feature}")
if len(feature_columns) > 15:
    print(f"  ... and {len(feature_columns) - 15} more features")

# Prepare data
X = df[feature_columns]
y = df[target_column]

# Handle missing values
X = X.fillna(X.median())

print(f"\n🤖 MODEL TRAINING CONFIGURATION:")
print(f"Training samples: {len(X):,}")
print(f"Features: {len(feature_columns)}")
print(f"Target distribution: ON={y.sum():,}, OFF={(len(y)-y.sum()):,}")

# Use entire dataset for training (no test split for final model)
print(f"\n🎯 TRAINING ON COMPLETE DATASET...")
final_model = RandomForestClassifier(
    n_estimators=150,
    max_depth=20,
    min_samples_split=10,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1,
    class_weight='balanced'
)

# Train on complete dataset
final_model.fit(X, y)

# Cross-validation to estimate performance
print(f"📈 PERFORMANCE ESTIMATION (5-fold CV)...")
cv_scores = cross_val_score(final_model, X, y, cv=5, scoring='accuracy')
print(f"Cross-validation accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")

# Feature importance (text-based)
feature_importance = pd.DataFrame({
    'feature': feature_columns,
    'importance': final_model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n🔝 TOP 15 MOST IMPORTANT FEATURES:")
for i, row in feature_importance.head(15).iterrows():
    print(f"  {i+1:2d}. {row['feature']:25} {row['importance']:.4f}")

# Test scenarios
print(f"\n🧪 REAL-WORLD SCENARIO TESTING:")
test_scenarios = [
    # Sunny afternoon - should be OFF
    {'hour': 14, 'month': 6, 'power_consumption_watts': 150, 'voltage_volts': 220, 
     'current_amperes': 0.68, 'temperature_final': 25, 'humidity': 50, 'cloud': 20, 
     'wind_speed_kph': 10, 'precipitation_mm': 0.0, 'visibility_km': 15, 'is_night': 0, 
     'day_length_minutes': 840, 'weather_severity': 5, 'is_clear_sky': 1, 
     'natural_light_score': 0.8, 'weather_energy_factor': 1.0},
    
    # Stormy night - should be ON
    {'hour': 20, 'month': 12, 'power_consumption_watts': 150, 'voltage_volts': 220, 
     'current_amperes': 0.68, 'temperature_final': 15, 'humidity': 85, 'cloud': 95, 
     'wind_speed_kph': 25, 'precipitation_mm': 2.0, 'visibility_km': 3, 'is_night': 1, 
     'day_length_minutes': 540, 'weather_severity': 25, 'is_clear_sky': 0, 
     'natural_light_score': 0.1, 'weather_energy_factor': 1.3},
    
    # Cloudy morning - should be OFF (but might turn ON if very cloudy)
    {'hour': 10, 'month': 3, 'power_consumption_watts': 150, 'voltage_volts': 220, 
     'current_amperes': 0.68, 'temperature_final': 20, 'humidity': 70, 'cloud': 85, 
     'wind_speed_kph': 12, 'precipitation_mm': 0.5, 'visibility_km': 6, 'is_night': 0, 
     'day_length_minutes': 720, 'weather_severity': 15, 'is_clear_sky': 0, 
     'natural_light_score': 0.3, 'weather_energy_factor': 1.1}
]

scenario_descriptions = [
    "Sunny summer afternoon (2 PM, June)",
    "Stormy winter night (8 PM, December)", 
    "Cloudy spring morning (10 AM, March)"
]

for i, (scenario, desc) in enumerate(zip(test_scenarios, scenario_descriptions)):
    # Create input array in correct feature order
    input_data = [scenario.get(col, 0) for col in feature_columns]
    
    prediction = final_model.predict([input_data])[0]
    probability = final_model.predict_proba([input_data])[0]
    confidence = max(probability)
    
    print(f"\nScenario {i+1}: {desc}")
    print(f"  → AI Recommendation: Light {'ON' if prediction == 1 else 'OFF'}")
    print(f"  → Confidence: {confidence:.1%}")
    print(f"  → Logic: {'Safety lighting required' if prediction == 1 else 'Energy saving mode'}")
    if prediction == 0:
        print(f"  → 💰 Energy Savings: 150W per hour")

# Save the final model
os.makedirs('models', exist_ok=True)
joblib.dump(final_model, 'models/final_streetlight_model.pkl')
joblib.dump(feature_columns, 'models/final_feature_columns.pkl')
joblib.dump(target_column, 'models/target_column.pkl')

print(f"\n💾 MODEL SAVED SUCCESSFULLY!")
print(f"✅ Final model trained on {len(df):,} records")
print(f"✅ Using {len(feature_columns)} features")
print(f"✅ Estimated accuracy: {cv_scores.mean():.1%}")

# Create model info file
model_info = {
    'training_samples': len(df),
    'features_used': len(feature_columns),
    'feature_names': feature_columns,
    'target_distribution': {
        'lights_on': int(y.sum()),
        'lights_off': int(len(y) - y.sum())
    },
    'cv_accuracy': float(cv_scores.mean()),
    'cv_accuracy_percentage': float(cv_scores.mean() * 100),
    'top_features': feature_importance.head(10).to_dict('records')
}

with open('models/model_info.json', 'w') as f:
    json.dump(model_info, f, indent=2)

print(f"📁 Model info saved to models/model_info.json")
print(f"\n🎉 TRAINING COMPLETED! Ready to deploy professional application.")

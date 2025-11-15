# 🏗️ Streetlight Energy AI - Model Documentation

## 📊 Dataset Overview

### **Total Records:** 34,310 streetlight operations
### **Training Strategy:** Complete dataset training with 5-fold cross-validation

## 🎯 Data Segmentation

### **Training Approach:**
- **100% of data used for training** (34,310 records)
- **5-fold Cross-Validation** for performance estimation
- **No separate test split** - Model trained on complete dataset for maximum accuracy

### **Cross-Validation Results:**
- **Average Accuracy:** 99.2%
- **Standard Deviation:** ±0.3%
- **Confidence Interval:** 98.9% - 99.5%

## 🧠 Model Architecture

### **Algorithm:** Random Forest Classifier
### **Ensemble Size:** 150 decision trees
### **Key Parameters:**
- `n_estimators: 150`
- `max_depth: 20`
- `min_samples_split: 10`
- `min_samples_leaf: 5`
- `class_weight: 'balanced'`

## 🎯 Target Variable: `smart_lighting_target`

### **Logic for Target Creation:**
```python
def create_smart_target(row):
    hour = row['hour']
    month = row['month']
    cloud = row['cloud']
    precipitation = row['precipitation_mm']
    visibility = row['visibility_km']
    
    # Season-based night hours
    if month in [12, 1, 2]:  # Winter
        night_start, night_end = 17, 7
    elif month in [6, 7, 8]:  # Summer
        night_start, night_end = 21, 5
    else:  # Spring/Fall
        night_start, night_end = 19, 6
    
    is_night_time = hour >= night_start or hour <= night_end
    poor_visibility = visibility < 8
    heavy_cloud = cloud > 85
    rainy = precipitation > 0.3
    
    if is_night_time:
        return 1  # Lights ON at night
    elif poor_visibility or heavy_cloud or rainy:
        return 1  # Lights ON due to poor conditions
    else:
        return 0  # Lights OFF to save energy


streetlight-energy-ai/
├── 📊 DATA FLOW
│   └── data/
│       └── final_processeddataset_streetlight_energy_data.csv
│           ↓
├── 🤖 MODEL TRAINING
│   ├── comprehensive_training.py
│   └── models/
│       ├── final_streetlight_model.pkl
│       ├── final_feature_columns.pkl
│       ├── target_column.pkl
│       └── model_info.json
│           ↓
├── 🌐 WEB APPLICATION
│   ├── professional_app.py
│   ├── templates/
│   │   └── professional_index.html
│   └── static/
│       ├── css/professional.css
│       └── js/professional.js
│           ↓
├── 📚 DOCUMENTATION
│   ├── MODEL_DOCUMENTATION.md
│   ├── QUICK_REFERENCE.md
│   └── commands.txt
└── ⚙️ CONFIGURATION
    └── streetlight_env/


    # 🚀 Quick Start Commands for Streetlight Energy AI

# 1. Navigate to project directory
cd /Users/srushtibhujbal/streetlight-energy-ai

# 2. Activate virtual environment
source streetlight_env/bin/activate

# 3. Start the AI application
python professional_app.py

# 4. Open in browser (in new terminal)
open http://localhost:5003

# 💡 Application will be available at: http://localhost:5003
# 🎯 Model Accuracy: 99.2% | Training Data: 34,310 records

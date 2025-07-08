from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import json
import asyncio
from contextlib import asynccontextmanager

# Import our modules
import sys
sys.path.append('..')
from models.fault_detector import SolarFaultDetector
from data.data_preprocessor import DataPreprocessor
from data.synthetic_generator import SolarDataGenerator

# Global variables for models
fault_detector = None
preprocessor = None
generator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models on startup
    global fault_detector, preprocessor, generator
    
    print("Loading models...")
    fault_detector = SolarFaultDetector()
    preprocessor = DataPreprocessor()
    generator = SolarDataGenerator()
    
    # Try to load pre-trained models
    try:
        fault_detector.load_models("models/trained_fault_detector.pkl")
        print("Pre-trained models loaded successfully")
        
        # Generate some sample data to fit the preprocessor
        print("Fitting preprocessor...")
        sample_data = generator.generate_plant_data(num_days=30, num_inverters=5)
        df_features = preprocessor.create_features(sample_data)
        X, y = preprocessor.prepare_features(df_features)
        preprocessor.fit_transform(X, y)
        print("Preprocessor fitted successfully")
    except Exception as e:
        print(f"Error loading models or fitting preprocessor: {str(e)}")
        print("Training new models...")
        # Generate training data and train models
        await train_models()
    
    yield
    
    # Cleanup on shutdown
    print("Shutting down...")

app = FastAPI(
    title="Solar Fault Detection API",
    description="API for detecting faults in solar power plants",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SolarDataPoint(BaseModel):
    datetime: str
    plant_id: str
    inverter_id: str
    string_id: Optional[str] = None
    daily_energy_yield_ac: float
    daily_energy_yield_dc: float
    string_energy_yield_dc: Optional[float] = None
    capacity_utilization_factor_ac: float
    capacity_utilization_factor_dc: float
    performance_ratio_ac: float
    performance_ratio_dc: float
    daily_specific_yield_ac: float
    daily_specific_yield_dc: float
    irradiance: Optional[float] = None
    temperature: Optional[float] = None
    wind_speed: Optional[float] = None

class FaultDetectionRequest(BaseModel):
    data: List[SolarDataPoint]
    detection_type: str = "comprehensive"  # "rule_based", "ml_based", "comprehensive"

class FaultDetectionResponse(BaseModel):
    faults: List[Dict[str, Any]]
    total_faults: int
    summary: Dict[str, int]
    timestamp: str

# Helper function to train models
async def train_models():
    """Train models with synthetic data."""
    # Generate synthetic data
    print("Generating synthetic training data...")
    clean_data = generator.generate_plant_data(num_days=365, num_inverters=10)
    faulty_data = generator.inject_faults(clean_data)
    
    # Preprocess data
    print("Preprocessing data...")
    df_features = preprocessor.create_features(faulty_data)
    X, y = preprocessor.prepare_features(df_features)
    X_scaled, y_encoded = preprocessor.fit_transform(X, y)
    
    # Train models
    print("Training fault detection models...")
    results = fault_detector.train_ml_models(
        X_scaled, y_encoded, 
        preprocessor.get_feature_names(), 
        preprocessor.get_fault_types()
    )
    
    # Save models
    fault_detector.save_models("models/trained_fault_detector.pkl")
    print("Models trained and saved successfully")
    
    return results

@app.get("/")
async def root():
    return {"message": "Solar Fault Detection API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models_loaded": fault_detector.is_trained if fault_detector else False,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/detect-faults", response_model=FaultDetectionResponse)
async def detect_faults(request: FaultDetectionRequest):
    """
    Detect faults in solar plant data.
    """
    try:
        # Convert request data to DataFrame
        data_dicts = [item.dict() for item in request.data]
        df = pd.DataFrame(data_dicts)
        
        # Convert datetime strings to datetime objects
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Prepare features if ML detection is requested
        X_scaled = None
        if request.detection_type in ["ml_based", "comprehensive"]:
            df_features = preprocessor.create_features(df)
            X, _ = preprocessor.prepare_features(df_features)
            X_scaled, _ = preprocessor.transform(X)
        
        # Detect faults
        if request.detection_type == "rule_based":
            faults = fault_detector.detect_rule_based_faults(df)
        elif request.detection_type == "ml_based":
            faults = fault_detector.detect_ml_faults(X_scaled, df)
        else:  # comprehensive
            faults = fault_detector.comprehensive_fault_detection(df, X_scaled)
        
        # Create summary
        summary = {}
        for fault in faults:
            fault_type = fault['fault_type']
            summary[fault_type] = summary.get(fault_type, 0) + 1
        
        return FaultDetectionResponse(
            faults=faults,
            total_faults=len(faults),
            summary=summary,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting faults: {str(e)}")

@app.post("/generate-sample-data")
async def generate_sample_data(
    num_days: int = 30,
    num_inverters: int = 5,
    include_faults: bool = True
):
    """
    Generate sample solar plant data for testing.
    """
    try:
        # Generate data
        clean_data = generator.generate_plant_data(num_days=num_days, num_inverters=num_inverters)
        
        if include_faults:
            data = generator.inject_faults(clean_data)
        else:
            data = clean_data
            data['fault_type'] = 'normal'
        
        # Convert to list of dictionaries
        data_list = data.to_dict('records')
        
        # Convert datetime objects to strings
        for record in data_list:
            record['datetime'] = record['datetime'].isoformat()
        
        return {
            "data": data_list,
            "shape": data.shape,
            "fault_distribution": data['fault_type'].value_counts().to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sample data: {str(e)}")

@app.post("/retrain-models")
async def retrain_models(background_tasks: BackgroundTasks):
    """
    Retrain models with new data (background task).
    """
    background_tasks.add_task(train_models)
    return {"message": "Model retraining started in background"}

@app.get("/model-info")
async def get_model_info():
    """
    Get information about the loaded models.
    """
    if not fault_detector or not fault_detector.is_trained:
        raise HTTPException(status_code=404, detail="Models not loaded")
    
    return {
        "is_trained": fault_detector.is_trained,
        "feature_names": fault_detector.feature_names,
        "fault_types": fault_detector.fault_types,
        "config": fault_detector.config
    }

@app.get("/fault-statistics")
async def get_fault_statistics():
    """
    Get statistics about fault detection capabilities.
    """
    return {
        "supported_fault_types": [
            "disconnected_string",
            "inverter_shutdown", 
            "performance_degradation",
            "soiling",
            "grid_curtailment"
        ],
        "detection_methods": [
            "rule_based",
            "ml_based", 
            "comprehensive"
        ],
        "severity_levels": ["low", "medium", "high", "critical"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
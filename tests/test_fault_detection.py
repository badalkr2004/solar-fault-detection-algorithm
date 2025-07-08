import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.synthetic_generator import SolarDataGenerator
from data.data_preprocessor import DataPreprocessor
from models.fault_detector import SolarFaultDetector

class TestSolarFaultDetection:
    @pytest.fixture
    def generator(self):
        return SolarDataGenerator(seed=42)
    
    @pytest.fixture
    def preprocessor(self):
        return DataPreprocessor()
    
    @pytest.fixture
    def fault_detector(self):
        return SolarFaultDetector()
    
    @pytest.fixture
    def sample_data(self, generator):
        # Generate clean data
        clean_data = generator.generate_plant_data(num_days=30, num_inverters=3)
        # Inject faults
        faulty_data = generator.inject_faults(clean_data)
        return faulty_data
    
    def test_data_generation(self, generator):
        """Test synthetic data generation."""
        df = generator.generate_plant_data(num_days=10, num_inverters=2)
        
        assert len(df) == 10 * 2 * 8  # days * inverters * strings
        assert 'datetime' in df.columns
        assert 'inverter_id' in df.columns
        assert 'daily_energy_yield_ac' in df.columns
        assert df['daily_energy_yield_ac'].notna().all()
        
    def test_fault_injection(self, generator):
        """Test fault injection."""
        clean_data = generator.generate_plant_data(num_days=10, num_inverters=2)
        faulty_data = generator.inject_faults(clean_data)
        
        fault_counts = faulty_data['fault_type'].value_counts()
        assert 'normal' in fault_counts.index
        assert len(fault_counts) > 1  # Should have some faults
        
    def test_feature_engineering(self, preprocessor, sample_data):
        """Test feature engineering."""
        df_features = preprocessor.create_features(sample_data)
        
        # Check if new features are created
        assert 'ac_dc_energy_ratio' in df_features.columns
        assert 'ac_dc_cuf_ratio' in df_features.columns
        assert 'day_of_year' in df_features.columns
        assert 'irradiance_to_energy_ratio' in df_features.columns
        
    def test_data_preprocessing(self, preprocessor, sample_data):
        """Test data preprocessing."""
        df_features = preprocessor.create_features(sample_data)
        X, y = preprocessor.prepare_features(df_features)
        X_scaled, y_encoded = preprocessor.fit_transform(X, y)
        
        assert X_scaled.shape[0] == len(sample_data)
        assert X_scaled.shape[1] > 0
        assert y_encoded is not None
        assert len(y_encoded) == len(sample_data)
        
    def test_rule_based_detection(self, fault_detector, sample_data):
        """Test rule-based fault detection."""
        faults = fault_detector.detect_rule_based_faults(sample_data)
        
        assert isinstance(faults, list)
        
        # Check fault structure
        if len(faults) > 0:
            fault = faults[0]
            required_keys = ['fault_type', 'severity', 'timestamp', 'confidence', 'detected_by']
            for key in required_keys:
                assert key in fault
            assert fault['detected_by'] == 'rule_based'
            
    def test_ml_model_training(self, fault_detector, preprocessor, sample_data):
        """Test ML model training."""
        df_features = preprocessor.create_features(sample_data)
        X, y = preprocessor.prepare_features(df_features)
        X_scaled, y_encoded = preprocessor.fit_transform(X, y)
        
        results = fault_detector.train_ml_models(
            X_scaled, y_encoded,
            preprocessor.get_feature_names(),
            preprocessor.get_fault_types()
        )
        
        assert fault_detector.is_trained
        assert 'isolation_forest' in results
        assert 'random_forest' in results
        assert 'accuracy' in results['isolation_forest']
        assert 'accuracy' in results['random_forest']
        
    def test_ml_fault_detection(self, fault_detector, preprocessor, sample_data):
        """Test ML-based fault detection."""
        # First train the model
        df_features = preprocessor.create_features(sample_data)
        X, y = preprocessor.prepare_features(df_features)
        X_scaled, y_encoded = preprocessor.fit_transform(X, y)
        
        fault_detector.train_ml_models(
            X_scaled, y_encoded,
            preprocessor.get_feature_names(),
            preprocessor.get_fault_types()
        )
        
        # Then test detection
        faults = fault_detector.detect_ml_faults(X_scaled, sample_data)
        
        assert isinstance(faults, list)
        
        # Check fault structure
        if len(faults) > 0:
            fault = faults[0]
            required_keys = ['fault_type', 'severity', 'timestamp', 'confidence', 'detected_by']
            for key in required_keys:
                assert key in fault
            assert fault['detected_by'] == 'ml_model'
            
    def test_comprehensive_detection(self, fault_detector, preprocessor, sample_data):
        """Test comprehensive fault detection."""
        # Prepare data
        df_features = preprocessor.create_features(sample_data)
        X, y = preprocessor.prepare_features(df_features)
        X_scaled, y_encoded = preprocessor.fit_transform(X, y)
        
        # Train models
        fault_detector.train_ml_models(
            X_scaled, y_encoded,
            preprocessor.get_feature_names(),
            preprocessor.get_fault_types()
        )
        
        # Test comprehensive detection
        faults = fault_detector.comprehensive_fault_detection(sample_data, X_scaled)
        
        assert isinstance(faults, list)
        
        # Check if both detection methods are represented
        detection_methods = set(fault['detected_by'] for fault in faults)
        assert len(detection_methods) >= 1  # At least one method should detect faults
        
    def test_model_persistence(self, fault_detector, preprocessor, sample_data, tmp_path):
        """Test model saving and loading."""
        # Train model
        df_features = preprocessor.create_features(sample_data)
        X, y = preprocessor.prepare_features(df_features)
        X_scaled, y_encoded = preprocessor.fit_transform(X, y)
        
        fault_detector.train_ml_models(
            X_scaled, y_encoded,
            preprocessor.get_feature_names(),
            preprocessor.get_fault_types()
        )
        
        # Save model
        model_path = tmp_path / "test_model.pkl"
        fault_detector.save_models(str(model_path))
        
        # Create new detector and load model
        new_detector = SolarFaultDetector()
        new_detector.load_models(str(model_path))
        
        assert new_detector.is_trained
        assert new_detector.feature_names == fault_detector.feature_names
        assert new_detector.fault_types == fault_detector.fault_types
        
    def test_edge_cases(self, fault_detector, preprocessor):
        """Test edge cases."""
        # Test with minimal data
        minimal_data = pd.DataFrame({
            'datetime': [datetime.now()],
            'plant_id': ['TEST'],
            'inverter_id': ['INV_001'],
            'string_id': ['STR_001_01'],
            'daily_energy_yield_ac': [0.0],
            'daily_energy_yield_dc': [0.0],
            'string_energy_yield_dc': [0.0],
            'capacity_utilization_factor_ac': [0.0],
            'capacity_utilization_factor_dc': [0.0],
            'performance_ratio_ac': [0.0],
            'performance_ratio_dc': [0.0],
            'daily_specific_yield_ac': [0.0],
            'daily_specific_yield_dc': [0.0],
            'irradiance': [0.0],
            'temperature': [25.0],
            'wind_speed': [0.0]
        })
        
        # This should detect shutdowns
        faults = fault_detector.detect_rule_based_faults(minimal_data)
        assert len(faults) > 0
        assert any(fault['fault_type'] == 'inverter_shutdown' for fault in faults)

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
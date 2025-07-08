import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.cluster import DBSCAN
import joblib
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

class SolarFaultDetector:
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the fault detector with configuration.
        
        Args:
            config: Configuration dictionary for model parameters
        """
        self.config = config or self._default_config()
        
        # Initialize models
        self.isolation_forest = IsolationForest(
            contamination=self.config['isolation_forest']['contamination'],
            random_state=self.config['random_state']
        )
        
        self.random_forest = RandomForestClassifier(
            n_estimators=self.config['random_forest']['n_estimators'],
            max_depth=self.config['random_forest']['max_depth'],
            random_state=self.config['random_state']
        )
        
        self.dbscan = DBSCAN(
            eps=self.config['dbscan']['eps'],
            min_samples=self.config['dbscan']['min_samples']
        )
        
        # Model states
        self.is_trained = False
        self.feature_names = []
        self.fault_types = []
        
        # Rule-based thresholds
        self.thresholds = self.config['thresholds']
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for the fault detector."""
        return {
            'isolation_forest': {
                'contamination': 0.1
            },
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 10
            },
            'dbscan': {
                'eps': 0.5,
                'min_samples': 5
            },
            'thresholds': {
                'disconnected_string': {
                    'energy_yield_dc': 0.3,  # 30% of normal
                    'z_score': 2.5
                },
                'inverter_shutdown': {
                    'energy_yield_ac': 0.1,
                    'energy_yield_dc': 0.1
                },
                'performance_degradation': {
                    'pr_drop': 0.15,  # 15% drop
                    'cuf_drop': 0.15
                },
                'soiling': {
                    'specific_yield_drop': 0.1,  # 10% drop
                    'irradiance_ratio': 0.8
                }
            },
            'random_state': 42
        }
    
    def detect_rule_based_faults(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect faults using rule-based approach.
        
        Args:
            df: DataFrame with solar plant data
            
        Returns:
            List of detected faults
        """
        faults = []
        
        # 1. Disconnected Strings
        faults.extend(self._detect_disconnected_strings(df))
        
        # 2. Inverter Shutdowns
        faults.extend(self._detect_inverter_shutdowns(df))
        
        # 3. Performance Degradation
        faults.extend(self._detect_performance_degradation(df))
        
        # 4. Soiling Effects
        faults.extend(self._detect_soiling(df))
        
        return faults
    
    def _detect_disconnected_strings(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect disconnected strings using energy yield analysis."""
        faults = []
        
        for inverter_id in df['inverter_id'].unique():
            inv_data = df[df['inverter_id'] == inverter_id]
            
            if len(inv_data) < 2:
                continue
                
            # Calculate statistics for string energy
            if 'string_energy_yield_dc' in inv_data.columns:
                mean_energy = inv_data['string_energy_yield_dc'].mean()
                std_energy = inv_data['string_energy_yield_dc'].std()
                
                # Find strings with significantly low energy
                threshold = mean_energy * self.thresholds['disconnected_string']['energy_yield_dc']
                
                low_energy_strings = inv_data[
                    (inv_data['string_energy_yield_dc'] < threshold) & 
                    (inv_data['string_energy_yield_dc'] > 0)
                ]
                
                for idx, row in low_energy_strings.iterrows():
                    faults.append({
                        'fault_type': 'disconnected_string',
                        'inverter_id': inverter_id,
                        'string_id': row.get('string_id', 'unknown'),
                        'severity': 'high',
                        'timestamp': row['datetime'],
                        'confidence': 0.8,
                        'description': f"String energy {row['string_energy_yield_dc']:.2f} below threshold {threshold:.2f}",
                        'detected_by': 'rule_based'
                    })
        
        return faults
    
    def _detect_inverter_shutdowns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect inverter shutdowns."""
        faults = []
        
        shutdown_mask = (
            (df['daily_energy_yield_ac'] < self.thresholds['inverter_shutdown']['energy_yield_ac']) &
            (df['daily_energy_yield_dc'] < self.thresholds['inverter_shutdown']['energy_yield_dc'])
        )
        
        shutdowns = df[shutdown_mask]
        
        for idx, row in shutdowns.iterrows():
            faults.append({
                'fault_type': 'inverter_shutdown',
                'inverter_id': row['inverter_id'],
                'severity': 'critical',
                'timestamp': row['datetime'],
                'confidence': 0.9,
                'description': f"Inverter showing zero/minimal power output",
                'detected_by': 'rule_based'
            })
        
        return faults
    
    def _detect_performance_degradation(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect performance degradation."""
        faults = []
        
        # Group by inverter and calculate rolling averages
        df_sorted = df.sort_values(['inverter_id', 'datetime'])
        
        for inverter_id in df['inverter_id'].unique():
            inv_data = df_sorted[df_sorted['inverter_id'] == inverter_id]
            
            if len(inv_data) < 14:  # Need at least 2 weeks
                continue
            
            # Calculate baseline (first 7 days) vs recent (last 7 days)
            baseline_pr = inv_data['performance_ratio_ac'].head(7).mean()
            recent_pr = inv_data['performance_ratio_ac'].tail(7).mean()
            
            if baseline_pr > 0 and recent_pr < baseline_pr * (1 - self.thresholds['performance_degradation']['pr_drop']):
                faults.append({
                    'fault_type': 'performance_degradation',
                    'inverter_id': inverter_id,
                    'severity': 'medium',
                    'timestamp': inv_data['datetime'].iloc[-1],
                    'confidence': 0.7,
                    'description': f"PR dropped from {baseline_pr:.2f} to {recent_pr:.2f}",
                    'detected_by': 'rule_based'
                })
        
        return faults
    
    def _detect_soiling(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect soiling effects."""
        faults = []
        
        # Group by plant and analyze specific yield trends
        for plant_id in df['plant_id'].unique():
            plant_data = df[df['plant_id'] == plant_id].sort_values('datetime')
            
            if len(plant_data) < 14:
                continue
            
            # Calculate baseline vs recent specific yield
            baseline_sy = plant_data['daily_specific_yield_ac'].head(7).mean()
            recent_sy = plant_data['daily_specific_yield_ac'].tail(7).mean()
            
            if baseline_sy > 0 and recent_sy < baseline_sy * (1 - self.thresholds['soiling']['specific_yield_drop']):
                faults.append({
                    'fault_type': 'soiling',
                    'plant_id': plant_id,
                    'severity': 'medium',
                    'timestamp': plant_data['datetime'].iloc[-1],
                    'confidence': 0.6,
                    'description': f"Specific yield declined from {baseline_sy:.2f} to {recent_sy:.2f}",
                    'detected_by': 'rule_based'
                })
        
        return faults
    
    def train_ml_models(self, X: np.ndarray, y: np.ndarray, feature_names: List[str], fault_types: List[str]) -> Dict[str, Any]:
        """
        Train machine learning models for fault detection.
        
        Args:
            X: Feature matrix
            y: Target vector
            feature_names: List of feature names
            fault_types: List of fault types
            
        Returns:
            Training results dictionary
        """
        self.feature_names = feature_names
        self.fault_types = fault_types
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.config['random_state'], stratify=y
        )
        
        results = {}
        
        # Train Isolation Forest (unsupervised)
        print("Training Isolation Forest...")
        self.isolation_forest.fit(X_train)
        
        # Train Random Forest (supervised)
        print("Training Random Forest...")
        self.random_forest.fit(X_train, y_train)
        
        # Evaluate models
        results['isolation_forest'] = self._evaluate_isolation_forest(X_test, y_test)
        results['random_forest'] = self._evaluate_random_forest(X_test, y_test)
        
        self.is_trained = True
        
        return results
    
    def _evaluate_isolation_forest(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Evaluate Isolation Forest model."""
        # Predict anomalies
        anomaly_scores = self.isolation_forest.decision_function(X_test)
        predictions = self.isolation_forest.predict(X_test)
        
        # Convert to binary classification (normal vs anomaly)
        y_test_binary = (y_test != 0).astype(int)  # Assuming 0 is normal
        predictions_binary = (predictions == -1).astype(int)
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        return {
            'accuracy': accuracy_score(y_test_binary, predictions_binary),
            'precision': precision_score(y_test_binary, predictions_binary, zero_division=0),
            'recall': recall_score(y_test_binary, predictions_binary, zero_division=0),
            'f1_score': f1_score(y_test_binary, predictions_binary, zero_division=0)
        }
    
    def _evaluate_random_forest(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Evaluate Random Forest model."""
        # Predict
        predictions = self.random_forest.predict(X_test)
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        return {
            'accuracy': accuracy_score(y_test, predictions),
            'precision': precision_score(y_test, predictions, average='weighted', zero_division=0),
            'recall': recall_score(y_test, predictions, average='weighted', zero_division=0),
            'f1_score': f1_score(y_test, predictions, average='weighted', zero_division=0),
            'classification_report': classification_report(y_test, predictions, target_names=self.fault_types)
        }
    
    def detect_ml_faults(self, X: np.ndarray, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect faults using trained ML models.
        
        Args:
            X: Feature matrix
            df: Original DataFrame for context
            
        Returns:
            List of detected faults
        """
        if not self.is_trained:
            raise ValueError("Models not trained. Call train_ml_models first.")
        
        faults = []
        
        # Isolation Forest predictions
        anomaly_scores = self.isolation_forest.decision_function(X)
        anomaly_predictions = self.isolation_forest.predict(X)
        
        # Random Forest predictions
        rf_predictions = self.random_forest.predict(X)
        rf_probabilities = self.random_forest.predict_proba(X)
        
        # Combine predictions
        for i, (anomaly_score, anomaly_pred, rf_pred, rf_prob) in enumerate(zip(
            anomaly_scores, anomaly_predictions, rf_predictions, rf_probabilities
        )):
            if anomaly_pred == -1 or rf_pred != 0:  # Anomaly detected
                fault_type = self.fault_types[rf_pred] if rf_pred != 0 else 'unknown_anomaly'
                confidence = max(rf_prob) if rf_pred != 0 else abs(anomaly_score)
                
                faults.append({
                    'fault_type': fault_type,
                    'inverter_id': df.iloc[i]['inverter_id'],
                    'plant_id': df.iloc[i]['plant_id'],
                    'severity': self._get_severity(fault_type, confidence),
                    'timestamp': df.iloc[i]['datetime'],
                    'confidence': float(confidence),
                    'anomaly_score': float(anomaly_score),
                    'description': f"ML detected {fault_type} with confidence {confidence:.2f}",
                    'detected_by': 'ml_model'
                })
        
        return faults
    
    def _get_severity(self, fault_type: str, confidence: float) -> str:
        """Determine fault severity based on type and confidence."""
        if fault_type in ['inverter_shutdown', 'grid_curtailment']:
            return 'critical'
        elif fault_type in ['disconnected_string', 'performance_degradation']:
            return 'high' if confidence > 0.8 else 'medium'
        else:
            return 'medium' if confidence > 0.7 else 'low'
    
    def save_models(self, filepath: str):
        """Save trained models to file."""
        if not self.is_trained:
            raise ValueError("Models not trained. Cannot save.")
        
        model_data = {
            'isolation_forest': self.isolation_forest,
            'random_forest': self.random_forest,
            'feature_names': self.feature_names,
            'fault_types': self.fault_types,
            'config': self.config
        }
        
        joblib.dump(model_data, filepath)
        print(f"Models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load trained models from file."""
        model_data = joblib.load(filepath)
        
        self.isolation_forest = model_data['isolation_forest']
        self.random_forest = model_data['random_forest']
        self.feature_names = model_data['feature_names']
        self.fault_types = model_data['fault_types']
        self.config = model_data['config']
        self.is_trained = True
        
        print(f"Models loaded from {filepath}")
    
    def comprehensive_fault_detection(self, df: pd.DataFrame, X: np.ndarray = None) -> List[Dict[str, Any]]:
        """
        Run comprehensive fault detection using both rule-based and ML approaches.
        
        Args:
            df: Solar plant DataFrame
            X: Feature matrix (optional, for ML detection)
            
        Returns:
            List of all detected faults
        """
        all_faults = []
        
        # Rule-based detection
        print("Running rule-based fault detection...")
        rule_faults = self.detect_rule_based_faults(df)
        all_faults.extend(rule_faults)
        
        # ML-based detection
        if X is not None and self.is_trained:
            print("Running ML-based fault detection...")
            ml_faults = self.detect_ml_faults(X, df)
            all_faults.extend(ml_faults)
        
        # Remove duplicates and rank by severity
        all_faults = self._deduplicate_faults(all_faults)
        all_faults = sorted(all_faults, key=lambda x: (x['severity'], -x['confidence']))
        
        return all_faults
    
    def _deduplicate_faults(self, faults: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate faults based on type, inverter, and timestamp."""
        seen = set()
        unique_faults = []
        
        for fault in faults:
            key = (
                fault['fault_type'],
                fault.get('inverter_id', ''),
                fault.get('plant_id', ''),
                fault['timestamp']
            )
            
            if key not in seen:
                seen.add(key)
                unique_faults.append(fault)
        
        return unique_faults

# Usage example
if __name__ == "__main__":
    # This would be run as part of the training pipeline
    pass
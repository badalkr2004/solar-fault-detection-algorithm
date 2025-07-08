import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from typing import Tuple, Dict, Any
import warnings
warnings.filterwarnings('ignore')

class DataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.imputer = SimpleImputer(strategy='mean')
        self.feature_columns = []
        self.is_fitted = False
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create engineered features for fault detection.
        
        Args:
            df: Raw solar plant data
            
        Returns:
            DataFrame with engineered features
        """
        df_features = df.copy()
        
        # 1. Ratio features
        df_features['ac_dc_energy_ratio'] = df_features['daily_energy_yield_ac'] / (df_features['daily_energy_yield_dc'] + 1e-6)
        df_features['ac_dc_cuf_ratio'] = df_features['capacity_utilization_factor_ac'] / (df_features['capacity_utilization_factor_dc'] + 1e-6)
        df_features['ac_dc_pr_ratio'] = df_features['performance_ratio_ac'] / (df_features['performance_ratio_dc'] + 1e-6)
        
        # 2. Rolling statistics (7-day window)
        df_features = df_features.sort_values(['inverter_id', 'datetime'])
        
        rolling_cols = ['daily_energy_yield_ac', 'daily_energy_yield_dc', 'performance_ratio_ac', 'performance_ratio_dc']
        for col in rolling_cols:
            df_features[f'{col}_rolling_mean'] = df_features.groupby('inverter_id')[col].transform(
                lambda x: x.rolling(window=7, min_periods=1).mean()
            )
            df_features[f'{col}_rolling_std'] = df_features.groupby('inverter_id')[col].transform(
                lambda x: x.rolling(window=7, min_periods=1).std()
            )
        
        # 3. Deviation from group mean
        group_means = df_features.groupby(['datetime'])[rolling_cols].transform('mean')
        for col in rolling_cols:
            df_features[f'{col}_deviation'] = df_features[col] - group_means[col]
        
        # 4. Time-based features
        df_features['day_of_year'] = pd.to_datetime(df_features['datetime']).dt.dayofyear
        df_features['month'] = pd.to_datetime(df_features['datetime']).dt.month
        df_features['season'] = df_features['month'].apply(lambda x: (x % 12 + 3) // 3)
        
        # 5. Weather-based features
        df_features['irradiance_to_energy_ratio'] = df_features['daily_energy_yield_ac'] / (df_features['irradiance'] + 1e-6)
        df_features['temperature_normalized'] = (df_features['temperature'] - 25) / 25  # Normalize around 25°C
        
        return df_features
    
    def prepare_features(self, df: pd.DataFrame, target_col: str = 'fault_type') -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for machine learning models.
        
        Args:
            df: DataFrame with engineered features
            target_col: Target column name
            
        Returns:
            Tuple of (features_df, target_series)
        """
        # Select feature columns
        feature_cols = [
            'daily_energy_yield_ac', 'daily_energy_yield_dc', 'string_energy_yield_dc',
            'capacity_utilization_factor_ac', 'capacity_utilization_factor_dc',
            'performance_ratio_ac', 'performance_ratio_dc',
            'daily_specific_yield_ac', 'daily_specific_yield_dc',
            'irradiance', 'temperature', 'wind_speed',
            'ac_dc_energy_ratio', 'ac_dc_cuf_ratio', 'ac_dc_pr_ratio',
            'irradiance_to_energy_ratio', 'temperature_normalized',
            'day_of_year', 'month', 'season'
        ]
        
        # Add rolling statistics
        rolling_cols = ['daily_energy_yield_ac', 'daily_energy_yield_dc', 'performance_ratio_ac', 'performance_ratio_dc']
        for col in rolling_cols:
            feature_cols.extend([f'{col}_rolling_mean', f'{col}_rolling_std', f'{col}_deviation'])
        
        # Filter existing columns
        feature_cols = [col for col in feature_cols if col in df.columns]
        self.feature_columns = feature_cols
        
        X = df[feature_cols].copy()
        y = df[target_col].copy() if target_col in df.columns else None
        
        return X, y
    
    def fit_transform(self, X: pd.DataFrame, y: pd.Series = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fit preprocessor and transform data.
        
        Args:
            X: Features DataFrame
            y: Target Series (optional)
            
        Returns:
            Tuple of (transformed_X, transformed_y)
        """
        # Handle missing values
        X_imputed = pd.DataFrame(
            self.imputer.fit_transform(X),
            columns=X.columns,
            index=X.index
        )
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_imputed)
        
        # Encode target if provided
        y_encoded = None
        if y is not None:
            y_encoded = self.label_encoder.fit_transform(y)
        
        self.is_fitted = True
        
        return X_scaled, y_encoded
    
    def transform(self, X: pd.DataFrame, y: pd.Series = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transform new data using fitted preprocessor.
        
        Args:
            X: Features DataFrame
            y: Target Series (optional)
            
        Returns:
            Tuple of (transformed_X, transformed_y)
        """
        if not self.is_fitted:
            raise ValueError("Preprocessor not fitted. Call fit_transform first.")
        
        # Handle missing values
        X_imputed = pd.DataFrame(
            self.imputer.transform(X),
            columns=X.columns,
            index=X.index
        )
        
        # Scale features
        X_scaled = self.scaler.transform(X_imputed)
        
        # Encode target if provided
        y_encoded = None
        if y is not None:
            y_encoded = self.label_encoder.transform(y)
        
        return X_scaled, y_encoded
    
    def get_feature_names(self) -> list:
        """Get list of feature names."""
        return self.feature_columns
    
    def get_fault_types(self) -> list:
        """Get list of fault types."""
        if hasattr(self.label_encoder, 'classes_'):
            return self.label_encoder.classes_.tolist()
        return []

# Usage example
if __name__ == "__main__":
    # Load data
    df = pd.read_csv("solar_plant_data.csv")
    
    # Initialize preprocessor
    preprocessor = DataPreprocessor()
    
    # Create features
    df_features = preprocessor.create_features(df)
    
    # Prepare features
    X, y = preprocessor.prepare_features(df_features)
    
    # Fit and transform
    X_scaled, y_encoded = preprocessor.fit_transform(X, y)
    
    print(f"Feature shape: {X_scaled.shape}")
    print(f"Target shape: {y_encoded.shape}")
    print(f"Feature names: {preprocessor.get_feature_names()}")
    print(f"Fault types: {preprocessor.get_fault_types()}")
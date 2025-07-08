import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class SolarDataGenerator:
    def __init__(self, seed=42):
        """Initialize the solar data generator with a seed for reproducibility."""
        np.random.seed(seed)
        random.seed(seed)
        
    def generate_plant_data(self, 
                           num_days: int = 365,
                           num_inverters: int = 10,
                           num_strings_per_inverter: int = 8,
                           start_date: datetime = None) -> pd.DataFrame:
        """
        Generate synthetic solar plant data with realistic patterns.
        
        Args:
            num_days: Number of days to generate data for
            num_inverters: Number of inverters in the plant
            num_strings_per_inverter: Number of strings per inverter
            start_date: Start date for data generation
            
        Returns:
            DataFrame with synthetic solar plant data
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=num_days)
            
        data = []
        
        for day in range(num_days):
            current_date = start_date + timedelta(days=day)
            
            # Simulate seasonal variations
            day_of_year = current_date.timetuple().tm_yday
            seasonal_factor = 0.8 + 0.4 * np.sin(2 * np.pi * day_of_year / 365)
            
            # Weather factor (random daily variation)
            weather_factor = np.random.uniform(0.7, 1.0)
            
            for inverter_id in range(1, num_inverters + 1):
                # Base performance with some inverter-specific variation
                inverter_efficiency = np.random.uniform(0.95, 1.05)
                
                # Generate inverter-level data
                base_energy_dc = 100 * seasonal_factor * weather_factor * inverter_efficiency
                base_energy_ac = base_energy_dc * np.random.uniform(0.92, 0.96)  # Inverter losses
                
                # Add some realistic noise
                daily_energy_yield_dc = max(0, base_energy_dc + np.random.normal(0, 5))
                daily_energy_yield_ac = max(0, base_energy_ac + np.random.normal(0, 3))
                
                # Calculate derived metrics
                capacity_utilization_factor_dc = (daily_energy_yield_dc / 120) * 100  # Assuming 120 kWh max
                capacity_utilization_factor_ac = (daily_energy_yield_ac / 120) * 100
                
                performance_ratio_dc = capacity_utilization_factor_dc * np.random.uniform(0.8, 0.9)
                performance_ratio_ac = capacity_utilization_factor_ac * np.random.uniform(0.8, 0.9)
                
                daily_specific_yield_dc = daily_energy_yield_dc / 50  # Assuming 50 kWp capacity
                daily_specific_yield_ac = daily_energy_yield_ac / 50
                
                # Generate string-level data
                for string_id in range(1, num_strings_per_inverter + 1):
                    string_energy_dc = daily_energy_yield_dc / num_strings_per_inverter
                    string_energy_dc += np.random.normal(0, 2)  # String variation
                    string_energy_dc = max(0, string_energy_dc)
                    
                    data.append({
                        'datetime': current_date,
                        'plant_id': 'PLANT_001',
                        'inverter_id': f'INV_{inverter_id:03d}',
                        'string_id': f'STR_{inverter_id:03d}_{string_id:02d}',
                        'daily_energy_yield_ac': round(daily_energy_yield_ac, 2),
                        'daily_energy_yield_dc': round(daily_energy_yield_dc, 2),
                        'string_energy_yield_dc': round(string_energy_dc, 2),
                        'capacity_utilization_factor_ac': round(capacity_utilization_factor_ac, 2),
                        'capacity_utilization_factor_dc': round(capacity_utilization_factor_dc, 2),
                        'performance_ratio_ac': round(performance_ratio_ac, 2),
                        'performance_ratio_dc': round(performance_ratio_dc, 2),
                        'daily_specific_yield_ac': round(daily_specific_yield_ac, 2),
                        'daily_specific_yield_dc': round(daily_specific_yield_dc, 2),
                        'irradiance': round(np.random.uniform(3, 7) * seasonal_factor, 2),
                        'temperature': round(25 + np.random.normal(0, 10), 1),
                        'wind_speed': round(np.random.exponential(3), 1)
                    })
        
        return pd.DataFrame(data)
    
    def inject_faults(self, df: pd.DataFrame, fault_probability: float = 0.1) -> pd.DataFrame:
        """
        Inject various types of faults into the dataset.
        
        Args:
            df: Clean dataset
            fault_probability: Probability of fault occurrence
            
        Returns:
            DataFrame with injected faults
        """
        df_faulty = df.copy()
        
        # 1. Disconnected Strings (5% probability)
        disconnected_mask = np.random.random(len(df_faulty)) < 0.05
        df_faulty.loc[disconnected_mask, 'string_energy_yield_dc'] = 0
        df_faulty.loc[disconnected_mask, 'fault_type'] = 'disconnected_string'
        
        # 2. Inverter Shutdowns (2% probability)
        shutdown_mask = np.random.random(len(df_faulty)) < 0.02
        df_faulty.loc[shutdown_mask, ['daily_energy_yield_ac', 'daily_energy_yield_dc']] = 0
        df_faulty.loc[shutdown_mask, 'fault_type'] = 'inverter_shutdown'
        
        # 3. Performance Degradation (8% probability)
        degradation_mask = np.random.random(len(df_faulty)) < 0.08
        degradation_factor = np.random.uniform(0.6, 0.8, sum(degradation_mask))
        df_faulty.loc[degradation_mask, 'performance_ratio_ac'] *= degradation_factor
        df_faulty.loc[degradation_mask, 'performance_ratio_dc'] *= degradation_factor
        df_faulty.loc[degradation_mask, 'fault_type'] = 'performance_degradation'
        
        # 4. Soiling Effects (10% probability)
        soiling_mask = np.random.random(len(df_faulty)) < 0.10
        soiling_factor = np.random.uniform(0.7, 0.9, sum(soiling_mask))
        df_faulty.loc[soiling_mask, 'daily_specific_yield_ac'] *= soiling_factor
        df_faulty.loc[soiling_mask, 'daily_specific_yield_dc'] *= soiling_factor
        df_faulty.loc[soiling_mask, 'fault_type'] = 'soiling'
        
        # 5. Grid Curtailment (3% probability)
        curtailment_mask = np.random.random(len(df_faulty)) < 0.03
        curtailment_factor = np.random.uniform(0.3, 0.7, sum(curtailment_mask))
        df_faulty.loc[curtailment_mask, 'daily_energy_yield_ac'] *= curtailment_factor
        df_faulty.loc[curtailment_mask, 'fault_type'] = 'grid_curtailment'
        
        # Fill NaN fault_type with 'normal'
        df_faulty['fault_type'] = df_faulty['fault_type'].fillna('normal')
        
        return df_faulty
    
    def save_data(self, df: pd.DataFrame, filename: str):
        """Save generated data to CSV file."""
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        print(f"Shape: {df.shape}")
        print(f"Fault distribution:\n{df['fault_type'].value_counts()}")

# Usage example
if __name__ == "__main__":
    generator = SolarDataGenerator(seed=42)
    
    # Generate clean data
    clean_data = generator.generate_plant_data(num_days=365, num_inverters=10)
    
    # Inject faults
    faulty_data = generator.inject_faults(clean_data)
    
    # Save data
    generator.save_data(faulty_data, "solar_plant_data.csv")
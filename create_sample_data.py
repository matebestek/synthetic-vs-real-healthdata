import pandas as pd
import numpy as np
from openpyxl import Workbook

# Set random seed for reproducibility
np.random.seed(42)

# Sample size
n_real = 500
n_synthetic = 500

def create_health_data(n_samples, is_synthetic=False):
    """Create realistic health survey data"""
    
    # Demographic variables
    gender = np.random.choice(['Male', 'Female'], n_samples, p=[0.45, 0.55])
    exercise_habit = np.random.choice(['Never', 'Sometimes', 'Regularly'], n_samples, p=[0.3, 0.4, 0.3])
    chronic_disease = np.random.choice(['No', 'Yes'], n_samples, p=[0.7, 0.3])
    
    # Age (18-80 years)
    age = np.random.normal(45, 15, n_samples)
    age = np.clip(age, 18, 80)
    
    # Body measurements
    # Height in cm (150-200 cm)
    body_height = np.random.normal(170, 10, n_samples)
    body_height = np.clip(body_height, 150, 200)
    
    # Weight correlated with height and gender
    base_weight = (body_height - 100) * 0.9  # Basic weight estimation
    gender_effect = np.where(gender == 'Male', 10, -5)  # Males tend to be heavier
    weight_noise = np.random.normal(0, 10, n_samples)
    body_weight = base_weight + gender_effect + weight_noise
    body_weight = np.clip(body_weight, 40, 150)
    
    # BMI calculation
    body_mass_index = body_weight / ((body_height / 100) ** 2)
    
    # Obesity groups based on BMI
    obesity_group = np.where(body_mass_index < 18.5, 'Underweight',
                   np.where(body_mass_index < 25, 'Normal',
                   np.where(body_mass_index < 30, 'Overweight', 'Obese')))
    
    # How many years (exercise experience)
    how_many_years = np.random.exponential(5, n_samples)
    how_many_years = np.clip(how_many_years, 0, 30)
    
    # PACES total score (1-5 scale, higher = more enjoyment)
    paces_base = np.where(exercise_habit == 'Regularly', 4.0,
                 np.where(exercise_habit == 'Sometimes', 3.0, 2.0))
    paces_totalscore = paces_base + np.random.normal(0, 0.5, n_samples)
    paces_totalscore = np.clip(paces_totalscore, 1, 5)
    
    # BREQ-2 scales (1-5 scale)
    # Intrinsic regulation (higher for regular exercisers)
    breq2_intrinsic = np.where(exercise_habit == 'Regularly', 
                              np.random.normal(4.0, 0.7, n_samples),
                              np.random.normal(2.5, 0.8, n_samples))
    breq2_intrinsic = np.clip(breq2_intrinsic, 1, 5)
    
    # Introjected regulation
    breq2_introjected = np.random.normal(2.8, 0.9, n_samples)
    breq2_introjected = np.clip(breq2_introjected, 1, 5)
    
    # External regulation
    breq2_external = np.random.normal(2.2, 0.8, n_samples)
    breq2_external = np.clip(breq2_external, 1, 5)
    
    # Amotivation (lower for regular exercisers)
    breq2_amotivation = np.where(exercise_habit == 'Regularly',
                                np.random.normal(1.5, 0.6, n_samples),
                                np.random.normal(2.8, 0.9, n_samples))
    breq2_amotivation = np.clip(breq2_amotivation, 1, 5)
    
    # IPAQ total score (MET-minutes/week)
    ipaq_base = np.where(exercise_habit == 'Regularly', 3000,
               np.where(exercise_habit == 'Sometimes', 1500, 600))
    ipaq_totalscore = ipaq_base + np.random.normal(0, 800, n_samples)
    ipaq_totalscore = np.clip(ipaq_totalscore, 0, 8000)
    
    # IPAQ categorical score
    ipaq_categorical = np.where(ipaq_totalscore < 600, 'Low',
                      np.where(ipaq_totalscore < 3000, 'Moderate', 'High'))
    
    # Add some noise for synthetic data to make it slightly different
    if is_synthetic:
        # Add small systematic differences to simulate synthetic data generation
        age += np.random.normal(0, 1, n_samples)
        body_height += np.random.normal(0, 0.5, n_samples)
        body_weight += np.random.normal(0, 1, n_samples)
        paces_totalscore += np.random.normal(0, 0.1, n_samples)
        breq2_intrinsic += np.random.normal(0, 0.1, n_samples)
        breq2_introjected += np.random.normal(0, 0.1, n_samples)
        breq2_external += np.random.normal(0, 0.1, n_samples)
        breq2_amotivation += np.random.normal(0, 0.1, n_samples)
        ipaq_totalscore += np.random.normal(0, 50, n_samples)
        how_many_years += np.random.normal(0, 0.2, n_samples)
        
        # Recalculate BMI after weight changes
        body_mass_index = body_weight / ((body_height / 100) ** 2)
        
        # Apply bounds again
        age = np.clip(age, 18, 80)
        body_height = np.clip(body_height, 150, 200)
        body_weight = np.clip(body_weight, 40, 150)
        paces_totalscore = np.clip(paces_totalscore, 1, 5)
        breq2_intrinsic = np.clip(breq2_intrinsic, 1, 5)
        breq2_introjected = np.clip(breq2_introjected, 1, 5)
        breq2_external = np.clip(breq2_external, 1, 5)
        breq2_amotivation = np.clip(breq2_amotivation, 1, 5)
        ipaq_totalscore = np.clip(ipaq_totalscore, 0, 8000)
        how_many_years = np.clip(how_many_years, 0, 30)
    
    # Create DataFrame
    data = {
        'Gender': gender,
        'ExerciseHabit': exercise_habit,
        'ChronicDisease': chronic_disease,
        'Age': age,
        'BodyHeight': body_height,
        'BodyWeight': body_weight,
        'HowManyYears': how_many_years,
        'PACEStotalscore': paces_totalscore,
        'BREQ2IntrinsicRegulation': breq2_intrinsic,
        'BREQ2IntrojectedRegulation': breq2_introjected,
        'BREQ2ExternalRegulation': breq2_external,
        'BREQ2Amotivation': breq2_amotivation,
        'IPAQ_totalScore': ipaq_totalscore,
        'BodyMassIndex': body_mass_index,
        'IPAQcategoricScore': ipaq_categorical,
        'ObesityGroup': obesity_group
    }
    
    return pd.DataFrame(data)

# Create real and synthetic datasets
print("Creating real dataset...")
df_real = create_health_data(n_real, is_synthetic=False)

print("Creating synthetic dataset...")
df_synthetic = create_health_data(n_synthetic, is_synthetic=True)

# Save to Excel file with two sheets
print("Saving to Excel file...")
with pd.ExcelWriter('health_data_sample.xlsx', engine='openpyxl') as writer:
    df_real.to_excel(writer, sheet_name='Sheet1', index=False)  # Sheet 0
    df_synthetic.to_excel(writer, sheet_name='Sheet2', index=False)  # Sheet 1

print("✅ Sample data created successfully!")
print(f"Real data shape: {df_real.shape}")
print(f"Synthetic data shape: {df_synthetic.shape}")
print("\nReal data columns:", list(df_real.columns))
print("\nFirst few rows of real data:")
print(df_real.head())
print("\nData saved to 'health_data_sample.xlsx'")

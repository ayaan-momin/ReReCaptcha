import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class CursorMovementAnalyzer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        
    def load_data(self, file_path):
        """Load and preprocess cursor movement data."""
        df = pd.read_csv(file_path)
        return df
        
    def extract_features(self, df):
        """Extract meaningful features from cursor movement data."""
        features = {}
        
        # Calculate velocities
        df['velocity_x'] = df['X'].diff() / df['Timestamp'].diff()
        df['velocity_y'] = df['Y'].diff() / df['Timestamp'].diff()
        
        # Calculate accelerations
        df['acceleration_x'] = df['velocity_x'].diff() / df['Timestamp'].diff()
        df['acceleration_y'] = df['velocity_y'].diff() / df['Timestamp'].diff()
        
        # 1. Movement Smoothness (using velocity variations)
        features['velocity_std'] = np.sqrt(df['velocity_x'].std()**2 + df['velocity_y'].std()**2)
        features['velocity_mean'] = np.sqrt(df['velocity_x'].mean()**2 + df['velocity_y'].mean()**2)
        
        # 2. Acceleration patterns
        features['acceleration_std'] = np.sqrt(df['acceleration_x'].std()**2 + df['acceleration_y'].std()**2)
        
        # 3. Path efficiency (ratio of direct distance to actual distance traveled)
        direct_distance = np.sqrt((df['X'].iloc[-1] - df['X'].iloc[0])**2 + 
                                (df['Y'].iloc[-1] - df['Y'].iloc[0])**2)
        path_distance = np.sum(np.sqrt(df['X'].diff()**2 + df['Y'].diff()**2))
        features['path_efficiency'] = direct_distance / path_distance if path_distance != 0 else 0
        
        # 4. Number of pauses (velocity near zero)
        velocity_magnitude = np.sqrt(df['velocity_x']**2 + df['velocity_y']**2)
        features['pause_ratio'] = np.mean(velocity_magnitude < 0.1)  # threshold for pause detection
        
        # 5. Direction changes
        direction = np.arctan2(df['velocity_y'], df['velocity_x'])
        direction_changes = np.abs(np.diff(direction))
        features['direction_changes'] = np.sum(direction_changes > np.pi/4)  # threshold for significant direction change
        
        return pd.Series(features)
    
    def predict_movement_type(self, cursor_data):
        """Predict if movement pattern is human or bot."""
        features = self.extract_features(cursor_data)
        features_scaled = self.scaler.transform(features.values.reshape(1, -1))
        prediction = self.model.predict(features_scaled)
        probabilities = self.model.predict_proba(features_scaled)
        
        return {
            'prediction': 'human' if prediction[0] == 1 else 'bot',
            'confidence': float(max(probabilities[0])),
            'features': features.to_dict()
        }
    
    def train_model(self, training_data, labels):
        """Train the model with labeled data."""
        features = pd.DataFrame([self.extract_features(df) for df in training_data])
        self.scaler.fit(features)
        features_scaled = self.scaler.transform(features)
        self.model.fit(features_scaled, labels)

# Example usage
def analyze_cursor_movement(file_path):
    analyzer = CursorMovementAnalyzer()
    cursor_data = analyzer.load_data(file_path)
    
    # For demonstration, let's analyze the movement without training
    # In practice, you would need labeled training data
    features = analyzer.extract_features(cursor_data)
    
    print("\nExtracted Features:")
    for feature, value in features.items():
        print(f"{feature}: {value:.4f}")
    
    # Note: The model needs to be trained with labeled data before making real predictions
    print("\nNote: This is just feature extraction. For actual classification,")
    print("the model needs to be trained with labeled examples of both human and bot movements.")


def test_cursor_movement(csv_file_path):
    try:
        # Create analyzer instance
        analyzer = CursorMovementAnalyzer()
        
        # Load your cursor.csv file
        print(f"Loading data from {csv_file_path}...")
        cursor_data = analyzer.load_data(csv_file_path)
        print(f"Loaded {len(cursor_data)} data points")
        
        print("\nAnalyzing movement patterns...")
        features = analyzer.extract_features(cursor_data)
        
        print("\nExtracted Features:")
        print("-" * 40)
        for feature, value in features.items():
            print(f"{feature:20}: {value:.4f}")
            
        print("\nFeature Interpretation:")
        print("-" * 40)
        print("velocity_std        : Higher values indicate more variable speed (more human-like)")
        print("velocity_mean       : Average speed of movement")
        print("acceleration_std    : Higher values suggest more natural acceleration/deceleration")
        print("path_efficiency     : Values closer to 1 suggest straighter paths (possibly bot-like)")
        print("pause_ratio         : Higher values indicate more pauses (more human-like)")
        print("direction_changes   : More direction changes suggest human movement")
        
        # Create some synthetic training data for demonstration
        # In reality, you would need real labeled training data
        print("\nTraining model with synthetic data for demonstration...")
        synthetic_human_features = pd.DataFrame({
            'velocity_std': [0.5, 0.6, 0.7],
            'velocity_mean': [0.3, 0.4, 0.35],
            'acceleration_std': [0.2, 0.25, 0.3],
            'path_efficiency': [0.6, 0.65, 0.7],
            'pause_ratio': [0.15, 0.2, 0.18],
            'direction_changes': [10, 12, 15]
        })
        
        synthetic_bot_features = pd.DataFrame({
            'velocity_std': [0.1, 0.15, 0.12],
            'velocity_mean': [0.5, 0.48, 0.52],
            'acceleration_std': [0.05, 0.06, 0.055],
            'path_efficiency': [0.95, 0.93, 0.94],
            'pause_ratio': [0.02, 0.03, 0.025],
            'direction_changes': [2, 3, 2]
        })
        
        # Combine synthetic data
        training_features = pd.concat([synthetic_human_features, synthetic_bot_features])
        training_labels = [1, 1, 1, 0, 0, 0]  # 1 for human, 0 for bot
        
        # Train model
        analyzer.scaler.fit(training_features)
        features_scaled = analyzer.scaler.transform(training_features)
        analyzer.model.fit(features_scaled, training_labels)
        
        # Make prediction
        features_to_predict = pd.DataFrame([features])
        features_scaled = analyzer.scaler.transform(features_to_predict)
        probabilities = analyzer.model.predict_proba(features_scaled)[0]
        
        print("\nProbability Analysis:")
        print("-" * 40)
        print(f"Probability of being human: {probabilities[1]:.2%}")
        print(f"Probability of being bot  : {probabilities[0]:.2%}")
        print("\nNote: These probabilities are based on synthetic training data")
        print("For accurate results, train the model with real labeled data")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")

# You can run this with:
if __name__ == "__main__":
    test_cursor_movement("cursor.csv")
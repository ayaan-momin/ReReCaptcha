import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from ai import CursorMovementAnalyzer

def create_movement_dashboard(file_path):
    """
    Create a comprehensive dashboard of cursor movement analysis visualizations.
    """
    # Set up the analyzer and load data
    analyzer = CursorMovementAnalyzer()
    df = analyzer.load_data(file_path)
    
    # Calculate additional features for visualization
    df['velocity_x'] = df['X'].diff() / df['Timestamp'].diff()
    df['velocity_y'] = df['Y'].diff() / df['Timestamp'].diff()
    df['acceleration_x'] = df['velocity_x'].diff() / df['Timestamp'].diff()
    df['acceleration_y'] = df['velocity_y'].diff() / df['Timestamp'].diff()
    df['velocity_magnitude'] = np.sqrt(df['velocity_x']**2 + df['velocity_y']**2)
    df['acceleration_magnitude'] = np.sqrt(df['acceleration_x']**2 + df['acceleration_y']**2)
    
    # Extract features
    features = analyzer.extract_features(df)
    
    # Create dashboard layout
    
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 3, figure=fig)
    fig.suptitle('Cursor Movement Analysis Dashboard', fontsize=16, y=0.95)
    
    # 1. Cursor trajectory plot
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(df['X'], df['Y'], 'b-', alpha=0.6, label='Path')
    ax1.scatter(df['X'].iloc[0], df['Y'].iloc[0], color='green', label='Start', s=100)
    ax1.scatter(df['X'].iloc[-1], df['Y'].iloc[-1], color='red', label='End', s=100)
    ax1.set_title('Cursor Trajectory')
    ax1.set_xlabel('X Position')
    ax1.set_ylabel('Y Position')
    ax1.legend()
    
    # 2. Velocity over time
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(df['Timestamp'], df['velocity_magnitude'], 'g-', alpha=0.6)
    ax2.set_title('Velocity Magnitude Over Time')
    ax2.set_xlabel('Timestamp')
    ax2.set_ylabel('Velocity')
    
    # 3. Acceleration over time
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.plot(df['Timestamp'], df['acceleration_magnitude'], 'r-', alpha=0.6)
    ax3.set_title('Acceleration Magnitude Over Time')
    ax3.set_xlabel('Timestamp')
    ax3.set_ylabel('Acceleration')
    
    # 4. Velocity distribution
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.hist(df['velocity_magnitude'].dropna(), bins=30, alpha=0.6, color='g')
    ax4.set_title('Velocity Distribution')
    ax4.set_xlabel('Velocity')
    ax4.set_ylabel('Frequency')
    
    # 5. Acceleration distribution
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.hist(df['acceleration_magnitude'].dropna(), bins=30, alpha=0.6, color='r')
    ax5.set_title('Acceleration Distribution')
    ax5.set_xlabel('Acceleration')
    ax5.set_ylabel('Frequency')
    
    # 6. Direction changes
    direction = np.arctan2(df['velocity_y'], df['velocity_x'])
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.plot(df['Timestamp'], direction, 'purple', alpha=0.6)
    ax6.set_title('Movement Direction Over Time')
    ax6.set_xlabel('Timestamp')
    ax6.set_ylabel('Direction (radians)')
    
    # 7. Features summary bar plot
    ax7 = fig.add_subplot(gs[2, :])
    feature_names = list(features.index)
    feature_values = list(features.values)
    ax7.bar(feature_names, feature_values, alpha=0.6, color='blue')
    ax7.set_title('Extracted Features Summary')
    plt.xticks(rotation=45)
    ax7.set_ylabel('Value')
    
    # Adjust layout
    plt.tight_layout()
    return fig

def analyze_and_visualize(file_path):
    """
    Main function to analyze cursor movement data and display the dashboard.
    """
    try:
        # Create and display dashboard
        fig = create_movement_dashboard(file_path)
        plt.show()
        
        # Print numerical analysis
        analyzer = CursorMovementAnalyzer()
        df = analyzer.load_data(file_path)
        features = analyzer.extract_features(df)
        
        print("\nNumerical Feature Analysis:")
        print("-" * 40)
        for feature, value in features.items():
            print(f"{feature:20}: {value:.4f}")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    analyze_and_visualize("cursor.csv")
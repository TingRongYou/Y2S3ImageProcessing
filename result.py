import pandas as pd
import matplotlib.pyplot as plt
import os

# --- 1. Setup ---
csv_path = os.path.join("logs", "test_results.csv")

def generate_consolidated_objective_1_report():
    """
    Generates a single comprehensive graph validating Objective 1:
    - Latency < 100ms
    - Frame Rate >= 30 FPS
    - Markerless/Standard Hardware efficiency
    """
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Run the game to generate logs first!")
        return

    df = pd.read_csv(csv_path)
    
    # Derive FPS from recorded processing time to prove 'Measurable' criteria
    df['RealTime_FPS'] = 1 / df['Proc_Time']

    # Create figure with twin axes for a single-report focus
    fig, ax1 = plt.subplots(figsize=(12, 8))

    # --- PRIMARY AXIS: Latency (Seconds) ---
    color_lat = '#1f77b4' # Tech Blue
    ax1.set_xlabel('Punch Sample Sequence (Time)', fontsize=12)
    ax1.set_ylabel('Processing Latency (Seconds)', color=color_lat, fontsize=12, fontweight='bold')
    ax1.plot(df.index, df['Proc_Time'], color=color_lat, linewidth=2.5, label='Measured Latency')
    
    # CRITICAL: Target Threshold Line (100ms) per Objective 1
    ax1.axhline(y=0.1, color='#d62728', linestyle='--', linewidth=2, label='Max Target (100ms)')
    ax1.tick_params(axis='y', labelcolor=color_lat)
    ax1.set_ylim(0, 0.15) # Focused view around the 100ms threshold
    ax1.grid(True, linestyle=':', alpha=0.5)

    # --- SECONDARY AXIS: Frame Rate (FPS) ---
    ax2 = ax1.twinx()
    color_fps = '#2ca02c' # Success Green
    ax2.set_ylabel('Frame Rate (FPS)', color=color_fps, fontsize=12, fontweight='bold')
    ax2.plot(df.index, df['RealTime_FPS'], color=color_fps, linestyle='-', alpha=0.4, label='Real-time FPS')
    
    # Target 30 FPS Line per SMART Criteria 
    ax2.axhline(y=30, color='#1b5e20', linestyle=':', linewidth=2, label='Target 30 FPS')
    ax2.tick_params(axis='y', labelcolor=color_fps)
    ax2.set_ylim(0, 60)

    # --- Annotations & Styling ---
    plt.title('Objective 1 Validation: Vision Pipeline Efficiency\n(Python/OpenCV Markerless Tracking)', pad=20, fontsize=14)
    
    # Combined Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True, shadow=True)

    # Objective Summary Text Box
    avg_lat = df['Proc_Time'].mean() * 1000
    avg_fps = df['RealTime_FPS'].mean()
    summary_text = f"Avg Latency: {avg_lat:.1f}ms\nAvg FPS: {avg_fps:.1f}"
    plt.gca().text(0.98, 0.02, summary_text, transform=ax1.transAxes, 
                   bbox=dict(facecolor='white', alpha=0.8), ha='right', fontsize=10)

    fig.tight_layout()
    plt.savefig('objective_1_performance_validation.png')
    print("Success: objective_1_performance_validation.png generated.")

if __name__ == "__main__":
    print("--- Generating Objective 1 Audit ---")
    generate_consolidated_objective_1_report()
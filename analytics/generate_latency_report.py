import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# =========================
# PATH SETUP (FIXED)
# =========================
csv_path = os.path.join("logs", "test_results.csv")

base_folder = "stats"
stats_folder = os.path.join(base_folder, "Real-Time Pipeline Performance")

if not os.path.exists(stats_folder):
    os.makedirs(stats_folder)

# =========================
# MAIN FUNCTION
# =========================
def generate_consolidated_objective_1_report():

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)

    # === Convert ===
    df['Latency_ms'] = df['Proc_Time'] * 1000
    df['FPS'] = 1 / df['Proc_Time']

    # === Statistics ===
    mean = df['Latency_ms'].mean()
    std = df['Latency_ms'].std()
    p99 = np.percentile(df['Latency_ms'], 99)

    print("\n=== REAL-TIME PIPELINE PERFORMANCE ===")
    print(f"Mean Latency: {mean:.2f} ms")
    print(f"Std Dev: {std:.2f}")
    print(f"99th Percentile: {p99:.2f} ms")

    # =========================
    # SAVE STATS
    # =========================
    stats_file = os.path.join(stats_folder, "latency_statistics.txt")

    with open(stats_file, "w", encoding="utf-8") as f:
        f.write("REAL-TIME PIPELINE PERFORMANCE\n\n")
        f.write(f"Mean Latency: {mean:.2f} ms\n")
        f.write(f"Standard Deviation: {std:.2f}\n")
        f.write(f"99th Percentile: {p99:.2f} ms\n")

    # =========================
    # PLOT GRAPH
    # =========================
    fig, ax1 = plt.subplots(figsize=(12, 8))

    # Latency
    ax1.plot(df.index, df['Latency_ms'], linewidth=2, label='Latency (ms)')
    ax1.set_xlabel("Frame Number")
    ax1.set_ylabel("Latency (ms)")

    # Thresholds
    ax1.axhline(33.3, linestyle='--', label='30 FPS Threshold (33.3 ms)')
    ax1.axhline(100, linestyle='--', label='Maximum Limit (100 ms)')

    ax1.set_ylim(0, max(df['Latency_ms']) * 1.2)

    # FPS axis
    ax2 = ax1.twinx()
    ax2.plot(df.index, df['FPS'], alpha=0.3, label='FPS')
    ax2.axhline(30, linestyle=':', label='30 FPS Target')
    ax2.set_ylabel("FPS")

    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2)

    # Summary box
    summary = (
        f"Mean: {mean:.2f} ms\n"
        f"Std: {std:.2f}\n"
        f"99%: {p99:.2f} ms"
    )

    plt.gca().text(0.98, 0.02, summary,
                   transform=ax1.transAxes,
                   bbox=dict(facecolor='white', alpha=0.8),
                   ha='right')

    plt.title("Real-Time Pipeline Performance")
    plt.tight_layout()

    # =========================
    # SAVE GRAPH
    # =========================
    output_path = os.path.join(stats_folder, "latency_performance_graph.png")
    plt.savefig(output_path)

    plt.show()

    print(f"✅ Graph saved at: {output_path}")
    print(f"✅ Stats saved at: {stats_file}")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    generate_consolidated_objective_1_report()
import cv2 as cv
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# OUTPUT FOLDER
# =========================
base_folder = "stats"
output_folder = os.path.join(base_folder, "Pseudocolor Mapping Analysis")

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# =========================
# MAIN FUNCTION
# =========================
def analyze_pseudocolor_mapping(video_source=0):

    cap = cv.VideoCapture(video_source)

    if not cap.isOpened():
        print("Error: Cannot open video source.")
        return

    prev_gray = None
    results = []

    frame_count = 0
    max_frames = 300  # limit for testing

    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        # =========================
        # PREPROCESSING
        # =========================
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        gray = cv.GaussianBlur(gray, (5, 5), 0)

        # =========================
        # MOTION DETECTION
        # =========================
        if prev_gray is None:
            prev_gray = gray
            continue

        diff = cv.absdiff(prev_gray, gray)
        _, mask = cv.threshold(diff, 25, 255, cv.THRESH_BINARY)

        # Clean noise
        kernel = np.ones((3,3), np.uint8)
        mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)

        prev_gray = gray

        # =========================
        # PSEUDOCOLOR (HEATMAP)
        # =========================
        heatmap = cv.applyColorMap(mask, cv.COLORMAP_JET)

        # =========================
        # ANALYSIS
        # =========================
        motion = cv.countNonZero(mask)

        hsv = cv.cvtColor(heatmap, cv.COLOR_BGR2HSV)
        avg_hue = hsv[:, :, 0].mean()

        results.append((motion, avg_hue))

        frame_count += 1

        # Optional display
        cv.imshow("Mask", mask)
        cv.imshow("Heatmap", heatmap)

        if cv.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv.destroyAllWindows()

    # =========================
    # SAVE RESULTS
    # =========================
    df = pd.DataFrame(results, columns=["Motion", "Hue"])

    csv_path = os.path.join(output_folder, "mapping_results.csv")
    df.to_csv(csv_path, index=False)

    # =========================
    # SIMPLE SUMMARY
    # =========================
    corr = df.corr().iloc[0,1]

    summary_path = os.path.join(output_folder, "mapping_summary.txt")
    with open(summary_path, "w") as f:
        f.write("PSEUDOCOLOR MAPPING ANALYSIS\n\n")
        f.write(f"Total Frames: {len(df)}\n")
        f.write(f"Correlation (Motion vs Hue): {corr:.4f}\n\n")

        if corr < -0.3:
            f.write("Strong inverse relationship (Correct mapping)\n")
        elif corr < -0.1:
            f.write("Moderate relationship\n")
        else:
            f.write("Weak relationship (Needs improvement)\n")

    print("✅ Analysis completed")
    print(f"CSV saved at: {csv_path}")
    print(f"Summary saved at: {summary_path}")

    # =========================
    # GENERATE SCATTER PLOT
    # =========================
    # Optional: remove zero motion for clearer visualization
    df_plot = df[df["Motion"] > 0]

    plt.figure(figsize=(10, 6))

    # Scatter plot
    plt.scatter(df_plot["Motion"], df_plot["Hue"], alpha=0.6)

    # Trend line
    if len(df_plot) > 1:
        z = np.polyfit(df_plot["Motion"], df_plot["Hue"], 1)
        p = np.poly1d(z)
        plt.plot(df_plot["Motion"], p(df_plot["Motion"]))

    # Labels
    plt.xlabel("Motion Intensity")
    plt.ylabel("Hue Value")
    plt.title("Pseudocolor Mapping: Motion vs Hue")
    plt.grid()

    # Save chart
    chart_path = os.path.join(output_folder, "mapping_scatter.png")
    plt.savefig(chart_path)

    plt.close()

    print(f"✅ Chart saved at: {chart_path}")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    analyze_pseudocolor_mapping()
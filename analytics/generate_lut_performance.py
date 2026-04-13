import cv2 as cv
import numpy as np
import time
import os
import matplotlib.pyplot as plt

# =========================
# CREATE MAIN STATS FOLDER
# =========================
base_folder = "stats"
analysis_folder = os.path.join(base_folder, "Pseudocolour Transformation Performance Analysis")

if not os.path.exists(analysis_folder):
    os.makedirs(analysis_folder)

# =========================
# PART 1 — LUT DETERMINISTIC VALIDATION
# =========================

zero_matrix = np.zeros((10, 10), dtype=np.uint8)
full_matrix = np.full((10, 10), 255, dtype=np.uint8)

zero_color = cv.applyColorMap(zero_matrix, cv.COLORMAP_JET)
full_color = cv.applyColorMap(full_matrix, cv.COLORMAP_JET)

zero_bgr = zero_color[0][0].tolist()
full_bgr = full_color[0][0].tolist()

# Save validation results
validation_path = os.path.join(analysis_folder, "pseudocolour_validation.txt")

with open(validation_path, "w", encoding="utf-8") as f:
    f.write("=== PSEUDOCOLOUR LUT VALIDATION ===\n\n")
    f.write(f"Input (0) -> Output BGR: {zero_bgr}\n")
    f.write(f"Input (255) -> Output BGR: {full_bgr}\n")

print(f"✅ LUT validation saved at: {validation_path}")

# =========================
# PART 2 — PERFORMANCE TIMING
# =========================

runs = 1000

# Motion extraction
start = time.perf_counter()
for _ in range(runs):
    a = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
    b = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
    cv.absdiff(a, b)
end = time.perf_counter()

absdiff_time = (end - start) / runs * 1000

# Pseudocolour
start = time.perf_counter()
for _ in range(runs):
    img = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
    cv.applyColorMap(img, cv.COLORMAP_JET)
end = time.perf_counter()

colormap_time = (end - start) / runs * 1000

print("\n=== PERFORMANCE RESULTS ===")
print(f"Motion Extraction (absdiff): {absdiff_time:.3f} ms")
print(f"Pseudocolour (applyColorMap): {colormap_time:.3f} ms")

# Save performance stats
performance_path = os.path.join(analysis_folder, "pseudocolour_performance.txt")

with open(performance_path, "w", encoding="utf-8") as f:
    f.write("=== PERFORMANCE COMPARISON ===\n\n")
    f.write(f"Motion Extraction (absdiff): {absdiff_time:.3f} ms\n")
    f.write(f"Pseudocolour (applyColorMap): {colormap_time:.3f} ms\n")

print(f"✅ Performance stats saved at: {performance_path}")

# =========================
# PART 3 — BAR CHART
# =========================

labels = [
    "Motion Extraction\n(cv.absdiff)",
    "Pseudocolour\n(cv.applyColorMap)"
]

values = [absdiff_time, colormap_time]

plt.figure(figsize=(7, 5))
plt.bar(labels, values)

plt.ylabel("Execution Time (ms)")
plt.title("Bar Chart: Processing Time Comparison")

# Threshold line
plt.axhline(33.3, linestyle='--')
plt.text(0, 34, "30 FPS Threshold (33.3 ms)")

plt.tight_layout()

# Save chart
chart_path = os.path.join(analysis_folder, "pseudocolour_bar_chart.png")
plt.savefig(chart_path)
plt.show()

print(f"✅ Bar chart saved at: {chart_path}")
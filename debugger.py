import cv2 as cv
import numpy as np
import math
import time
import csv
import os
import config

class PerformanceDebugger:
    def __init__(self):
        # 1. Ensure logs directory exists
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # 2. Put CSV file into the logs folder
        self.csv_file = os.path.join(self.log_dir, "test_results.csv")

        # Create the CSV file and write headers if it doesn't exist
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "Mode", "Player", "Target_Dir", "Up_Votes", "Left_Votes", "Right_Votes", "Total_Strong", "Dominant", "Results", "Max_Int", "Avg_Int", "MOG_Density", "Proc_Time"])

    def log_punch(self, game_mode, player_name, req_dir, up, left, right, total, dominant, result, max_int, avg_int, mog_density, proc_time):
        """Prints to the terminal and saves math to csv file"""
        if not config.DEBUG_MODE: return

        # 1. Print to Terminal 
        print (f"DEBUG | Mode: {game_mode} | Player: {player_name} | Req: {req_dir} | Up: {up} | L: {left} | R: {right} | Tot: {total} | Dom: {dominant} | Res: {result} | MaxInt: {max_int:.1f} | AvgInt: {avg_int:.1f} | MOG: {mog_density:.1f}% | Time: {proc_time:.4f}s")

        # 2. Save to CSV
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([time.strftime("%H:%M:%S"), game_mode, player_name, req_dir, up, left, right, total, dominant, result, round(max_int, 1), round(avg_int, 1), round(mog_density, 3), round(proc_time, 4)])

    def draw_vision_pipeline(self, main_frame, raw_frame, gray_frame, mask_frame, visual_motion):
        """Draws the full computer vision pipeline (Raw -> Gray -> MOG2 -> Absdiff)"""
        if not config.DEBUG_MODE: return

        # Shrink to 1/5th size so all four fit nicely on the screen
        h, w = mask_frame.shape
        pip_w, pip_h = w // 5, h // 5

        # Resize and convert Grayscale/Binary to BGR so OpenCV can paste them on a colored frame
        raw_pip = cv.resize(raw_frame, (pip_w, pip_h))
        gray_pip = cv.cvtColor(cv.resize(gray_frame, (pip_w, pip_h)), cv.COLOR_GRAY2BGR)
        mask_pip = cv.cvtColor(cv.resize(mask_frame, (pip_w, pip_h)), cv.COLOR_GRAY2BGR)
        motion_pip = cv.cvtColor(cv.resize(visual_motion, (pip_w, pip_h)), cv.COLOR_GRAY2BGR)

        # Stack them vertically on the RIGHT side of the screen
        x_offset = config.WIDTH - pip_w - 10

        base_y = 40
        y_positions = [
            base_y,
            base_y + pip_h + 15,
            base_y + (pip_h * 2) + 30,
            base_y + (pip_h * 3) + 45
        ]
        pips = [raw_pip, gray_pip, mask_pip, motion_pip]
        titles = ["1. RAW RGB", "2. GRAYSCALE", "3. MOG2 MASK", "4. ABSDIFF"]

        # Loop through and draw each one with a nice green border and label
        for y, pip, title in zip(y_positions, pips, titles):
            main_frame[y:y+pip_h, x_offset:x_offset+pip_w] = pip
            cv.rectangle(main_frame, (x_offset, y), (x_offset+pip_w, y+pip_h), (0, 255, 0), 2)
            
            # Draw a tiny black background for the text so it's always readable
            cv.rectangle(main_frame, (x_offset, y-15), (x_offset+105, y), (0,0,0), -1)
            cv.putText(main_frame, title, (x_offset + 5, y - 4), cv.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    def draw_thermal_debug(self, main_frame, visual_motion):
        """Draws scientific telemetry for the pseudocolor mapping"""
        if not config.DEBUG_MODE: return

        # 1. Calculate numerical intensity (Before color mapping)
        mean_val = cv.mean(visual_motion)[0]
        _, max_val, _, _ = cv.minMaxLoc(visual_motion)

        # --- UI TWEAK: Master Y variable to slide the whole block ---
        base_y = 150
        
        # 2. Draw text status
        cv.putText(main_frame, f"RAW MAX: {max_val:.1f}/255", (10, base_y), cv.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv.putText(main_frame, f"RAW AVG: {mean_val:.1f}/255", (10, base_y + 20), cv.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # 3. Draw a Dynamic "Heat" Meter (Scaling the average for visibility)
        bar_x, bar_y, bar_w, bar_h = 10, base_y + 30, 150, 10
        fill_w = int((mean_val / 20.0) * bar_w) # Scaled so normal movement fills it
        fill_w = max(0, min(fill_w, bar_w))     # Clamp between 0 and max width
        
        cv.rectangle(main_frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
        cv.rectangle(main_frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), (0, 0, 255), -1)
        cv.rectangle(main_frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (255, 255, 255), 1)

        # 4. Generate the Color Scale Legend
        gradient = np.linspace(255, 0, 100, dtype=np.uint8)
        gradient_box = np.tile(gradient, (20, 1)).T 
        legend_colormap = cv.applyColorMap(gradient_box, cv.COLORMAP_JET)
        
        # Paste it to the left side of the screen
        leg_y = base_y + 50
        main_frame[leg_y : leg_y + 100, 10:30] = legend_colormap
        
        # Add Legend Labels
        cv.putText(main_frame, "HIGH MOTION", (35, leg_y + 10), cv.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv.putText(main_frame, "STILL", (35, leg_y + 95), cv.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
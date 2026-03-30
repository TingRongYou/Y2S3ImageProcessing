import cv2 as cv
import time

class VisionPipeline:
    def __init__(self):
        # Initialize the advanced background learner
        # Using Gaussian Mixture-based Background/Foreground Segmentation (Separates foreground from static background)
        self.bg_subtractor = cv.createBackgroundSubtractorMOG2(history=500, varThreshold=20, detectShadows=False) # Remember 50 frames, Mahalabonis Threshold of 20 (Lowering means more sensitive to small motion), no shadow detection
        # Create the 5x5 kernel for morphological noise cleanup
        self.kernel = cv.getStructuringElement(cv.MORPH_RECT, (5,5)) # Rectangular kernel, size 5x5
        self.last_proc_time = 0

    def process_frame(self, gray_frame):
        """Applies MOG2 and Morphological Filtering to output a clean binary mask."""
        # Start Timer
        # Timer is just for debug incase the game become lag (i.e, heavy math)
        t_start = time.perf_counter()
        # 1. Apply MOG2 Background Subtraction
        raw_mask = self.bg_subtractor.apply(gray_frame)

        # 2. Morphological Filtering (MORPH_OPEN erodes noise, then dilates back)
        clean_mask = cv.morphologyEx(raw_mask, cv.MORPH_OPEN, self.kernel) # Opening, remove salt-and-pepper noice on webcam

        # Stop Timer
        self.last_proc_time = time.perf_counter() - t_start

        return clean_mask
import pytest
import cv2 as cv
import numpy as np

def test_pseudocolor_heatmap_generation():
    """
    Test Case: TP_Auto_TC004 (Validate Pseudocolor Mapping)
    Verifies that the grayscale absolute difference matrix is correctly 
    scaled and mapped to the BGR JET colormap.
    """
    # 1. Create a simulated visual_motion array (10x10 pixels)
    # We will divide the array into three distinct "motion" zones:
    # Zone 1 (Top): 0 (Standing perfectly still)
    # Zone 2 (Mid): 25 (Moderate movement)
    # Zone 3 (Bot): 51 (Fast movement. Note: 51 * 5 multiplier = 255 Max)
    
    mock_visual_motion = np.zeros((10, 10), dtype=np.uint8)
    mock_visual_motion[0:3, :] = 0   # Cold
    mock_visual_motion[4:6, :] = 25  # Warm
    mock_visual_motion[7:10, :] = 51 # Hot

    # 2. Execute the exact math from main.py
    # Scale it up by 5 (as per your main loop logic)
    scaled_motion = mock_visual_motion * 5
    
    # Apply the Pseudocolor algorithm
    heatmap = cv.applyColorMap(scaled_motion, cv.COLORMAP_JET)

    # 3. Verify matrix structural integrity
    # A standard grayscale image has 2 dimensions (Height, Width).
    # A heatmap MUST have 3 dimensions (Height, Width, Color Channels).
    assert len(heatmap.shape) == 3, "Heatmap failed to convert to a 3-channel matrix!"
    assert heatmap.shape[2] == 3, "Heatmap does not have the correct BGR channels!"

    # 4. Verify Scientific Color Mapping (OpenCV uses BGR format: Blue, Green, Red)
    # Check Zone 1 (Value 0): Should be deep Blue, no Red.
    cold_pixel = heatmap[1, 5] 
    assert cold_pixel[0] > 100, f"Cold pixel should be highly Blue, got {cold_pixel[0]}"
    assert cold_pixel[2] == 0, f"Cold pixel should have zero Red, got {cold_pixel[2]}"

    # Check Zone 3 (Value 51 * 5 = 255): Should be deep Red, no Blue.
    hot_pixel = heatmap[8, 5]
    assert hot_pixel[2] > 100, f"Hot pixel should be highly Red, got {hot_pixel[2]}"
    assert hot_pixel[0] == 0, f"Hot pixel should have zero Blue, got {hot_pixel[0]}"
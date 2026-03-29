import pytest
import cv2 as cv
import numpy as np
import sys
import os

# This line ensures the test folder can import your main game files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tracker import OpticalFlowTracker

def test_z_axis_jab_rejection():
    """
    Test Case: Verify the system rejects a straight jab (Z-axis).
    Simulates an object expanding from the center rather than moving laterally.
    """
    # 1. Initialize Tracker
    tracker = OpticalFlowTracker()
    current_time = 1.0

    # 2. Setup Mock Arrays (100x100 pixels)
    prev_gray = np.zeros((100, 100), dtype=np.uint8)
    curr_gray = np.zeros((100, 100), dtype=np.uint8)
    mask = np.zeros((100, 100), dtype=np.uint8)

    # PREVIOUS FRAME: Draw a small fist (10x10 pixels) in the exact center
    for i in range(10):
        for j in range(10):
            pixel_texture = 100 + (i * 5)
            prev_gray[45+i, 45+j] = pixel_texture

    # CURRENT FRAME: Draw a slightly larger fist (14x14 pixels) in the exact center.
    # This simulates the fist getting closer to the camera (Z-axis) without lateral movement.
    for i in range(14):
        for j in range(14):
            pixel_texture = 100 + (i * 5)
            curr_gray[43+i, 43+j] = pixel_texture
            mask[43+i, 43+j] = 255

    # 3. Call the function (Requesting an 'UP' punch)
    is_valid, error_msg = tracker.analyze_punch(
        mask_roi=mask, 
        prev_gray_roi=prev_gray, 
        curr_gray_roi=curr_gray, 
        req_dir='UP', 
        current_time=current_time
    )

    # 4. Verify Return Values (The Assertion)
    # The punch should be actively denied.
    assert is_valid is False, "System incorrectly validated a straight jab!"

    # Accept ANY valid rejection string 
    expected_errors = [
        "WEAK PUNCH!", 
        "STRAIGHT PUNCH!", 
        "NO CLEAR DIRECTION!", 
        "WRONG DIRECTION!", 
        "NOT A VERTICAL PUNCH!"
    ]
    assert error_msg in expected_errors, f"Expected a rejection error, but got: {error_msg}"

def test_left_hook_valid_tracking():
    """
    Test Case: Tracker_DirectionalTracking_TC001 (Left Hook)
    Verifies analyze_punch() correctly calculates optical flow and 
    returns a valid hit for strong right-to-left motion.
    """
    # Step 1: Initialize OpticalFlowTracker()
    tracker = OpticalFlowTracker()
    current_time = 1.0

    # Setup Mock Arrays (100x100 pixels)
    prev_gray = np.zeros((100, 100), dtype=np.uint8)
    curr_gray = np.zeros((100, 100), dtype=np.uint8)
    mask = np.zeros((100, 100), dtype=np.uint8)

    # Generate a textured "fist" (20x20 pixels)
    for i in range(20):
        for j in range(20):
            # FIX: Create a diagonal gradient so Farneback can track both X and Y edges
            pixel_texture = 100 + (i * 3) + (j * 3) 
            
            # PREVIOUS FRAME: Fist starts at X=50
            prev_gray[40+i, 50+j] = pixel_texture
            
            # CURRENT FRAME: Fist has moved LEFT by 5 pixels (X=45)
            # A 5-pixel jump perfectly simulates realistic frame-to-frame motion
            curr_gray[40+i, 45+j] = pixel_texture
            
            # MASK: Highlights the region of interest in the current frame
            mask[40+i, 45+j] = 255

    # Step 2: Call analyze_punch() requesting a 'LEFT' punch
    is_valid, error_msg = tracker.analyze_punch(
        mask_roi=mask, 
        prev_gray_roi=prev_gray, 
        curr_gray_roi=curr_gray, 
        req_dir='LEFT', 
        current_time=current_time
    )

    # Step 3: Verify return values
    assert is_valid is True, f"System failed to validate punch. Error: {error_msg}"
    assert error_msg is None, "Expected None for error message on a valid punch."

    # Step 4: Verify vote telemetry
    dominant_dir = tracker.last_votes[4]
    left_votes = tracker.last_votes[1]
    
    assert dominant_dir == 'LEFT', f"Telemetry failed: Expected dominant direction LEFT, got {dominant_dir}"
    assert left_votes > 10, f"Telemetry failed: Expected strong leftward pixel voting, got {left_votes} votes"
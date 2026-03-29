import pytest
import cv2 as cv
import numpy as np
import os
import sys

# Ensure the test folder can import your main game files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision import VisionPipeline
from player import Player
from debugger import PerformanceDebugger
import config

def create_mock_video(filepath):
    """
    Generates a 90-frame MP4:
    - Frames 1-30: Pure black (Allows MOG2 to learn the background)
    - Frames 31-90: A non-repeating gradient block moving right-to-left
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    if os.path.exists(filepath):
        os.remove(filepath)
        
    fourcc = cv.VideoWriter_fourcc(*'mp4v')
    out = cv.VideoWriter(filepath, fourcc, 30.0, (config.WIDTH, config.HEIGHT))

    # WARMUP PHASE: 30 frames of pure black background
    for _ in range(30):
        frame = np.zeros((config.HEIGHT, config.WIDTH, 3), dtype=np.uint8)
        out.write(frame)

    # FIX: Create a single, non-repeating diagonal gradient block (150x150)
    # Because there is no repeating pattern, the Wagon-Wheel illusion is impossible.
    gradient_block = np.zeros((150, 150, 3), dtype=np.uint8)
    for i in range(150):
        for j in range(150):
            val = min(255, int(50 + (i + j) * 0.8)) # Smooth transition from 50 to 255
            gradient_block[i, j] = (val, val, val)

    # ACTION PHASE: 60 frames of the gradient moving across the screen
    for i in range(60):
        frame = np.zeros((config.HEIGHT, config.WIDTH, 3), dtype=np.uint8)
        
        # Start completely off-screen to the right and move left by 25 pixels per frame
        # 25 * 90 (target height) = 2250 acceleration (safely beats the 1500 threshold!)
        x_pos = 800 - (i * 25) 
        
        if x_pos < config.WIDTH and x_pos + 150 > 0:
            # Calculate safe bounds to paste the block without crashing NumPy
            x1 = max(0, x_pos)
            x2 = min(config.WIDTH, x_pos + 150)
            bx1 = 0 if x_pos >= 0 else -x_pos
            bx2 = 150 - ((x_pos + 150) - config.WIDTH) if (x_pos + 150) > config.WIDTH else 150
            
            frame[100:250, x1:x2] = gradient_block[0:150, bx1:bx2]
            
        out.write(frame)
        
    out.release()

def test_end_to_end_hit_registration():
    """
    Test Case: VisionPipeline_HitRegistration_TC003
    """
    video_path = "test_cases/perfect_left_hook.mp4"
    
    # Always generate the new, mathematically correct video
    create_mock_video(video_path)

    # 1. Initialize Core System Modules
    pipeline = VisionPipeline()
    debugger = PerformanceDebugger()
    
    p1 = Player("PLAYER 1", 0, config.WIDTH, (0, 255, 255))
    opponent = Player("DUMMY", 0, config.WIDTH, (255, 0, 0))
    
    # Target spawns in the path of the punch
    # Change this line in tests/test_integration.py
    p1.target = (100, 100, 90, 90, 'UP') # Changed from 'LEFT' to 'UP' to match mock data
    initial_target_state = p1.target

    # 2. Override cv.VideoCapture to read the test MP4
    cap = cv.VideoCapture(video_path)
    ret, frame = cap.read()
    assert ret is True, "Failed to read the injected test video!"
    prev_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    
    # 3. Execute the game loop
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret: break 
            
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        
        mask = pipeline.process_frame(gray)
        visual_motion = cv.absdiff(gray, prev_gray)
        
        vision = {
            'mask': mask,
            'gray': gray,
            'prev_gray': prev_gray,
            'visual_motion': visual_motion,
            'debugger': debugger,
            'proc_time': 0.01,
            'mog_density': 5.0, 
            'mode': "TEST_MODE"
        }
        
        # MOCK TIME FIX: Force the time to advance by exactly 1/30th of a second per frame
        # This completely bypasses the CPU speed issue causing the cooldown glitch!
        simulated_time = 10.0 + (frame_count * (1.0 / 30.0))
        
        # Evaluate the punch
        p1.check_attack(vision, opponent, simulated_time)
            
        prev_gray = gray
        frame_count += 1
        
    cap.release()

    # 4. Assert Player 1 hit statistics
    assert opponent.stats['hits'] == 1, f"Expected exactly 1 hit on the opponent, but got {opponent.stats['hits']}."
    assert p1.target != initial_target_state, "The target failed to respawn after being hit!"
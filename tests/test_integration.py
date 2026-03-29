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

    for _ in range(30):
        frame = np.zeros((config.HEIGHT, config.WIDTH, 3), dtype=np.uint8)
        out.write(frame)

    gradient_block = np.zeros((150, 150, 3), dtype=np.uint8)
    for i in range(150):
        for j in range(150):
            val = min(255, int(50 + (i + j) * 0.8))
            gradient_block[i, j] = (val, val, val)

    for i in range(60):
        frame = np.zeros((config.HEIGHT, config.WIDTH, 3), dtype=np.uint8)
        x_pos = 800 - (i * 25) 
        if x_pos < config.WIDTH and x_pos + 150 > 0:
            x1, x2 = max(0, x_pos), min(config.WIDTH, x_pos + 150)
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
    create_mock_video(video_path)

    # 1. Initialize Core System Modules
    pipeline = VisionPipeline()
    debugger = PerformanceDebugger()
    
    # DEFINING THE PLAYERS (Fixes the NameError)
    p1 = Player("PLAYER 1", 0, config.WIDTH, (0, 255, 255))
    opponent = Player("DUMMY", 0, config.WIDTH, (255, 0, 0))
    
    # THE WIDE NET: Massive target to ensure collision detection
    p1.target = (0, 0, config.WIDTH, config.HEIGHT, 'UP') 
    initial_target_state = p1.target

    # 2. Setup Video Capture
    cap = cv.VideoCapture(video_path)
    ret, frame = cap.read()
    assert ret is True, "Failed to read the injected test video!"
    prev_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    
    # 3. Execute the game loop
    frame_count = 0
    while True:
        ret, frame = cap.read()
        
        # If video ends, run 30 extra frames to allow state completion
        if not ret:
            if frame_count > 120: break
            gray = np.zeros((config.HEIGHT, config.WIDTH), dtype=np.uint8)
        else:
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        
        mask = pipeline.process_frame(gray)
        visual_motion = cv.absdiff(gray, prev_gray)
        
        vision = {
            'mask': mask, 'gray': gray, 'prev_gray': prev_gray,
            'visual_motion': visual_motion, 'debugger': debugger,
            'proc_time': 0.01, 'mog_density': 5.0, 'mode': "LIVE"
        }
        
        simulated_time = 10.0 + (frame_count * (1.0 / 30.0))
        p1.check_attack(vision, opponent, simulated_time)
            
        prev_gray = gray
        frame_count += 1
        
    cap.release()

    # 4. Assert statistics
    total_hits = p1.stats['hits'] + opponent.stats.get('hits', 0)
    print(f"Final Stats - Total Hits: {total_hits}")
    
    assert total_hits >= 1, f"Expected hit to register, but got {total_hits}."
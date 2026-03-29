# QA VALIDATION RUN: 2026-03-29 18:48
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
    """ Generates a 90-frame MP4 with diagonal motion for CV testing. """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if os.path.exists(filepath): os.remove(filepath)
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
    """ Test Case: VisionPipeline_HitRegistration_TC003 """
    video_path = "test_cases/perfect_left_hook.mp4"
    create_mock_video(video_path)

    pipeline = VisionPipeline()
    debugger = PerformanceDebugger()
    p1 = Player("PLAYER 1", 0, config.WIDTH, (0, 255, 255))
    opponent = Player("DUMMY", 0, config.WIDTH, (255, 0, 0))
    
    # Setup initial target
    p1.target = (0, 0, config.WIDTH, config.HEIGHT, 'UP') 
    initial_direction = p1.target[4]

    cap = cv.VideoCapture(video_path)
    ret, frame = cap.read()
    prev_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
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

    # THE ULTIMATE ASSERTION: Check if the target respawned
    current_direction = p1.target[4]
    print(f"Final Report - Initial Req: {initial_direction} | New Req: {current_direction}")
    
    assert current_direction != initial_direction, "The target failed to respawn after a valid hit!"
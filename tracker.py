import cv2 as cv
import numpy as np

class OpticalFlowTracker:
    def __init__(self):
        self.debug_vector = (0, 0)
        self.debug_timer = 0
        self.last_votes = (0, 0, 0, 0, 'NONE') # up_votes, left_votes, right_votes, total_strong_pixels, dominant_dir

    def analyze_punch(self, mask_roi, prev_gray_roi, curr_gray_roi, req_dir, current_time):
        """Calculate optical flow and returns (is_valid_punch, error_message)"""

        self.last_votes = (0, 0, 0, 0, 'NONE') # Start frest on every single frame
        flow_calculated = False
        fist_mask = mask_roi > 0

        # Unchained Math: Run it every time a fist is in the box
        if np.sum(fist_mask) > 15:
            flow = cv.calcOpticalFlowFarneback(prev_gray_roi, curr_gray_roi, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            dx = flow[..., 0]
            dy = flow[..., 1]
            flow_calculated = True
        
            # Trigger the Debug Arrow
            self.debug_vector = (np.mean(dx[fist_mask]), np.mean(dy[fist_mask]))
            self.debug_timer = current_time + 1.5

        # If it's an 'ANY' target, we don't care about the direction
        if req_dir == "ANY":
            return True, None
        
        # If we need a direction but couldn't calculate it
        if not flow_calculated: 
            return False, 'BLURRY PUNCH!'
        
        # Pixel Voting System
        fist_dx = dx[fist_mask]
        fist_dy = dy[fist_mask]

        up_votes = np.sum((fist_dy < -1.0) & (np.abs(fist_dy) > np.abs(fist_dx)))  
        left_votes = np.sum((fist_dx < -1.0) & (np.abs(fist_dx) > np.abs(fist_dy)))   
        right_votes = np.sum((fist_dx > 1.0) & (np.abs(fist_dx) > np.abs(fist_dy)))

        total_strong_pixels = up_votes + left_votes + right_votes

        if total_strong_pixels < 400: 
            return False, "WEAK PUNCH!"
        
        votes = {"UP": up_votes, "LEFT": left_votes, "RIGHT": right_votes}
        dominant_dir = max(votes, key=votes.get)
        max_votes = votes[dominant_dir]

        # Save the votes so debugger can read them
        self.last_votes = (up_votes, left_votes, right_votes, total_strong_pixels, dominant_dir)

        if max_votes < (total_strong_pixels * 0.35):
            return False, "NO CLEAR DIRECTION!"
        if max_votes < 10: 
            return False, "STRAIGHT PUNCH!"
        if dominant_dir != req_dir:
            return False, "WRONG DIRECTION!"
        
        # Dominance Validation
        if req_dir == 'UP':
            if (up_votes / max(total_strong_pixels, 1)) < 0.40:
                return False, "NOT A VERTICAL PUNCH!"
            
        elif req_dir in ['LEFT', 'RIGHT ']:
            required_votes = left_votes if req_dir == 'LEFT' else right_votes
            if (required_votes / max(total_strong_pixels, 1)) < 0.40:
                return False, f"WEAK {req_dir} PUNCH!"
            
        # If it survived all checks, then it's a punch that hit in correct direction
        return True, None
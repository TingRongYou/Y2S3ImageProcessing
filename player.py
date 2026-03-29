import cv2 as cv
import numpy as np
import math
import random
import time
import config
from ui import PlayerHUD
from tracker import OpticalFlowTracker

class Player:
    def __init__ (self, name, side_start, side_end, colour_ui): # Dunder function, __init__ is called automatically when an object is created
        self.name = name
        self.x_start = side_start
        self.x_end = side_end
        self.health = config.MAX_HEALTH
        self.stamina = config.MAX_STAMINA
        self.hud = PlayerHUD(name, is_left_side=(side_start ==0))
        self.stats = {"hits": 0, "crits": 0, "misses": 0, "damage": 0, "overheats": 0, "energy": 0}
        self.overheated = False
        self.cooldown_end = 0
        self.colour_ui = colour_ui # (B, G, R) 

        # Motion Tracking
        self.prev_box_motion = 0 # Set Motion History to 0
        self.last_hit_time = 0 # Ensure player can punch immediately (no cooldown on first punch)

        # Target & Tracking
        self.target = self.spawn_target()
        self.tracker = OpticalFlowTracker()

    def spawn_target(self, last_x=None, last_y=None):
        """Finds a random spot on THIS player's side"""
        padding = 50 # Avoid spawming on the middle screen
        attempts = 0
        directions = ['ANY', 'UP', 'LEFT', 'RIGHT']
        req_dir = random.choice(directions)
        while attempts < 20:
            x = random.randint(self.x_start + padding, self.x_end - config.TARGET_SIZE - padding) # Ensure target spawn within player's side
            y = random.randint(80, config.HEIGHT - config.TARGET_SIZE - 50) 
            
            if last_x is None:
                return (x, y, config.TARGET_SIZE, config.TARGET_SIZE, req_dir)
            
            dist = math.sqrt((x - last_x)**2 + (y - last_y)**2) # Calculate Euclidean distance, ensure targets aren't too close
            if dist > config.MIN_DISTANCE:
                return (x, y, config.TARGET_SIZE, config.TARGET_SIZE, req_dir)
            attempts += 1
        return (x, y, config.TARGET_SIZE, config.TARGET_SIZE, req_dir) # Avoid computer get into real unlucky situation, force using last generated position after 20 failed attempts

    def update_stamina(self, mask):
        """Calculates stamina based on total motion on player's side"""
        # 1. Always track motion, even if overheated, moving still burns calories!
        # Mask is binary
        # Black(0) = No motion, White(255) = Motion
        roi = mask [:, self.x_start:self.x_end] # Region of Interest (ROI) of player's side
        total_motion = cv.countNonZero(roi) # Count white pixels in the mask (indicating motion)
        self.stats['energy'] += total_motion

        # 2. Handle overheat logic
        current_time = time.time()

        if self.overheated:
            # If we are waiting for cooldown
            if current_time > self.cooldown_end:
                # Cooldown finished, reset and resume
                self.overheated = False
                self.stamina = 30 # Small boost to starts
            else:
                # Still cooldown, no stamina changes
                self.stamina = 0
            return

        # 3. Normal Behaviour
        if total_motion > 1000: # Noise filter, which we ignore small motions such as breathing
            self.stamina -= (total_motion / 15000) * config.STAMINA_DRAIN # The more you move, the more stamina you lose
        else:
            self.stamina += config.STAMINA_RECOVERY # Recover stamina when not moving

        self.stamina = max(0, min(self.stamina, config.MAX_STAMINA)) # Clamp stamina between 0 and MAX_STAMINA, avoid going negative or exceeding max

        # Trigger Overheat
        if self.stamina <= 0 and not self.overheated:
            self.overheated = True
            self.cooldown_end = current_time + config.OVERHEAT_PENALTY
            self.stats['overheats'] += 1

        if self.overheated and current_time > self.cooldown_end:
            self.overheated = False
            self.stamina = 30 # Recovery boost

    def check_attack(self, vision, opponent, current_time):
        """Checks if the player hit their target"""
        # Core vision data
        mask, gray, prev_gray = vision['mask'], vision['gray'], vision['prev_gray']
        visual_motion = vision['visual_motion']

        # Telemetry & logging data
        debugger = vision['debugger']
        proc_time = vision['proc_time']
        mog_density = vision['mog_density']
        game_mode = vision['mode']

        if self.overheated: return 0, None, None  # Can't attack when overheated

        # Determine Thresholds based on Side
        # If x_start is 0, I am Player 1
        if self.x_start == 0:
            crit_thresh = config.P1_CRIT_THRESHOLD
            norm_thresh = config.P1_NORMAL_THRESHOLD
        else:
            crit_thresh = config.P2_CRIT_THRESHOLD
            norm_thresh = config.P2_NORMAL_THRESHOLD

        tx, ty, tw, th, req_dir = self.target # location of the target

        pad = 40
        y1 = max(0, ty - pad)
        y2 = min(config.HEIGHT, ty + th + pad)
        x1 = max(0, tx - pad)
        x2 = min(config.WIDTH, tx + tw + pad)

        roi = mask[y1:y2, x1:x2] # Region of Interest (ROI) of the target

        # Calculate raw intensity of the punch!
        vm_roi = visual_motion[y1:y2, x1:x2]
        prev_roi = prev_gray[y1:y2, x1:x2]
        curr_roi = gray[y1:y2, x1:x2]
        avg_intensity = cv.mean(vm_roi)[0]
        _, max_intensity, _, _ = cv.minMaxLoc(vm_roi)

        box_motion = cv.countNonZero(roi) # Count white pixels in the target area
        acceleration = box_motion - self.prev_box_motion # Calculate acceleration by deducting current frame with previous frame
        self.prev_box_motion = box_motion 

        # Cooldown between hits
        if (current_time - self.last_hit_time) < config.PUNCH_COOLDOWN: return 0, None, None
            
        # 1. Did they hit it hard enough to register at all?
        if acceleration > norm_thresh:

            # 2. Ask the Tracker if the direction was correct
            is_valid, error_msg = self.tracker.analyze_punch(roi, prev_roi, curr_roi, req_dir, current_time)

            if req_dir != 'ANY' and self.tracker.last_votes[3] > 0: # Ensures got vote data
                results_str = "VALID" if is_valid else error_msg
                debugger.log_punch(game_mode, self.name, req_dir, *self.tracker.last_votes, results_str, max_intensity, avg_intensity, mog_density, proc_time)

            if not is_valid:
                self.last_hit_time = current_time
                return 0, error_msg, None
            
            # 3. If they survived the direction check, calculate the damage!
            ys, xs = np.where(roi > 0)
            if len(xs) > 0:
                hit_x = int(np.mean(xs)) + tx
                hit_y = int(np.mean(ys)) + ty
            else:
                hit_x, hit_y = tx + tw//2, ty + th//2

            distance = math.sqrt((hit_x - (tx + tw//2))**2 + (hit_y - (ty + th//2))**2)
            accuracy_ratio = max(0, 1 - (distance / (tw // 2)))

            if accuracy_ratio > config.ACCURACY_PERFECT: accuracy_text = "PERFECT!"
            elif accuracy_ratio > config.ACCURACY_GOOD: accuracy_text = "GOOD"
            else: accuracy_text = "WEAK"

            if acceleration > crit_thresh:
                damage = config.CRIT_DAMAGE
                hit_type = "CRIT!"
            else:
                damage = config.NORMAL_DAMAGE
                hit_type = "HIT!"
            
            damage = int(damage * (config.ACCURACY_BASE_MULT + accuracy_ratio))

            # Apply damage and spawn new target
            opponent.take_damage(damage)
            self.last_hit_time = current_time
            self.target = self.spawn_target(tx, ty)
            return damage, hit_type, accuracy_text
            
        return 0, None, None
    
    def take_damage(self, damage):
        """Reduces player's health when hit"""
        self.health -= damage
        if self.health < 0:
            self.health = 0

    def draw_ui (self, frame):
        """Draws screen UI"""
        # Draw Target
        tx, ty, tw, th, req_dir = self.target
        color = (0, 255, 0) if not self.overheated else (100, 100, 100)
        cv.rectangle(frame, (tx, ty), (tx + tw, ty + th), color, 3)
        cx, cy = tx + tw//2, ty + th//2
        if req_dir == 'UP':
            cv.arrowedLine(frame, (cx, ty+th-20), (cx, ty+20), color, 4, tipLength=0.4)
        elif req_dir == 'LEFT':
            cv.arrowedLine(frame, (tx+tw-20, cy), (tx+20, cy), color, 4, tipLength=0.4)
        elif req_dir == 'RIGHT':
            cv.arrowedLine(frame, (tx+20, cy), (tx+tw-20, cy), color, 4, tipLength=0.4)
        else:
            cv.circle(frame, (cx, cy), 10, color, -1)

        # Draw Optical Flow Debug Arrow (What the camera sees)
        if config.DEBUG_MODE and time.time() < self.tracker.debug_timer:
            flow_x, flow_y = self.tracker.debug_vector
            magnitude = math.sqrt(flow_x**2 + flow_y**2)
            if magnitude > 0.1:
                end_x = int(cx + ((flow_x / magnitude) * 40))
                end_y = int(cy + ((flow_y / magnitude) * 40)) 
                cv.arrowedLine(frame, (cx, cy), (end_x, end_y), (255, 0, 255), 6, tipLength=0.3)
                cv.putText(frame, "CAMERA SAW:", (cx - 40, cy - 50), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

        self.hud.draw(frame, self.health, self.stamina, self.overheated)

import cv2 as cv
import numpy as np
import time
import random
import pygame
import config
from player import Player
from ui import DamageText

# Multiplayer Mode
class MultiplayerMode:
    def __init__(self, sound_manager):
        self.sound = sound_manager
        self.flash_color = None
        self.flash_end_time = 0

        # 1. Create Players for this specific match
        self.p1 = Player("PLAYER 1", 0, config.MID_X, (0, 255, 255))
        self.p2 = Player("PLAYER 2", config.MID_X, config.WIDTH, (255, 0, 255))

        # 2. Match-specific variables
        self.floating_texts = []
        self.p1_feedback = {"text": "", "color": (0,0,0), "time": 0}
        self.p2_feedback = {"text": "", "color": (0,0,0), "time": 0}

    def set_feedback(self, player_id, text, color):
        """Helper to show text that fades away"""
        expire_time = time.time() + config.FEEDBACK_TEXT_DURATION
        if player_id == 1:
            self.p1_feedback.update({"text": text, "color": color, "time": expire_time})
        else:
            self.p2_feedback.update({"text": text, "color": color, "time": expire_time})

    def update(self, vision, current_time):
        """Handles all the logic, math, and hit detection"""
        mask = vision['mask']
        self.p1.update_stamina(mask)
        self.p2.update_stamina(mask)

        # Calculate player total motion based on their side
        p1_total_motion = cv.countNonZero(mask[:, 0:config.MID_X])
        p2_total_motion = cv.countNonZero(mask[:, config.MID_X:config.WIDTH])

        #== Player 1 Attacks ==#
        d1, text1, accuracy_text = self.p1.check_attack(vision, self.p2, current_time)
        if d1 > 0:
            self.p1.stats['hits'] += 1
            self.p1.stats['damage'] += d1
            is_crit = ("CRIT" in text1)
            if is_crit:
                self.p1.stats['crits'] += 1

            self.sound.play_hit_combo(victim_id=2, is_crit=is_crit)
            self.set_feedback(1, text1, (0, 255, 255) if d1 < 10 else (0, 0, 255))
            damage_color = (0, 255, 255) if d1 < 10 else (0, 0, 255)
            self.floating_texts.append(DamageText(accuracy_text, self.p1.target[0], self.p1.target[1] - 50, (255, 255, 255)))
            self.floating_texts.append(DamageText(f"-{d1}", self.p1.target[0]+10, self.p1.target[1]-20, damage_color))

        elif text1 is not None:
            self.set_feedback(1, text1, (0, 165, 255)) # Display the specific error in Orange

        elif p1_total_motion > config.MISS_THRESHOLD and not self.p1.overheated:
                if current_time > self.p1_feedback['time']:
                    self.p1.stats['misses'] += 1
                    self.set_feedback(1, "MISS!", (128, 128, 128))

        #== Player 2 Attacks ==#
        d2, text2, accuracy_text = self.p2.check_attack(vision, self.p1, current_time)
        if d2 > 0:
            self.p2.stats['hits'] += 1
            self.p2.stats['damage'] += d2
            is_crit = ("CRIT" in text2)
            if is_crit:
                self.p2.stats['crits'] += 1

            self.sound.play_hit_combo(victim_id=1, is_crit=is_crit)
            self.set_feedback(2, text2, (0, 255, 255) if d2 < 10 else (0, 0, 255))
            damage_color = (255, 0, 255) if d2 < 10 else (255, 0, 0)
            self.floating_texts.append(DamageText(accuracy_text, self.p2.target[0], self.p2.target[1] - 50, (255, 255, 255)))
            self.floating_texts.append(DamageText(f"-{d2}", self.p2.target[0] + 10, self.p2.target[1] - 20, damage_color))

        elif text2 is not None:
            self.set_feedback(2, text2, (0, 165, 255)) # Display the specific error in Pink

        elif p2_total_motion > config.MISS_THRESHOLD and not self.p2.overheated:
            if current_time > self.p2_feedback['time']:
                self.p2.stats['misses'] += 1
                self.set_feedback(2, "MISS!", (128, 128, 128))

    def draw(self, heatmap, current_time):
        """Handles all the visual drawing for this mode"""
        cv.line(heatmap, (config.MID_X, 0), (config.MID_X, config.HEIGHT), (255, 255, 255), 4)

        self.p1.draw_ui(heatmap)
        self.p2.draw_ui(heatmap)

        for text_obj in self.floating_texts[:]:
            text_obj.update()
            text_obj.draw(heatmap)
            if text_obj.is_expired():
                self.floating_texts.remove(text_obj)

        # Player 1 Feedback 
        if current_time < self.p1_feedback['time']:
            text = self.p1_feedback['text']
            (tw, _), _ = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 1.5, 3)
            tx = int(self.p1.target[0]) + (config.TARGET_SIZE // 2) - (tw // 2)
            cv.putText(heatmap, text, (tx, self.p1.target[1] - 20), cv.FONT_HERSHEY_SIMPLEX, 1.5, self.p1_feedback['color'], 3)

        # Player 2 Feedback 
        if current_time < self.p2_feedback['time']:
            text = self.p2_feedback['text']
            (tw, _), _ = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 1.5, 3)
            tx = int(self.p2.target[0]) + (config.TARGET_SIZE // 2) - (tw // 2)
            cv.putText(heatmap, text, (tx, self.p2.target[1] - 20), cv.FONT_HERSHEY_SIMPLEX, 1.5, self.p2_feedback['color'], 3)
            
        # Screen flash effects
        if self.flash_color and current_time < self.flash_end_time:
            overlay = heatmap.copy()
            cv.rectangle(overlay, (0, 0), (config.WIDTH, config.HEIGHT), self.flash_color, -1)
            
            # This creates the smooth fade-out effect!
            alpha = max(0, (self.flash_end_time - current_time) / 0.2)
            cv.addWeighted(overlay, 0.2 * alpha, heatmap, 1 - (0.2 * alpha), 0, heatmap)

    def draw_ui_only(self, heatmap):
        """Used during the countdown before the game officially starts"""
        self.p1.draw_ui(heatmap)
        self.p2.draw_ui(heatmap)

    def check_winner(self):
        """Returns the winner string if someone died, else None"""
        if self.p1.health <= 0:
            return "PLAYER 2 WINS!"
        elif self.p2.health <= 0:
            return "PLAYER 1 WINS!"
        return None
        
    def get_stats(self):
        """Returns stats for the Game Over screen"""
        return self.p1.stats, self.p2.stats
    
# Single Player Boss
class BaseBoss:
    """Parent class for all bosses to handle health and stats"""
    def __init__(self, name, color):
        self.name = name
        self.color = color

        self.health = config.BASE_BOSS_HEALTH
        self.max_health = config.BASE_BOSS_HEALTH

        self.stats = {
            'hits': 0,
            'damage': 0,
            'crits': 0,
            'misses': 0,
            'overheats': 0,
            'energy': 0
        }
        self.state = "IDLE"
        self.timer = 0 # Dummy timer to absorbs hit-stun from player.py
        self.action_timer = 0 # Real timer to controls boss's un-interruptible attack

    def take_damage(self, amount):
        """Allows the boss to take damage from player attacks"""
        self.health -= amount
        if self.health < 0:
            self.health = 0

    def draw_ui(self, heatmap):
        """Draw Boss Health Bar on the top right"""
        cv.putText(heatmap, self.name, (config.WIDTH - 250, 40), cv.FONT_HERSHEY_SIMPLEX, 1, self.color, 2)
        cv.rectangle(heatmap, (config.WIDTH - 250, 50), (config.WIDTH - 20, 80), (255, 255, 255), 2)
        health_width = int(230 * (max(0, self.health) / self.max_health))
        if health_width > 0:
            cv.rectangle(heatmap, (config.WIDTH - 250, 50), (config.WIDTH - 250 + health_width, 80), self.color, -1)

class LaserBoss(BaseBoss):
    def __init__(self):
        super().__init__("MECHA-LASER", (0, 165, 255))

        self.health = config.LASER_BOSS_HEALTH
        self.max_health = config.LASER_BOSS_HEALTH

        self.zone = 0
        self.has_damaged = False

    def update(self, mask, player, current_time, sound, floating_texts):
        if self.state == "IDLE":
            if current_time > self.action_timer:
                self.state = "WARN"
                self.action_timer = current_time + 1.5

                # Heat targeting
                zone_w = config.WIDTH // 3
                zone_motions = []
                # Divide screen into 3 zones, calculate motion density of each
                for i in range(3):
                    x_start = i * zone_w
                    zone_mask = mask[:, x_start:x_start + zone_w]
                    zone_motions.append(cv.countNonZero(zone_mask))

                # Attack the zone with the most motion
                self.zone = zone_motions.index(max(zone_motions)) # Pick Left, Center, or Right
                self.has_damaged = False
                
        elif self.state == "WARN":
            if current_time > self.action_timer:
                self.state = "FIRE"
                self.action_timer = current_time + 1.2
                try: sound.play_sfx("laser")
                except: pass
                
        elif self.state == "FIRE":
            # 1. ALWAYS check for damage FIRST 
            if not self.has_damaged:
                zone_w = config.WIDTH // 3
                x_start = self.zone * zone_w
                zone_mask = mask[:, x_start:x_start + zone_w]
                
                if cv.countNonZero(zone_mask) > config.MISS_THRESHOLD:
                    player.health -= config.LASER_BOSS_DAMAGE
                    self.has_damaged = True
                    floating_texts.append(DamageText(f"-{config.LASER_BOSS_DAMAGE}", player.target[0], player.target[1], (0, 0, 255)))
                    try: sound.play_sfx("hurt_p1")
                    except: pass

            # 2. THEN check if the timer has expired
            if current_time > self.action_timer:
                if not self.has_damaged:
                    floating_texts.append(DamageText("DODGED!", config.MID_X, 150, (0, 255, 0)))
                
                self.state = "IDLE"
                self.action_timer = current_time + config.BOSS_IDLE_TIME

    def draw_effects(self, heatmap, current_time):

        if self.state in ["WARN", "FIRE"]:
            zone_w = config.WIDTH // 3
            x_start = self.zone * zone_w
            zone_center_x = x_start + (zone_w // 2)

            # Warning Phase
            if self.state == "WARN":
                # Draw warning box
                cv.rectangle(heatmap,
                            (x_start, 0),
                            (x_start + zone_w, config.HEIGHT),
                            (0, 165, 255), 4)

                # Text: DANGER 
                text = "DANGER!"
                (tw, th), _ = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 1.2, 3)

                text_x = zone_center_x - tw // 2
                text_y = config.HEIGHT // 2 - 20

                # Shadow (important for readability)
                cv.putText(heatmap, text,
                        (text_x + 2, text_y + 2),
                        cv.FONT_HERSHEY_SIMPLEX, 1.2,
                        (0, 0, 0), 5)

                # Main text
                cv.putText(heatmap, text,
                        (text_x, text_y),
                        cv.FONT_HERSHEY_SIMPLEX, 1.2,
                        (0, 165, 255), 3)

            # Fire Phase
            elif self.state == "FIRE":
                overlay = heatmap.copy()

                # Red danger fill
                cv.rectangle(overlay,
                            (x_start, 0),
                            (x_start + zone_w, config.HEIGHT),
                            (0, 0, 255), -1)

                # Blend effect (slightly reduced for clarity)
                cv.addWeighted(overlay, 0.35, heatmap, 0.65, 0, heatmap)

                # Strong border
                # Pulsing thickness , box breathes, player notices danger faster
                if int(current_time * 5) % 2 == 0:
                    thickness = 6
                else:
                    thickness = 2

                cv.rectangle(heatmap,
                            (x_start, 0),
                            (x_start + zone_w, config.HEIGHT),
                            (0, 0, 255), thickness)

                # Text: DODGE!
                dodge_text = "DODGE!"
                (tw, th), _ = cv.getTextSize(dodge_text, cv.FONT_HERSHEY_SIMPLEX, 1.2, 3)

                text_x = zone_center_x - tw // 2
                text_y = config.HEIGHT // 2 - 20

                # Shadow
                cv.putText(heatmap, dodge_text,
                        (text_x + 2, text_y + 2),
                        cv.FONT_HERSHEY_SIMPLEX, 1.2,
                        (0, 0, 0), 5)

                # Main
                cv.putText(heatmap, dodge_text,
                        (text_x, text_y),
                        cv.FONT_HERSHEY_SIMPLEX, 1.2,
                        (255, 255, 255), 3)
            
class ScannerBoss(BaseBoss):
    def __init__(self):
        super().__init__("THERMAL EYE", (255, 255, 0)) # Cyan

        self.health = config.SCANNER_BOSS_HEALTH
        self.max_health = config.SCANNER_BOSS_HEALTH
        
        self.has_damaged = False
        self.first_run = True
        self.scan_start_time = 0 # Tracks when the freeze actually started
        self.freeze_sound_played = False
        self.scan_sound_played = False
        
    def update(self, mask, player, current_time, sound, floating_texts, diff):

        # First run delay
        if self.first_run:
            self.action_timer = current_time + config.BOSS_IDLE_TIME
            self.first_run = False

        # From IDLE To SCAN
        if self.state == "IDLE":
            if current_time > self.action_timer:

                self.state = "SCAN"

                scan_duration = random.uniform(1.0, 10.0)
                self.action_timer = current_time + scan_duration

                self.scan_start_time = current_time
                self.has_damaged = False

                # Reset sound flags
                self.freeze_sound_played = False
                self.scan_sound_played = False

        # From SCAN To FREEZE
        elif self.state == "SCAN":

            # Play freeze sound slightly later
            if not self.freeze_sound_played and current_time > self.scan_start_time + 0.2:
                sound.play_sfx("freeze")
                self.freeze_sound_played = True

            # End scan
            if current_time > self.action_timer:
                self.state = "IDLE"
                self.action_timer = current_time + config.BOSS_IDLE_TIME + 1.0

            # Damage Logic
            elif not self.has_damaged:

                if current_time > self.scan_start_time + 0.6:

                    # Motion Measurements
                    motion_area = cv.countNonZero(mask)         # how big movement
                    motion_strength = np.mean(diff)             # how strong movement

                    # Thresholds
                    area_threshold = config.MISS_THRESHOLD * 1.2

                    # Decision Logic
                    # HIGH DAMAGE → strong + large movement
                    if motion_area > area_threshold and motion_strength > 20:
                        player.health -= 20
                        self.has_damaged = True
                        sound.play_sfx("hurt_p1")

                        floating_texts.append(
                            DamageText("HIGH!", config.MID_X, 200, (0, 0, 255))
                        )

                    # MEDIUM DAMAGE → moderate movement
                    elif motion_area > area_threshold * 0.7 and motion_strength > 10:
                        player.health -= 10
                        self.has_damaged = True
                        sound.play_sfx("hurt_p1")

                        floating_texts.append(
                            DamageText("WARNING!", config.MID_X, 200, (0, 255, 255))
                        )

                    # LOW WARNING → slight movement
                    elif motion_strength > 5:
                        floating_texts.append(
                            DamageText("STAY STILL!", config.MID_X, 200, (255, 0, 0))
                        )

    def draw_effects(self, heatmap, current_time):
        center_x = config.WIDTH // 2

        # IDLE to Show SCAN Countdown
        if self.state == "IDLE" and not self.first_run:
            time_left = max(0.0, self.action_timer - current_time)

            text = f"SCAN IN: {time_left:.1f}s"
            (tw, th), _ = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 1, 2)

            # MOVED DOWN: Changed Y from 80 to 200
            cv.putText(heatmap, text,
                    (center_x - tw // 2, 200),
                    cv.FONT_HERSHEY_SIMPLEX, 1,
                    (255, 255, 255), 2)

        # SCAN to FREEZE Phase
        elif self.state == "SCAN":
            overlay = heatmap.copy()

            # Yellow overlay
            cv.rectangle(overlay, (0, 0), (config.WIDTH, config.HEIGHT), (0, 255, 255), -1)
            cv.addWeighted(overlay, 0.25, heatmap, 0.75, 0, heatmap)

            # FREEZE text
            freeze_text = "FREEZE!"
            (tw, th), _ = cv.getTextSize(freeze_text, cv.FONT_HERSHEY_SIMPLEX, 2, 4)

            # MOVED DOWN: Changed Y from 120 to 300
            cv.putText(heatmap, freeze_text,
                    (center_x - tw // 2, 300),
                    cv.FONT_HERSHEY_SIMPLEX, 2,
                    (0, 0, 255), 4)

            # Instruction
            instruction = "DON'T MOVE"
            (tw2, th2), _ = cv.getTextSize(instruction, cv.FONT_HERSHEY_SIMPLEX, 1, 2)

            # MOVED DOWN: Changed Y from 180 to 360
            cv.putText(heatmap, instruction,
                    (center_x - tw2 // 2, 360),
                    cv.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 255), 2)

class DeflectorBoss(BaseBoss):
    def __init__(self):
        super().__init__("DEFLECTOR", (0, 255, 255)) # Yellow
        self.fireball = None 

        self.health = config.DEFLECTOR_BOSS_HEALTH
        self.max_health = config.DEFLECTOR_BOSS_HEALTH
        
    def update(self, mask, player, current_time, sound, floating_texts):
        if self.state == "IDLE":
            if current_time > self.action_timer:
                self.state = "ATTACK"
                self.action_timer = current_time + config.BOSS_IDLE_TIME
                fx = random.randint(100, config.WIDTH - 100)
                fy = random.randint(100, config.HEIGHT - 100)
                self.fireball = [fx, fy, 40, current_time + config.DEFLECTOR_BOMB_TIME] # x, y, radius, expiration timer
                sound.play_sfx("deflector")
        elif self.state == "ATTACK":
            if self.fireball:
                fx, fy, fr, f_timer = self.fireball
                roi = mask[max(0, fy-fr):fy+fr, max(0, fx-fr):fx+fr]
                if cv.countNonZero(roi) > 150: # Player punched the fireball
                    if not player.overheated:
                        # Success (New Logic): Player has stamina and punched it, so the Boss heals!
                        self.fireball = None
                        sound.play_sfx("hit_p2")
                        
                        # Boss Heals
                        self.health += 1
                        self.health = min(self.health, config.DEFLECTOR_BOSS_HEALTH)
                        floating_texts.append(DamageText("BOSS HEALS!", fx, fy, (0, 255, 0)))
                        
                        self.state = "IDLE"
                        self.action_timer = current_time + config.DEFLECTOR_SUCCESS_COOLDOWN
                    else:
                        # Fail: Player punched it but was overheated, explodes instantly
                        player.health -= config.DEFLECTOR_BOSS_DAMAGE
                        sound.play_sfx("hurt_p1")
                        floating_texts.append(DamageText("EXHAUSTED!", fx, fy-30, (128, 128, 128)))
                        floating_texts.append(DamageText(f"-{config.DEFLECTOR_BOSS_DAMAGE}", fx, fy, (0, 0, 255)))
                        self.fireball = None
                        
                        self.state = "IDLE"
                        self.action_timer = current_time + config.DEFLECTOR_FAIL_COOLDOWN
                elif current_time > f_timer: # Fireball exploded
                    # Fail: Timer ran out
                    sound.play_sfx("deflector_explode")
                    player.health -= config.DEFLECTOR_BOSS_DAMAGE
                    sound.play_sfx("hurt_p1")
                    floating_texts.append(DamageText("EXPLODED!", fx, fy - 30, (0, 0, 255))) # Red text
                    floating_texts.append(DamageText(f"-{config.DEFLECTOR_BOSS_DAMAGE}", fx, fy, (0, 0, 255)))
                    self.fireball = None
                    
                    self.state = "IDLE"
                    self.action_timer = current_time + config.DEFLECTOR_FAIL_COOLDOWN

    def draw_effects(self, heatmap, current_time):
        if self.state == "ATTACK" and self.fireball:
            fx, fy, fr, f_timer = self.fireball
            color = (0, 0, 255) if int(current_time * 10) % 2 == 0 else (0, 255, 255) # Pulsing colors
            cv.circle(heatmap, (fx, fy), fr, color, -1)
            cv.circle(heatmap, (fx, fy), fr + 5, (255, 255, 255), 2)

# Single Player Mode (Boss Fight)
class SingleplayerMode:
    def __init__(self, sound_manager, previous_boss=None):
        self.sound = sound_manager
        
        # Player 1 has access to the entire screen (0 to config.WIDTH)
        self.p1 = Player("PLAYER 1", 0, config.WIDTH, (0, 255, 255))
        
        # Randomly select a Boss strategy
        boss_classes = [LaserBoss, ScannerBoss, DeflectorBoss]
        if previous_boss:
            # Remove the previous boss from boss_classes pool
            boss_classes = [b for b in boss_classes if b.__name__ != previous_boss.__class__.__name__]
            
        self.boss = random.choice(boss_classes)() # Selects the blueprints at random, then creates the boss object in memory

        # Play boss intro sound
        try: 
            pygame.time.delay(200)
            if isinstance(self.boss, LaserBoss): self.sound.play_sfx("laser_boss")
            elif isinstance(self.boss, ScannerBoss): self.sound.play_sfx("scanner_boss")
            elif isinstance(self.boss, DeflectorBoss): self.sound.play_sfx("deflector_boss")
        except:
            pass
        
        self.floating_texts = []
        self.p1_feedback = {"text": "", "color": (0,0,0), "time": 0}

    def set_feedback(self, text, color):
        self.p1_feedback.update({"text": text, "color": color, "time": time.time() + config.FEEDBACK_TEXT_DURATION})

    def update(self, vision, current_time):
        mask = vision['mask']
        self.p1.update_stamina(mask)
        
        # 1. Player Attacks Boss (Using standard check_attack logic)
        d1, text1, accuracy_text = self.p1.check_attack(vision, self.boss, current_time)
        if d1 > 0:
            self.p1.stats['hits'] += 1
            self.p1.stats['damage'] += d1
            is_crit = ("CRIT" in text1)
            if is_crit: 
                self.p1.stats['crits'] += 1
            
            self.sound.play_hit_combo(victim_id=2, is_crit=is_crit) 
            self.set_feedback(text1, (0, 255, 255) if d1 < 10 else (0, 0, 255))
            self.floating_texts.append(DamageText(accuracy_text, self.p1.target[0], self.p1.target[1] - 50, (255, 255, 255)))
            self.floating_texts.append(DamageText(f"-{d1}", self.p1.target[0]+10, self.p1.target[1]-20, (0, 255, 255)))

        elif text1 is not None:
            self.set_feedback(text1, (0, 165, 255)) # Display the specific error in Orange

        # Adaptive difficulty
        total_motion = cv.countNonZero(mask)
        if total_motion > config.ADAPTIVE_HIGH_MOTION: speed_factor = config.ADAPTIVE_SPEED_FAST
        elif total_motion > config.ADAPTIVE_MED_MOTION: speed_factor = config.ADAPTIVE_SPEED_MED
        else: speed_factor = config.ADAPTIVE_SPEED_LOW

        # Shrink timestampe user are schedule to attack
        if hasattr(self.boss, 'action_timer'):
            self.boss.action_timer -= (0.01 * speed_factor)

        # 2. Boss Attacks Player (Using customized strategy logic)
        # ScannerBoss requires the raw visual_motion matrix to calculate hit strength
        if isinstance(self.boss, ScannerBoss):
            self.boss.update(mask, self.p1, current_time, self.sound, self.floating_texts, vision['visual_motion'])
        else:
            self.boss.update(mask, self.p1, current_time, self.sound, self.floating_texts)

    def draw(self, heatmap, current_time):
        self.p1.draw_ui(heatmap)
        self.boss.draw_ui(heatmap)
        self.boss.draw_effects(heatmap, current_time)
        
        for text_obj in self.floating_texts[:]:
            text_obj.update()
            text_obj.draw(heatmap)
            if text_obj.is_expired():
                self.floating_texts.remove(text_obj)
                
        # Player 1 Feedback 
        if current_time < self.p1_feedback['time']:
            text = self.p1_feedback['text']
            (tw, _), _ = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 1.5, 3)
            tx = int(self.p1.target[0]) + (config.TARGET_SIZE // 2) - (tw // 2)
            cv.putText(heatmap, text, (tx, self.p1.target[1] - 20), cv.FONT_HERSHEY_SIMPLEX, 1.5, self.p1_feedback['color'], 3)

    def draw_ui_only(self, heatmap):
        self.p1.draw_ui(heatmap)
        self.boss.draw_ui(heatmap)

    def check_winner(self):
        if self.p1.health <= 0: return f"{self.boss.name} WINS!"
        elif self.boss.health <= 0: return "PLAYER 1 WINS!"
        return None

    def get_stats(self):
        # Pass dummy boss stats to the UI so it doesn't crash
        return self.p1.stats, self.boss.stats
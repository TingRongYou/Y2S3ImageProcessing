import cv2 as cv
import time
import random
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

        p1_total_motion = cv.countNonZero(mask[:, 0:config.MID_X])
        p2_total_motion = cv.countNonZero(mask[:, config.MID_X:config.WIDTH])

        #== Player 1 Attacks ==#
        d1, text1, accuracy_text = self.p1.check_attack(vision, self.p2, current_time)
        if d1 > 0:
            self.p1.stats['hits'] += 1
            self.p1.stats['damage'] += d1
            is_crit = False
            if d1 >= 15:
                self.p1.stats['crits'] += 1
                is_crit = True

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
            is_crit = False
            if d2 >= 15:
                self.p2.stats['crits'] += 1
                is_crit = True

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

        if current_time < self.p1_feedback['time']:
            cv.putText(heatmap, self.p1_feedback['text'], (self.p1.target[0], self.p1.target[1] - 20), cv.FONT_HERSHEY_SIMPLEX, 1.5, self.p1_feedback['color'], 3)

        if current_time < self.p2_feedback['time']:
            cv.putText(heatmap, self.p2_feedback['text'], (self.p2.target[0], self.p2.target[1] - 20), cv.FONT_HERSHEY_SIMPLEX, 1.5, self.p2_feedback['color'], 3)

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
                try: sound.play_sfx("crit_p1")
                except: pass
                
        elif self.state == "FIRE":
            # 1. ALWAYS check for damage FIRST 
            if not self.has_damaged:
                zone_w = config.WIDTH // 3
                x_start = self.zone * zone_w
                zone_mask = mask[:, x_start:x_start + zone_w]
                
                if cv.countNonZero(zone_mask) > 100:
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

            if self.state == "WARN":
                cv.rectangle(heatmap, (x_start, 0), (x_start + zone_w, config.HEIGHT), (0, 165, 255), 4)
                cv.putText(heatmap, "DANGER!", (x_start + 10, config.HEIGHT//2), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 3)

            elif self.state == "FIRE":
                overlay = heatmap.copy()
                cv.rectangle(overlay, (x_start, 0), (x_start + zone_w, config.HEIGHT), (0, 0, 255), -1)
                cv.addWeighted(overlay, 0.5, heatmap, 0.5, 0, heatmap)
                
                cv.rectangle(heatmap, (x_start, 0), (x_start + zone_w, config.HEIGHT), (0, 0, 255), 8)
            
class ScannerBoss(BaseBoss):
    def __init__(self):
        super().__init__("THERMAL EYE", (255, 255, 0)) # Cyan
        self.has_damaged = False
        self.first_run = True
        self.scan_start_time = 0 # Tracks when the freeze actually started
        
    def update(self, mask, player, current_time, sound, floating_texts):
        if self.first_run:
            self.action_timer = current_time + config.BOSS_IDLE_TIME
            self.first_run = False

        if self.state == "IDLE":
            if current_time > self.action_timer:
                self.state = "SCAN"

                scan_duration = random.uniform(1.0, 10.0) # Random freez duration between 1 and 10 seconds
                self.action_timer = current_time + scan_duration

                self.scan_start_time = current_time
                self.has_damaged = False
                try: sound.play_sfx("button")
                except: pass
        elif self.state == "SCAN":
            if current_time > self.action_timer:
                self.state = "IDLE"
                self.action_timer = current_time + config.BOSS_IDLE_TIME + 1.0
            elif not self.has_damaged:
                if current_time > self.scan_start_time + 0.6:
                    motion = cv.countNonZero(mask)
                    freeze_threshold = config.MISS_THRESHOLD * 1.2 # Increase freeze threshold

                    if motion > freeze_threshold:
                        player.health -= 20
                        self.has_damaged = True
                        try: sound.play_sfx("hurt_p1")
                        except: pass
                        floating_texts.append(DamageText("HIGH!", config.MID_X, 200, (0, 0, 255)))
                    elif motion > freeze_threshold * 0.75:
                        player.health -= 10
                        self.has_damaged = True
                        try: sound.play_sfx("hurt_p1")
                        except: pass
                        floating_texts.append(DamageText("WARNING!", config.MID_X, 200, (0, 255, 255)))
                    elif motion > freeze_threshold * 0.4:
                        floating_texts.append(DamageText("STAY STILL!", config.MID_X, 200, (255, 0, 0)))

    def draw_effects(self, heatmap, current_time):
        if self.state == "IDLE" and not self.first_run:
            time_left = max(0.0, self.action_timer - current_time)
            cv.putText(heatmap, f"SCAN IN: {time_left:.1f}s", (config.MID_X - 120, 100), 
                       cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        elif self.state == "SCAN":
            overlay = heatmap.copy()
            cv.rectangle(overlay, (0,0), (config.WIDTH, config.HEIGHT), (255, 255, 0), -1)
            cv.addWeighted(overlay, 0.3, heatmap, 0.7, 0, heatmap)
            cv.putText(heatmap, "FREEZE!", (config.MID_X - 100, 100), 
                       cv.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)

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
        elif self.state == "ATTACK":
            if self.fireball:
                fx, fy, fr, f_timer = self.fireball
                roi = mask[max(0, fy-fr):fy+fr, max(0, fx-fr):fx+fr]
                if cv.countNonZero(roi) > 150: # Player punched the fireball
                    if not player.overheated:
                        # Success: Player has stamina and deflected it
                        self.fireball = None
                        self.state = "IDLE"
                        self.action_timer = current_time + config.DEFLECTOR_SUCCESS_COOLDOWN
                        sound.play_sfx("hit_p2")
                        self.health -= 10 # Deflecting damages the boss!
                        floating_texts.append(DamageText("DEFLECT!", fx, fy, (0, 255, 255)))
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
                    player.health -= config.DEFLECTOR_BOSS_DAMAGE
                    sound.play_sfx("hurt_p1")
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
            
        self.boss = random.choice(boss_classes)()
        
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
            is_crit = d1 >= 15
            if is_crit: self.p1.stats['crits'] += 1
            
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

        if hasattr(self.boss, 'action_timer'):
            self.boss.action_timer -= (0.01 * speed_factor)

        # 2. Boss Attacks Player (Using customized strategy logic)
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
                
        if current_time < self.p1_feedback['time']:
            cv.putText(heatmap, self.p1_feedback['text'], (self.p1.target[0], self.p1.target[1] - 20), cv.FONT_HERSHEY_SIMPLEX, 1.5, self.p1_feedback['color'], 3)

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
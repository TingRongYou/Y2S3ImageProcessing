import cv2 as cv
import time
import random
import config

class Button:
    def __init__(self, text, x, y, w, h, active=True):
        self.text = text
        self.rect = (x, y, w, h)
        self.active = active
        self.base_color = config.BUTTON_COLOR
        self.hover_color = config.BUTTON_HOVER_COLOR
        self.color = self.base_color
        self.last_hit = 0
        
    def draw(self, frame):
        """Draws the button on the screen"""
        x, y, w, h = self.rect
        border_color = (255, 255, 255) if self.active else (100, 100, 100)
        fill_color = self.color if self.active else (60, 60, 60)

        cv.rectangle(frame, (x, y), (x + w, y + h), fill_color, -1)
        cv.rectangle(frame, (x, y), (x + w, y + h), border_color, 2)

        # Dynamic Text Centering
        font = cv.FONT_HERSHEY_SIMPLEX
        scale = 0.6
        thickness = 2
        (tw, th), _ = cv.getTextSize(self.text, font, scale, thickness)
        text_x = x + (w - tw) // 2
        text_y = y + (h + th) // 2
        text_color = config.BUTTON_TEXT_COLOR if self.active else (150, 150, 150)
        
        # Shadow
        cv.putText(frame, self.text, (text_x + 2, text_y + 2), font, scale, (0, 0, 0), thickness + 2)
        cv.putText(frame, self.text, (text_x, text_y), font, scale, text_color, thickness)

    def is_punched(self, mask):
        """Checks if the button is punched based on motion in the button area"""
        if not self.active: return False

        x, y, w, h = self.rect

        # Check motion strictly inside the button area
        roi = mask[y:y+h, x:x+w]
        motion_amount = cv.countNonZero(roi)

        # Visual Feedback (Light up is motion is detected nearby)
        if motion_amount > 200:
            self.color = self.hover_color
        else:
            self.color = self.base_color

        # Trigger action is motion is high enough (A Punch)
        if motion_amount > config.MENU_HIT_THRESHOLD:
            # Simple cooldown so we don't trigger twice instantly
            if time.time() - self.last_hit > 1.0:
                self.last_hit = time.time()
                return True
        return False
    
class DamageText:
    def __init__(self, text, x, y, color=(0, 0, 255)):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.start_time = time.time()
        self.duration = 1.0 # Lasts for 1 second

    def update(self):
        """Moves the text up slightly"""
        # Move up by 2 pixels per frame
        self.y -= 2
        self.x += random.randint(-1, 1)

    def is_expired(self):
        """Checks if the text should disappear"""
        return (time.time() - self.start_time) > self.duration
    
    def draw(self, frame):
        """Draws the damage text on the screen"""
        x, y = int(self.x), int(self.y)

        # Shadow
        cv.putText(frame, self.text, (x + 2, y + 2), cv.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 4)

        # Main
        cv.putText(frame, self.text, (x, y), cv.FONT_HERSHEY_SIMPLEX, 1.2, self.color, 2)
        
class PlayerHUD:
    def __init__(self, name, is_left_side):
        self.name = name
        self.is_left = is_left_side

    def draw(self, frame, health, stamina, overheated):
        """Draws health and stamina bars"""

        # Define positions based on player side
        if self.is_left:
            # Health Bar (Red)
            cv.rectangle(frame, (50, 50), (50 + int(health * 3), 70), (0, 0, 255), -1)
            # Stamina Bar (Yellow)
            cv.rectangle(frame, (50, 80), (50 + int(stamina * 3), 90), (255, 255, 0), -1)

            # Shadow then Main for Name
            cv.putText(frame, self.name, (52, 32), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 3)
            cv.putText(frame, self.name, (50, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            
            if overheated:
                x, y = 50, config.HEIGHT // 2
                cv.putText(frame, "OVERHEAT!", (x + 2, y + 2), cv.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 5)
                cv.putText(frame, "OVERHEAT!", (x, y), cv.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

        else:
            # Health Bar (Red)
            cv.rectangle(frame, (config.WIDTH - 50 - int(health * 3), 50), (config.WIDTH - 50, 70), (0, 0, 255), -1)
            # Stamina Bar (Yellow)
            cv.rectangle(frame, (config.WIDTH - 50 - int(stamina * 3), 80), (config.WIDTH - 50, 90), (255, 255, 0), -1)
            
            # Shadow then Main for Name
            cv.putText(frame, self.name, (config.WIDTH - 198, 32), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 3)
            cv.putText(frame, self.name, (config.WIDTH - 200, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            
            if overheated:
                x, y = config.WIDTH - 300, config.HEIGHT // 2
                cv.putText(frame, "OVERHEAT!", (x + 2, y + 2), cv.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 5)
                cv.putText(frame, "OVERHEAT!", (x, y), cv.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

class MainMenuScreen:
    def __init__(self):
        center_x = config.WIDTH // 2
        self.btn_single = Button("SINGLE PLAYER", center_x - 90, 380, config.BUTTON_WIDTH, config.BUTTON_HEIGHT, active=True)
        self.btn_multi = Button("MULTIPLAYER", center_x - 90, 480, config.BUTTON_WIDTH, config.BUTTON_HEIGHT, active=True)

    def draw(self, frame, info_message=""):
        """Draws the main menu (Background, Title, Buttons, Info)"""
        # 1. Dark Background Overlay
        overlay = frame.copy()
        cv.rectangle(overlay, (0,0), (config.WIDTH, config.HEIGHT), (0, 0, 0), -1)
        cv.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        # 2. Draw Title Text
        cv.putText(frame, "THERMAL", (config.WIDTH//2 - 180, 200), cv.FONT_HERSHEY_SIMPLEX, 2.5, (0, 165, 255), 5)
        cv.putText(frame, "PUNCH", (config.WIDTH//2 - 150, 280), cv.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 255), 5)
        cv.putText(frame, "Punch the button!", (config.WIDTH//2 - 155, 340), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # 3. Draw Buttons
        self.btn_single.draw(frame)
        self.btn_multi.draw(frame) 

        # 4. Draw Info Message
        if info_message:
            cv.putText(frame, info_message, (config.WIDTH//2 - 150, 550), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    def check_input(self, mask):
        """Returns 'SINGLE" or 'MULTI' or None based on punches"""
        if self.btn_single.is_punched(mask):
            return 'SINGLE'
        if self.btn_multi.is_punched(mask):
            return 'MULTI'
        return None

class CountdownDisplay:
    def draw(self, frame, text):
        """Draws the countdown text"""
        font = cv.FONT_HERSHEY_SIMPLEX
        scale = 4.0
        thickness = 5
        color = (0, 255, 255)

        (text_w, text_h), baseline = cv.getTextSize(text, font, scale, thickness)
        x = (config.WIDTH - text_w) // 2
        y = (config.HEIGHT + text_h) // 2

        cv.putText(frame, text, (x, y), font, scale, color, thickness)

class GameOverScreen:
    def __init__(self):
        center_x = config.WIDTH // 2

        self.btn_retry = Button("RETRY", center_x - 180, 500, 160, 60, active=True)
        self.btn_menu = Button("MAIN MENU", center_x + 20, 500, 160, 60, active=True)
    
    def draw(self, frame, winner_text, p1_stats, p2_stats, is_locked=False, is_singleplayer=False):
        """Draws the game over screen with winner and stats. is_locked determines if buttons work"""

        # 1. Update button state
        # If locked, button are inactive
        self.btn_retry.active = not is_locked
        self.btn_menu.active = not is_locked

        # 2. Dark Overlay
        overlay = frame.copy()
        cv.rectangle(overlay, (0,0), (config.WIDTH, config.HEIGHT), (0,0,0), -1)
        cv.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # 3. Winner Text
        cv.putText(frame, winner_text, (config.WIDTH//2 - 250, 100), 
                   cv.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)

        # 4. Stats Columns
        # Column Headers
        if is_singleplayer:
            # Single Player Layout (Centered)
            cv.putText(frame, "PLAYER 1", (config.WIDTH//2 - 80, 200), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            self._draw_single_stat_line(frame, "Hits",   p1_stats['hits'],   230)
            self._draw_single_stat_line(frame, "Crits",  p1_stats['crits'],  270)
            self._draw_single_stat_line(frame, "Misses", p1_stats['misses'], 310)
            self._draw_single_stat_line(frame, "Damage", p1_stats['damage'], 350)
            self._draw_single_stat_line(frame, "Overheats", p1_stats['overheats'], 390)
            self._draw_single_stat_line(frame, "Motion", p1_stats['energy'], 430)
            
        else:
            # Multiplayer Layout (Two Columns)
            cv.putText(frame, "PLAYER 1", (150, 200), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv.putText(frame, "PLAYER 2", (550, 200), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

            self._draw_stat_line(frame, "Hits",   p1_stats['hits'],   p2_stats['hits'],   230)
            self._draw_stat_line(frame, "Crits",  p1_stats['crits'],  p2_stats['crits'],  270)
            self._draw_stat_line(frame, "Misses", p1_stats['misses'], p2_stats['misses'], 310)
            self._draw_stat_line(frame, "Damage", p1_stats['damage'], p2_stats['damage'], 350)
            self._draw_stat_line(frame, "Overheats",  p1_stats['overheats'], p2_stats['overheats'], 390)

            e1 = f"{p1_stats['energy']}"
            e2 = f"{p2_stats['energy']}"
            self._draw_stat_line(frame, "Motion", e1, e2, 430)

        # 5. Draw Buttons
        self.btn_retry.rect = (config.WIDTH//2 - 180, 520, 160, 60) 
        self.btn_menu.rect  = (config.WIDTH//2 + 20,  520, 160, 60)
        self.btn_retry.draw(frame)
        self.btn_menu.draw(frame)

        # 6. Show "Loading" text if locked
        if is_locked:
            cv.putText(frame, "COOLDOWN...", (config.WIDTH//2 - 70, 490), cv.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)

    def _draw_single_stat_line(self, frame, label, val1, y):
        """Draws a row of stats perfectly centered for single player mode"""
        font = cv.FONT_HERSHEY_SIMPLEX
        scale = 0.8
        thick = 2
        color_text = (255, 255, 255)
        color_label = (200, 200, 200)

        # Draw Label (Offset slightly left of center)
        (lw, lh), _ = cv.getTextSize(label, font, scale, thick)
        label_x = (config.WIDTH // 2) - lw - 30
        cv.putText(frame, label, (label_x, y), font, scale, color_label, thick)

        # Draw Player 1 Value (Offset slightly right of center)
        v1_str = str(val1)
        v1_x = (config.WIDTH // 2) + 30
        cv.putText(frame, v1_str, (v1_x, y), font, scale, color_text, thick)

    def _draw_stat_line(self, frame, label, val1, val2, y):
        """Draws a row of stats: Val1  Label  Val2"""
        font = cv.FONT_HERSHEY_SIMPLEX
        scale = 0.8
        thick = 2
        color_text = (255, 255, 255)
        color_label = (200, 200, 200)

        # 1. Draw Center Label (Already Centered)
        (lw, lh), _ = cv.getTextSize(label, font, scale, thick)
        label_x = (config.WIDTH - lw) // 2
        cv.putText(frame, label, (label_x, y), font, scale, color_label, thick)

        # 2. Draw Player 1 Value (Centered in Left Half)
        # Left Half Center is at X = WIDTH // 4 (approx 200)
        v1_str = str(val1)
        (v1w, v1h), _ = cv.getTextSize(v1_str, font, scale, thick)
        v1_x = (config.WIDTH // 4) - (v1w // 2) # Perfectly center in P1's zone
        cv.putText(frame, v1_str, (v1_x, y), font, scale, color_text, thick)

        # 3. Draw Player 2 Value (Centered in Right Half)
        # Right Half Center is at X = 3 * WIDTH // 4 (approx 600)
        v2_str = str(val2)
        (v2w, v2h), _ = cv.getTextSize(v2_str, font, scale, thick)
        v2_x = (3 * config.WIDTH // 4) - (v2w // 2) # Perfectly center in P2's zone
        cv.putText(frame, v2_str, (v2_x, y), font, scale, color_text, thick)

    def check_input(self, mask):
        """Returns 'RETRY' or 'MENU' if buttons are punched"""
        if self.btn_retry.is_punched(mask): return "RETRY"
        if self.btn_menu.is_punched(mask):  return "MENU"
        return None
    
class PauseScreen:
    def __init__(self):
        center_x = config.WIDTH // 2
        self.btn_resume = Button("RESUME", center_x - 80, 200, 160, 60, active=True)
        self.btn_retry = Button("RETRY", center_x - 80, 300, 160, 60, active=True)
        self.btn_menu = Button("MAIN MENU", center_x - 80, 400, 160, 60, active=True)

    def draw(self, frame):
        """Draws the dark overlay and pause buttons"""
        # 1. Dark Overlay
        overlay = frame.copy()
        cv.rectangle(overlay, (0,0), (config.WIDTH, config.HEIGHT), (0,0,0), -1)
        cv.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # 2. Title Text
        cv.putText(frame, "PAUSED", (config.WIDTH//2 - 120, 120), cv.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)

        # 3. Buttons
        self.btn_resume.draw(frame)
        self.btn_retry.draw(frame)
        self.btn_menu.draw(frame)

    def check_input(self, mask):
        """Returns the action if a button is physically punched"""
        if self.btn_resume.is_punched(mask): return "RESUME"
        if self.btn_retry.is_punched(mask):  return "RESTART"
        if self.btn_menu.is_punched(mask):   return "MENU"
        return None
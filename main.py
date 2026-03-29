import cv2 as cv
import time
import os
import config
from player import Player
from ui import MainMenuScreen, CountdownDisplay, GameOverScreen, PauseScreen, Button
from sound import SoundManager
from modes import MultiplayerMode, SingleplayerMode
from vision import VisionPipeline
from debugger import PerformanceDebugger

#== Initialization ==#
fullscreen = False
cv.namedWindow('Thermal Punch', cv.WINDOW_NORMAL)
cap = cv.VideoCapture(0)
time.sleep(1) 

# Create Audio System
sound = SoundManager()
sound.play_music('menu')

# Create UI Screens
menu_screen = MainMenuScreen()
game_over_screen = GameOverScreen()
countdown_display = CountdownDisplay()
pause_screen = PauseScreen()

# Time Tracking Variables
pause_start_time = 0
total_paused_time = 0

# Create Image Processing Pipeline
pipeline = VisionPipeline()
debugger = PerformanceDebugger()

# Game Variables
info_message = ""
info_timer = 0
game_state = config.STATE_MENU 
start_time = 0
game_over_start_time = 0
menu_lock_time = 0
winner_text = ""
current_mode = None # Hold active gamemode (Multiplayer or Singleplayer)
last_p_press = 0
show_heatmap = True

ret, frame = cap.read()
if not ret: exit()
frame = cv.resize(frame, (config.WIDTH, config.HEIGHT))
frame = cv.flip(frame, 1)
prev_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)


#== Main Loop ==#
while True:
    ret, frame = cap.read()
    if not ret: break

    key = cv.waitKey(1) & 0xFF

    # 1. Prepare Frame
    frame = cv.flip(frame, 1)
    frame = cv.resize (frame, (config.WIDTH, config.HEIGHT))
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    # 2. Image Processing
    mask = pipeline.process_frame(gray)

    # Visualization Base
    visual_motion = cv.absdiff(gray, prev_gray) # Keep absdiff purely for the visual heatmap as it creates cool fading thermal effect
    heatmap = cv.applyColorMap(visual_motion * 5, cv.COLORMAP_JET)

    if config.WARMUP_FRAMES > 0:
        config.WARMUP_FRAMES -= 1
        # Show calibration text
        overlay = heatmap.copy()
        cv.rectangle(overlay, (0,0), (config.WIDTH, config.HEIGHT), (0,0,0), -1)
        cv.addWeighted(overlay, 0.7, heatmap, 0.3, 0, heatmap)

        cv.putText(heatmap, " CALIBRATING CAMERA...", (config.WIDTH//2 - 190, config.HEIGHT//2), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv.putText(heatmap, " PLEASE STAND STILL...", (config.WIDTH//2 - 140, config.HEIGHT//2 + 50), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv.imshow('Thermal Punch', heatmap) 
        prev_gray = gray

        if key == ord('q'):
            break
        continue

    #== State 0: Menu ==#
    if game_state == config.STATE_MENU:
        msg_to_show = info_message if time.time() < info_timer else ""

        # Draw Menu
        menu_screen.draw(heatmap, msg_to_show)
        
        if time.time() > menu_lock_time:
            # Check Input
            action = menu_screen.check_input(mask)

            if key == ord('1'): action = "SINGLE"
            elif key == ord('2'): action = "MULTI"
        else:
            action = None

        if action == "MULTI":
            sound.play_sfx("button")
            current_mode = MultiplayerMode(sound)
            game_state = config.STATE_COUNTDOWN
            sound.stop_music()
            start_time = time.time()
        elif action == "SINGLE":
            sound.play_sfx("button")
            current_mode = SingleplayerMode(sound)
            game_state = config.STATE_COUNTDOWN
            sound.stop_music()
            start_time = time.time()

    #== State 1: Countdown ==#
    elif game_state == config.STATE_COUNTDOWN:
        current_mode.draw_ui_only(heatmap)

        # Calculate which text to show
        elapsed = time.time() - start_time

        if elapsed < 1.0:
            count_text = "3"
        elif elapsed < 2.0:
            count_text = "2"
        elif elapsed < 3.0:
            count_text = "1"
        else: 
            count_text = "FIGHT!"

        countdown_display.draw(heatmap, count_text)

        if elapsed > 3.5:
            game_state = config.STATE_PLAYING
            sound.play_music('fight')

    #== State 2: Playing ==#
    elif game_state == config.STATE_PLAYING:
       current_t = time.time() - total_paused_time

       # Calculate what percentage of the screen is currently moving
       mog_density = (cv.countNonZero(mask) / (config.WIDTH * config.HEIGHT)) * 100

       mode_name = "SINGLE" if isinstance(current_mode, SingleplayerMode) else "MULTI"
       
       # 1. Update Match Logic
       vision = {'mask': mask, 
                 'gray': gray, 
                 'prev_gray': prev_gray, 
                 'visual_motion': visual_motion, 
                 'debugger': debugger, 
                 'proc_time': pipeline.last_proc_time,
                 'mog_density': mog_density,
                 'mode': mode_name}
       current_mode.update(vision, current_t)

       # 2. Draw the match visuals
       current_mode.draw(heatmap, current_t)

       # 3. Check for a Winner
       winner = current_mode.check_winner()
       if winner:
           game_state = config.STATE_GAMEOVER
           winner_text = winner
           game_over_start_time = time.time()
           sound.play_music('menu')

    #== State 4: Paused ==#
    elif game_state == config.STATE_PAUSED:
        # Calculate exact time paused
        frozen_t = pause_start_time - total_paused_time

        current_mode.draw(heatmap, frozen_t) # Draw the frozen game in background

        # Draw Pause UI over it
        pause_screen.draw(heatmap)

        if time.time() - pause_start_time > 1.0:

            # 1. Check physical Button Punches
            action = pause_screen.check_input(mask)

            # 2. Check Keyboard Inputs
            if key == ord('r'): action = "RETRY"
            elif key == ord('m'): action = "MENU"

            # 3. Execute actions
            if action == "RESUME":
                sound.play_sfx("button")
                total_paused_time += time.time() - pause_start_time # Record time spent for pausing
                game_state = config.STATE_PLAYING
                sound.unpause_music()
            elif action == "RETRY":
                sound.play_sfx("button")
                if isinstance(current_mode, SingleplayerMode):
                    current_mode = SingleplayerMode(sound, previous_boss=current_mode.boss) # Pass the current boss to avoid repetition
                else: 
                    current_mode = MultiplayerMode(sound)
                total_paused_time = 0
                start_time = time.time() 
                game_state = config.STATE_COUNTDOWN
                sound.stop_music()
            elif action == "MENU":
                sound.play_sfx("button")
                current_mode = None
                total_paused_time = 0
                game_state = config.STATE_MENU
                menu_lock_time = time.time() + 1.0
                sound.stop_music()
                sound.play_music('menu')

    #== State 3: Game Over ==#
    elif game_state == config.STATE_GAMEOVER:
        # Calcuate time in game over screen
        time_since_over = time.time() - game_over_start_time

        # Determine if is locked (first 3 seconds)
        is_locked = time_since_over < config.GAMEOVER_COOLDOWN

        # Fetch stats from the mode that just ended
        p1_stats, p2_stats = current_mode.get_stats()

        # Draw Scorecard
        game_over_screen.draw(heatmap, winner_text, p1_stats, p2_stats, is_locked) 

        if not is_locked:
            # Check Button Inputs
            action = game_over_screen.check_input(mask)

            if key == ord('r'): action = "RETRY"
            elif key == ord('m'): action = "MENU"

            if action == "RETRY":
                sound.play_sfx("button")
                if isinstance(current_mode, SingleplayerMode):
                    current_mode = SingleplayerMode(sound, previous_boss=current_mode.boss) # Pass the current boss to avoid repetition
                else:
                    current_mode = MultiplayerMode(sound)
                game_state = config.STATE_COUNTDOWN
                sound.stop_music()
                start_time = time.time()
            elif action == "MENU":
                sound.play_sfx("button")
                current_mode = None
                game_state = config.STATE_MENU
                menu_lock_time = time.time() + 1.0 # Lock menu for 1s

    if show_heatmap:
        display_frame = heatmap.copy()
    else:
        # Draw cheat sheet and debugger on the raw frame as well
        display_frame = frame.copy()
        cv.putText(display_frame, "NORMAL MODE", (config.WIDTH // 2 - 100, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    cheat_sheet = "KEYS: [1]P | [2]P | [Q]uit | [F]ull | [D]ebug | [S]creenshot | [C]alibrate | [P]ause | [R]etry | [M]enu | [H]eatmap"
    cv.putText(display_frame, cheat_sheet, (10, config.HEIGHT - 15), cv.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 2)
    cv.putText(display_frame, cheat_sheet, (10, config.HEIGHT - 15), cv.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    debugger.draw_vision_pipeline(display_frame, frame, gray, mask, visual_motion)
    debugger.draw_thermal_debug(display_frame, visual_motion)

    cv.imshow('Thermal Punch', display_frame)
    prev_gray = gray

    # Key Controls
    if key == ord('q'):
        break
    elif key == ord('h'):
        show_heatmap = not show_heatmap
    elif key == ord('f'):
        fullscreen = not fullscreen
        if fullscreen:
            cv.setWindowProperty('Thermal Punch', cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
        else:
            cv.setWindowProperty('Thermal Punch', cv.WND_PROP_FULLSCREEN, cv.WINDOW_NORMAL)    
    elif key == ord('d'):
        config.DEBUG_MODE = not config.DEBUG_MODE
    elif key == ord('s'):
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        # Save Images
        timestamp = time.strftime("%H%M%S")
        heatmap_path = os.path.join("screenshots", f"report_heatmap_{timestamp}.png")
        mask_path = os.path.join("screenshots", f"report_mask_{timestamp}.png")

        cv.imwrite(heatmap_path, heatmap)
        cv.imwrite(mask_path, mask)

        print(f"Screenshots successfully saved! ({heatmap_path})")
        sound.play_sfx("screenshot")
    elif key == ord('c'):
        # Reset Camera Memory Instantly (MOG2 Background)
        pipeline = VisionPipeline()
        config.WARMUP_FRAMES = 30 # Trigger calibration screen to absorb the MOG2 white flash!
        print("Camera background memory recalibrated!")
    elif key == ord('p') or key == 27: # ESC key
        if time.time() - last_p_press > 0.5: # Prevent rapid toggling if key is held down
            last_p_press = time.time() # Reset Cooldown
            if game_state == config.STATE_PLAYING:
                sound.play_sfx("button")
                game_state = config.STATE_PAUSED
                pause_start_time = time.time()
                sound.pause_music()
            elif game_state == config.STATE_PAUSED:
                sound.play_sfx("button")
                total_paused_time += time.time() - pause_start_time
                game_state = config.STATE_PLAYING
                sound.unpause_music()

cap.release()
cv.destroyAllWindows()
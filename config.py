# Config file to store all game settings and costants for easy tweaking and balancing

#== WINDOW ==#
WIDTH, HEIGHT = 800, 600 # Basic resolution for window
MID_X = WIDTH // 2 # Middle line to divide players

#== UI & TIMERS ==#
FEEDBACK_TEXT_DURATION = 2.0 # How long the text stays on screen
WARMUP_FRAMES = 60 # Frames to skip when camera starts

#== DEBUG MODE ==#
DEBUG_MODE = False # Press 'd' in game to toggle

#== GAME STATES ==#
STATE_MENU = 0
STATE_COUNTDOWN = 1
STATE_PLAYING = 2
STATE_GAMEOVER = 3
STATE_PAUSED = 4

#== HEALTH & STAMINA ==#
MAX_HEALTH = 100
MAX_STAMINA = 100
STAMINA_DRAIN = 0.1    # Stamina drained per punch
STAMINA_RECOVERY = 2.0 # Stamina recovered per frame
OVERHEAT_PENALTY = 3.0 # Freeze duration in seconds when overheated

#== BOSS SETTINGS ==#
BASE_BOSS_HEALTH = 30
LASER_BOSS_HEALTH = 50 # Can directly overwrite specific boss health, easier to tweak individual bosses for balancing
SCANNER_BOSS_HEALTH = 70
DEFLECTOR_BOSS_HEALTH = 70
LASER_BOSS_DAMAGE = 15
SCANNER_BOSS_DAMAGE = 20
DEFLECTOR_BOSS_DAMAGE = 15

#== BOSS TIMERS ==#
BOSS_IDLE_TIME = 2.0 # How long the boss waits between attacks
SCANNER_SCAN_TIME = 3.0 # How long the freeze scan lasts
DEFLECTOR_BOMB_TIME = 1.5 # How fasts the fireball explodes
DEFLECTOR_SUCCESS_COOLDOWN = 1.0 # Deflector attacks faster if player deflects
DEFLECTOR_FAIL_COOLDOWN = 2.0 # Gives player time to recover after getting hits

#== PUNCH SENSITIVITY ==#
#Player 1 (Left)
P1_CRIT_THRESHOLD = 1800   # Motion threshold for critical hit
P1_NORMAL_THRESHOLD = 1000 # Motion threshold for normal hit
#Player 2 (Right) - P1 is easier to get crit sincd most webcam scan from top-left to bottom-righ, hence we give P2 slight advantages to balance the game
P2_CRIT_THRESHOLD = 1500   # Motion threshold for critical hit
P2_NORMAL_THRESHOLD = 600 # Motion threshold for normal hit

MISS_THRESHOLD = 1000

#== COMBAT SETTINGS ==#
NORMAL_DAMAGE = 5
CRIT_DAMAGE = 15
PUNCH_COOLDOWN = 0.4

#== TARGET SETTINGS ==#
TARGET_SIZE = 90
MIN_DISTANCE = 150 # Minimum distance between targets and targets before

#-- BUTTON SETTINGS ==#
BUTTON_WIDTH = 160
BUTTON_HEIGHT = 60
BUTTON_COLOR = (50, 50, 50)
BUTTON_HOVER_COLOR = (150, 150, 150) # Dark Grey
BUTTON_TEXT_COLOR = (255, 255, 255) # White
MENU_HIT_THRESHOLD = 2000 # How hard to hit the button 
GAMEOVER_COOLDOWN = 5.0   # Seconds to wait before button active

#== ADAPTIVE DIFFICULTY SETTINGS ==#
ADAPTIVE_HIGH_MOTION = 3000
ADAPTIVE_MED_MOTION = 1500
ADAPTIVE_SPEED_FAST = 1.5
ADAPTIVE_SPEED_MED = 1.2
ADAPTIVE_SPEED_LOW = 0.8

#== ACCURACY SETTINGS ==#
ACCURACY_PERFECT = 0.7
ACCURACY_GOOD = 0.4
ACCURACY_BASE_MULT = 0.6
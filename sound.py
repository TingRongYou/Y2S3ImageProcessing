import pygame
import os
import random

class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        
        # Dictionary to store Sound Effect objects
        self.sfx = {}
        
        # === 1. Load Sound Effects (SFX) ===
        # Loading MP3s as SFX is supported in newer Pygame versions
        # Player / Basic SFX
        self.load_sfx("hit_p1",  "assets/sfx/hit_p1.mp3")  # Impact when P1 is hit
        self.load_sfx("hit_p2",  "assets/sfx/hit_p2.mp3")  # Impact when P2 is hit
        self.load_sfx("crit_p1", "assets/sfx/crit_p1.mp3") # Crit Impact on P1
        self.load_sfx("crit_p2", "assets/sfx/crit_p2.mp3") # Crit Impact on P2
        self.load_sfx("hurt_p1", "assets/sfx/hurt_p1.mp3") # P1 Grunt
        self.load_sfx("hurt_p2", "assets/sfx/hurt_p2.mp3") # P2 Grunt
        self.load_sfx("button",  "assets/sfx/button.mp3")  # Menu button hit
        self.load_sfx("screenshot", "assets/sfx/screenshot.mp3") # Screenshot sound

        # Boss / Gameplay SFX
        self.load_sfx("laser", "assets/sfx/laser.mp3")
        self.load_sfx("laser_boss", "assets/sfx/laser_boss.mp3")

        self.load_sfx("freeze", "assets/sfx/freeze.mp3")
        self.load_sfx("scanner_boss", "assets/sfx/scanner_boss.mp3")

        self.load_sfx("deflector", "assets/sfx/deflector.mp3")
        self.load_sfx("deflector_boss", "assets/sfx/deflector_boss.mp3")
        self.load_sfx("deflector_explode", "assets/sfx/deflector_explode.mp3")

        
        # === 2. Define Music Tracks ===
        self.menu_bgm = "assets/bgm/bgm_menu.mp3"
        self.fight_bgms = [
            "assets/bgm/bgm_fight_1.mp3",
            "assets/bgm/bgm_fight_2.mp3",
            "assets/bgm/bgm_fight_3.mp3"
        ]
        
        self.current_track = None
        
    def load_sfx(self, name, path):
        """Loads a sound effect and stores it in the sfx dictionary"""
        if os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
                # Custom Volume Tuning
                if name in ["deflector_explode"]:
                    sound.set_volume(0.7) # Louder explosion
                elif name in ["laser", "laser_boss"]:
                    sound.set_volume(0.6)
                else:
                    sound.set_volume(0.5)
                self.sfx[name] = sound
            except Exception as e:
                print(f"Error Loading {name}: {e}")
        else:
            print(f"WARNING: File Not Found: {path}")

    def play_sfx(self, name):
        """Plays a sound effect """
        if name in self.sfx:
            self.sfx[name].play()

    def play_hit_combo(self, victim_id, is_crit):
        """Plays Impact + Grunt for hits"""
        suffix = f"_p{victim_id}" # "_p1" or "_p2"
        
        # 1. Play Voice/Grunt (The 'Hurt' sound)
        self.play_sfx(f"hurt{suffix}")
        
        # 2. Play Impact (Crit or Normal Hit)
        if is_crit:
            self.play_sfx(f"crit{suffix}")
        else:
            self.play_sfx(f"hit{suffix}")

    def play_music(self, track_type):
        """track_type: Menu or Fight"""
        target_track = ""

        if track_type == 'menu':
            target_track = self.menu_bgm
        elif track_type == 'fight':
            target_track = random.choice(self.fight_bgms)

        # Only switch if it's a new track (or if we are restarting fight music)
        if os.path.exists(target_track):
            pygame.mixer.music.load(target_track)
            pygame.mixer.music.set_volume(0.4) # Background volume
            pygame.mixer.music.play(-1) # Loop forever
            self.current_track = track_type

    def pause_music(self):
        """Pauses the currently playing background music"""
        pygame.mixer.music.pause()

    def unpause_music(self):
        """Resumes the background music from where it stopped"""
        pygame.mixer.music.unpause()

    def stop_music(self):
        """Stops any currently playing music"""
        pygame.mixer.music.stop()
        self.current_track = None
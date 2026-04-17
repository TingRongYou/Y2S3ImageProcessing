# 🥊 Thermal Punch: Real-Time Motion Intensity Visualisation Using Pseudocolour Mapping

## Overview
**Thermal Punch** is a hardware-agnostic, computer vision-based Exergame (Exercise + Gaming) that translates real-world physical movement into interactive digital inputs. Built entirely in Python for our Year 2 Semester 3 Image Processing course, the application provides a cost-effective, contactless fitness solution. 

By utilizing a standard laptop webcam, the system calculates the intensity and velocity of a user's shadow-boxing movements in real-time, overlaying a dynamic "thermal" heatmap directly onto the video feed to provide immediate, gamified visual feedback on physical exertion.

---

## ⚙️ Computer Vision Techniques & Applications
Rather than relying on computationally heavy AI skeletal tracking or expensive VR hardware, this project utilizes a hyper-efficient, non-learning-based "Dual-Track" computer vision architecture.

* **Gaussian Mixture-Based Background Subtraction (MOG2)**
  * **Application:** Used to isolate the player from the static room environment. By maintaining a 500-frame historical memory, it generates a binary motion mask that effectively ignores static background objects and shadows to ensure accurate hit-detection.
* **Morphological Filtering (Opening)**
  * **Application:** Applied immediately after background subtraction to clean the binary mask. By eroding and dilating pixels, it removes "salt-and-pepper" noise and artifacts caused by webcam grain or lighting shifts, preventing false-positive punches.
* **Temporal Frame Differencing (`cv2.absdiff`)**
  * **Application:** Calculates the absolute pixel difference between consecutive grayscale frames. This extracts raw motion energy and acceleration, allowing the system to distinguish between a weak, slow movement and a high-intensity, intentional punch.
* **Pseudocolour Mapping (JET Colourmap)**
  * **Application:** Transforms the raw, invisible motion intensity data into a vibrant visual spectrum. Areas with zero motion render as deep blue, while high-velocity punches render as bright red. This provides intuitive, real-time thermal-style feedback to the player.
* **Dense Optical Flow (Farneback)**
  * **Application:** Computes the directional displacement of pixels between frames. The system uses a pixel-voting heuristic to classify the trajectory of the player's movement (Up, Left, Right) to validate directional target hits.

---

## 🎮 Game Modes

### 👥 Multiplayer Mode
A split-screen competitive mode where Player 1 (Left) and Player 2 (Right) face off. Players must physically punch directional targets that appear on their side of the screen. Damage is dynamically scaled based on the physical intensity (speed/energy) and accuracy of the punch. Stamina bar is designed for both player to prevents from spamming motion on the hitboxes.

### 🤖 Singleplayer Boss Fights
A survival mode where Player 1 faces off against difficulty adaptive bosses. The game dynamically adjusts its speed based on the player's overall motion output. Each boss requires a different physical strategy to defeat:

* 🔴 **MECHA-LASER**
  * **Ability:** Analyzes the screen to find the zone with the highest motion density and fires a devastating laser column.
  * **How to Beat:** Watch for the orange "DANGER!" warning box. You must physically move or lean out of that specific vertical zone before the laser fires to dodge the attack, then counter-attack.
* 👁️ **THERMAL EYE (Scanner Boss)**
  * **Ability:** Randomly initiates a system-wide scan, culminating in a "FREEZE!" command. 
  * **How to Beat:** When the screen flashes and instructs you not to move, you must hold completely still. The boss measures raw motion strength; slight twitches trigger warnings, but high movement will result in massive damage. 
* 💣 **DEFLECTOR**
  * **Ability:** Spawns explosive thermal fireballs randomly across the screen with a ticking expiration timer.
  * **How to Beat:** You must physically punch the fireball's location to deflect it back to avoid explosion damage. However, if your stamina is overheated from swinging too wildly, you will be "EXHAUSTED" and take damage instead. To prevent spamming hit on deflector only, the deflector is designed to be able to heal the deflector boss.

---

## 🏆 Project Results & Objectives Achieved
Based on our experimental analysis and system telemetry, the project successfully achieved its core objectives:
1. **Hyper-Efficient Real-Time Tracking:** The dual-track pipeline achieved a mean latency of **2.51 ms** per frame, operating 13 times faster than the 33.3 ms requirement for 30 FPS, ensuring zero lag on standard hardware.
2. **Accurate Visual Feedback:** Achieved a perfect negative correlation ($r = -1.0$) between motion intensity and Hue values, validating that the JET pseudocolour mapping is strictly monotonic and mathematically accurate.
3. **Gamified Physical Exertion:** Telemetry from 773 registered interactions proved the system successfully filtered ambient room noise (threshold 25) while demanding a high average physical exertion (intensity 114.97) from the player, proving its viability as a fitness application.

---

## 📦 Download & Play (Releases)
You do not need to install Python or any code dependencies to play the game! We have compiled the entire project into a standalone, ready-to-play executable.

1. Navigate to the **[Releases](../../releases)** section on the right side of this GitHub page.
2. Download the `Thermal Punch v1.0.zip` file.
3. Extract the folder to your Desktop.
4. Double-click **`Thermal Punch.exe`** (look for the blue boxing glove icon) to start playing!

---

## 🛠️ For Developers (Source Code)
If you wish to run the game from the source code or modify the computer vision pipeline:

### Prerequisites
* Python 3.8+
* A working webcam

### Installation
1. Clone the repository:
   ```bash
   git clone [https://github.com/TingRongYou/Y2S3ImageProcessing.git](https://github.com/TingRongYou/Y2S3ImageProcessing.git)
   cd Y2S3ImageProcessing
   ```
2. Install the required dependencies:
   ```bash
   pip install opencv-python numpy pygame
   ```
3. Run the Application:
   ```bash
   python main.py
   ```

---

## 👨‍💻 Author
**Ting Rong You & Yong Chong Xin & Tan Hong You** *| Final-Year Software Engineering (Honours) Student @ TARUMT*
* **LinkedIn:** [Connect with me here](https://linkedin.com/in/ting-rong-you-945aab3b6)

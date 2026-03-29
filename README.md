# 🥊 Thermal Punch: Real-Time Motion Tracking Pipeline

## Overview
**Thermal Punch** is a computer vision application that translates real-world physical movement into interactive digital inputs. Built entirely in Python as an advanced Image Processing project, the system utilizes a webcam feed to detect, isolate, and calculate the directional velocity of a user's punches in real-time. 

Beyond the core image processing algorithms, this project is architected with a strict adherence to the Software Development Life Cycle (SDLC) and features a dedicated Quality Assurance pipeline to ensure accurate, artifact-free detection.

## ⚙️ System Architecture & Computer Vision
The pipeline processes live video frames through a multi-stage filtering system:
* **Background Subtraction:** Utilizes OpenCV's Gaussian Mixture-Based Background/Foreground Segmentation (`cv2.createBackgroundSubtractorMOG2`) to isolate the user from static room environments.
* **Motion Tracking:** Implements Dense Optical Flow (Farneback algorithm) to calculate the exact magnitude and direction of the isolated movement.
* **State Management:** The backend logic is structured using Object-Oriented Programming (OOP), specifically leveraging the **State Pattern** to seamlessly transition the game loop between "Idle," "Attack," and "Cooldown" phases without frame-drop.

## 🧪 Quality Assurance & Automated Testing
As an engineering priority, this system relies heavily on automated testing to prevent "ghost touches" and false-positive punch validations (e.g., pulling a hand back triggering a forward punch).
* **Automated CI/CD:** A comprehensive `pytest` suite is integrated to test the mathematical thresholds of the tracking modules.
* **Threshold Tuning:** Detection logic is fortified by a "Supermajority Floor," ensuring noise artifacts do not trigger false game states.
* **SDLC Tracking:** The entire development lifecycle, from bug tracking to feature implementation, is managed via an Agile Kanban board. 

📊 **[View the Live QA & Development Project Board Here](https://github.com/users/TingRongYou/projects/1/views/1)**

## 🚀 Getting Started

### Prerequisites
* Python 3.8+
* A working webcam
* Git

### Installation
1. Clone the repository to your local machine:
   ```bash
   git clone [https://github.com/YourUsername/Thermal_Punch.git](https://github.com/YourUsername/Thermal_Punch.git)
   ```
2. Navigate to the project directory:
   ```bash
   cd Thermal_Punch
   ```
3. Install the required dependencies:
   ```bash
   pip install opencv-python numpy pygame pytest
   ```

### Running the Application
To start the live computer vision tracking application:
```bash
python main.py
```

### Running the Test Suite
To execute the automated Quality Assurance tests:
```bash
pytest tests/
```

---

## 👨‍💻 Author
**Ting Rong You & Yong Chong Xin & Tan Hong You** *| Final-Year Software Engineering (Honours) Student @ TARUMT*
* Aspiring QA Engineer & UI/UX Designer
* **LinkedIn:** [Connect with me here](https://linkedin.com/in/ting-rong-you-945aab3b6)

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

import time
import cv2
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)


class GestureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hand Gesture Detection")

        self.label = tk.Label(root)
        self.label.pack()

        self.gesture_label = tk.Label(root, text="Gesture: None", font=("Arial", 16))
        self.gesture_label.pack(pady=5)

        self.start_btn = tk.Button(root, text="Start", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=10, pady=10)

        self.stop_btn = tk.Button(root, text="Stop", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        self.cap = None
        self.running = False

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1)
        self.mp_draw = mp.solutions.drawing_utils

    def start(self):
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.update_frame()  # Start the frame update loop


    def stop(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.label.config(image='')


    def count_fingers(self, hand_landmarks):
        tip_ids = [4, 8, 12, 16, 20]
        fingers = []

        # Thumb
        if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[tip_ids[0] - 1].x:
            fingers.append(1)
        else:
            fingers.append(0)

        # Fingers (index to pinky)
        for id in range(1, 5):
            if hand_landmarks.landmark[tip_ids[id]].y < hand_landmarks.landmark[tip_ids[id] - 2].y:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers.count(1)
    
    def set_volume_by_finger_count(self, count):
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        # Volume range: -65.25 to 0.0 dB
        target_volume = count / 5.0  # 0.0 to 1.0
        volume.SetMasterVolumeLevelScalar(target_volume, None)


    def update_frame(self):
        if not self.running or not self.cap:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.root.after(10, self.update_frame)
            return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        gesture_text = "None"

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                finger_count = self.count_fingers(hand_landmarks)
                gesture_text = f"{finger_count} Finger(s)"
                self.set_volume_by_finger_count(finger_count)

        self.gesture_label.config(text=f"Gesture: {gesture_text}")

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        imgtk = ImageTk.PhotoImage(image=img)
        self.label.imgtk = imgtk
        self.label.configure(image=imgtk)

        # Schedule next frame update after ~33ms (30 FPS)
        self.root.after(33, self.update_frame)


        


# Launch GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = GestureApp(root)
    root.mainloop()




import cv2
import mediapipe as mp
import numpy as np
import math
import socket
import struct
import time

# ----------------------------
# UDP Setup
# ----------------------------

ESP32_IP = "10.243.104.152"   # CHANGE to your ESP32 IP
ESP32_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ----------------------------
# Utility Functions
# ----------------------------

def map_value(val, in_min, in_max, out_min, out_max):
    val = max(in_min, min(val, in_max))
    return int((val - in_min) * (out_max - out_min) /
               (in_max - in_min) + out_min)

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

# ----------------------------
# MediaPipe Setup
# ----------------------------

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# Smoothing buffers
base_hist = []
shoulder_hist = []
elbow_hist = []
wrist_hist = []
grip_hist = []

SMOOTH = 5
last_send = 0

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
) as hands:

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        result = hands.process(rgb)

        h, w, _ = frame.shape

        if result.multi_hand_landmarks:

            for hand in result.multi_hand_landmarks:

                mp_draw.draw_landmarks(
                    frame,
                    hand,
                    mp_hands.HAND_CONNECTIONS
                )

                lm = hand.landmark

                wrist = lm[0]
                thumb_tip = lm[4]
                index_tip = lm[8]
                index_base = lm[5]
                middle_mcp = lm[9]

                wrist_x = int(wrist.x * w)
                wrist_y = int(wrist.y * h)

                thumb_x = int(thumb_tip.x * w)
                thumb_y = int(thumb_tip.y * h)

                index_x = int(index_tip.x * w)
                index_y = int(index_tip.y * h)

                # ---------------- Base ----------------
                base_angle = map_value(wrist_x, 100, w-100, 30, 150)
                base_angle = clamp(base_angle, 30, 150)

                # ---------------- Shoulder ----------------
                shoulder_angle = map_value(wrist_y, 100, h-100, 120, 30)
                shoulder_angle = clamp(shoulder_angle, 20, 120)

                # ---------------- Elbow ----------------
                elbow_dist = math.hypot(
                    wrist.x - index_base.x,
                    wrist.y - index_base.y
                )

                elbow_angle = map_value(elbow_dist, 0.05, 0.30, 40, 140)
                elbow_angle = clamp(elbow_angle, 40, 140)

                # ---------------- Wrist ----------------
                dx = middle_mcp.x - wrist.x
                dy = middle_mcp.y - wrist.y

                tilt_angle = math.degrees(math.atan2(dy, dx))

                wrist_angle = map_value(tilt_angle, -90, 90, 40, 140)
                wrist_angle = clamp(wrist_angle, 40, 140)

                # ---------------- Grip ----------------
                pinch_dist = math.hypot(
                    index_x - thumb_x,
                    index_y - thumb_y
                )

                grip_angle = map_value(pinch_dist, 20, 150, 90, 20)
                grip_angle = clamp(grip_angle, 20, 90)

                # ---------------- Smoothing ----------------
                base_hist.append(base_angle)
                shoulder_hist.append(shoulder_angle)
                elbow_hist.append(elbow_angle)
                wrist_hist.append(wrist_angle)
                grip_hist.append(grip_angle)

                if len(base_hist) > SMOOTH:
                    base_hist.pop(0)
                    shoulder_hist.pop(0)
                    elbow_hist.pop(0)
                    wrist_hist.pop(0)
                    grip_hist.pop(0)

                base_angle = int(np.mean(base_hist))
                shoulder_angle = int(np.mean(shoulder_hist))
                elbow_angle = int(np.mean(elbow_hist))
                wrist_angle = int(np.mean(wrist_hist))
                grip_angle = int(np.mean(grip_hist))

                # ---------------- Send UDP ----------------
                if time.time() - last_send > 0.03:  # 30 Hz

                    packet = struct.pack(
                        '5B',
                        base_angle,
                        shoulder_angle,
                        elbow_angle,
                        wrist_angle,
                        grip_angle
                    )

                    sock.sendto(packet, (ESP32_IP, ESP32_PORT))
                    last_send = time.time()

                # Display values
                cv2.putText(frame,f"B:{base_angle}",(10,30),
                            cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)
                cv2.putText(frame,f"S:{shoulder_angle}",(10,60),
                            cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)
                cv2.putText(frame,f"E:{elbow_angle}",(10,90),
                            cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)
                cv2.putText(frame,f"W:{wrist_angle}",(10,120),
                            cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)
                cv2.putText(frame,f"G:{grip_angle}",(10,150),
                            cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)

        cv2.imshow("Hand Arm Control", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
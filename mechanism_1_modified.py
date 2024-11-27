import cv2
import socket
import mediapipe as mp
import time

# ESP32 details
esp32_ip = "192.168.130.201"  # Replace with your ESP32's IP address
esp32_port = 12345            # Port to send UDP packets

# Set up UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Function to send UDP command
def send_command(command):
    sock.sendto(command.encode(), (esp32_ip, esp32_port))
    print(f"Sent command: {command}")

# Mediapipe setup for hand detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# OpenCV setup
cap = cv2.VideoCapture(0)
box_left = (50, 100, 150, 150)   # (x, y, width, height) for the left box
box_right = (400, 100, 150, 150) # (x, y, width, height) for the right box

# Timer variables
hand_in_box_start_time = None  # Timer to track the time the hand stays in the box
command_start_time = None      # Timer to track when to stop sending the command
active_command = None          # To store the currently active command
command_duration = 2           # Command will be sent for 2 seconds after detection
last_box = None                # To track which box was last used

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally to act as a mirror
    frame = cv2.flip(frame, 1)

    # Convert the frame to RGB for Mediapipe processing
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Draw the boxes
    cv2.rectangle(frame, (box_left[0], box_left[1]), (box_left[0] + box_left[2], box_left[1] + box_left[3]), (0, 255, 0), 2)
    cv2.rectangle(frame, (box_right[0], box_right[1]), (box_right[0] + box_right[2], box_right[1] + box_right[3]), (0, 0, 255), 2)

    if results.multi_hand_landmarks:
        for hand_landmarks, hand_label in zip(results.multi_hand_landmarks, results.multi_handedness):
            # Check if the hand is a right hand
            if hand_label.classification[0].label == "Right":
                # Draw landmarks on the frame
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Get the positions of middle_finger_mcp and ring_finger_mcp
                middle_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
                ring_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP]

                # Convert normalized coordinates to pixel coordinates
                middle_x = int(middle_finger_mcp.x * frame.shape[1])
                middle_y = int(middle_finger_mcp.y * frame.shape[0])
                ring_x = int(ring_finger_mcp.x * frame.shape[1])
                ring_y = int(ring_finger_mcp.y * frame.shape[0])

                # Check if middle_finger_mcp and ring_finger_mcp are in the left box
                if (box_left[0] <= middle_x <= box_left[0] + box_left[2] and
                        box_left[1] <= middle_y <= box_left[1] + box_left[3] and
                        box_left[0] <= ring_x <= box_left[0] + box_left[2] and
                        box_left[1] <= ring_y <= box_left[1] + box_left[3]):
                    if active_command != "CW" and last_box != "left":
                        if hand_in_box_start_time is None:
                            hand_in_box_start_time = time.time()  # Start the timer when hand enters the box
                        elif time.time() - hand_in_box_start_time >= 1:  # Wait for 1 second
                            active_command = "CW"
                            send_command(active_command)
                            command_start_time = time.time()  # Start sending the command for 2 seconds
                            last_box = "left"  # Update the last box to "left"

                # Check if middle_finger_mcp and ring_finger_mcp are in the right box
                elif (box_right[0] <= middle_x <= box_right[0] + box_right[2] and
                      box_right[1] <= middle_y <= box_right[1] + box_right[3] and
                      box_right[0] <= ring_x <= box_right[0] + box_right[2] and
                      box_right[1] <= ring_y <= box_right[1] + box_right[3]):
                    if active_command != "CCW" and last_box != "right":
                        if hand_in_box_start_time is None:
                            hand_in_box_start_time = time.time()  # Start the timer when hand enters the box
                        elif time.time() - hand_in_box_start_time >= 1:  # Wait for 1 second
                            active_command = "CCW"
                            send_command(active_command)
                            command_start_time = time.time()  # Start sending the command for 2 seconds
                            last_box = "right"  # Update the last box to "right"
                else:
                    # Reset timer and send STOP command if landmarks are outside boxes
                    if active_command:
                        send_command("STOP")
                        active_command = None
                    hand_in_box_start_time = None  # Reset timer when hand is outside the box

    else:
        # Reset timer and send STOP command if no hands are detected
        if active_command:
            send_command("STOP")
            active_command = None
        hand_in_box_start_time = None  # Reset timer when no hand is detected

    # Continuously send the command for 2 seconds after detection
    if active_command and command_start_time and time.time() - command_start_time <= 2:
        # Keep sending the command for 2 seconds
        send_command(active_command)

    # After 2 seconds, stop sending the command
    elif command_start_time and time.time() - command_start_time > 2:
        send_command("STOP")
        active_command = None
        command_start_time = None  # Reset the timer after sending the command for 2 seconds

    # Display the frame
    cv2.imshow("Hand Gesture Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

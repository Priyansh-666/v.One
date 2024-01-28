import cv2
import socket
import numpy as np
from PIL import Image
import time
import threading

collage_width = 640 * 3
collage_height = 480 * 3

def generate_collage(frames):
    collage = Image.new('RGB', (collage_width, collage_height))
    row = 0
    col = 0
    for i in range(len(frames)):
        resized_frame = cv2.resize(frames[i][0], (640, 480))
        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(resized_frame)
        collage.paste(img_pil, (col * 640, row * 480))
        col += 1
        if col == 3:
            col = 0
            row += 1

    display_collage = cv2.cvtColor(cv2.resize(np.array(collage), (640, 480)), cv2.COLOR_RGB2BGR)
    return display_collage

def send_video_frames(conn):
    # Open the camera once
    cap = cv2.VideoCapture(0)

    frames = [(cap.read()[1], "") for _ in range(9)]  # Capture 9 frames initially with text

    while True:
        frames = frames[1:]  # Remove the first frame
        frames.append((cap.read()[1], ""))  # Add a new frame with text at the end

        # Generate collage from captured frames
        collage = generate_collage(frames)

        # Convert the collage image to bytes
        _, img_encoded = cv2.imencode('.jpg', collage)
        collage_bytes = img_encoded.tobytes()

        # Send the size of the collage image first
        size = len(collage_bytes)
        conn.sendall(size.to_bytes(4, byteorder='big'))

        # Send the collage image data
        conn.sendall(collage_bytes)

        # Add a delay to control the sending rate (modify as needed)
        time.sleep(1)

def send_text_data(conn):
    while True:
        text_data = input("Send to server: ")  # Replace with the desired text
        conn.sendall(text_data.encode('utf-8'))

def receive_text_data(conn):
    while True:
        # Receive and print text data
        text_data = conn.recv(1024).decode('utf-8')
        print('Received Text:', text_data)

if __name__ == "__main__":
    host = 'localhost'
    port_video = 12345
    port_chat = 12346

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_video, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_chat:
        s_video.connect((host, port_video))
        s_chat.connect((host, port_chat))

        video_thread = threading.Thread(target=send_video_frames, args=(s_video,))
        text_thread = threading.Thread(target=send_text_data, args=(s_chat,))
        receive_thread = threading.Thread(target=receive_text_data, args=(s_chat,))

        video_thread.start()
        text_thread.start()
        receive_thread.start()

        video_thread.join()
        text_thread.join()
        receive_thread.join()

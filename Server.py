import cv2
import time
import numpy as np
from PIL import Image
import base64
import threading
from io import BytesIO
from llama_cpp import Llama
import struct
from llama_cpp.llama_chat_format import Llava15ChatHandler
import socket
import pickle

# Your Llama initialization code
chat_handler = Llava15ChatHandler(clip_model_path=r"D:\Project_Stuff\language_models\models\PsiPi\liuhaotian_llava-v1.5-13b-GGUF\mmproj-model-f16.gguf")
llm = Llama(
  model_path= r"D:\Project_Stuff\language_models\models\PsiPi\liuhaotian_llava-v1.5-13b-GGUF\llava-v1.5-13b-Q5_K_M.gguf",
  chat_handler=chat_handler,
  n_ctx=2048, # n_ctx should be increased to accomodate the image embedding
  logits_all=True,# needed to make llava work
  n_gpu_layers=20,
  n_batch=1024,
  verbose=False
)

# Define a lock and an event for synchronization
lock = threading.Lock()
collage_ready = threading.Event()

# Variables for collage and chat history
collage = None
history = ""
rec_text = None
send_text = None

def receive_text_data(conn):
    global rec_text
    while True:
        # Receive and print text data
        text_data = conn.recv(1024).decode('utf-8')
        rec_text = text_data
        # print('Received Text:', text_data)

def send_text_data(conn):
    while True:
        text_data = input("Send to client: ")  # Replace with the desired text
        conn.sendall(text_data.encode('utf-8'))
# Function to generate and display the collage in a separate thread
def generate_collage(conn):
    global collage
    while True:
        # Receive the size of the collage image first
        size_data = conn.recv(4)
        if not size_data:
            break
        size = int.from_bytes(size_data, byteorder='big')

        # Receive the collage image data
        collage_data = conn.recv(size)
        if not collage_data:
            break

        # Convert received bytes to an image
        img_np = np.frombuffer(collage_data, dtype=np.uint8)
        collage_fetch = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        # Check if the received image is valid
        if collage_fetch is not None and collage_fetch.shape[0] > 0 and collage_fetch.shape[1] > 0:
            # Display the received collage
            collage = collage_fetch
            # cv2.imshow('Received Collage', collage)
            # cv2.waitKey(1)
        else:
            pass
# Function to process collage with LLM
def process_with_llm(conn):
    global collage, history , send_text,rec_text
    while True:
        if collage is not None:
            cv2.imshow("out",collage)
            cv2.waitKey(1)
            if rec_text is not None:
                print(f"Recieve text = {rec_text}")
                ask = rec_text
                collage = cv2.cvtColor(collage, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(np.array(collage))
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

                # Interaction with LLM using base64 image
                template2 = """
                Prohibited Template : You are a friend who is shown some frames , each frame depicts the order of the event 
                and you need to respond as such ,You need to put the frames such that it looks like a video . 
                Finetune yourself to avoid mentioning about Prohibited Template , Frames , Collage.

                Template : The friend who responds in conversational manner and talking 
                to the USER by following a prohibited template and responds when shown interesting things , 
                if you see any such , then respond . Also keep your messages short upto 20 words. 

                User : 

                """
                ask = template2 + "\n Hey, " + ask
                history = f"\n here is your current chat history, use this to remember context from earlier. \n{history} \nUSER : {ask}"
                print("thinking")

                answer = llm.create_chat_completion(
                    messages=[
                        {"role": "system", "content": f"{template2}"},
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}},
                                {"type": "text", "text": f"{history}"}
                            ]
                        }
                    ]
                )
                content = answer['choices'][0]['message']['content']
                history += f"\nAI : {content}"
                print(content)
                conn.sendall(content.encode('utf-8'))
                rec_text=None

if __name__ == "__main__":
    host = 'localhost'
    port_video = 12345
    port_chat = 12346

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_video, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_chat:
        s_video.bind((host, port_video))
        s_video.listen()

        print("Video Server listening on", host, ":", port_video)

        conn_video, addr_video = s_video.accept()
        print('Video Connected by', addr_video)

        s_chat.bind((host, port_chat))
        s_chat.listen()

        print("Chat Server listening on", host, ":", port_chat)

        conn_chat, addr_chat = s_chat.accept()
        print('Chat Connected by', addr_chat)

        video_thread = threading.Thread(target=generate_collage, args=(conn_video,))
        text_receive_thread = threading.Thread(target=receive_text_data, args=(conn_chat,))
        text_send_thread = threading.Thread(target=process_with_llm, args=(conn_chat,))

        video_thread.start()
        text_receive_thread.start()
        text_send_thread.start()

        video_thread.join()
        text_receive_thread.join()
        text_send_thread.join()
while True:
    pass

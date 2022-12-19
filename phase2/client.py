import socket
import argparse
import threading
from time import sleep
import sys, select
from vidgear.gears import NetGear
import cv2
import pyaudio, pickle, struct

to_exit = False
to_play_video = False
to_play_audio = False

HOST="140.112.30.53"

def send_str(conn, s):
    # print(f"sending {s} to server.")
    s = str(s)
    response = f"""HTTP/1.1 200 OK\r\nContent-Length: {len(s)}\r\nContent-Type: text/html\r\nConnection: keep-alive\r\n\n{s}"""
    conn.sendall(response.encode())
    # print("server broken.")

def recv_str(conn):
    data = str(conn.recv(1024).decode()).split("\n\n")[-1]
    # print(f"receive {data} from server.")
    return data

def recv_thread(conn):
    global to_exit
    global to_play_video
    global to_play_audio
    while True:
        if not to_play_video and not to_play_audio:
            data = recv_str(conn)
            if data == "playing_video":
                to_play_video = True
            elif data == "playing_audio":
                to_play_audio = True
            else:
                print(f"{data}", end='')
                if "not" in data.split() or "Logout." in data.split():
                    print("server closed.")
                    to_exit = True
                    exit()
        else:
            sleep(1)

def play_video():
    client = NetGear(address=HOST, port="23456", receive_mode = True)
    while True:
        frame = client.recv()
        if frame is None:
            break
        cv2.imshow("Output Frame", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    client.close()

def play_audio():
    p = pyaudio.PyAudio()
    CHUNK = 1024
    stream = p.open(format=p.get_format_from_width(2),
                    channels=1,
                    rate=96000,
                    output=True,
                    frames_per_buffer=CHUNK)
                    
    # create socket
    client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socket_address = (HOST, 34566)
    client_socket.connect(socket_address)
    data = b""
    payload_size = struct.calcsize("Q")
    while True:
        try:
            while len(data) < payload_size:
                packet = client_socket.recv(4*1024) # 4K
                if not packet: break
                data+=packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q",packed_msg_size)[0]
            while len(data) < msg_size:
                data += client_socket.recv(4*1024)
            frame_data = data[:msg_size]
            data  = data[msg_size:]
            frame = pickle.loads(frame_data)
            stream.write(frame)

        except:
            
            break
    client_socket.close()

def client_program(address):
    global to_play_video
    global to_play_audio
    global HOST

    HOST = args.host

    host = HOST # socket.gethostname()
    conn = socket.socket()
    conn.connect((host, args.p))

    t = threading.Thread(target=recv_thread, args=(conn,))
    t.start()
    
    while True:
        try:
            data, _, __ = select.select([sys.stdin], [], [], 1)
            if data:
                data = sys.stdin.readline().strip()
                send_str(conn, data)
            if to_play_video:
                play_video()
                to_play_video = False
            if to_play_audio:
                play_audio()
                to_play_audio = False
        except:
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", type=int, default=19777)
    parser.add_argument("--host", type=str, default="140.112.30.53")
    args = parser.parse_args()
    client_program(args)

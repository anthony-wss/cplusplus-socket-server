import socket
import threading
from time import sleep
import pickle
from vidgear.gears import VideoGear
from vidgear.gears import NetGear
import wave, pyaudio, struct

WELCOME_MSG = """Welcome! This is a simple server developed by B09902033 from NTU CSIE\n"""
LOGIN_MSG = [
    """[Login]\nPlease enter your username (or type -1 to register)\n> """,
    """Username does not exist.\n""",
    """Password\n> """,
    """Login Successfully!\n""",
    """The Password is not correct.\n"""
]
REGISTRATION_MSG = [
    """[Registration]\nPlease enter your desired username\n> """,
    """Password\n> """,
    """Successfully Registered! Please login with your new account.\n""",
    """Sorry that the username has already existed.\n"""
]
ACTION_MSG = "[Action]\n(1) leave a message\n(2) watch a short video\n(3) listen to a short audio clip\n(others) logout/exit\n> "

LEAVE_A_MESSAGE = [
    """Please leave some message here\n> """,
    """Message saved.\n""",
]

LOGOUT = """Logout. Have a nice day!\n"""

active_client = {} # address -> client socket
lobby = []
database = {"user": [], "password": [], "msg": []}

def send_str(address, s):
    # print(f"sending {s} to client")
    try:
        conn = active_client[address]
        s = str(s)
        response = f"""HTTP/1.1 200 OK\r\nContent-Length: {len(s)}\r\nContent-Type: text/html\r\nConnection: keep-alive\r\n\n{s}"""
        conn.sendall(response.encode())
    except:
        # print("client error.")
        del active_client[address]

def recv_str(address):
    # print(f"receiving from client")
    conn = active_client[address]
    data = str(conn.recv(1024).decode()).split("\n\n")[-1]
    # print(f"received: {data}")
    return data

def client_exit(address):
    del active_client[address]

def get_lobby_message_board(lobby):
    lobby_str = "\nCurrent online users:\n"
    for user in lobby:
        lobby_str += user + "\n"
    lobby_str += "---Message Board---\n"
    for i in range(len(database["msg"])):
        lobby_str += '(' + str(i+1) + ')' + database["msg"][i] + "\n"
    lobby_str += ACTION_MSG
    return lobby_str

def play_video_clip():
    stream = VideoGear(source='./video_preview_h264.mp4').start()
    server = NetGear(address="127.0.0.1", port="23456")

    while True:
        try: 
            frame = stream.read()
            if frame is None:
                break
            server.send(frame)
        
        except KeyboardInterrupt:
            break

    stream.stop()
    server.close()

def play_audio_clip():
    server_socket = socket.socket()
    server_socket.bind(('127.0.0.1', 34566))
    print("start sending audio")

    server_socket.listen(5)
    CHUNK = 1024
    wf = wave.open("./sample_audio.wav", 'rb')
    p = pyaudio.PyAudio()

    client_socket,addr = server_socket.accept()
 
    data = None
    while True:
        try:
            data = wf.readframes(CHUNK)
            # print(data)
            if len(data) < 10:
                break
            a = pickle.dumps(data)
            message = struct.pack("Q",len(a))+a
            client_socket.sendall(message)
        except:
            break

def new_client_thread(address):

    global lobby
    global active_client
    global database
    
    send_str(address, WELCOME_MSG)
    # Login loop
    while True:

        send_str(address, LOGIN_MSG[0])
        username = recv_str(address)
        print(f"receive '{username}' from client.")
        if username == "-1":
            send_str(address, REGISTRATION_MSG[0])
            username = recv_str(address)
            # print(f"from client {address}: " + str(username))
            # while username in lobby:
            #     send_str(address, REGISTRATION_MSG[2])
            #     username = recv_str(conn)
            send_str(address, REGISTRATION_MSG[1])
            password = recv_str(address)
            database["user"].append(username)
            database["password"].append(password)
            pickle.dump(database, open("database.pkl", "wb"))
            send_str(address, REGISTRATION_MSG[2])

        elif username not in database["user"]:
            send_str(address, LOGIN_MSG[1])
            client_exit(address)
            return
        
        else:
            send_str(address, LOGIN_MSG[2])
            password = recv_str(address)
            if password != database["password"][database["user"].index(username)]:
                send_str(address, LOGIN_MSG[4])
                client_exit(address)
                return
            lobby.append(username)
            send_str(address, LOGIN_MSG[3])
            break

    # Server loop
    while True:
        send_str(address, get_lobby_message_board(lobby))
        choice = recv_str(address)
        
        if str(choice) == '1':
            send_str(address, LEAVE_A_MESSAGE[0])
            msg = recv_str(address)
            database["msg"].append(f"{msg} -by {username}")
            pickle.dump(database, open("database.pkl", "wb"))
            send_str(address, LEAVE_A_MESSAGE[1])
        elif str(choice) == '2':
            send_str(address, "playing_video")
            play_video_clip()
        elif str(choice) == '3':
            send_str(address, "playing_audio")
            play_audio_clip()
        else:
            send_str(address, LOGOUT)
            client_exit(address)
            return

def server_program():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", type=int, default=19777)
    args = parser.parse_args()
    host = socket.gethostname()
    port = args.p

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            server_socket.bind((host, port))
        except OSError:
            sleep(1)
        break
    print(f"Server is on {host}:{port}")

    server_socket.listen(20)
    global database
    database = pickle.load(open("database.pkl", "rb"))

    while True:
        try:
            conn, address = server_socket.accept()
            print("Connection from: " + str(address))
            # conn.settimeout(2)
            active_client[address] = conn
            t = threading.Thread(target=new_client_thread, args=(address,))
            t.start()
        except:
            break
    
    conn.close()

if __name__ == '__main__':
    server_program()
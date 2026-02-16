import socket
import struct
import mss
import pyautogui
from PIL import Image
import io
import threading
import subprocess
import os
import time

HOST = '0.0.0.0'
PORT = 8888
# Get the project root directory (parent of server folder)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = os.path.join(PROJECT_ROOT, 'platform-tools', 'adb.exe')

def setup_adb_reverse():
    try:
        subprocess.run([ADB_PATH, 'reverse', 'tcp:8888', 'tcp:8888'], 
                      capture_output=True, timeout=5)
        return True
    except:
        return False

def monitor_adb_connection():
    while True:
        try:
            result = subprocess.run([ADB_PATH, 'devices'], 
                                   capture_output=True, text=True, timeout=5)
            if 'device' in result.stdout and result.stdout.count('\n') > 1:
                setup_adb_reverse()
        except:
            pass
        time.sleep(10)

def capture_screen():
    with mss.mss() as sct:
        try:
            # Try to capture monitor 2 (extended display)
            monitor = sct.monitors[2] if len(sct.monitors) > 2 else sct.monitors[1]
        except:
            # Fallback to primary monitor
            monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=70)
        return buf.getvalue()

def handle_client(conn):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            cmd = data.decode('utf-8', errors='ignore').strip()
            
            if cmd == 'GET_SCREEN':
                img_data = capture_screen()
                conn.sendall(struct.pack('>I', len(img_data)))
                conn.sendall(img_data)
            
            elif cmd.startswith('TOUCH'):
                parts = cmd.split()
                x, y = float(parts[1]), float(parts[2])
                pyautogui.click(x, y)
                conn.sendall(b'OK')
    except:
        pass
    finally:
        conn.close()

def main():
    # Setup ADB reverse on startup
    print(f"Setting up ADB reverse...")
    if setup_adb_reverse():
        print("ADB reverse configured")
    else:
        print("Warning: ADB reverse failed. Make sure tablet is connected.")
    
    # Start ADB monitoring thread
    adb_thread = threading.Thread(target=monitor_adb_connection, daemon=True)
    adb_thread.start()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn,))
            thread.daemon = True
            thread.start()

if __name__ == '__main__':
    main()

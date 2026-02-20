import socket
import struct
import mss
import pyautogui
import threading
import subprocess
import os
import time
import win32api
import cv2
import numpy as np

HOST = '0.0.0.0'
PORT = 8888
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = os.path.join(PROJECT_ROOT, 'platform-tools', 'adb.exe')
monitor_offset_x = 0
monitor_offset_y = 0
frame_count = 0
last_fps_time = time.time()
sct = None
target_monitor = None

def setup_adb_reverse():
    try:
        subprocess.run([ADB_PATH, 'start-server'], capture_output=True, timeout=10)
        time.sleep(2)
        result = subprocess.run([ADB_PATH, 'devices'], capture_output=True, text=True, timeout=5)
        if 'device' not in result.stdout or result.stdout.count('\n') <= 1:
            return False
        subprocess.run([ADB_PATH, 'reverse', 'tcp:8888', 'tcp:8888'], capture_output=True, timeout=5)
        subprocess.run([ADB_PATH, 'shell', 'am', 'start', '-n', 'com.tabletmonitor/.MainActivity'], capture_output=True, timeout=5)
        return True
    except:
        return False

def monitor_adb_connection():
    while True:
        try:
            result = subprocess.run([ADB_PATH, 'devices'], capture_output=True, text=True, timeout=5)
            if 'device' in result.stdout and result.stdout.count('\n') > 1:
                setup_adb_reverse()
        except:
            pass
        time.sleep(10)

def capture_screen():
    global monitor_offset_x, monitor_offset_y, sct, target_monitor
    if sct is None:
        sct = mss.mss()
    if target_monitor is None:
        target_monitor = next((m for m in sct.monitors[1:] if (m['width'] == 1080 and m['height'] == 1920) or (m['width'] == 864 and m['height'] == 1536)), 
                             sct.monitors[3] if len(sct.monitors) > 3 else sct.monitors[2] if len(sct.monitors) > 2 else sct.monitors[1])
        monitor_offset_x = target_monitor['left']
        monitor_offset_y = target_monitor['top']
    
    screenshot = sct.grab(target_monitor)
    img_array = np.frombuffer(screenshot.rgb, dtype=np.uint8).reshape(screenshot.height, screenshot.width, 3)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    cursor_x, cursor_y = win32api.GetCursorPos()
    rel_x, rel_y = cursor_x - monitor_offset_x, cursor_y - monitor_offset_y
    
    if 0 <= rel_x < screenshot.width and 0 <= rel_y < screenshot.height:
        cv2.circle(img_bgr, (rel_x, rel_y), 15, (0, 255, 255), -1)
        cv2.circle(img_bgr, (rel_x, rel_y), 15, (0, 0, 0), 3)
    
    _, img_data = cv2.imencode('.jpg', img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    return img_data.tobytes(), screenshot.width, screenshot.height

def handle_client(conn):
    global monitor_offset_x, monitor_offset_y, frame_count, last_fps_time
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            cmd = data.decode('utf-8', errors='ignore').strip()
            
            if cmd == 'GET_SCREEN':
                img_data, w, h = capture_screen()
                conn.sendall(struct.pack('>III', w, h, len(img_data)) + img_data)
                frame_count += 1
                if time.time() - last_fps_time >= 5:
                    print(f"FPS: {frame_count / 5:.1f}")
                    frame_count = 0
                    last_fps_time = time.time()
            elif cmd.startswith(('TOUCH', 'DOWN', 'MOVE', 'UP')):
                parts = cmd.split()
                x, y = float(parts[1]) + monitor_offset_x, float(parts[2]) + monitor_offset_y
                {'TOUCH': pyautogui.click, 'DOWN': pyautogui.mouseDown, 'MOVE': pyautogui.moveTo, 'UP': pyautogui.mouseUp}[parts[0]](x, y)
                conn.sendall(b'OK')
    except:
        pass
    finally:
        conn.close()

def main():
    print("Setting up ADB reverse...")
    print("ADB reverse configured" if setup_adb_reverse() else "Warning: ADB reverse failed. Make sure tablet is connected.")
    
    threading.Thread(target=monitor_adb_connection, daemon=True).start()
    
    def start_clock():
        time.sleep(2)
        clock_path = os.path.join(PROJECT_ROOT, 'clock', 'clock.py')
        if os.path.exists(clock_path):
            try:
                subprocess.Popen(['python', clock_path], cwd=os.path.dirname(clock_path))
                print("Clock app started")
            except Exception as e:
                print(f"Failed to start clock app: {e}")
    
    threading.Thread(target=start_clock, daemon=True).start()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        
        while True:
            conn, _ = s.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == '__main__':
    main()

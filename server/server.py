import socket
import struct
import mss
import pyautogui
from PIL import Image, ImageDraw
import io
import threading
import subprocess
import os
import time
import win32gui
import win32api
import cv2
import numpy as np

HOST = '0.0.0.0'
PORT = 8888
# Get the project root directory (parent of server folder)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = os.path.join(PROJECT_ROOT, 'platform-tools', 'adb.exe')

# Global variables for monitor position
monitor_offset_x = 0
monitor_offset_y = 0

def setup_adb_reverse():
    try:
        # Start ADB server first
        subprocess.run([ADB_PATH, 'start-server'], 
                      capture_output=True, timeout=10)
        time.sleep(2)
        # Run adb devices to detect tablet
        result = subprocess.run([ADB_PATH, 'devices'], 
                      capture_output=True, text=True, timeout=5)
        if 'device' not in result.stdout or result.stdout.count('\n') <= 1:
            return False
        # Setup port forwarding
        subprocess.run([ADB_PATH, 'reverse', 'tcp:8888', 'tcp:8888'], 
                      capture_output=True, timeout=5)
        # Launch app automatically
        subprocess.run([ADB_PATH, 'shell', 'am', 'start', '-n', 
                       'com.tabletmonitor/.MainActivity'],
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
    global monitor_offset_x, monitor_offset_y
    with mss.mss() as sct:
        # Use monitor 3 for tablet (if available), otherwise monitor 2, then monitor 1
        if len(sct.monitors) > 3:
            monitor = sct.monitors[3]  # Third display for tablet
        elif len(sct.monitors) > 2:
            monitor = sct.monitors[2]  # Second extended display
        else:
            monitor = sct.monitors[1]  # Primary monitor
        
        screenshot = sct.grab(monitor)
        
        # Store original dimensions and position
        original_width = screenshot.width
        original_height = screenshot.height
        monitor_offset_x = monitor['left']
        monitor_offset_y = monitor['top']
        
        # Convert to numpy array
        img_array = np.frombuffer(screenshot.rgb, dtype=np.uint8).reshape(screenshot.height, screenshot.width, 3)
        
        # Convert RGB to BGR for OpenCV first
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Get cursor position and draw it
        cursor_x, cursor_y = win32api.GetCursorPos()
        rel_cursor_x = cursor_x - monitor_offset_x
        rel_cursor_y = cursor_y - monitor_offset_y
        
        # Draw large visible cursor
        if 0 <= rel_cursor_x < original_width and 0 <= rel_cursor_y < original_height:
            cv2.circle(img_bgr, (rel_cursor_x, rel_cursor_y), 15, (0, 255, 255), -1)
            cv2.circle(img_bgr, (rel_cursor_x, rel_cursor_y), 15, (0, 0, 0), 3)
        
        # Resize if needed
        if original_width > 1920 or original_height > 1080:
            img_bgr = cv2.resize(img_bgr, (1920, 1080), interpolation=cv2.INTER_NEAREST)
        
        # Fast JPEG encoding
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
        _, img_data = cv2.imencode('.jpg', img_bgr, encode_param)
        return img_data.tobytes(), original_width, original_height

def handle_client(conn):
    global monitor_offset_x, monitor_offset_y
    screen_width = 1920
    screen_height = 1080
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            cmd = data.decode('utf-8', errors='ignore').strip()
            
            if cmd == 'GET_SCREEN':
                img_data, screen_width, screen_height = capture_screen()
                # Send screen dimensions first
                conn.sendall(struct.pack('>II', screen_width, screen_height))
                # Then send image
                conn.sendall(struct.pack('>I', len(img_data)))
                conn.sendall(img_data)
            
            elif cmd.startswith('TOUCH'):
                parts = cmd.split()
                x, y = float(parts[1]), float(parts[2])
                # Add monitor offset to coordinates
                pyautogui.click(x + monitor_offset_x, y + monitor_offset_y)
                conn.sendall(b'OK')
            
            elif cmd.startswith('DOWN'):
                parts = cmd.split()
                x, y = float(parts[1]), float(parts[2])
                # Add monitor offset to coordinates
                pyautogui.mouseDown(x + monitor_offset_x, y + monitor_offset_y)
                conn.sendall(b'OK')
            
            elif cmd.startswith('MOVE'):
                parts = cmd.split()
                x, y = float(parts[1]), float(parts[2])
                # Add monitor offset to coordinates
                pyautogui.moveTo(x + monitor_offset_x, y + monitor_offset_y)
                conn.sendall(b'OK')
            
            elif cmd.startswith('UP'):
                parts = cmd.split()
                x, y = float(parts[1]), float(parts[2])
                # Add monitor offset to coordinates
                pyautogui.mouseUp(x + monitor_offset_x, y + monitor_offset_y)
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
    
    # Start clock app in separate thread
    def start_clock():
        time.sleep(2)  # Wait for server to be ready
        clock_path = os.path.join(PROJECT_ROOT, 'clock', 'clock.py')
        if os.path.exists(clock_path):
            try:
                subprocess.Popen(['python', clock_path], cwd=os.path.dirname(clock_path))
                print("Clock app started")
            except Exception as e:
                print(f"Failed to start clock app: {e}")
    
    clock_thread = threading.Thread(target=start_clock, daemon=True)
    clock_thread.start()
    
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

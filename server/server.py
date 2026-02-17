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
from turbojpeg import TurboJPEG

HOST = '0.0.0.0'
PORT = 8888
# Get the project root directory (parent of server folder)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = os.path.join(PROJECT_ROOT, 'platform-tools', 'adb.exe')

# Global variables for monitor position
monitor_offset_x = 0
monitor_offset_y = 0

# Initialize TurboJPEG for hardware-accelerated encoding
try:
    jpeg = TurboJPEG()
except:
    jpeg = None

def setup_adb_reverse():
    try:
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
        # Check if we have multiple monitors
        if len(sct.monitors) > 2:
            # Use monitor 2 (extended display)
            monitor = sct.monitors[2]
        else:
            # Use primary monitor - capture full screen
            monitor = sct.monitors[1]
        
        screenshot = sct.grab(monitor)
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        
        # Store original dimensions and position
        original_width = screenshot.width
        original_height = screenshot.height
        monitor_offset_x = monitor['left']
        monitor_offset_y = monitor['top']
        
        # Get cursor position and draw it
        cursor_x, cursor_y = win32api.GetCursorPos()
        # Adjust cursor position relative to this monitor
        rel_cursor_x = cursor_x - monitor_offset_x
        rel_cursor_y = cursor_y - monitor_offset_y
        
        # Draw cursor if it's within this monitor
        if 0 <= rel_cursor_x < original_width and 0 <= rel_cursor_y < original_height:
            draw = ImageDraw.Draw(img)
            # Draw a simple cursor (white arrow with black outline)
            cursor_size = 20
            points = [
                (rel_cursor_x, rel_cursor_y),
                (rel_cursor_x, rel_cursor_y + cursor_size),
                (rel_cursor_x + cursor_size//3, rel_cursor_y + cursor_size*2//3),
                (rel_cursor_x + cursor_size//2, rel_cursor_y + cursor_size//2)
            ]
            draw.polygon(points, fill='white', outline='black')
        
        img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        
        # Use TurboJPEG for hardware-accelerated encoding if available
        if jpeg:
            import numpy as np
            img_array = np.array(img)
            img_data = jpeg.encode(img_array, quality=85, jpeg_subsample=2)
            return img_data, original_width, original_height
        else:
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=85, optimize=False, subsampling=0)
            return buf.getvalue(), original_width, original_height

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

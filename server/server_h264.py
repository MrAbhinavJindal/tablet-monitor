import socket
import struct
import mss
import pyautogui
import threading
import subprocess
import os
import time
import win32api
import numpy as np

HOST = '0.0.0.0'
PORT = 8888
TOUCH_PORT = 8889
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = os.path.join(PROJECT_ROOT, 'platform-tools', 'adb.exe')
FFMPEG_PATH = os.path.join(PROJECT_ROOT, 'ffmpeg', 'bin', 'ffmpeg.exe')
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
        subprocess.run([ADB_PATH, 'reverse', 'tcp:8889', 'tcp:8889'], capture_output=True, timeout=5)
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

def stream_h264(conn):
    global monitor_offset_x, monitor_offset_y, sct, target_monitor, frame_count, last_fps_time
    
    if sct is None:
        sct = mss.mss()
    if target_monitor is None:
        target_monitor = next((m for m in sct.monitors[1:] if (m['width'] == 1080 and m['height'] == 1920) or (m['width'] == 864 and m['height'] == 1536)), 
                             sct.monitors[3] if len(sct.monitors) > 3 else sct.monitors[2] if len(sct.monitors) > 2 else sct.monitors[1])
        monitor_offset_x = target_monitor['left']
        monitor_offset_y = target_monitor['top']
    
    w, h = target_monitor['width'], target_monitor['height']
    conn.sendall(struct.pack('>II', w, h))
    
    ffmpeg_cmd = [
        FFMPEG_PATH, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', '30',
        '-i', '-', '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
        '-crf', '23', '-profile:v', 'baseline', '-level', '3.1', '-f', 'h264', '-'
    ]
    
    ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    def read_h264():
        try:
            while True:
                chunk = ffmpeg_process.stdout.read(4096)
                if not chunk:
                    break
                conn.sendall(struct.pack('>I', len(chunk)) + chunk)
        except:
            pass
    
    threading.Thread(target=read_h264, daemon=True).start()
    
    try:
        while True:
            screenshot = sct.grab(target_monitor)
            img_array = np.frombuffer(screenshot.rgb, dtype=np.uint8).reshape(h, w, 3)
            
            cursor_x, cursor_y = win32api.GetCursorPos()
            rel_x, rel_y = cursor_x - monitor_offset_x, cursor_y - monitor_offset_y
            
            if 0 <= rel_x < w and 0 <= rel_y < h:
                img_array[max(0, rel_y-15):min(h, rel_y+15), max(0, rel_x-15):min(w, rel_x+15)] = [0, 255, 255]
            
            ffmpeg_process.stdin.write(img_array.tobytes())
            ffmpeg_process.stdin.flush()
            
            frame_count += 1
            if time.time() - last_fps_time >= 5:
                print(f"FPS: {frame_count / 5:.1f}")
                frame_count = 0
                last_fps_time = time.time()
            
            time.sleep(1/30)
    except:
        pass
    finally:
        if ffmpeg_process:
            ffmpeg_process.terminate()
            ffmpeg_process.wait()
        conn.close()

def handle_touch(conn):
    global monitor_offset_x, monitor_offset_y
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            cmd = data.decode('utf-8', errors='ignore').strip()
            
            if cmd.startswith(('TOUCH', 'DOWN', 'MOVE', 'UP')):
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
            except:
                pass
    
    threading.Thread(target=start_clock, daemon=True).start()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"H.264 server listening on {HOST}:{PORT}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as touch_s:
            touch_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            touch_s.bind((HOST, TOUCH_PORT))
            touch_s.listen()
            print(f"Touch server listening on {HOST}:{TOUCH_PORT}")
            
            def accept_video():
                while True:
                    conn, _ = s.accept()
                    threading.Thread(target=stream_h264, args=(conn,), daemon=True).start()
            
            def accept_touch():
                while True:
                    conn, _ = touch_s.accept()
                    threading.Thread(target=handle_touch, args=(conn,), daemon=True).start()
            
            threading.Thread(target=accept_video, daemon=True).start()
            threading.Thread(target=accept_touch, daemon=True).start()
            
            while True:
                time.sleep(1)

if __name__ == '__main__':
    main()

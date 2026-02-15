import socket
import struct
import mss
import pyautogui
from PIL import Image
import io

HOST = '0.0.0.0'
PORT = 8888

def capture_screen():
    with mss.mss() as sct:
        print(sct.monitors)
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=70)
        return buf.getvalue()

def handle_client(conn):
    print("Client connected")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            try:
                cmd = data.decode('utf-8', errors='ignore').strip()
                print(f"Received command: {cmd}")
            except:
                continue
            
            if cmd == 'GET_SCREEN':
                img_data = capture_screen()
                conn.sendall(struct.pack('>I', len(img_data)))
                conn.sendall(img_data)
            
            elif cmd.startswith('TOUCH'):
                parts = cmd.split()
                x, y = float(parts[1]), float(parts[2])
                pyautogui.click(x, y)
                conn.sendall(b'OK')
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        
        while True:
            conn, addr = s.accept()
            print(f"Connection from {addr}")
            handle_client(conn)

if __name__ == '__main__':
    main()

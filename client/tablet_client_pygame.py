import socket
import struct
from PIL import Image
import io
import pygame
import threading

HOST = 'localhost'
PORT = 8888

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()
pygame.display.set_caption("Tablet Monitor")
clock = pygame.time.Clock()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

running = True
current_image = None
scale_ratio = 1.0
offset_x = 0
offset_y = 0

def get_screen():
    global current_image, scale_ratio, offset_x, offset_y
    while running:
        try:
            sock.sendall(b'GET_SCREEN\n')
            
            size_data = sock.recv(4)
            if not size_data:
                break
            size = struct.unpack('>I', size_data)[0]
            
            img_data = b''
            while len(img_data) < size:
                chunk = sock.recv(min(size - len(img_data), 4096))
                if not chunk:
                    break
                img_data += chunk
            
            img = Image.open(io.BytesIO(img_data))
            
            # Scale to fit screen while maintaining aspect ratio
            img_width, img_height = img.size
            scale_x = screen_width / img_width
            scale_y = screen_height / img_height
            scale_ratio = min(scale_x, scale_y)
            
            new_width = int(img_width * scale_ratio)
            new_height = int(img_height * scale_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            offset_x = (screen_width - new_width) // 2
            offset_y = (screen_height - new_height) // 2
            
            mode = img.mode
            size = img.size
            data = img.tobytes()
            
            current_image = pygame.image.fromstring(data, size, mode)
        except Exception as e:
            print(f"Error: {e}")
            break

threading.Thread(target=get_screen, daemon=True).start()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Convert tablet coordinates to laptop coordinates
            x = (event.pos[0] - offset_x) / scale_ratio
            y = (event.pos[1] - offset_y) / scale_ratio
            try:
                msg = f'TOUCH {x} {y}\n'.encode()
                sock.sendall(msg)
                sock.recv(2)
            except:
                pass
    
    screen.fill((0, 0, 0))
    if current_image:
        screen.blit(current_image, (offset_x, offset_y))
    pygame.display.flip()
    clock.tick(30)

sock.close()
pygame.quit()

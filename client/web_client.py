from flask import Flask, Response, request
import socket
import struct
import threading
import time

app = Flask(__name__)

HOST = '127.0.0.1'
PORT = 5555

def get_frame():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        sock.sendall(b'GET_SCREEN\n')
        
        size_data = sock.recv(4)
        size = struct.unpack('>I', size_data)[0]
        
        img_data = b''
        while len(img_data) < size:
            chunk = sock.recv(min(size - len(img_data), 4096))
            if not chunk:
                break
            img_data += chunk
        
        sock.close()
        return img_data
    except:
        return None

def generate():
    while True:
        frame = get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.1)

@app.route('/')
def index():
    return '''
    <html>
    <head><title>Tablet Monitor</title></head>
    <body style="margin:0;overflow:hidden">
    <img id="screen" src="/video" style="width:100%;height:100vh;object-fit:contain" 
         ontouchstart="sendTouch(event)">
    <script>
    function sendTouch(e) {
        e.preventDefault();
        const rect = e.target.getBoundingClientRect();
        const x = e.touches[0].clientX - rect.left;
        const y = e.touches[0].clientY - rect.top;
        fetch('/touch?x='+x+'&y='+y);
    }
    </script>
    </body>
    </html>
    '''

@app.route('/video')
def video():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/touch')
def touch():
    x = request.args.get('x')
    y = request.args.get('y')
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        sock.sendall(f'TOUCH {x} {y}\n'.encode())
        sock.recv(2)
        sock.close()
    except:
        pass
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

import socket, os
from PIL import Image
from src.classifier import Classifier

import signal, sys
signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

SOCKET_PATH = "/tmp/manok.sock"

clf = Classifier()   # loaded ONCE at startup

if os.path.exists(SOCKET_PATH):
    os.remove(SOCKET_PATH)

server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(SOCKET_PATH)
server.listen(1)
print("[Worker] Ready", flush=True)

while True:
    conn, _ = server.accept()
    data = conn.recv(256).decode().strip()   # receives image path
    try:
        image = Image.open(data)
        label, conf, probs = clf.predict(image)
        response = f"{label},{conf},{probs[0]},{probs[1]},{probs[2]}\n"
    except Exception as e:
        response = f"error,0,0,0,0\n"
    conn.sendall(response.encode())
    conn.close()

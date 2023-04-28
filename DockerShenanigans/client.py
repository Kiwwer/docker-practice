import time
import socket


while True:
    cmd = input()
    message = cmd
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(60.0)
    addr = ("0.0.0.0", 2000)
    message = message.encode('utf-8')
    start = time.time()
    client_socket.sendto(message, addr)
    try:
        data, server = client_socket.recvfrom(1024)
        data = data.decode('utf-8')
        end = time.time()
        elapsed = end - start
        print(f'{data}')
    except socket.timeout:
        print('REQUEST TIMED OUT')	

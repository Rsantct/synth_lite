#!/usr/bin/env python3

import socket
import sys

def send_recv( cmd, addr='localhost', port=9800):
    ans = ''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((addr, port))
    s.sendall(cmd.encode())
    s.shutdown(socket.SHUT_WR)
    while True:
        data = s.recv(1024)
        if not data:
            break
        ans += data.decode()
    s.close()
    return  ans

if __name__ == "__main__":
    cmd = "help"
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])

    ans = send_recv(cmd)
    print(ans)

#!/usr/bin/env python3

import synth_lite as sl
from subprocess import check_output

def seqClients():
    tmp = check_output("aconnect -l", shell=True).decode().split("\n")
    clients = []
    client = []
    for cosa in tmp:
        if cosa.startswith("client"):
            if client:
                clients.append(client)
                client = []
        if cosa:
            client.append(cosa.strip())
    if client:
        clients.append(client)
    return clients

def seq_connections():
    connections = []
    for client in seqClients():
        cname = []
        port =  []
        pair =  []
        for campo in client:
            if campo[0].isdigit():
                port = campo
            if campo.startswith("Connect"):
                pair = campo.split()[-1]
        tmp = client[0].split()
        cname = tmp[0].ljust(6) + tmp[1].rjust(5) + " " + tmp[2].ljust(20)
        if pair:
            connections.append(cname.ljust(20) + "port:" + port.ljust(35) + " <---> " + pair)
    return connections

if __name__ == "__main__":

    kbd_available = False
    tmp = check_output("aconnect -l", shell=True).decode().split("\n")
    for x in tmp:
        #print (x)
        if 'key' in x.lower():
            kbd_available = True
        
    if not kbd_available:
        print('Keyboard not available under alsa sequencer (aconnect -l)')
        exit()

    sl.connect_kb_synth()
    print()
    for cosa in seq_connections():
        print(cosa)

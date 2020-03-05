#!/usr/bin/env python3
""" Set reverbs to fluidsynth from 'fluid_reverb_presets.cfg'

    Usage:  fluid_reverb_presets.py N
"""

import sys
import yaml
from os.path import dirname, realpath, basename
from fluid_cmd import send_recv

def set_reverb_settings(room=40, dampening=50, width=40, level=40):

    if room      > 1:  room = room /100.0
    if dampening > 1:  dampening = dampening/100.0
    if width     > 1:  width = width/100.0
    if level     > 1:  level = level/100.0
    send_recv( f'rev_setroomsize    {str(room)}'        )
    send_recv( f'rev_setdamp        {str(dampening)}'   )
    send_recv( f'rev_setwidth       {str(width)}'       )
    send_recv( f'rev_setlevel       {str(level)}'       )

def read_presets():
    thisDir =   dirname( realpath(__file__) )
    cfg_file= basename( realpath(__file__) ).replace('.py','.cfg')
    with open(f'{thisDir}/{cfg_file}', 'r') as f:
        presets = yaml.safe_load(f)
    for p in presets.keys():
        tmp = presets[p]
        tmp = [x.strip().replace('"','').replace("'","") for x in tmp.split(',')]
        presets[p]={}
        presets[p]["room"]         = tmp[0]
        presets[p]["dampening"]    = tmp[1]
        presets[p]["width"]        = tmp[2]
        presets[p]["level"]        = tmp[3]
        presets[p]["name"]         = tmp[4]
    return presets

if __name__ == '__main__':

    # Read presets
    presets = read_presets()
    
    # default preset
    if len(sys.argv) > 1:
        p = int(sys.argv[1])
    else:
        print()
        print(__doc__)
        for p in presets:
            print( presets[p]["name"] )
        print()
        exit()
        
    if p in range(1, len(presets)+1):
        room        = float( presets[p]["room"]      )
        dampening   = float( presets[p]["dampening"] )
        width       = float( presets[p]["width"]     )
        level       = float( presets[p]["level"]     )
        set_reverb_settings(room, dampening, width, level)
        print( f'setting: {presets[p]["name"]}' )
    else:
        print( f'must select 1...{str(len(presets))}' )


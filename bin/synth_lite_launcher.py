#!/usr/bin/env python3
"""
    A daemon that auto starts or stops 'synth_lite.py'
    whenever your midi keyboard is available.

    usage:  synth_lite_launcher.py  start | stop  &

"""

from sys import argv
from subprocess import check_output, Popen
from time import sleep
from os.path import expanduser

UHOME = expanduser("~")

def kill_bill():
    """ killing any previous instance of this, becasue
        some residual can be alive accidentaly.
    """

    # List processes like this one
    processString = f'python3 {UHOME}/bin/synth_lite_launcher.py start'
    rawpids = []
    cmd = ( f'ps -eo etimes,pid,cmd' +
            f' | grep "{processString}"' +
            f' | grep -v grep'  )
    try:
        rawpids = check_output( cmd, shell=True ).decode().split('\n')
    except:
        pass
    # Discard blanks and strip spaces:
    rawpids = [ x.strip().replace('\n','')  for x in rawpids if x]
    # A 'rawpid' element has 3 fields 1st:etimes 2nd:pid 2th:comand_string
    # Sorting by 1st_field:etimes (elapsed time seconds, see 'man ps'):
    rawpids.sort( key=lambda x: int(x.split()[0]) )
    # Now we have the 'rawpids' ordered the oldest the last.

    # Discard the first one because it is **the own pid**
    if rawpids:
        rawpids.pop(0)

    # Extracting just the 'pid' at 2ndfield [1]:
    pids = [ x.split()[1] for x in rawpids ]

    # Killing the remaining pids, if any:
    for pid in pids:
        print('(synth_lite_launcher) killing old \'start.py\' processes:', pid)
        Popen( f'kill -KILL {pid}'.split() )
        sleep(.1)
    sleep(.5)

def is_kbd_connected():
    tmp = check_output( 'aconnect -l'.split() ).decode().split('\n')
    for line in tmp:
        if 'key' in line.lower():
            return True
    return False

def kbd_watchdog_loop():

    # LOOPING FOREVER
    kbd = False
    while True:

        if kbd != is_kbd_connected():
            kbd = not kbd
            state = {True:'',False:'dis'}[kbd] + 'connected'
            print(f'(synth_lite_launcher) kbd is {state}')

            if kbd:
                # Starts the synth
                Popen( f'{UHOME}/synth_lite/synth_lite.py start'.split() )
                sleep(5) # avoid bouncing
            else:
                # Stops the synth
                Popen( f'{UHOME}/synth_lite/synth_lite.py stop'.split() )
                sleep(5) # avoid bouncing

        sleep(3)

if __name__ == '__main__':

    # KILLING ANY PREVIOUS INSTANCE OF THIS
    kill_bill()

    if argv[1:]:

        if argv[1] == 'start':
            # LOOP
            kbd_watchdog_loop()

        elif argv[1] == 'stop':
            # arakiri
            Popen( f'pkill -f synth_lite_launcher'.split() )

        else:
            print(__doc__)

    else:
        print(__doc__)

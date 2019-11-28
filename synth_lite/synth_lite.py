#!/usr/bin/env python3
"""
    A fluidsynth launcher
"""
import sys
from os.path import dirname, realpath, basename
from subprocess import check_output, Popen, STDOUT
from time import sleep
import yaml

class Dict2obj(object):
    """ Turns a dictionary into a class """
    def __init__(self, d):
        """ Constructor """
        for key in d:
            setattr(self, key, d[key])

def releaseSC(pcms=["*"]):
    """ Kills processes using a pcm list
        By default, we use *, i.e all pcms
    """
    for pcm in pcms:
        # fuser: -v shows the process name, -k kills the process
        tmp = check_output("fuser -v -k /dev/snd/" + pcm + "; exit 0",
                           stderr=STDOUT, shell=True).decode()
        tmp = tmp.split("\n")
        # reading killed processes
        tmp = [x for x in tmp if x != "" and "/dev/snd/" in x]
        if tmp:
            processes = []
            for line in tmp:
                p = line.split()[-1]
                if not p in processes:
                    print( "(synth) release_sound_card killed  process: " + p )
                    processes.append(p)
        else:
            print( "(synth) release_sound_card /dev/snd/" + pcm + " not used." )

def PA_release_card( alsa_card ):
    """ Release the card from Pulseaudio """

    def get_pulse_cards():
        pa_cards = {}
        try:
            tmp = sp.check_output( 'pactl list cards'.split() ).decode().split('\n')
            new_card = False
            for line in tmp:

                if line.startswith("Card #"):
                    new_card = True
                    cardN = line.strip()
                    pa_cards[ cardN ] = {}

                if new_card and 'Name: ' in line:
                    pa_cards[cardN]['pa_name'] = line.split(':')[-1].strip()

                if new_card and 'alsa.card_name' in line:
                    pa_cards[cardN]['alsa_name'] = line.split('=')[-1].strip() \
                                                    .replace('"','')

        except:
            pass

        return pa_cards

    # The set of cards managed under PA
    pa_cards = get_pulse_cards()

    if not pa_cards:
        return

    # Release out card from PA
    for pa_card in pa_cards:
        #print (mycard, pa_cards[pa_card]["alsa_name"],
        #       pa_cards[pa_card]["pa_name"])
        if pa_cards[pa_card]["alsa_name"] in alsa_card:
            pa_name = pa_cards[pa_card]["pa_name"]
            sp.Popen( f'pactl set-card-profile {pa_name} off'.split() )
            print( f'releasing {pa_name} from Pulseaudio' )

def is_jack_running():
    try:
        print( f'(synth) checking JACKD')
        check_output( 'jack_lsp' )
        return True
    except:
        return False

def start_jackd():

    print( f'(synth) starting JACKD')

    jack_cmd = f'jackd -R -dalsa -dhw:{CFG.alsaCard} -r{str(CFG.rate)}'

    if 'pulseaudio' in check_output("pgrep -fl pulseaudio", shell=True).decode():
        jack_cmd = ['pasuspender', '--'] + jack_cmd

    Popen( jack_cmd, shell=True )
    sleep(1)

    # will check if JACK ports are available
    c = 6
    while c:
        print( '(synth) waiting for jackd ' + '.'*c )
        try:
            check_output( 'jack_lsp >/dev/null 2>&1'.split() )
            sleep(1)
            print( '(synth) JACKD STARTED' )
            return True
        except:
            c -= 1
            sleep(.5)
    return False

def stop_synth():
    with open('/dev/null', 'w') as fNull:
        Popen( 'killall -KILL  qsynth'.split(),     stderr=fNull, stdout=fNull )
        Popen( 'killall -KILL  fluidsynth'.split(), stderr=fNull, stdout=fNull )
    sleep(.5)

def get_alsa_seq_client(pattern, mode='input'):
    mode = {'input':'-i', 'in':'-i', 'i':'-i',
            'output':'-o', 'out':'-o', 'o':'-o'}[mode]
    tmp = check_output( f'aconnect {mode}'.split() ).decode()
    # example:
    # client 128: 'FLUID Synth (11469)' [type=user,pid=11469]
    for line in [x for x in tmp.split('\n') if x[:6]=='client']:
        if pattern.lower() in line.lower():
            return line.split(':')[0].split()[-1]

def connect_kb_synth():
    print( '(synth) Connecting ALSA SEQ PORTS: keyboard <--> synth' )
    tmp = f'aconnect {get_alsa_seq_client("key", "input")}' \
          + f' {get_alsa_seq_client("synth", "output")}'
    Popen( tmp.split() )

def prints_some_fluid_settings():
    print()
    gain    = check_output( "echo 'get synth.gain'          | nc -CN localhost 9800", shell=True ).decode()
    reverb  = check_output( "echo 'get synth.reverb.active' | nc -CN localhost 9800", shell=True ).decode()
    chorus  = check_output( "echo 'get synth.chorus.active' | nc -CN localhost 9800", shell=True ).decode()
    print( f'Gain:    {gain}')
    print( f'Reverb:  {reverb}')
    print( f'Chorus:  {chorus}')
    print()

def start_synth():
    # -i no interactive, - s tcp server on port 9800
    # 0 < gain < 5, default 0.2. Beware if set >1.0 and you use high armonic instruments.
    if "fluid" in CFG.engine:
        tmp =  "fluidsynth -i -s"
    else:
        tmp =  "qsynth"

    tmp += " --gain " + str(CFG.gain)
    tmp += " --chorus " + CFG.chorus
    tmp += " --reverb " + CFG.reverb
    tmp += " --sample-rate " + str(CFG.rate)
    tmp += " --audio-bufsize " + str(CFG.buffersize)
    tmp += " --audio-bufcount " + str(CFG.buffers)

    if CFG.driver == "alsa":
        try:
            PA_release_card(CFG.alsaDevice)
        except:
            pass
        tmp += " -a alsa -o audio.alsa.device=" + CFG.alsaDevice

    elif CFG.driver == "jack":
        if not is_jack_running():
            start_jackd()
        if CFG.jackautoconnect in (True, 'yes'):
            print( f'(synth) WARNING will autoconnect to SOUND CARD jack ports' )
            tmp += " --connect-jack-outputs"

    elif CFG.driver == "pulseaudio":
        Popen( 'pacmd set-card-profile 0 "output:analog-stereo+input:analog-stereo"'.split() )
        tmp += " -a pulseaudio -o audio.pulseaudio.device=" + pulseDevice

    else:
        print ( f'ERROR with audio driver: {CFG.driver}' )
        exit(-1)
    tmp += " -m alsa_seq " + CFG.soundFontPath


    print( f'(synth) launching:\n\t{tmp}' )
    Popen( tmp.split() )

    # Wait until 10 s for the synth to be available under 'alsa sequencer system':
    n = 10
    print( '(synth) waiting for fluidsynth under alsa sequencer ports ...' )
    while n:
        if get_alsa_seq_client("synth", mode='output'):
            print( f'(synth) the synth {CFG.engine} has started' )
            return True
        sleep(1)
        print( "." * (10-n+1) )
        n -=1

    # This should not occur:
    print( "(synth) ERROR: the synth is not detected under alsa sequencer ports (aconnect -l)" )
    return False


if __name__ == "__main__":

    shutdown = False
    if sys.argv[1:]:
        for opc in sys.argv[1:]:
            if 'kill' in opc or 'shutdown' in opc or 'stop' in opc:
                shutdown = True

    # Read config
    thisDir  = dirname( realpath(__file__) )
    cfg_file = basename( realpath(__file__) ).replace('.py','.cfg')
    with open(f'{thisDir}/{cfg_file}', 'r') as f:
        CFG = yaml.load(f)

    CFG["reverb"] = {False:'no', True:'yes'}[CFG["reverb"]]
    CFG["chorus"] = {False:'no', True:'yes'}[CFG["chorus"]]

    CFG = Dict2obj(CFG)

    # Stopping if any synth running
    print( '(synth) killing synths' )
    stop_synth()

    # Exiting if desired
    if shutdown:
        exit(0)

    # Release the sound card if necessary
    if CFG.driver == 'alsa':
        print( "(synth) releasing sound card: 'fuse -k /dev/snd/pcm*'" )
        releaseSC()

    # Starting the synth
    print()
    print( f'(synth) starting: buffsize={str(CFG.buffersize)} reverb={str(CFG.reverb)}' )
    if not start_synth():
        print( f'ERROR starting {CFG.engine}' )
        exit(-1)
    else:
        prints_some_fluid_settings()

    # Connects keyboard to synth
    connect_kb_synth()

    # Lets map the channels to our favorite instruments
    print( '(synth) mapping favourites instruments' )
    print( '--- channels map:' )
    Popen( f'{thisDir}/fluid_set_map'.split() )


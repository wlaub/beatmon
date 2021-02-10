import websocket
import json
import os
import time
import math

import monitor

"""
Loopmidi needs to be running with an appropriatedly named port
"""

import midi
import record

if __name__ == "__main__":

    config = {
        'midi_port': 'beatsaber'
        }
    try:
        cfgs = json.load(open('config.json', 'r'))
        config.update(cfgs)
    except:
        pass

    midi_out = midi.init_midi(config['midi_port'])

    bsmon = monitor.BeatSaberMonitor()

    bsmon.message_processors.extend([
        midi.BlockCutNoteGenerator(0,1),
        midi.EventNoteTrigger('bombCut', channel=2),   
        midi.EventNoteTrigger('noteMissed', channel=3),    
        midi.EventNoteGate('obstacleEnter', 'obstacleExit', channel=4), #in a wall
        midi.SongBPMNote(channel = 5), #in a song w/ bpm info
        midi.EventNoteGate('pause', ['resume','menu'], channel=6), #song paused
        midi.PerformanceCCGenerator(),
        midi.MidiNoteCleanup(), #Stops notes at the end of the song
        record.SongArchive('dump.json'),
        ])


    ws = bsmon.get_ws_app()

    print("Started, Connecting to Beat Saber...", flush=True)
    ws.run_forever()
       
    midi_out.close()   
    

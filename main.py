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
import mido

def find_midi(name):
    """
    case instensitive contains serach for midi id of a name
    """
    names = mido.get_output_names()
    for match in names:
        if name.lower() in match.lower(): return match
    raise KeyError(f'No matching device for \'{name}\' in {names}')

class MidiNote():
    def __init__(self, note_id, **kwargs):
        self.note_id = note_id
        self.start_msg = mido.Message('note_on', **kwargs)
        self.stop_msg = mido.Message('note_off', **kwargs)

    def start(self, port):
        port.send(self.start_msg)
        
    def stop(self, port):
        port.send(self.stop_msg)

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

    handler = monitor.MessageHandler(midi_out)

    handler.message_processors.extend([
        midi.BlockCutNoteGenerator(),
        ])


    ws = handler.get_ws_app()

    print("Started, Connecting to Beat Saber...", flush=True)
    ws.run_forever()
       
    midi_out.close()   
    

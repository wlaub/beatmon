from __future__ import print_function
import websocket
import json
import os
import time
import math

"""
Loopmidi needs to be running with an appropriatedly named port
"""

import mido

def find_midi(name):
    """
    case instensitive contains serach for midi id of a name
    """
    names = mido.get_output_names()
    for match in names:
        if name.lower() in match.lower(): return match
    raise KeyError(f'No matching device for {name} in {names}')

class MidiNote():
    def __init__(self, note_id, **kwargs):
        self.note_id = note_id
        self.start_msg = mido.Message('note_on', **kwargs)
        self.stop_msg = mido.Message('note_off', **kwargs)

    def start(self, port):
        port.send(self.start_msg)
        
    def stop(self, port):
        port.send(self.stop_msg)

class MessageHandler():
    note_channel_map = {
            'NoteA': 0,
            'NoteB': 1,
            'Bomb': 2, 
            'Obstacle': 3,
        }

    midi_cc_map = {
        'score': 0,
        'health': 1,
        'softfail': 2,
        'fullcombo': 3,
        'bpm': 4
    }
    resting_ccs = {
            'score': 1,
            'health': 1,
            'softfail': 0,
            'fullcombo': 1,
            'bpm': 0.5,
    }

    def __init__(self, midi_port):
        self.pending_notes = []
        self.midi_out = midi_port
        self.current_map = None
        
        self.wscallbacks = {
            'on_message': lambda x: self.on_message(x[0], x[1]),
            'on_open': lambda x: self.on_open(x),
            'on_error': lambda x: self.on_error(x),
            'on_close': lambda x: self.on_close(x),
        }
         
    def clear_midi(self):
        for entry in self.pending_notes:
            entry.stop(self.midi_out)
        self.pending_notes = []
        self.send_ccs(self.resting_ccs)
         
    def stop_midi_note(self, note_id):
        for entry in self.pending_notes:
            if entry.note_id == note_id:
                print(f'stoping note: {entry}')
                entry.stop(self.midi_out)
                self.pending_notes.remove(entry)
                break

    def send_ccs(self, cc_dict):
        print(cc_dict)
        for key, val in cc_dict.items():
            msg = mido.Message('control_change', control=self.midi_cc_map[key], value=int(val*127))
            self.midi_out.send(msg)
            
    def performance_ccs(self, perf):
        if perf == None: return
        print('Updating performance CCs')
        bpm_oct= math.log(self.current_map['songBPM']/120)/math.log(2)
        
        score = 1
        try:
            score = perf['score']/perf['currentMaxScore']
        except: pass
        
        cc_dict = {
            'score': score,
            'health': 1, #perf['batteryEnergy'] #this is only battery not health
            'softfail': 1 if perf['soft Failed'] else 0,
            'fullcombo': 1 if perf['combo'] == perf['passedNotes'] else 0,
            'bpm': 0.5+bpm_oct/10,
        }
        self.send_ccs(cc_dict)



    def on_message(self, ws, message):
        try:
            message=json.loads(message)
            event = message['event']
            print(f'Message received: {event}', flush=True)
            
            beatmap = message['status'].get('beatmap', None)
            if beatmap != None: self.current_map = beatmap
            
            performance = message['status'].get('performance', None)
            self.performance_ccs(performance)
            
            #print(message, flush=True)
            if event == "noteCut":
                print('note cut event')
                cut_data = message['noteCut']
                
                pitch = 74+int(cut_data['initialScore']*24/85)-12
                velocity = int(cut_data['cutDistanceScore']*127/15)
                channel = self.note_channel_map.get(cut_data['noteType'], 15)
                print(f'sending note')
                mnote = MidiNote(cut_data['noteID'], note=pitch, velocity = velocity, channel=channel)
                mnote.start(self.midi_out)
                
                self.pending_notes.append(mnote)
                print('note cut event over')
            elif event == "noteFullyCut":
                cut_data = message['noteCut']
                note_id = cut_data['noteID']
                self.stop_midi_note(note_id)
            elif event == 'obstacleEnter':
                mnote = MidiNote('obstacle', channel=self.channel_map['Obstacle'])
                mnote.start(self.midi_out)
            elif event == 'obstacleExit':
                self.stop_midi_note('obstacle')
            elif event in ['finished', 'failed', 'menu']:
                self.clear_midi()
                self.current_map = None
            elif event == 'songStart':
                self.current_map = message['status']['beatmap']
                
        except Exception as e:
            print(str(e))
            raise e

    def on_open(self, ws):
        print('Socket opened', flush=True)
    
    def on_error(self, ws, error):
        print(f'Error:\n{error}', flush=True)   
    
    def on_close(self, ws):
        print(f'Connection closed')

if __name__ == "__main__":

    config = {
        'midi_port': 'beatsaber'
        }
    try:
        cfgs = json.load(open('config.json', 'r'))
        config.update(cfgs)
    except:
        pass
    
    midi_name = find_midi(config['midi_port'])
    
    midi_out = mido.open_output(midi_name)
            
    print("Started, Connecting to Beat Saber...", flush=True)
    
    handler = MessageHandler(midi_out)
        
    def on_message(ws, msg):
        return handler.on_message(ws, msg)
    def on_open(ws):
        return handler.on_open(ws)
    def on_error(ws):
        return handler.on_error(ws)
    def on_close(ws):
        return handler.on_message(ws)
    
    ws = websocket.WebSocketApp("ws://127.0.0.1:6557/socket",
        on_message = on_message,
        on_error = on_error, 
        on_open = on_open,
        on_close = on_close,
        )
    ws.run_forever()
       
    midi_out.close()   
    

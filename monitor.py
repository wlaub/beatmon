import websocket
import json
import os
import time
import math

class BeatSaberMonitor():

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
        self.midi_out = midi_port
        self.current_map = None
        
        self.wscallbacks = {
            'on_message': lambda x,y: self.on_message(x,y),
            'on_open': lambda x: self.on_open(x),
            'on_error': lambda x,y: self.on_error(x,y),
            'on_close': lambda x: self.on_close(x),
        }

        #list of class instances that are passed messages to do stuff with via process()
        self.message_processors = [] 

         
    def clear_midi(self):
        self.send_ccs(self.resting_ccs)
         
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

            for processor in self.message_processors:
                result = processor.process(self, message)
                if result == True: break

            #print(message, flush=True)
            if event in ['finished', 'failed', 'menu']:
                self.clear_midi()
                self.current_map = None
            elif event == 'songStart':
                self.current_map = message['status']['beatmap']
                
        except Exception as e:
            print(str(e))
            raise e
        print('Done', flush=True)

    def on_open(self, ws):
        print('Socket opened', flush=True)
    
    def on_error(self, ws, error):
        print(f'Error:\n{error}', flush=True)   
    
    def on_close(self, ws):
        print(f'Connection closed', flush=True)

    def get_ws_app(self, host = '127.0.0.1', port = 6557):
        """
        """
       
        ws = websocket.WebSocketApp(f"ws://{host}:{port}/socket",
            **self.wscallbacks,
            )

        return ws


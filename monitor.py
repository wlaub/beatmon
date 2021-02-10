import websocket
import json
import os
import time
import math

import traceback

class BeatSaberMonitor():

    def __init__(self):
        
        self.wscallbacks = {
            'on_message': lambda x,y: self.on_message(x,y),
            'on_open': lambda x: self.on_open(x),
            'on_error': lambda x,y: self.on_error(x,y),
            'on_close': lambda x: self.on_close(x),
        }

        #list of class instances that are passed messages to do stuff with via process()
        self.message_processors = [] 

        self.current_map = {}
        self.current_performance = {}
        self.current_modifiers = {}
        self.current_playersettings = {}
        self.current_gameinfo = {}

        self.in_map = False
        self.paused = False
        self.softfailed = False

    def update_state(self, message):
        status = message['status']
        self.current_map = status.get('beatmap', self.current_map)
        self.current_performance = status.get('performance', self.current_performance)
        self.current_modifiers = status.get('mod', self.current_modifiers)
        self.current_playersettings = status.get('playerSettings', self.current_playersettings)
        self.current_gameinfo = status.get('game', self.current_gameinfo)

    def on_message(self, ws, message):
        try:
            message=json.loads(message)
            start_time = message['time']/1000
            event = message['event']
            #print(f'Message received: {event}', flush=True)

            self.update_state(message)

            hit = False
            lines = []
            for processor in self.message_processors:
                try:
                    result = processor.process(self, message)
                    if result == False:
                        hit = True
                        lines.append(f'* {(time.time()-start_time)*1000:.2f}ms - {processor}')
                    elif result == True: 
                        lines.append(f'# {processor}')
                        break
                except Exception as exc:
                    print(f'Exception while running {processor}')
                    traceback.print_exc()
                    
            if hit:
                print(f'Event {event} received by the following processors:')
                print('\n'.join(lines), flush=True)
            elif not hit and False:
                print(f'Did not process event {event}')

            #Game state transitions
            if event in ['finished', 'failed', 'menu']:
                self.in_map = False
                self.paused = False
                print(f'Exited map')
            elif event == 'songStart':
                print('\n'*20)
                print(f'Entered map')
                self.in_map = True
                self.softfailed = False
            elif event =='pause':
                self.paused = True
            elif event == 'resume':
                self.paused = False
            elif event == 'softFailed':
                self.softfailed = True


        except Exception as e:
            print(f'Error processing message {message}:\n')
            traceback.print_exc()
            print('', flush=True)
            raise e
        if hit:
            print('Done', flush=True)

    def on_open(self, ws):
        print('Socket opened', flush=True)
    
    def on_error(self, ws, error):
        print(f'Error:\n{error}', flush=True)   
    
    def on_close(self, ws):
        print(f'Connection closed', flush=True)

    def get_ws_app(self, host = '127.0.0.1', port = 6557):
        """
        Creates the websocket app instance and wires up the relevant callbacks
        """
       
        ws = websocket.WebSocketApp(f"ws://{host}:{port}/socket",
            **self.wscallbacks,
            )

        return ws


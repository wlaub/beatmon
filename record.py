import time
import os
import json
import math

class SongArchive():
    def __init__(self, filename):
        self.data = []
        self.filename = filename
        try:
            with open(self.filename,'r') as fp:
                self.data = json.load(fp)
        except Exception as e:
            print(f'Load fail - {e}')
        self.current_data = []
            
    def save(self):
        with open(self.filename, 'w') as fp:
            json.dump(self.data, fp)
        print(f'Saved archive {self.filename}')
    
    def process(self, monitor, message):
        event = message['event']
        if event == 'hello':
            return False
            
        if monitor.in_map:
            self.current_data.append(message)
        
        if event in ['finished', 'failed', 'menu']:
            print(f'Archiver noticed that song finished with {len(self.current_data)} events')
            if len(self.current_data) > 0:
                if self.current_data[-1] != message:
                    self.current_data.append(message)
                self.data.append(self.current_data)
                self.current_data = []
                self.save()
            return False

        if not monitor.in_map:
            return None
                
            
    def __str__(self):
        return f'Complete Message Archive per-song writing to {self.filename}'
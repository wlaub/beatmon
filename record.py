import time
import os
import json
import math
import hashlib

class SessionArchive():
    def __init__(self, song_file, session_filename):
        self.data = []
        self.song_map = {}

        self.song_filename = song_file
        self.session_filename = session_filename

        try:
            with open(self.song_filename,'r') as fp:
                self.song_map = json.load(fp)
        except Exception as e:
            print(f'Failed to load song index file {self.song_filename}: {e}')

        try:
            with open(self.session_filename,'r') as fp:
                self.data = json.load(fp)
        except Exception as e:
            print(f'Failed to load session file {self.session_filename}: {e}')


        self.clear()

    def clear(self):
   
        self.current_data = {
            'events': [],
            'performance': {},
            'modifiers': {},
            'playersettings': {},
            'gameinfo': {},
            'map_hash': '',
            }

    def save(self):
        with open(self.song_filename, 'w') as fp:
            json.dump(self.song_map, fp)
        print(f'Saved song index {self.song_filename}')

        with open(self.session_filename, 'w') as fp:
            json.dump(self.data, fp)
        print(f'Saved archive {self.session_filename}')

    def get_map_hash(self, map_info):
        result = map_info['levelId']
        return result

    def process(self, monitor, message):
        event = message['event']
        if event == 'hello':
            return False

        event_entry = dict(message)
        event_entry.pop('status')

        if monitor.in_map:
            self.current_data['events'].append(event_entry)
        
        if event in ['finished', 'failed', 'menu']:
            print(f'Archiver noticed that song finished with {len(self.current_data)} events')
            if len(self.current_data) > 0:
                if self.current_data[-1] != event_entry:
                    self.current_data['events'].append(event_entry)
                    self.current_data['performance'] = monitor.current_performance
                    self.current_data['modifiers'] = monitor.current_modifiers
                    self.current_data['playersettings'] = monitor.current_playersettings
                    self.current_data['gameinfo'] = monitor.current_gameinfo

                    map_info = monitor.current_map
                    map_hash = self.get_map_hash(map_info)
                    
                    if not map_hash in self.song_map:
                        self.song_map[map_hash] = map_info

                    self.current_data['map_hash'] = map_hash

                self.data.append(self.current_data)
                self.clear()
                self.save()
            return False

        if not monitor.in_map:
            return None
                
            
    def __str__(self):
        return f'Complete Session Archive per-song writing to {self.session_filename} with songs in {self.song_filename}'

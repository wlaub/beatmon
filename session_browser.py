import sys, os
import math, time
import json

from matplotlib import widgets
from matplotlib import pyplot as plt

class App():
    def __init__(self, datadir):
        self.datadir = datadir
        
        songsfile = os.path.join(datadir, 'songs.json')
        with open(songsfile, 'r') as fp:
            self.songmap = songmap = json.load(fp)

        self.sessions = sessions = []

        _, _, filenames = next(os.walk(datadir))
        for filename in filenames:
            if filename == 'songs.json': continue
            with open(os.path.join(datadir, filename), 'r') as fp:
                tsession = json.load(fp)
            sessions.extend(tsession)

        #extract song hashs in sessions
        self.session_hashes = list(set([x['map_hash'] for x in sessions]))
        
        #ui state?
        self.selected_map = self.session_hashes[0]

        self.fig, self.axes = plt.subplots()
        self.buttons = []

        next_song = widgets.Button(plt.axes([.9, .95, .1, .05]), label = '>>>')
        next_song.on_clicked(lambda x: self.cycle_song(x, 1))
        prev_song = widgets.Button(plt.axes([0, .95, .1, .05]), label = '<<<')
        prev_song.on_clicked(lambda x: self.cycle_song(x, -1))

        self.buttons.extend([next_song, prev_song])

    def cycle_song(self, event, inc):
        idx = self.session_hashes.index(self.selected_map)
        idx += inc
        idx %= len(self.session_hashes)
        self.selected_map = self.session_hashes[idx]

        self.axes.clear()
        data, map_info = self.get_song_entries(self.selected_map)
        for entry in data:
            self.draw_timing(self.axes, entry, map_info)
        plt.draw()

    def get_song_entries(self, selection):
        data = filter(lambda x: x['map_hash'] == selection, self.sessions)
        return data, self.songmap[selection]

    def draw_timing(self, ax, entry, map_info):
        events = entry['events']

        map_name = f"{map_info['songName']} - {map_info['songAuthorName']} - {map_info['levelAuthorName']}"

        cuts = [x for x in events if x['event']=='noteFullyCut']

        times = [x['time'] for x in cuts]
        data_values = {
            'precision': [x['noteCut']['cutDistanceScore'] for x in cuts],
            'score': [x['noteCut']['finalScore'] for x in cuts],
            'cutscore': [x['noteCut']['finalScore']-x['noteCut']['cutDistanceScore'] for x in cuts],       
            'timing': [x['noteCut']['timeDeviation']*1000 for x in cuts],       
        }

        ax.scatter(times, data_values['timing'], label = map_info['songName'], s=4)

        ax.set_title(f'Timing Accuracy\n{map_name}')
        ax.set_xlabel(f'Cut Time (seconds since epoch)')
        ax.set_ylabel(f'Time Deviation (ms)')
        ax.grid(True)



    def run(self):
        data, map_info = self.get_song_entries(self.selected_map)
        for entry in data:
            self.draw_timing(self.axes, entry, map_info)

        plt.show()
                

app = App('sample_data')
app.run()

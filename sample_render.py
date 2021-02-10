import json,time

from matplotlib import pyplot as plt

song_file = 'sample_data/songs.json'
session_file = 'sample_data/session20210210_044904.json'

song_map = json.load(open(song_file, 'r'))
data = json.load(open(session_file, 'r'))

for entry in data:
    map_info = song_map[entry['map_hash']]
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

    """
    plt.title('Timing Accuracy')
    plt.scatter(times, data_values['timing'], label = map_info['songName'], s=4)
    plt.xlabel('Cut Time (seconds since epoch)')
    plt.ylabel('Time Deviation (ms)')
    """

    """
    misses = [x for x in events if x['event']=='noteMissed']
    times = [x['time'] for x in misses]
    yvals = [0 for x in misses]
    plt.scatter(times, yvals, c='r', marker='x', s=6)
    """

    plt.hist(data_values['precision'], label=map_info['songName'], density=True, bins=[x-0.5 for x in range(17)])
    plt.title('Cut Distance Score Histogram',)

plt.legend()

plt.grid()
plt.show()
    


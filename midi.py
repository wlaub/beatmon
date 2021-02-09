import time
import os
import json

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
    """
    A midi note with a note_id for matching. The intended use for this is to
    allow notes to start on a noteCut event and stop on a noteFullyCut event,
    but the note_id can also be other things. For example you might use a note
    id of 'wall' to represent a note that starts when the player enters a wall
    and stops when the player leaves.

    kwargs goes straight to the midi note_on and note_off messages.
    """
    def __init__(self, note_id, **kwargs):
        self.note_id = note_id
        self.start_msg = mido.Message('note_on', **kwargs)
        self.stop_msg = mido.Message('note_off', **kwargs)

    def start(self, port):
        print(f'Note on - {self.note_id} - {self.start_msg}')
        port.send(self.start_msg)
        
    def stop(self, port):
        print(f'Note off - {self.note_id} - {self.stop_msg}')
        port.send(self.stop_msg)

class MessageProcessor():
    def process(self, monitor, message):
        """
        monitor is the BeatSaberMonitor class that called this
        message is the rate Beat Saber HTTP Status message that was received

        Return True if the message should not propagate
        Return False if the message should propagate
        return None if the nothing happened
        """

class MidiNoteGenerator(MessageProcessor):
    """
    Shared storage for managing midi notes from multiple classes
    """
    note_list = []
    midi_out = None #Make sure to set this at some point?

    def process_aborts(self, message):
        """
        Certain events, e.g. menu, fail, finish should stop all notes
        """
        if message['event'] in ['finished', 'failed', 'menu']:
            self.all_notes_off()
            return False
        return None

    def all_notes_off(self):
        cls = MidiNoteGenerator
        print(f'Switching off {len(cls.note_list)} notes')
        for note in cls.note_list:
            note.stop(cls.midi_out)
        cls.note_list = []

    def single_note_off(self, note_id):
        cls = MidiNoteGenerator   
        delete_list = []
        for note in cls.note_list:
            if note.note_id == note_id:
                delete_list.append(note)
        for note in delete_list:
            note.stop(cls.midi_out)
            cls.note_list.remove(note)

    def add_note(self, note, play=False):
        cls = MidiNoteGenerator   
        if play:
            note.start(cls.midi_out)
        cls.note_list.append(note)
    

class MidiNoteCleanup(MidiNoteGenerator):
    """
    This just cleans up notes when the song ends
    """
    def process(self, monitor, message):
        if message['event'] == 'hello': return False
        return self.process_aborts(message)

    def __str__(self):
        return 'Midi Note Cleanup Processor'

class BlockCutNoteGenerator(MidiNoteGenerator):
    """
    This is a class for generating midi notes associated with beat saber note/block
    cuts.
    """
    def __init__(self, left_channel=0, right_channel=1):
        self.note_channel_map = {
            'NoteA': left_channel,
            'NoteB': right_channel,
        }

    def process(self, monitor, message):
        event = message['event']
        if event == 'noteCut':
            cut_data = message['noteCut']
            
            pitch = 74+int(cut_data['initialScore']*24/85)-12
            velocity = int(cut_data['cutDistanceScore']*127/15)
            channel = self.note_channel_map.get(cut_data['noteType'], 15)

            mnote = MidiNote(cut_data['noteID'], note=pitch, velocity = velocity, channel=channel)
            self.add_note(mnote, play=True)

            return False
        elif event == 'noteFullyCut':

            cut_data = message['noteCut']
            note_id = cut_data['noteID']
            self.single_note_off(note_id)

            return False
        elif event == 'hello':
            return False
        return None    

    def __str__(self):
        return f'Block -> Note generator with Left on {self.note_channel_map["NoteA"]} and Right on {self.note_channel_map["NoteB"]}'

class EventNoteTrigger(MidiNoteGenerator):
    """
    Generates a short note on a given channel every time a given event happens.
    Event name may be a list or string.
    """

    def __init__(self, event_name, channel, note_kwargs = None):
        self.event_name = event_name

        self.note_kwargs = {'note': 74, 'velocity': 127}
        if note_kwargs != None:
            self.note_kwargs.update(note_kwargs)
        self.note_kwargs['channel'] = channel

        self.channel = channel

    def process(self, monitor, message):
        event = message['event']
        if event in self.event_name:
            mnote = MidiNote(None, **self.note_kwargs)
            mnote.start(MidiNoteGenerator.midi_out)
            time.sleep(0.001)
            mnote.stop(MidiNoteGenerator.midi_out)

            return False
        elif event == 'hello':
            return False
        return None

    def __str__(self):
        return f'Event -> Trigger generator mapping \'{self.event_name}\' to {self.channel}'

class EventNoteGate(MidiNoteGenerator):
    """
    Like EventNoteTrigger, but with start and stop conditions
    """
    def __init__(self, start_event, stop_event, channel, note_kwargs = None):
        self.start_event = start_event
        self.stop_event = stop_event
        self.note_kwargs = {'note': 74, 'velocity': 127}
        if note_kwargs != None:
            self.note_kwargs.update(note_kwargs)
        self.note_kwargs['channel'] = channel

        self.channel = channel

        self.note_id = f'gate_{self.start_event}_{self.stop_event}'

    def process(self, monitor, message):
        event = message['event']
        if event in self.start_event:
            mnote = MidiNote(self.note_id, **self.note_kwargs)
            self.add_note(mnote, play=True)
            return False
        elif event in self.stop_event:
            self.single_note_off(self.note_id)
            return False
        elif event == 'hello':
            return False
        return None

    def __str__(self):
        return f'Event -> Gate generator mapping \'{self.start_event}\' through \'{self.stop_event}\' to {self.channel}'


#Initialization of midi port

global_midi_out = None

def init_midi(midi_name):
    global midi_out
    try:
        midi_name = find_midi(midi_name)
    except KeyError as exc:
        print(f'Failed to acquire midi device because:\n{exc}')
        exit(1)
    
    global_midi_out = mido.open_output(midi_name)
    MidiNoteGenerator.midi_out = global_midi_out
    return global_midi_out


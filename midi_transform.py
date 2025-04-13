import mido
import numpy as np
import pygame
from perlin_noise import PerlinNoise
from scipy.integrate import odeint
import random
import soundfile as sf
import os

class MIDITransformer:
    def __init__(self):
        self.sample_rate = 44100
        pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2)

    def load_midi(self, file_path):
        """Load a MIDI file and return its contents."""
        return mido.MidiFile(file_path)

    def game_of_life_transform(self, midi_file, generations=100):
        """Game of Life MIDI transformation with GoL + MIDI injection + special rules."""
        tempo = self._get_midi_tempo(midi_file)
        ticks_per_beat = midi_file.ticks_per_beat

        # Create note timeline from MIDI
        note_timeline = [[] for _ in range(generations)]
        current_time = 0

        def ticks_to_seconds(ticks):
            return (ticks * tempo) / (ticks_per_beat * 1_000_000)

        for msg in midi_file:
            current_time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                seconds = ticks_to_seconds(current_time)
                frame_index = int(seconds * 20)
                if frame_index < generations:
                    note_timeline[frame_index].append((msg.note, msg.velocity))

        # Find first active frame
        start_frame = next((i for i, notes in enumerate(note_timeline) if notes), 0)

        # Initialize grid and lifespan map
        grid = np.zeros((128, 128))
        note_durations = np.zeros((128, 128))

        transformed_frames = []

        for frame in range(start_frame, generations):
            new_grid = np.zeros_like(grid)

            # Apply Game of Life + MIDI + fading
            for i in range(128):  # pitch
                for j in range(128):  # time column
                    cell_alive = grid[i, j] > 0

                    # Count neighbors
                    neighbors = self._count_neighbors(grid, i, j)

                    # MIDI activity on this pitch
                    midi_triggered = any(note == i for note, _ in note_timeline[frame])

                    # Rule: Immortal C notes stay forever
                    if i % 12 == 0 and cell_alive:
                        new_grid[i, j] = grid[i, j]
                        continue

                    # Rule: refresh existing note if MIDI re-triggers it
                    if cell_alive and midi_triggered:
                        new_grid[i, j] = max(grid[i, j], 10)  # Renew lifespan
                        continue

                    # Game of Life logic
                    if cell_alive:
                        if neighbors < 2 or neighbors > 3:
                            new_grid[i, j] = max(0, grid[i, j] - 1)  # fade
                        else:
                            new_grid[i, j] = grid[i, j]  # stay alive
                    else:
                        if neighbors == 3 or midi_triggered:
                            new_grid[i, j] = 10  # new cell born

            grid = new_grid
            transformed_frames.append(self._grid_to_notes(grid))

        return transformed_frames


    def _get_midi_tempo(self, midi_file):
        """Extract tempo from MIDI file."""
        default_tempo = 500000  # Default MIDI tempo (120 BPM)
        for msg in midi_file:
            if msg.type == 'set_tempo':
                return msg.tempo
        return default_tempo

    def _midi_to_grid_with_duration(self, midi_file, tempo, ticks_per_beat):
        """Convert MIDI notes to a 2D grid with duration information."""
        grid = np.zeros((128, 128))  # MIDI note range (0-127)
        note_durations = np.zeros((128, 128))  # Store note durations

        # Convert ticks to seconds
        def ticks_to_seconds(ticks):
            return (ticks * tempo) / (ticks_per_beat * 1000000)

        # Track active notes and their start times
        active_notes = {}
        current_time = 0

        for msg in midi_file:
            current_time += msg.time
            if msg.type == 'note_on':
                note = int(msg.note)
                time_step = int(current_time) % 128
                active_notes[(note, time_step)] = current_time
            elif msg.type == 'note_off':
                note = int(msg.note)
                time_step = int(current_time) % 128
                if (note, time_step) in active_notes:
                    start_time = active_notes[(note, time_step)]
                    duration = current_time - start_time
                    duration_frames = int(ticks_to_seconds(duration) * 20)
                    grid[note, time_step] = duration_frames
                    note_durations[note, time_step] = duration_frames
                    del active_notes[(note, time_step)]

        return grid, note_durations

    def perlin_transform(self, midi_file, scale=0.1, octaves=6):
        """Transform MIDI using Perlin noise."""
        noise = PerlinNoise(octaves=octaves)
        notes = []
        for msg in midi_file:
            if msg.type == 'note_on':
                x = msg.note * scale
                y = msg.time * scale
                value = noise([x, y])
                new_note = int((value + 1) * 64)
                notes.append((new_note, msg.velocity, msg.time))
        return notes

    def lorenz_transform(self, midi_file, sigma=10, rho=28, beta=8/3):
        """Transform MIDI using Lorenz attractor."""
        def lorenz_deriv(state, t):
            x, y, z = state
            return [sigma*(y-x), x*(rho-z)-y, x*y-beta*z]

        notes = []
        t = np.linspace(0, 100, len(midi_file.tracks[0]))
        state0 = [1.0, 1.0, 1.0]
        states = odeint(lorenz_deriv, state0, t)

        for i, msg in enumerate(midi_file):
            if msg.type == 'note_on':
                x, y, z = states[i]
                new_note = int((x + 30) * 2) % 128
                new_velocity = int((y + 30) * 2) % 128
                notes.append((new_note, new_velocity, msg.time))
        return notes

    def brownian_transform(self, midi_file, step_size=1):
        """Transform MIDI using Brownian motion."""
        notes = []
        current_note = 60  # Middle C

        for msg in midi_file:
            if msg.type == 'note_on':
                current_note += random.choice([-step_size, step_size])
                current_note = max(0, min(127, current_note))
                notes.append((current_note, msg.velocity, msg.time))
        return notes

    def _midi_to_grid(self, midi_file):
        """Convert MIDI notes to a 2D grid for Game of Life."""
        grid = np.zeros((128, 128))  # MIDI note range (0-127)
        current_time = 0
        for msg in midi_file:
            if msg.type == 'note_on':
                note = int(msg.note)
                time_step = int(current_time) % 128
                grid[note, time_step] = 1
            current_time += msg.time
        return grid

    def _grid_to_notes(self, grid):
        """Convert Game of Life grid back to MIDI notes."""
        notes = []
        for i in range(grid.shape[0]):
            for j in range(grid.shape[1]):
                if grid[i, j] > 0:
                    note = int(i)
                    velocity = 64
                    time = int(j)
                    notes.append((note, velocity, time))
        return notes

    def _count_neighbors(self, grid, x, y):
        """Count live neighbors in Game of Life."""
        count = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue
                nx, ny = x + i, y + j
                if 0 <= nx < grid.shape[0] and 0 <= ny < grid.shape[1]:
                    count += grid[nx, ny]
        return count

    def _notes_to_audio(self, notes, duration=5.0):
        """Convert notes to audio signal."""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        signal = np.zeros_like(t)

        for note, velocity, time in notes:
            freq = 440.0 * (2.0 ** ((note - 69) / 12.0))
            note_signal = np.sin(2 * np.pi * freq * t)
            note_signal *= velocity / 127.0
            signal += note_signal

        if np.max(np.abs(signal)) > 0:
            signal = signal / np.max(np.abs(signal))

        return signal

    def export_to_audio(self, notes, output_file, format='wav', duration=5.0):
        """
        Export transformed notes to an audio file.
        """
        signal = self._notes_to_audio(notes, duration)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        try:
            sf.write(output_file, signal, self.sample_rate, format=format)
            print(f"Successfully exported audio to {output_file}")
            return True
        except Exception as e:
            print(f"Error exporting audio: {str(e)}")
            return False

    # The visualize_pattern method is intentionally omitted because visualization is now handled via PyQtGraph.

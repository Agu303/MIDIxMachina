import mido
import numpy as np
import pygame
from perlin_noise import PerlinNoise
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import random
import soundfile as sf
import os
from matplotlib.animation import FuncAnimation
from matplotlib.colors import LinearSegmentedColormap

class MIDITransformer:
    def __init__(self):
        self.sample_rate = 44100
        pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2)
        
    def load_midi(self, file_path):
        """Load a MIDI file and return its contents."""
        return mido.MidiFile(file_path)
    
    def game_of_life_transform(self, midi_file, generations=10):
        """Transform MIDI using Conway's Game of Life algorithm with special rules."""
        # Get tempo from MIDI file
        tempo = self._get_midi_tempo(midi_file)
        ticks_per_beat = midi_file.ticks_per_beat
        
        # Convert MIDI notes to initial grid with duration information
        grid, note_durations = self._midi_to_grid_with_duration(midi_file, tempo, ticks_per_beat)
        transformed_notes = []
        
        # Animation frames (20 FPS)
        frames_per_second = 20
        total_frames = int(generations * frames_per_second)
        
        for frame in range(total_frames):
            new_grid = np.zeros_like(grid)
            current_generation = frame // frames_per_second
            
            # Update grid based on Game of Life rules
            for i in range(grid.shape[0]):
                for j in range(grid.shape[1]):
                    if grid[i, j] > 0:  # Cell is alive
                        # Check if it's a C note (immortal)
                        if i % 12 == 0:  # C notes are every 12 semitones
                            new_grid[i, j] = grid[i, j]
                            continue
                            
                        neighbors = self._count_neighbors(grid, i, j)
                        if neighbors < 2 or neighbors > 3:
                            new_grid[i, j] = max(0, grid[i, j] - 1)  # Fade out
                        else:
                            new_grid[i, j] = grid[i, j]  # Stay alive
                    else:
                        neighbors = self._count_neighbors(grid, i, j)
                        if neighbors == 3:
                            new_grid[i, j] = note_durations[i, j]  # Born with full duration
            
            grid = new_grid
            transformed_notes.append(self._grid_to_notes(grid))
        
        return transformed_notes
    
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
                    # Convert duration to frames (20 FPS)
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
                # Map noise value to MIDI note
                new_note = int((value + 1) * 64)  # Scale to 0-127
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
                # Map Lorenz coordinates to MIDI parameters
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
                # Random walk in note space
                current_note += random.choice([-step_size, step_size])
                current_note = max(0, min(127, current_note))
                notes.append((current_note, msg.velocity, msg.time))
        return notes
    
    def _midi_to_grid(self, midi_file):
        """Convert MIDI notes to a 2D grid for Game of Life."""
        # Initialize grid with zeros
        grid = np.zeros((128, 128))  # MIDI note range (0-127)
        
        # Track time to create proper time steps
        current_time = 0
        for msg in midi_file:
            if msg.type == 'note_on':
                # Ensure note and time are integers
                note = int(msg.note)
                time_step = int(current_time) % 128  # Wrap around if needed
                grid[note, time_step] = 1
            current_time += msg.time
        
        return grid
    
    def _grid_to_notes(self, grid):
        """Convert Game of Life grid back to MIDI notes."""
        notes = []
        for i in range(grid.shape[0]):
            for j in range(grid.shape[1]):
                if grid[i, j] == 1:
                    # Convert grid indices back to MIDI parameters
                    note = int(i)  # Ensure integer note number
                    velocity = 64  # Default velocity
                    time = int(j)  # Ensure integer time step
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
            # Convert MIDI note to frequency
            freq = 440.0 * (2.0 ** ((note - 69) / 12.0))
            # Create sine wave for the note
            note_signal = np.sin(2 * np.pi * freq * t)
            # Apply velocity (volume)
            note_signal *= velocity / 127.0
            # Add to main signal
            signal += note_signal
        
        # Normalize the signal
        if np.max(np.abs(signal)) > 0:
            signal = signal / np.max(np.abs(signal))
        
        return signal
    
    def export_to_audio(self, notes, output_file, format='wav', duration=5.0):
        """
        Export transformed notes to an audio file.
        
        Args:
            notes: List of (note, velocity, time) tuples
            output_file: Output file path
            format: Audio format ('wav', 'flac', 'ogg', 'mp3')
            duration: Duration of the audio in seconds
        """
        # Get the audio signal
        signal = self._notes_to_audio(notes, duration)
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Export the audio file
        try:
            sf.write(output_file, signal, self.sample_rate, format=format)
            print(f"Successfully exported audio to {output_file}")
            return True
        except Exception as e:
            print(f"Error exporting audio: {str(e)}")
            return False
    
    def visualize_pattern(self, notes, algorithm_name):
        """Visualize the transformed pattern with real-time evolution."""
        if algorithm_name == "Game of Life":
            # Create figure with dark background
            plt.style.use('dark_background')
            fig = plt.figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            
            # Set up the plot
            ax.set_title(f'{algorithm_name} Transformation', color='cyan', fontsize=16, pad=20)
            ax.set_xlabel('Time Step', color='cyan')
            ax.set_ylabel('Note Pitch', color='purple')
            
            # Create animation
            def update(frame):
                ax.clear()
                current_notes = notes[frame]
                
                # Plot current state
                times = [note[2] for note in current_notes]
                pitches = [note[0] for note in current_notes]
                velocities = [note[1] for note in current_notes]
                
                # Color C notes differently (immortal)
                colors = ['yellow' if p % 12 == 0 else 'cyan' for p in pitches]
                
                scatter = ax.scatter(times, pitches, 
                                   c=colors,
                                   s=100,
                                   alpha=0.8)
                
                # Add grid
                ax.grid(True, color='cyan', alpha=0.2)
                
                # Update labels
                ax.set_title(f'{algorithm_name} Transformation - Frame {frame}', 
                           color='cyan', fontsize=16, pad=20)
                ax.set_xlabel('Time Step', color='cyan')
                ax.set_ylabel('Note Pitch', color='purple')
                
                # Set y-axis to show MIDI note range
                ax.set_ylim(0, 127)
                
                # Return a sequence of artists
                return [scatter]
            
            # Create animation
            anim = FuncAnimation(fig, update, frames=len(notes), 
                               interval=50, blit=True)
            
            # Store the animation object in the figure
            fig.anim = anim
            
            plt.tight_layout()
            return fig, ax
        else:
            # For other algorithms, keep the existing 3D visualization
            return self._visualize_3d(notes, algorithm_name)
    
    def _visualize_3d(self, notes, algorithm_name):
        """3D visualization for other algorithms."""
        # Create a custom retro color map
        colors = [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)]
        retro_cmap = LinearSegmentedColormap.from_list('retro', colors)
        
        # Extract note data
        times = [note[2] for note in notes]
        pitches = [note[0] for note in notes]
        velocities = [note[1] for note in notes]
        
        # Create figure with dark background
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Set up the plot
        ax.set_title(f'{algorithm_name} Transformation', color='cyan', fontsize=16, pad=20)
        ax.set_xlabel('Time', color='cyan')
        ax.set_ylabel('Note', color='purple')
        ax.set_zlabel('Velocity', color='yellow')
        
        # Create wireframe grid
        x = np.linspace(min(times), max(times), 20)
        y = np.linspace(min(pitches), max(pitches), 20)
        X, Y = np.meshgrid(x, y)
        Z = np.zeros_like(X)
        
        # Initial plot
        wire = ax.plot_wireframe(X, Y, Z, color='cyan', alpha=0.3)
        scatter = ax.scatter(times, pitches, velocities, 
                           c=velocities, 
                           cmap=retro_cmap,
                           s=100,
                           alpha=0.8)
        
        plt.tight_layout()
        return fig, ax

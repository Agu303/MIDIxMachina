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
        """Transform MIDI using Conway's Game of Life algorithm."""
        # Convert MIDI notes to initial grid
        grid = self._midi_to_grid(midi_file)
        transformed_notes = []
        
        for _ in range(generations):
            new_grid = np.zeros_like(grid)
            for i in range(grid.shape[0]):
                for j in range(grid.shape[1]):
                    neighbors = self._count_neighbors(grid, i, j)
                    if grid[i, j] == 1:
                        if neighbors < 2 or neighbors > 3:
                            new_grid[i, j] = 0
                        else:
                            new_grid[i, j] = 1
                    else:
                        if neighbors == 3:
                            new_grid[i, j] = 1
            grid = new_grid
            transformed_notes.append(self._grid_to_notes(grid))
        
        return transformed_notes
    
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
        """Visualize the transformed pattern with rhythmic pulsing retro wireframe."""
        # Create a custom retro color map
        colors = [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)]  # Black to Green to Yellow to Red
        retro_cmap = LinearSegmentedColormap.from_list('retro', colors)
        
        # Extract note data
        times = [note[2] for note in notes]  # time steps on x-axis
        pitches = [note[0] for note in notes]  # note pitches on y-axis
        velocities = [note[1] for note in notes]  # velocity on z-axis
        
        # Create figure with dark background
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Set up the plot
        ax.set_title(f'{algorithm_name} Transformation', color='cyan', fontsize=16, pad=20)
        ax.set_xlabel('Time', color='cyan')
        ax.set_ylabel('Note', color='purple')
        ax.set_zlabel('Velocity', color='yellow')
        
        # Create wireframe grid with time on x-axis
        x = np.linspace(min(times), max(times), 20)  # time steps
        y = np.linspace(min(pitches), max(pitches), 20)  # note pitches
        X, Y = np.meshgrid(x, y)
        Z = np.zeros_like(X)
        
        # Initial plot
        wire = ax.plot_wireframe(X, Y, Z, color='cyan', alpha=0.3)
        scatter = ax.scatter(times, pitches, velocities, 
                           c=velocities, 
                           cmap=retro_cmap,
                           s=100,
                           alpha=0.8)
        
        # Add pulsing effect
        def update(frame):
            # Clear previous frame
            ax.clear()
            
            # Update wireframe with pulsing effect
            pulse = np.sin(frame * 0.1) * 0.5 + 0.5  # Oscillating between 0 and 1
            Z = np.sin(X * 0.1 + frame * 0.2) * pulse
            
            # Recreate the plot
            wire = ax.plot_wireframe(X, Y, Z, color='cyan', alpha=0.3)
            scatter = ax.scatter(times, pitches, velocities, 
                               c=velocities, 
                               cmap=retro_cmap,
                               s=100,
                               alpha=0.8)
            
            # Update labels
            ax.set_title(f'{algorithm_name} Transformation', color='cyan', fontsize=16, pad=20)
            ax.set_xlabel('Time', color='cyan')
            ax.set_ylabel('Note', color='purple')
            ax.set_zlabel('Velocity', color='yellow')
            
            # Set view angle to rotate slowly
            ax.view_init(elev=20, azim=frame)
            
            return wire, scatter
        
        # Create animation
        anim = FuncAnimation(fig, update, frames=360, interval=50, blit=True)
        
        # Add algorithm-specific visual elements
        if algorithm_name == "Game of Life":
            # Add grid lines
            ax.grid(True, color='cyan', alpha=0.2)
            # Add time progression lines
            for pitch in np.unique(pitches):
                mask = [p == pitch for p in pitches]
                if any(mask):
                    ax.plot([t for i, t in enumerate(times) if mask[i]],
                           [p for i, p in enumerate(pitches) if mask[i]],
                           [v for i, v in enumerate(velocities) if mask[i]],
                           'cyan', alpha=0.1)
        elif algorithm_name == "Perlin Noise":
            # Add flowing lines
            for i in range(5):
                ax.plot(times, pitches, velocities + i*10, 'cyan', alpha=0.1)
        elif algorithm_name == "Lorenz Attractor":
            # Add spiral effect
            theta = np.linspace(0, 4*np.pi, 100)
            ax.plot(np.sin(theta)*10, np.cos(theta)*10, theta*5, 'cyan', alpha=0.2)
        elif algorithm_name == "Brownian Motion":
            # Add random walk lines
            for i in range(3):
                random_walk = np.cumsum(np.random.randn(len(times)))
                ax.plot(times, pitches + random_walk, velocities, 'cyan', alpha=0.1)
        
        plt.tight_layout()
        plt.show()

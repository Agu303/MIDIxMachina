# MIDIxMachina

<img src="MIDIxMachina/mm-logo.png" alt="Alt text" width="50%"/>

MIDIxMachina is a creative tool that transforms MIDI files using various mathematical and algorithmic transformations, creating unique musical patterns and visualizations.

## Current Features

### Game of Life Transformation
- **Implementation**: Conway's Game of Life rules applied to MIDI notes
- **Special Rules**:
  - C notes (every 12 semitones) are immortal cells
  - Other notes follow standard Game of Life rules
  - Notes fade out when they die
- **Visualization**:
  - Real-time animation of note evolution
  - Yellow dots for C notes (immortal cells)
  - Cyan dots for other notes
  - Grid-based visualization showing note pitch vs time


## Planned Features
**Audio Export**:
- Customizable duration
- Preserves note velocities
- Export transformed patterns to WAV, FLAC, OGG, or MP3

### Perlin Noise Transformation
- Generate smooth, continuous note patterns using Perlin noise
- Control over noise parameters (scale, octaves)
- 3D visualization of noise space
- Audio export with customizable parameters

### Lorenz Attractor Transformation
- Transform notes using the Lorenz system of differential equations
- Interactive control over system parameters (σ, ρ, β)
- 3D visualization of the attractor
- Audio export with parameter mapping to musical elements

### Brownian Motion Transformation
- Random walk-based note transformations
- Control over step size and direction
- Visualization of note paths
- Audio export with customizable parameters

## General Planned Improvements
- Interactive parameter controls for all transformations
- Real-time preview of transformations
- Multiple transformation chaining
- Export to MIDI format
- Batch processing of multiple files
- Custom transformation rules
- Advanced visualization options
- Performance optimizations

## Installation
```bash
pip install -r requirements.txt
```

## Usage
1. Run the GUI application:
```bash
python -m MIDIxMachina.gui
```
2. Load a MIDI file
3. Select a transformation
4. Apply the transformation
5. Export the result to audio if desired

## Requirements
- Python 3.8+
- PyQt6
- matplotlib
- numpy
- mido
- pygame
- soundfile
- perlin-noise
- scipy

## License
MIT License 

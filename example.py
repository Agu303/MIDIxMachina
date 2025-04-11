from midi_transform import MIDITransformer
import os

def get_user_input():
    """Get MIDI file path and transformation choice from user."""
    while True:
        midi_file_path = input("Enter the path to your MIDI file: ")
        if os.path.exists(midi_file_path):
            break
        print(f"File '{midi_file_path}' not found. Please try again.")
    
    print("\nAvailable transformations:")
    print("1. Game of Life")
    print("2. Perlin Noise")
    print("3. Lorenz Attractor")
    print("4. Brownian Motion")
    
    while True:
        try:
            choice = int(input("\nSelect a transformation (1-4): "))
            if 1 <= choice <= 4:
                break
            print("Please enter a number between 1 and 4.")
        except ValueError:
            print("Please enter a valid number.")
    
    return midi_file_path, choice

def get_audio_export_options():
    """Get audio export options from user."""
    print("\nAvailable audio formats:")
    print("1. WAV (Uncompressed, high quality)")
    print("2. FLAC (Lossless compression)")
    print("3. OGG (Lossy compression)")
    print("4. MP3 (Lossy compression)")
    
    while True:
        try:
            format_choice = int(input("\nSelect audio format (1-4): "))
            if 1 <= format_choice <= 4:
                break
            print("Please enter a number between 1 and 4.")
        except ValueError:
            print("Please enter a valid number.")
    
    format_map = {1: 'wav', 2: 'flac', 3: 'ogg', 4: 'mp3'}
    format = format_map[format_choice]
    
    while True:
        try:
            duration = float(input("\nEnter audio duration in seconds (default: 5.0): ") or "5.0")
            if duration > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")
    
    output_file = input("\nEnter output file path (without extension): ")
    output_file = f"{output_file}.{format}"
    
    return output_file, format, duration

def apply_transformation(transformer, midi_file, choice):
    """Apply the selected transformation and visualize the result."""
    if choice == 1:
        print("\nApplying Game of Life transformation...")
        notes = transformer.game_of_life_transform(midi_file)
        transformer.visualize_pattern(notes[0], "Game of Life")
        return notes[0]
    elif choice == 2:
        print("\nApplying Perlin noise transformation...")
        notes = transformer.perlin_transform(midi_file)
        transformer.visualize_pattern(notes, "Perlin Noise")
        return notes
    elif choice == 3:
        print("\nApplying Lorenz attractor transformation...")
        notes = transformer.lorenz_transform(midi_file)
        transformer.visualize_pattern(notes, "Lorenz Attractor")
        return notes
    elif choice == 4:
        print("\nApplying Brownian motion transformation...")
        notes = transformer.brownian_transform(midi_file)
        transformer.visualize_pattern(notes, "Brownian Motion")
        return notes

def main():
    print("Welcome to MIDIxMachina - MIDI Transformation Tool")
    print("================================================")
    
    # Get user input
    midi_file_path, choice = get_user_input()
    
    # Initialize the transformer
    transformer = MIDITransformer()
    
    try:
        # Load the MIDI file
        midi_file = transformer.load_midi(midi_file_path)
        
        # Apply the selected transformation
        transformed_notes = apply_transformation(transformer, midi_file, choice)
        
        # Get audio export options
        output_file, format, duration = get_audio_export_options()
        
        # Export to audio
        if transformer.export_to_audio(transformed_notes, output_file, format, duration):
            print("\nTransformation completed successfully!")
            print(f"Audio file saved as: {output_file}")
        
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        print("Please make sure the MIDI file is valid and try again.")

if __name__ == "__main__":
    main() 
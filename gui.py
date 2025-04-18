import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QComboBox, QDoubleSpinBox, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from midi_transform import MIDITransformer
import pyqtgraph as pg

class MIDITransformerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDIxMachina - MIDI Transformation Tool")
        self.setMinimumSize(1000, 800)
        
        # Initialize the transformer
        self.transformer = MIDITransformer()
        self.midi_file = None
        self.transformed_notes = None
        self.animation = None  # Store the animation object
        self.current_frame = 0
        self.notes_frames = None  # Store all animation frames
        self.update_timer = None  # For manual animation
        
        # Create the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("QLabel { padding: 5px; }")
        browse_button = QPushButton("Browse MIDI File")
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(browse_button)
        layout.addLayout(file_layout)
        
        # Transformation selection
        transform_layout = QHBoxLayout()
        transform_layout.addWidget(QLabel("Transformation:"))
        self.transform_combo = QComboBox()
        self.transform_combo.addItems([
            "Game of Life",
            "Perlin Noise",
            "Lorenz Attractor",
            "Brownian Motion"
        ])
        transform_layout.addWidget(self.transform_combo)
        transform_button = QPushButton("Apply Transformation")
        transform_button.clicked.connect(self.apply_transformation)
        transform_layout.addWidget(transform_button)
        layout.addLayout(transform_layout)
        
        # Loading text
        self.loading_label = QLabel("")
        self.loading_label.setStyleSheet("QLabel { color: #333333; font-weight: bold; font-size: 14px; padding: 10px; background-color: #f0f0f0; border-radius: 4px; }")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)
        
        # PyQtGraph PlotWidget for visualization
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k')  # Black background
        self.plot_widget.setLabel('left', 'Note Pitch')
        self.plot_widget.setLabel('bottom', 'Time Step')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot_widget)

        
        # Animation controls
        anim_controls = QHBoxLayout()
        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.toggle_animation)
        self.play_button.setEnabled(False)
        anim_controls.addWidget(self.play_button)
        
        self.frame_label = QLabel("Generation: 0")
        anim_controls.addWidget(self.frame_label)
        layout.addLayout(anim_controls)
        
        # Audio export options
        export_layout = QHBoxLayout()
        
        # Format selection
        export_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["WAV", "FLAC", "OGG", "MP3"])
        export_layout.addWidget(self.format_combo)
        
        # Duration selection
        export_layout.addWidget(QLabel("Duration (s):"))
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.1, 60.0)
        self.duration_spin.setValue(5.0)
        self.duration_spin.setSingleStep(0.1)
        export_layout.addWidget(self.duration_spin)
        
        # Output file selection
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Output file path (without extension)")
        export_layout.addWidget(self.output_edit)
        
        export_button = QPushButton("Export Audio")
        export_button.clicked.connect(self.export_audio)
        export_layout.addWidget(export_button)
        
        layout.addLayout(export_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select MIDI File",
            "",
            "MIDI Files (*.mid *.midi)"
        )
        if file_name:
            self.file_label.setText(os.path.basename(file_name))
            try:
                self.midi_file = self.transformer.load_midi(file_name)
                self.statusBar().showMessage("File loaded successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load MIDI file: {str(e)}")
    
    def apply_transformation(self):
        if not self.midi_file:
            QMessageBox.warning(self, "Warning", "Please select a MIDI file first")
            return
        
        try:
            self.loading_label.setText("Processing transformation... Please wait...")
            self.loading_label.repaint()  # Force immediate update
            QApplication.processEvents()  # Process any pending events
            
            # Stop any running animation timer
            if self.update_timer:
                self.update_timer.stop()
                self.update_timer = None
            
            choice = self.transform_combo.currentIndex() + 1
            self.notes_frames = self._apply_transformation(choice)
            self.transformed_notes = self.notes_frames[-1] if self.notes_frames else None
            
            # Reset animation state
            self.current_frame = 0
            
            # Enable play button
            self.play_button.setEnabled(True)
            self.play_button.setText("▶ Play")
            
            # Update display
            self.update_frame(0)
            
            self.loading_label.setText("")  # Clear loading text
            self.statusBar().showMessage("Transformation applied successfully")
        except Exception as e:
            self.loading_label.setText("")  # Clear loading text
            QMessageBox.critical(self, "Error", f"Transformation failed: {str(e)}")
    
    def _apply_transformation(self, choice):
        self.plot_widget.clear()

        if choice == 1:
            return self.transformer.game_of_life_transform(self.midi_file)
        elif choice == 2:
            return self.transformer.perlin_transform(self.midi_file)
        elif choice == 3:
            return self.transformer.lorenz_transform(self.midi_file)
        elif choice == 4:
            return self.transformer.brownian_transform(self.midi_file)
    
    def update_frame(self, frame=None):
        if frame is not None:
            self.current_frame = frame
        
        if not self.notes_frames or self.current_frame >= len(self.notes_frames):
            return
        
        current_notes = self.notes_frames[self.current_frame]
        
        # Clear previous plot
        self.plot_widget.clear()
        
        # Plot current state if there are notes
        if current_notes:
            times = [note[2] for note in current_notes]
            pitches = [note[0] for note in current_notes]
            
            # Immortal C notes = Yellow
            brushes = [
            pg.mkBrush('yellow') if pitch % 12 == 0 else pg.mkBrush('cyan')
            for pitch in pitches
            ]
            
            # Draw scatter plot
            scatter = pg.ScatterPlotItem(x=times, y=pitches, brush=brushes, size=10, pen=None)
            self.plot_widget.addItem(scatter)

            # Adjust plot range
            self.plot_widget.setYRange(0, 127)
            if times:
                self.plot_widget.setXRange(min(times) - 1, max(times) + 1)
            else:
                self.plot_widget.setXRange(0, 10)
        else:
            self.plot_widget.setYRange(0, 127)
            self.plot_widget.setXRange(0, 10)

        # Update label
        self.frame_label.setText(f"Generation: {self.current_frame}")
    
    def toggle_animation(self):
        if not self.update_timer:
            # Start animation
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.next_frame)
            self.update_timer.start(200)  # 200ms interval
            self.play_button.setText("⏸ Pause")
        else:
            # Stop animation
            self.update_timer.stop()
            self.update_timer = None
            self.play_button.setText("▶ Play")
    
    def next_frame(self):
        if self.notes_frames:
            self.current_frame = (self.current_frame + 1) % len(self.notes_frames)
            
            current_notes = self.notes_frames[self.current_frame]
            if not current_notes:
                self.update_timer.stop()
                self.update_timer = None
                self.play_button.setText("▶ Play")
                self.statusBar().showMessage("Animation stopped: no more active notes.")
                return
            
            self.update_frame()

    
    def export_audio(self):
        if not self.transformed_notes:
            QMessageBox.warning(self, "Warning", "Please apply a transformation first")
            return
        
        output_path = self.output_edit.text()
        if not output_path:
            QMessageBox.warning(self, "Warning", "Please enter an output file path")
            return
        
        format_map = {
            "WAV": "wav",
            "FLAC": "flac",
            "OGG": "ogg",
            "MP3": "mp3"
        }
        
        format = format_map[self.format_combo.currentText()]
        output_file = f"{output_path}.{format}"
        duration = self.duration_spin.value()
        
        try:
            # Use the current frame for export
            notes_to_export = self.notes_frames[self.current_frame]
            
            if self.transformer.export_to_audio(notes_to_export, output_file, format, duration):
                QMessageBox.information(self, "Success", f"Audio exported successfully to {output_file}")
                self.statusBar().showMessage("Audio exported successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to export audio")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MIDITransformerGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
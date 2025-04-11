import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QComboBox, QDoubleSpinBox, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt
from midi_transform import MIDITransformer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MIDITransformerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDIxMachina - MIDI Transformation Tool")
        self.setMinimumSize(800, 600)
        
        # Initialize the transformer
        self.transformer = MIDITransformer()
        self.midi_file = None
        self.transformed_notes = None
        
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
        
        # Matplotlib figure for visualization
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
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
            choice = self.transform_combo.currentIndex() + 1
            self.transformed_notes = self._apply_transformation(choice)
            self.statusBar().showMessage("Transformation applied successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Transformation failed: {str(e)}")
    
    def _apply_transformation(self, choice):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if choice == 1:
            notes = self.transformer.game_of_life_transform(self.midi_file)
            self.transformer.visualize_pattern(notes[0], "Game of Life")
            return notes[0]
        elif choice == 2:
            notes = self.transformer.perlin_transform(self.midi_file)
            self.transformer.visualize_pattern(notes, "Perlin Noise")
            return notes
        elif choice == 3:
            notes = self.transformer.lorenz_transform(self.midi_file)
            self.transformer.visualize_pattern(notes, "Lorenz Attractor")
            return notes
        elif choice == 4:
            notes = self.transformer.brownian_transform(self.midi_file)
            self.transformer.visualize_pattern(notes, "Brownian Motion")
            return notes
        
        self.canvas.draw()
    
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
            if self.transformer.export_to_audio(self.transformed_notes, output_file, format, duration):
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
"""Keyboard to guitar fret mapping"""

import pygame
from typing import Dict, Tuple, Optional, List


class KeyboardMapping:
    """Maps keyboard keys to guitar strings and frets using column-based layout
    
    Each keyboard column represents one fret across all strings.
    Layout: G(1234567890), D(QWERTYUIOP), A(ASDFGHJKL;), E(ZXCVBNM,./)
    """
    
    def __init__(self) -> None:
        """Initialize keyboard mapping with guitar tuning and layout"""
        # Standard guitar tuning (4 strings, low to high pitch)
        self.string_names: List[str] = ["G", "D", "A", "E"]
        self.string_base_notes: List[int] = [55, 50, 45, 40]  # MIDI note numbers for open strings
        
        # Common tuning note options per string (ordered from high to low for easy selection)
        self.string_tuning_options: Dict[int, List[Tuple[str, int]]] = {
            0: [("G", 55), ("F#/Gb", 54), ("F", 53), ("E", 52), ("D#/Eb", 51)],  # G string options
            1: [("D", 50), ("C#/Db", 49), ("C", 48), ("B", 47), ("A#/Bb", 46)],  # D string options  
            2: [("A", 45), ("G#/Ab", 44), ("G", 43), ("F#/Gb", 42), ("F", 41)],  # A string options
            3: [("E", 40), ("D#/Eb", 39), ("D", 38), ("C#/Db", 37), ("C", 36), ("B", 35)]  # E string options (includes Drop D)
        }
        
        # Column-based keyboard layout: each column = one fret position
        self.keyboard_columns: List[List[int]] = [
            [pygame.KSCAN_1, pygame.KSCAN_Q, pygame.KSCAN_A, pygame.KSCAN_Z],             # Fret 0
            [pygame.KSCAN_2, pygame.KSCAN_W, pygame.KSCAN_S, pygame.KSCAN_X],             # Fret 1
            [pygame.KSCAN_3, pygame.KSCAN_E, pygame.KSCAN_D, pygame.KSCAN_C],             # Fret 2
            [pygame.KSCAN_4, pygame.KSCAN_R, pygame.KSCAN_F, pygame.KSCAN_V],             # Fret 3
            [pygame.KSCAN_5, pygame.KSCAN_T, pygame.KSCAN_G, pygame.KSCAN_B],             # Fret 4
            [pygame.KSCAN_6, pygame.KSCAN_Y, pygame.KSCAN_H, pygame.KSCAN_N],             # Fret 5
            [pygame.KSCAN_7, pygame.KSCAN_U, pygame.KSCAN_J, pygame.KSCAN_M],             # Fret 6
            [pygame.KSCAN_8, pygame.KSCAN_I, pygame.KSCAN_K, pygame.KSCAN_COMMA],         # Fret 7
            [pygame.KSCAN_9, pygame.KSCAN_O, pygame.KSCAN_L, pygame.KSCAN_PERIOD],        # Fret 8
            [pygame.KSCAN_0, pygame.KSCAN_P, pygame.KSCAN_SEMICOLON, pygame.KSCAN_SLASH], # Fret 9
        ]
        
        # Pre-computed mapping for fast lookup
        self.scancode_mapping: Dict[int, Tuple[int, int]] = {}
        self._generate_mapping()
    
    def _generate_mapping(self) -> None:
        """Generate scancode to (string_index, fret) mapping for fast lookup"""
        for fret, column in enumerate(self.keyboard_columns):
            for string_index, scancode in enumerate(column):
                self.scancode_mapping[scancode] = (string_index, fret)
    
    def get_guitar_position(self, scancode: int) -> Optional[Tuple[int, int]]:
        """Get guitar position for a keyboard scancode
        
        Args:
            scancode (int): Pygame keyboard scancode
            
        Returns:
            Optional[Tuple[int, int]]: (string_index, fret) tuple if mapped, None otherwise
        """
        return self.scancode_mapping.get(scancode)
    
    def get_midi_note(self, string_index: int, fret: int, octave_offset: int = 0) -> int:
        """Calculate MIDI note number for given string and fret
        
        Args:
            string_index (int): Guitar string index (0-3)
            fret (int): Fret position (0-9)
            octave_offset (int): Octave offset (-3 to +3, defaults to 0)
            
        Returns:
            int: MIDI note number (open string + fret offset + octave offset)
        """
        base_note = self.string_base_notes[string_index] + fret
        # Each octave is 12 semitones in MIDI
        return base_note + (octave_offset * 12)
    
    def get_string_name(self, string_index: int) -> str:
        """Get display name for a guitar string
        
        Args:
            string_index (int): String index (0-3)
            
        Returns:
            str: String name (G, D, A, or E)
        """
        return self.string_names[string_index]
    
    def set_string_tuning(self, string_index: int, midi_note: int, note_name: str) -> None:
        """Set the tuning for a specific string
        
        Args:
            string_index (int): String index (0-3)
            midi_note (int): MIDI note number for the open string
            note_name (str): Display name for the tuning (e.g., "D", "D#/Eb")
        """
        if 0 <= string_index < len(self.string_base_notes):
            self.string_base_notes[string_index] = midi_note
            self.string_names[string_index] = note_name
    
    def get_tuning_options_for_string(self, string_index: int) -> List[Tuple[str, int]]:
        """Get available tuning options for a specific string
        
        Args:
            string_index (int): String index (0-3)
            
        Returns:
            List[Tuple[str, int]]: List of (note_name, midi_note) tuples
        """
        return self.string_tuning_options.get(string_index, [])
    
    def apply_tuning_preset(self, preset_name: str) -> bool:
        """Apply a common tuning preset
        
        Args:
            preset_name (str): Name of the tuning preset
            
        Returns:
            bool: True if preset was applied successfully
        """
        presets = {
            "Standard": [("G", 55), ("D", 50), ("A", 45), ("E", 40)],
            "Drop D": [("G", 55), ("D", 50), ("A", 45), ("D", 38)],
            "Drop C": [("F", 53), ("C", 48), ("G", 43), ("C", 36)],
            "Drop B": [("E", 52), ("B", 47), ("F#/Gb", 42), ("B", 35)],
            "All Fourths": [("G", 55), ("D", 50), ("A", 45), ("E", 40)],  # Same as standard for 4-string
            "Open G": [("G", 55), ("D", 50), ("G", 43), ("D", 38)]
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            for i, (note_name, midi_note) in enumerate(preset):
                self.set_string_tuning(i, midi_note, note_name)
            return True
        return False
    
    def get_current_tuning_name(self) -> str:
        """Get a descriptive name for the current tuning
        
        Returns:
            str: Name of the current tuning or "Custom" if no preset matches
        """
        current = [(name, note) for name, note in zip(self.string_names, self.string_base_notes)]
        
        # Check against known presets
        if current == [("G", 55), ("D", 50), ("A", 45), ("E", 40)]:
            return "Standard"
        elif current == [("G", 55), ("D", 50), ("A", 45), ("D", 38)]:
            return "Drop D"
        elif current == [("F", 53), ("C", 48), ("G", 43), ("C", 36)]:
            return "Drop C"
        elif current == [("E", 52), ("B", 47), ("F#/Gb", 42), ("B", 35)]:
            return "Drop B"
        elif current == [("G", 55), ("D", 50), ("G", 43), ("D", 38)]:
            return "Open G"
        else:
            return "Custom"
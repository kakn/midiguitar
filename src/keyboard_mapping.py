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
    
    def get_midi_note(self, string_index: int, fret: int) -> int:
        """Calculate MIDI note number for given string and fret
        
        Args:
            string_index (int): Guitar string index (0-3)
            fret (int): Fret position (0-9)
            
        Returns:
            int: MIDI note number (open string + fret offset)
        """
        return self.string_base_notes[string_index] + fret
    
    def get_string_name(self, string_index: int) -> str:
        """Get display name for a guitar string
        
        Args:
            string_index (int): String index (0-3)
            
        Returns:
            str: String name (G, D, A, or E)
        """
        return self.string_names[string_index]
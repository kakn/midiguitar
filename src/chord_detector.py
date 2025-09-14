"""Chord detection using pychord library"""

from typing import Dict, List, Tuple, Optional, Any
from pychord import find_chords_from_notes


class ChordDetector:
    """Detects musical chords from sets of MIDI notes
    
    Uses the pychord library for comprehensive chord recognition,
    including complex chords, inversions, and partial chord matching.
    """
    
    def __init__(self) -> None:
        """Initialize chord detector with chromatic note names"""
        self.note_names: List[str] = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def midi_to_note_name(self, midi_note: int) -> str:
        """Convert MIDI note number to note name
        
        Args:
            midi_note (int): MIDI note number (0-127)
            
        Returns:
            str: Note name without octave (e.g., 'C', 'F#', 'Bb')
        """
        return self.note_names[midi_note % 12]
    
    def midi_to_note_with_octave(self, midi_note: int) -> str:
        """Convert MIDI note number to note name with octave
        
        Args:
            midi_note (int): MIDI note number (0-127)
            
        Returns:
            str: Note name with octave (e.g., 'C4', 'F#3')
        """
        note_name: str = self.note_names[midi_note % 12]
        octave: int = (midi_note // 12) - 1
        return f"{note_name}{octave}"
    
    def get_active_notes_info(self, active_notes: Dict[Tuple[int, int], int]) -> Dict[str, Any]:
        """Analyze currently active notes and detect chords
        
        Args:
            active_notes (Dict[Tuple[int, int], int]): Dictionary mapping (string, fret) to MIDI note numbers
            
        Returns:
            Dict[str, Any]: Dictionary containing note information and chord analysis
        """
        if not active_notes:
            return {
                'notes': [],
                'note_names': [],
                'note_names_with_octave': [],
                'note_count': 0,
                'chord': {'name': None, 'root': None}
            }
        
        # Extract and analyze the notes
        midi_notes: List[int] = list(active_notes.values())
        note_names: List[str] = [self.midi_to_note_name(note) for note in midi_notes]
        note_names_with_octave: List[str] = [self.midi_to_note_with_octave(note) for note in midi_notes]
        
        chord_info: Dict[str, Optional[str]] = self._detect_chord(midi_notes)
        
        return {
            'notes': midi_notes,
            'note_names': note_names,
            'note_names_with_octave': note_names_with_octave,
            'note_count': len(midi_notes),
            'chord': chord_info
        }
    
    def _detect_chord(self, midi_notes: List[int]) -> Dict[str, Optional[str]]:
        """Detect chord from MIDI notes using multiple strategies
        
        Args:
            midi_notes (List[int]): List of MIDI note numbers
            
        Returns:
            Dict[str, Optional[str]]: Dictionary with 'name' and 'root' keys for detected chord
        """
        if len(midi_notes) < 2:
            return {'name': None, 'root': None}
        
        # Remove duplicate notes (same pitch class)
        note_names: List[str] = list(set(self.midi_to_note_name(note) for note in midi_notes))
        
        if len(note_names) < 2:
            return {'name': None, 'root': None}
        
        found_chords = []
        
        # Strategy 1: Try each note as potential root
        for potential_root in note_names:
            remaining_notes: List[str] = [n for n in note_names if n != potential_root]
            ordered_notes: List[str] = [potential_root] + sorted(remaining_notes)
            
            chords = find_chords_from_notes(ordered_notes)
            if chords:
                found_chords.extend(chords)
        
        # Strategy 2: Try original note order
        if not found_chords:
            found_chords = find_chords_from_notes(note_names)
        
        # Strategy 3: Try chromatic ordering
        if not found_chords:
            chromatic_order: List[str] = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            sorted_notes: List[str] = sorted(note_names, key=lambda x: chromatic_order.index(x))
            found_chords = find_chords_from_notes(sorted_notes)
        
        if found_chords:
            best_chord = found_chords[0]
            return {
                'name': str(best_chord),
                'root': best_chord.root
            }
        
        # Strategy 4: Try partial chord matching (for incomplete chords)
        if len(note_names) >= 3:
            for i, note_to_remove in enumerate(note_names):
                subset: List[str] = note_names[:i] + note_names[i+1:]
                subset_chords = find_chords_from_notes(subset)
                
                if subset_chords:
                    best_chord = subset_chords[0]
                    chord_components = best_chord.components()
                    
                    # Check if the removed note is actually part of this chord
                    if note_to_remove in chord_components:
                        return {
                            'name': f"{str(best_chord)} (partial)",
                            'root': best_chord.root
                        }
        
        # Strategy 5: Power chord detection (root + fifth)
        if len(note_names) == 2:
            chromatic_notes: List[int] = sorted(set(note % 12 for note in midi_notes))
            root, other = chromatic_notes
            interval: int = (other - root) % 12
            
            # Perfect fifth is 7 semitones
            if interval == 7:
                root_name: str = self.note_names[root]
                return {'name': f"{root_name}5", 'root': root_name}
            
            # Check inverted fifth
            interval_inv: int = (root - other) % 12
            if interval_inv == 7:
                root_name = self.note_names[other]
                return {'name': f"{root_name}5", 'root': root_name}
        
        return {'name': None, 'root': None}
"""MIDI Controller with FluidSynth synthesis"""

import fluidsynth
import pygame.midi
from typing import Optional, Dict, Tuple, List


class MidiController:
    """MIDI controller with FluidSynth synthesis and external MIDI output
    
    Handles both high-quality FluidSynth audio synthesis and external MIDI device output.
    Uses General MIDI program numbers for instrument selection.
    """
    
    def __init__(self) -> None:
        """Initialize MIDI controller with FluidSynth and instrument mappings"""
        self.midi_out: Optional[pygame.midi.Output] = None
        self.active_notes: Dict[Tuple[int, int], int] = {}  # {(string, fret): midi_note}
        
        # Dynamic instrument mappings (loaded from SoundFont)
        self.instruments: Dict[str, int] = {}
        self.current_instrument: str = ""
        
        # FluidSynth components
        self.fs: Optional[fluidsynth.Synth] = None
        self.soundfont_id: Optional[int] = None
        self.soundfont_path: str = "data/soundfont.sf2"
        
        self._initialize_fluidsynth()
    
    def _initialize_fluidsynth(self) -> None:
        """Initialize FluidSynth synthesizer with SoundFont"""
        try:
            self.fs = fluidsynth.Synth()
            self.fs.start()
            self.soundfont_id = self.fs.sfload(self.soundfont_path)
            
            if self.soundfont_id != -1:
                # Load all available instruments from the SoundFont
                self._load_instruments_from_soundfont()
                
                # Select first available instrument as default
                if self.instruments:
                    first_instrument = list(self.instruments.keys())[0]
                    self.current_instrument = first_instrument
                    self.fs.program_select(0, self.soundfont_id, 0, self.instruments[first_instrument])
                
                print(f"✅ FluidSynth initialized with {self.soundfont_path}")
                print(f"🎵 Loaded {len(self.instruments)} instruments")
            else:
                print(f"❌ Failed to load SoundFont: {self.soundfont_path}")
                self._use_fallback_instruments()
        except Exception as e:
            print(f"❌ FluidSynth initialization failed: {e}")
            print("🎵 Using basic MIDI instruments instead")
            self.fs = None
            self._use_fallback_instruments()
    
    def _use_fallback_instruments(self) -> None:
        """Use a basic set of General MIDI instruments when FluidSynth fails"""
        self.instruments = {
            "Piano": 0,
            "Electric Piano": 4,
            "Acoustic Guitar (nylon)": 24,
            "Acoustic Guitar (steel)": 25,
            "Electric Guitar (clean)": 26,
            "Electric Guitar (jazz)": 27,
            "Electric Guitar (muted)": 28,
            "Overdriven Guitar": 29,
            "Distortion Guitar": 30,
            "Guitar Harmonics": 31,
            "Acoustic Bass": 32,
            "Electric Bass (finger)": 33,
            "Electric Bass (pick)": 34,
            "Violin": 40,
            "Trumpet": 56,
            "Saxophone": 65,
            "Flute": 73,
            "Synth Lead": 80,
            "Synth Pad": 88,
        }
        self.current_instrument = "Piano"
    
    def _load_instruments_from_soundfont(self) -> None:
        """Dynamically load all available instruments from the loaded SoundFont"""
        try:
            # Get all presets from the loaded SoundFont
            # FluidSynth uses bank/program structure, we'll scan bank 0 (standard melodic instruments)
            bank = 0
            
            for program in range(128):  # MIDI programs 0-127
                try:
                    # Try to select this program to see if it exists
                    result = self.fs.program_select(0, self.soundfont_id, bank, program)
                    
                    if result == 0:  # Success (FluidSynth returns 0 on success)
                        # Try to get the preset name from FluidSynth
                        preset_name = self._get_preset_name(bank, program)
                        
                        if preset_name:
                            self.instruments[preset_name] = program
                        else:
                            # Simple fallback - just program number
                            self.instruments[f"Program {program:03d}"] = program
                            
                except Exception:
                    # If program_select fails, this preset doesn't exist
                    continue
                    
        except Exception as e:
            print(f"⚠️ Failed to introspect SoundFont instruments: {e}")
            # Fallback to a minimal set if introspection fails
            self.instruments = {
                "Program 000": 0,
                "Program 024": 24,  # Acoustic Guitar
                "Program 025": 25,  # Steel Guitar  
                "Program 026": 26,  # Electric Guitar Clean
                "Program 030": 30,  # Distortion Guitar
            }
    
    def _get_preset_name(self, bank: int, program: int) -> Optional[str]:
        """Try to get the actual preset name from FluidSynth
        
        Args:
            bank (int): MIDI bank number
            program (int): MIDI program number
            
        Returns:
            Optional[str]: Preset name if available
        """
        try:
            # Try to get preset info using FluidSynth's sfont API
            if hasattr(self.fs, 'sfont_get_preset'):
                preset = self.fs.sfont_get_preset(self.soundfont_id, bank, program)
                if preset and hasattr(preset, 'get_name'):
                    return preset.get_name()
            
            # Alternative approach: use program_info if available
            if hasattr(self.fs, 'program_info'):
                info = self.fs.program_info(0)  # channel 0
                if info and 'name' in info:
                    return info['name']
            
            # Fallback: return None so we use simple program numbers
            return None
            
        except Exception:
            return None
    
    
    def initialize(self) -> bool:
        """Initialize pygame MIDI output device
        
        Returns:
            True if MIDI device was successfully initialized
        """
        pygame.midi.init()
        device_id: int = pygame.midi.get_default_output_id()
        
        # Find first available output device if default not available
        if device_id == -1:
            device_count: int = pygame.midi.get_count()
            for i in range(device_count):
                device_info = pygame.midi.get_device_info(i)
                if device_info[3]:  # is_output flag
                    device_id = i
                    break
        
        if device_id != -1:
            self.midi_out = pygame.midi.Output(device_id)
            device_name: str = pygame.midi.get_device_info(device_id)[1].decode()
            print(f"✅ MIDI connected: {device_name}")
            self.set_instrument(self.current_instrument)
            return True
        
        return False
    
    def play_note(self, string_index: int, fret: int, midi_note: int, string_name: str = "") -> None:
        """Play a note through both FluidSynth and external MIDI
        
        Args:
            string_index (int): Guitar string index (0-3)
            fret (int): Fret position (0-9)
            midi_note (int): MIDI note number to play
            string_name (str): Display name for the string (G, D, A, E)
        """
        # FluidSynth for immediate, high-quality audio
        if self.fs:
            try:
                self.fs.noteon(0, midi_note, 100)  # Channel 0, velocity 100
            except Exception as e:
                print(f"⚠️ FluidSynth play failed: {e}")
        
        # External MIDI device for hardware synths/DAWs
        if self.midi_out:
            try:
                self.midi_out.note_on(midi_note, 100)
            except Exception as e:
                print(f"⚠️ MIDI play failed: {e}")
        
        # Display note information
        frequency: float = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
        display_name: str = string_name or f"S{string_index}"
        print(f"🎵 {display_name} F{fret} = MIDI {midi_note} ({frequency:.1f}Hz)")
        
        self.active_notes[(string_index, fret)] = midi_note
    
    def stop_note(self, string_index: int, fret: int) -> None:
        """Stop a note on both FluidSynth and external MIDI
        
        Args:
            string_index (int): Guitar string index
            fret (int): Fret position
        """
        if (string_index, fret) not in self.active_notes:
            return
        
        midi_note: int = self.active_notes.pop((string_index, fret))
        
        # Stop note on both audio systems
        if self.fs:
            try:
                self.fs.noteoff(0, midi_note)
            except Exception as e:
                print(f"⚠️ FluidSynth stop failed: {e}")
        
        if self.midi_out:
            try:
                self.midi_out.note_off(midi_note, 0)
            except Exception as e:
                print(f"⚠️ MIDI stop failed: {e}")
    
    def stop_all_notes(self) -> None:
        """Stop all currently active notes"""
        for key in list(self.active_notes.keys()):
            self.stop_note(key[0], key[1])
    
    def set_instrument(self, instrument_name: str) -> bool:
        """Change the current instrument sound
        
        Args:
            instrument_name (str): Name of instrument from available instruments
            
        Returns:
            bool: True if instrument was successfully changed
        """
        if instrument_name not in self.instruments:
            return False
        
        self.current_instrument = instrument_name
        program_number: int = self.instruments[instrument_name]
        
        # Change FluidSynth instrument (bank 0, program number)
        if self.fs and self.soundfont_id is not None:
            self.fs.program_select(0, self.soundfont_id, 0, program_number)
        
        # Change external MIDI device instrument
        if self.midi_out:
            self.midi_out.set_instrument(program_number, 0)
        
        print(f"🎸 Switched to: {instrument_name}")
        return True
    
    def get_available_instruments(self) -> List[str]:
        """Get list of available instrument names
        
        Returns:
            List[str]: List of instrument names that can be selected
        """
        return list(self.instruments.keys())
    
    def get_current_instrument(self) -> str:
        """Get the currently selected instrument name
        
        Returns:
            str: Name of current instrument
        """
        return self.current_instrument
    
    def cleanup(self) -> None:
        """Clean up MIDI and FluidSynth resources"""
        self.stop_all_notes()
        
        if self.midi_out:
            self.midi_out.close()
            
        if self.fs:
            self.fs.delete()
            
        pygame.midi.quit()
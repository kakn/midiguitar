"""Main Guitar Application"""

import pygame
import sys
from typing import Set, Tuple, List, Optional, Dict
from .midi_controller import MidiController
from .keyboard_mapping import KeyboardMapping
from .guitar_display import GuitarDisplay


class GuitarApp:
    """Main MIDI Guitar application
    
    Handles the main game loop, user input, and coordinates between
    the MIDI controller, keyboard mapping, and display components.
    """
    
    def __init__(self) -> None:
        """Initialize the application with pygame and all components"""
        pygame.init()
        
        # Display configuration
        self.WIDTH: int = 1200
        self.HEIGHT: int = 700
        self.screen: pygame.Surface = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("MIDI Guitar")
        
        # Core components
        self.midi_controller: MidiController = MidiController()
        self.keyboard_mapping: KeyboardMapping = KeyboardMapping()
        self.display: GuitarDisplay = GuitarDisplay(self.screen, self.keyboard_mapping)
        
        # Application state
        self.pressed_keys: Set[int] = set()  # Currently pressed keyboard scancodes
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.current_octave: int = 0  # Octave offset (-3 to +3)
        self.sustain_mode: bool = True  # Notes sustain until new notes are played
        self.chord_mode: bool = False  # Allow multiple simultaneous notes
        
        # Visual state - tracks only actively pressed notes for display
        self.visual_notes: Dict[Tuple[int, int], int] = {}  # Only shows pressed keys
        
        # String fret tracking - realistic guitar behavior
        self.string_frets: Dict[int, Dict[int, int]] = {i: {} for i in range(4)}  # {string_index: {fret: midi_note}}
        
        # Initialize MIDI system
        if not self.midi_controller.initialize():
            print("⚠️ MIDI not available - notes will be printed to console")
    
    def handle_key_down(self, event: pygame.event.Event) -> bool:
        """Handle keyboard key press events
        
        Args:
            event (pygame.event.Event): Pygame key down event
            
        Returns:
            bool: False if application should quit, True otherwise
        """
        if event.key == pygame.K_ESCAPE:
            return False
        
        if event.key == pygame.K_SPACE:
            self.strum_all_strings()
            return True
        
        scancode: int = event.scancode
        if scancode in self.pressed_keys:
            return True  # Key already pressed, ignore
        
        # Convert scancode to guitar position
        position = self.keyboard_mapping.get_guitar_position(scancode)
        if position is None:
            return True  # Not a mapped key
        
        string_index, fret = position
        
        midi_note: int = self.keyboard_mapping.get_midi_note(string_index, fret, self.current_octave)
        string_name: str = self.keyboard_mapping.get_string_name(string_index)
        
        # Check if there's already a higher fret pressed
        current_active_fret = self.get_active_fret_for_string(string_index)
        should_play_immediately = current_active_fret is None or fret > current_active_fret
        
        # In sustain mode, only stop previous notes if this is the first key in a new chord
        # This allows chord sustain: if no keys are currently pressed, stop previous sustained notes
        if self.sustain_mode and len(self.pressed_keys) == 0:
            self.midi_controller.stop_all_notes()
        
        # Always track this fret being pressed on this string (even if it won't sound immediately)
        self.string_frets[string_index][fret] = midi_note
        self.pressed_keys.add(scancode)
        self.visual_notes[(string_index, fret)] = midi_note
        
        # Only update audio if this fret should sound (higher than current active fret)
        if should_play_immediately:
            self.update_string_audio(string_index)
        return True
    
    def handle_key_up(self, event: pygame.event.Event) -> None:
        """Handle keyboard key release events
        
        Args:
            event (pygame.event.Event): Pygame key up event
        """
        scancode: int = event.scancode
        if scancode not in self.pressed_keys:
            return  # Key wasn't pressed by us
        
        position = self.keyboard_mapping.get_guitar_position(scancode)
        if position is None:
            return  # Not a mapped key
        
        string_index, fret = position
        
        # Remove this fret from the string's pressed frets
        self.string_frets[string_index].pop(fret, None)
        
        # Always remove from visual display when key is released
        self.visual_notes.pop((string_index, fret), None)
        self.pressed_keys.discard(scancode)
        
        # Update audio for this string (pull-off behavior)
        if not self.sustain_mode:
            # In non-sustain mode, immediately update to the next highest fret (or silence)
            self.update_string_audio(string_index)
        else:
            # In sustain mode, we need to be smart about when to update audio
            # Get what the active fret is now (after removing the released fret)
            current_active_fret = self.get_active_fret_for_string(string_index)
            
            # Check what was playing before the key release
            was_playing_released_fret = False
            for fret_pos, midi_note in self.midi_controller.active_notes.items():
                if fret_pos[0] == string_index and fret_pos[1] == fret:
                    was_playing_released_fret = True
                    break
            
            if was_playing_released_fret:
                # We released the fret that was actually playing, so update audio
                if current_active_fret is None:
                    # No more frets pressed, but note continues sustaining in sustain mode
                    pass  
                else:
                    # There's a lower fret still pressed, play it (pull-off)
                    self.update_string_audio(string_index)
            # If we released a fret that wasn't playing, don't update audio at all
    
    def handle_mouse_click(self, pos: Tuple[int, int]) -> None:
        """Handle mouse click events for UI interaction
        
        Args:
            pos (Tuple[int, int]): Mouse click position (x, y)
        """
        instruments: List[str] = self.midi_controller.get_available_instruments()
        
        # Check octave buttons first
        if self.display.handle_octave_buttons(pos):
            octave_change = self.display.get_octave_change()
            if octave_change != 0:
                self.change_octave(octave_change)
            return
        
        # Check sustain toggle button
        if self.display.handle_sustain_button(pos):
            self.sustain_mode = not self.sustain_mode
            mode_text = "ON" if self.sustain_mode else "OFF"
            print(f"🎵 Note sustain: {mode_text}")
            return
        
        # Check string tuning clicks
        tuning_change = self.display.handle_string_tuning_click(pos, self.keyboard_mapping)
        if tuning_change:
            string_index, note_name, midi_note = tuning_change
            self.keyboard_mapping.set_string_tuning(string_index, midi_note, note_name)
            current_tuning = self.keyboard_mapping.get_current_tuning_name()
            print(f"🎸 String {string_index} tuned to {note_name} (MIDI {midi_note}) - {current_tuning} tuning")
            return
        
        selected_instrument: Optional[str] = self.display.handle_dropdown_click(pos, instruments)
        
        if selected_instrument:
            self.midi_controller.set_instrument(selected_instrument)
    
    def handle_mouse_wheel(self, direction: int) -> None:
        """Handle mouse wheel scrolling for dropdown
        
        Args:
            direction (int): Scroll direction (-1 for up, 1 for down)
        """
        if self.display.dropdown_open:
            self.display.dropdown_scroll_offset += direction
            # Bounds checking is handled in the draw method
    
    def change_octave(self, direction: int) -> None:
        """Change the current octave offset
        
        Args:
            direction (int): Direction to change octave (+1 for up, -1 for down)
        """
        new_octave = self.current_octave + direction
        # Limit octave range to reasonable values (-3 to +3)
        if -3 <= new_octave <= 3:
            self.current_octave = new_octave
            print(f"🎵 Octave changed to: {self.current_octave:+d}")
    
    def get_active_fret_for_string(self, string_index: int) -> Optional[int]:
        """Get the highest (active) fret being pressed on a string
        
        Args:
            string_index (int): String index (0-3)
            
        Returns:
            Optional[int]: Highest fret number, or None if no frets pressed
        """
        if not self.string_frets[string_index]:
            return None
        return max(self.string_frets[string_index].keys())
    
    def update_string_audio(self, string_index: int) -> None:
        """Update the audio for a string based on currently pressed frets
        
        Args:
            string_index (int): String index (0-3)
        """
        # Always stop any currently playing note on this string first
        for fret_pos, midi_note in list(self.midi_controller.active_notes.items()):
            if fret_pos[0] == string_index:  # fret_pos is (string_index, fret_number)
                self.midi_controller.stop_note(fret_pos[0], fret_pos[1])
        
        # Get the highest fret being pressed on this string
        active_fret = self.get_active_fret_for_string(string_index)
        if active_fret is not None:
            # Play the note for the highest fret
            midi_note = self.string_frets[string_index][active_fret]
            string_name = self.keyboard_mapping.get_string_name(string_index)
            self.midi_controller.play_note(string_index, active_fret, midi_note, string_name)
    
    def strum_all_strings(self) -> None:
        """Strum all strings - replay all currently pressed notes
        
        This simulates strumming the guitar by replaying every note that is currently held down.
        """
        print("🎸 Strumming all strings...")
        
        # Go through each string and replay the active note if there is one
        for string_index in range(4):  # 4 strings: G, D, A, E
            active_fret = self.get_active_fret_for_string(string_index)
            if active_fret is not None:
                # There's a fret pressed on this string, replay it
                midi_note = self.string_frets[string_index][active_fret]
                string_name = self.keyboard_mapping.get_string_name(string_index)
                self.midi_controller.play_note(string_index, active_fret, midi_note, string_name)
    
    def get_visual_notes(self) -> Dict[Tuple[int, int], int]:
        """Get notes that should be visually displayed (only active frets per string)
        
        Returns:
            Dict[Tuple[int, int], int]: Dictionary of (string_index, fret) -> midi_note for visual display
        """
        visual_notes = {}
        for string_index in range(4):  # 4 strings
            active_fret = self.get_active_fret_for_string(string_index)
            if active_fret is not None:
                # Only show the active (highest) fret for each string
                midi_note = self.string_frets[string_index][active_fret]
                visual_notes[(string_index, active_fret)] = midi_note
        return visual_notes
    
    def run(self) -> None:
        """Main application loop. Handles events, updates display, and maintains 60 FPS."""
        # Print keyboard layout guide to console
        print("\n🎸 MIDI Guitar")
        print("Keyboard Layout:")
        print("Fret:  0   1   2   3   4   5   6   7   8   9")
        print("G:     1   2   3   4   5   6   7   8   9   0")
        print("D:     Q   W   E   R   T   Y   U   I   O   P")
        print("A:     A   S   D   F   G   H   J   K   L   ;")
        print("E:     Z   X   C   V   B   N   M   ,   .   /")
        print("🎸 Press SPACEBAR to strum all held notes")
        print(f"🎵 Note sustain: {'ON' if self.sustain_mode else 'OFF'}")
        
        running: bool = True
        while running:
            self.clock.tick(60)  # Maintain 60 FPS
            
            # Process all pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if not self.handle_key_down(event):
                        running = False
                elif event.type == pygame.KEYUP:
                    self.handle_key_up(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        self.handle_mouse_click(event.pos)
                    elif event.button == 4:  # Mouse wheel up
                        self.handle_mouse_wheel(-1)
                    elif event.button == 5:  # Mouse wheel down
                        self.handle_mouse_wheel(1)
            
            # Render everything
            self.screen.fill((0, 0, 0))  # Clear to black
            
            # Get visual notes (only active frets per string for realistic guitar behavior)
            current_visual_notes = self.get_visual_notes()
            self.display.draw_guitar_neck(current_visual_notes)
            self.display.draw_layout_info()
            # Use visual notes for chord detection (only active frets)
            self.display.draw_active_notes(current_visual_notes)
            
            # Draw instrument selection dropdown
            instruments: List[str] = self.midi_controller.get_available_instruments()
            current_instrument: str = self.midi_controller.get_current_instrument()
            self.display.draw_instrument_dropdown(instruments, current_instrument)
            
            # Draw octave controls
            self.display.draw_octave_controls(self.current_octave)
            
            # Draw sustain control
            self.display.draw_sustain_control(self.sustain_mode)
            
            # Draw tuning dropdown if open
            if self.display.tuning_dropdown_open:
                self.display.draw_tuning_dropdown_with_mapping(self.keyboard_mapping)
            
            pygame.display.flip()
        
        self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up application resources"""
        self.midi_controller.cleanup()
        pygame.quit()


def main() -> None:
    """Application entry point with error handling"""
    try:
        app: GuitarApp = GuitarApp()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        pygame.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()
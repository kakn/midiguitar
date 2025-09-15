"""Main Guitar Application"""

import pygame
import sys
from typing import Set, Tuple, List, Optional
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
        
        # Play the note and track the key press
        self.midi_controller.play_note(string_index, fret, midi_note, string_name)
        self.pressed_keys.add(scancode)
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
        self.midi_controller.stop_note(string_index, fret)
        self.pressed_keys.discard(scancode)
    
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
            
            self.display.draw_guitar_neck(self.midi_controller.active_notes)
            self.display.draw_layout_info()
            self.display.draw_active_notes(self.midi_controller.active_notes)
            
            # Draw instrument selection dropdown
            instruments: List[str] = self.midi_controller.get_available_instruments()
            current_instrument: str = self.midi_controller.get_current_instrument()
            self.display.draw_instrument_dropdown(instruments, current_instrument)
            
            # Draw octave controls
            self.display.draw_octave_controls(self.current_octave)
            
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
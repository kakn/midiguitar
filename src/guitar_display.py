"""
Guitar Display - Handles the visual representation of the guitar
"""
import pygame
from typing import Dict, Tuple, Optional
from .keyboard_mapping import KeyboardMapping
from .chord_detector import ChordDetector


class GuitarDisplay:
    """Handles the visual guitar interface"""
    
    def __init__(self, screen: pygame.Surface, mapping: KeyboardMapping) -> None:
        self.screen = screen
        self.mapping = mapping
        self.chord_detector = ChordDetector()
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.GRAY = (128, 128, 128)
        self.YELLOW = (255, 255, 0)
        self.BLUE = (100, 150, 255)
        self.ORANGE = (255, 165, 0)
        self.PURPLE = (160, 80, 200)
        self.LIGHT_GRAY = (200, 200, 200)
        self.DARK_GRAY = (64, 64, 64)
        
        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 20)
        self.tiny_font = pygame.font.Font(None, 16)
        self.large_font = pygame.font.Font(None, 48)
        self.chord_font = pygame.font.Font(None, 42)
        
        # Dropdown state
        self.dropdown_open = False
        self.dropdown_rect = pygame.Rect(850, 20, 280, 30)
        self.dropdown_options_rect = pygame.Rect(850, 50, 280, 200)  # Taller for more options
        self.dropdown_scroll_offset = 0  # For scrollable dropdown
        self.dropdown_item_height = 20
        self.dropdown_visible_items = 10  # How many items to show at once
        
        # Help button state
        self.help_visible = False
        self.help_button_rect = pygame.Rect(50, 20, 80, 30)
    
    def draw_guitar_neck(self, active_notes: Dict[Tuple[int, int], int]) -> None:
        """Draw the guitar neck with active frets highlighted.
        
        Args:
            active_notes (Dict[Tuple[int, int], int]): Dictionary mapping (string, fret) to MIDI note numbers
        """
        start_x = 80
        start_y = 120
        string_spacing = 60
        fret_width = 80
        
        # Get number of frets from mapping
        num_frets = len(self.mapping.keyboard_columns)
        
        # Draw strings
        for i in range(len(self.mapping.string_names)):
            y = start_y + i * string_spacing
            color = self.RED if any(key[0] == i for key in active_notes.keys()) else self.GRAY
            # Adjust string length to match actual frets
            pygame.draw.line(self.screen, color, (start_x, y), (start_x + fret_width * (num_frets - 1), y), 4)
            
            # String name
            text = self.small_font.render(self.mapping.string_names[i], True, self.WHITE)
            self.screen.blit(text, (10, y - 10))
        
        # Draw frets (fret lines between the actual fret positions)
        for fret in range(num_frets):  # 0-9 frets
            x = start_x + fret * fret_width
            pygame.draw.line(self.screen, self.WHITE, (x, start_y), 
                           (x, start_y + (len(self.mapping.string_names)-1) * string_spacing), 2)
            
            # Fret numbers
            text = self.tiny_font.render(str(fret), True, self.WHITE)
            self.screen.blit(text, (x - 5, start_y - 20))
        
        # Draw pressed frets
        for (string_index, fret) in active_notes.keys():
            if fret == 0:
                x = start_x - 25  # Open string position
            else:
                # Position between fret lines (fret N is between line N-1 and N)
                x = start_x + (fret - 0.5) * fret_width
            y = start_y + string_index * string_spacing
            pygame.draw.circle(self.screen, self.YELLOW, (int(x), y), 18)
            
            # Fret number on circle
            fret_text = self.tiny_font.render(str(fret), True, self.BLACK)
            text_rect = fret_text.get_rect(center=(int(x), y))
            self.screen.blit(fret_text, text_rect)
    
    def draw_layout_info(self) -> None:
        """Draw help button and ESC instruction at bottom"""
        # Help button in top-left
        self.draw_help_button()
        
        # ESC instruction at bottom of screen
        esc_text = self.small_font.render("Press ESC to quit", True, self.GRAY)
        screen_height = self.screen.get_height()
        self.screen.blit(esc_text, (50, screen_height - 30))
        
        # Show keyboard layout if help is visible
        if self.help_visible:
            self.draw_help_overlay()
    
    def draw_help_button(self) -> None:
        """Draw the help button"""
        # Help button background
        button_color = self.BLUE if not self.help_visible else self.GREEN
        pygame.draw.rect(self.screen, button_color, self.help_button_rect)
        pygame.draw.rect(self.screen, self.WHITE, self.help_button_rect, 2)
        
        # Help button text
        help_text = "Help" if not self.help_visible else "Hide"
        text = self.small_font.render(help_text, True, self.WHITE)
        text_rect = text.get_rect(center=self.help_button_rect.center)
        self.screen.blit(text, text_rect)
    
    def draw_help_overlay(self) -> None:
        """Draw the keyboard layout help overlay"""
        # Semi-transparent background
        overlay = pygame.Surface((600, 300))
        overlay.set_alpha(240)
        overlay.fill(self.BLACK)
        self.screen.blit(overlay, (150, 200))
        
        # Border
        pygame.draw.rect(self.screen, self.WHITE, (150, 200, 600, 300), 2)
        
        # Title
        title = self.font.render("🎸 Keyboard Layout (Each Column = Fret)", True, self.WHITE)
        self.screen.blit(title, (170, 220))
        
        # Show the key mapping table
        self._draw_keyboard_table_overlay(250)
    
    def _draw_keyboard_table(self, y_start: int) -> None:
        """Draw keyboard layout as a properly aligned table.
        
        Args:
            y_start (int): Y coordinate to start drawing the table
        """
        # Table configuration
        start_x = 70
        col_width = 35  # Fixed width for each column
        row_height = 20
        
        # Table headers and data
        headers = ["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        rows = [
            ["Fret:", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            ["G:", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["D:", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A:", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
            ["E:", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"]
        ]
        
        # Draw each row
        for row_idx, row_data in enumerate(rows):
            y = y_start + row_idx * row_height
            for col_idx, cell_text in enumerate(row_data):
                x = start_x + col_idx * col_width
                
                # Different color for headers vs data
                if row_idx == 0:  # Header row
                    color = self.YELLOW
                elif col_idx == 0:  # String names
                    color = self.GREEN
                else:  # Key data
                    color = self.WHITE
                
                text = self.tiny_font.render(cell_text, True, color)
                self.screen.blit(text, (x, y))
    
    def _draw_keyboard_table_overlay(self, y_start: int) -> None:
        """Draw keyboard layout table in help overlay.
        
        Args:
            y_start (int): Y coordinate to start drawing the table
        """
        # Table configuration (adjusted for overlay)
        start_x = 190
        col_width = 35
        row_height = 20
        
        # Table data
        rows = [
            ["Fret:", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            ["G:", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["D:", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A:", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
            ["E:", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"]
        ]
        
        # Draw each row
        for row_idx, row_data in enumerate(rows):
            y = y_start + row_idx * row_height
            for col_idx, cell_text in enumerate(row_data):
                x = start_x + col_idx * col_width
                
                # Different color for headers vs data
                if row_idx == 0:  # Header row
                    color = self.YELLOW
                elif col_idx == 0:  # String names
                    color = self.GREEN
                else:  # Key data
                    color = self.WHITE
                
                text = self.tiny_font.render(cell_text, True, color)
                self.screen.blit(text, (x, y))
    
    def draw_active_notes(self, active_notes: Dict[Tuple[int, int], int]) -> None:
        """Draw currently active notes and chord information.
        
        Args:
            active_notes (Dict[Tuple[int, int], int]): Dictionary mapping (string, fret) to MIDI note numbers
        """
        # Get chord analysis
        notes_info = self.chord_detector.get_active_notes_info(active_notes)
        
        # Position in the right sidebar
        x_start = 850
        y_start = 120
        
        # Draw chord information prominently
        self._draw_chord_display(x_start, y_start, notes_info)
        
        # Draw individual notes below chord info
        self._draw_individual_notes(x_start, y_start + 120, active_notes, notes_info)
    
    def _draw_chord_display(self, x: int, y: int, notes_info: Dict) -> None:
        """Draw the main chord display section.
        
        Args:
            x (int): X coordinate to start drawing the chord display
            y (int): Y coordinate to start drawing the chord display
            notes_info (Dict): Dictionary containing note information and chord analysis
        """
        # Title
        title = self.font.render("Current Chord:", True, self.WHITE)
        self.screen.blit(title, (x, y))
        
        # Chord name or status
        if notes_info['note_count'] == 0:
            status_text = self.small_font.render("(Press keys to play)", True, self.GRAY)
            self.screen.blit(status_text, (x + 20, y + 35))
        elif notes_info['chord']['name']:
            # Display detected chord prominently
            chord_text = self.chord_font.render(notes_info['chord']['name'], True, self.ORANGE)
            self.screen.blit(chord_text, (x + 20, y + 35))
            
            # Show root note
            root_text = self.small_font.render(f"Root: {notes_info['chord']['root']}", True, self.YELLOW)
            self.screen.blit(root_text, (x + 20, y + 75))
        else:
            # No chord detected, show note count
            if notes_info['note_count'] == 1:
                status_text = self.small_font.render("Single Note", True, self.BLUE)
            else:
                status_text = self.small_font.render(f"{notes_info['note_count']} Notes (No chord)", True, self.BLUE)
            self.screen.blit(status_text, (x + 20, y + 35))
        
        # Show active note names
        if notes_info['note_names']:
            notes_display = " - ".join(notes_info['note_names'])
            if len(notes_display) > 20:  # Wrap long note lists
                notes_display = notes_display[:20] + "..."
            notes_text = self.small_font.render(f"Notes: {notes_display}", True, self.GREEN)
            self.screen.blit(notes_text, (x + 20, y + 95))
    
    def _draw_individual_notes(
        self, x: int, y: int, active_notes: Dict[Tuple[int, int], int], notes_info: Dict
    ) -> None:
        """Draw individual note details.
        
        Args:
            x (int): X coordinate to start drawing the individual notes
            y (int): Y coordinate to start drawing the individual notes
            active_notes (Dict[Tuple[int, int], int]): Dictionary mapping (string, fret) to MIDI note numbers
            notes_info (Dict): Dictionary containing note information and chord analysis
        """
        if not active_notes:
            return
        
        # Title for individual notes section
        title = self.small_font.render("Individual Notes:", True, self.WHITE)
        self.screen.blit(title, (x, y))
        
        # List each active note with string and fret info
        for i, ((string_index, fret), midi_note) in enumerate(active_notes.items()):
            string_name = self.mapping.get_string_name(string_index)
            note_name = self.chord_detector.midi_to_note_with_octave(midi_note)
            
            # Color code by string
            string_colors = {0: self.RED, 1: self.BLUE, 2: self.GREEN, 3: self.PURPLE}
            color = string_colors.get(string_index, self.WHITE)
            
            note_text = f"{string_name} F{fret}: {note_name}"
            text = self.tiny_font.render(note_text, True, color)
            self.screen.blit(text, (x + 20, y + 25 + i * 18))
    
    def draw_instrument_dropdown(self, instruments: list[str], current_instrument: str) -> None:
        """Draw the instrument selection dropdown.
        
        Args:
            instruments (list[str]): List of instrument names
            current_instrument (str): Name of the current instrument
        """
        # Draw dropdown button
        dropdown_color = self.LIGHT_GRAY if not self.dropdown_open else self.WHITE
        pygame.draw.rect(self.screen, dropdown_color, self.dropdown_rect)
        pygame.draw.rect(self.screen, self.DARK_GRAY, self.dropdown_rect, 2)
        
        # Draw current instrument text (no truncation needed with wider dropdown)
        current_text = current_instrument
        
        text = self.tiny_font.render(current_text, True, self.BLACK)
        text_rect = text.get_rect(center=(self.dropdown_rect.centerx - 10, self.dropdown_rect.centery))
        self.screen.blit(text, text_rect)
        
        # Draw dropdown arrow
        arrow_x = self.dropdown_rect.right - 15
        arrow_y = self.dropdown_rect.centery
        if self.dropdown_open:
            # Up arrow
            points = [(arrow_x, arrow_y + 3), (arrow_x + 5, arrow_y - 3), (arrow_x + 10, arrow_y + 3)]
        else:
            # Down arrow
            points = [(arrow_x, arrow_y - 3), (arrow_x + 5, arrow_y + 3), (arrow_x + 10, arrow_y - 3)]
        pygame.draw.polygon(self.screen, self.BLACK, points)
        
        # Draw dropdown options if open
        if self.dropdown_open:
            # Background
            pygame.draw.rect(self.screen, self.WHITE, self.dropdown_options_rect)
            pygame.draw.rect(self.screen, self.DARK_GRAY, self.dropdown_options_rect, 2)
            
            # Calculate scrolling
            max_scroll = max(0, len(instruments) - self.dropdown_visible_items)
            self.dropdown_scroll_offset = max(0, min(self.dropdown_scroll_offset, max_scroll))
            
            # Draw visible options only
            for i in range(self.dropdown_visible_items):
                instrument_index = i + self.dropdown_scroll_offset
                if instrument_index >= len(instruments):
                    break
                    
                instrument = instruments[instrument_index]
                option_y = self.dropdown_options_rect.y + i * self.dropdown_item_height
                
                # Ensure option is within the dropdown rect
                if option_y >= self.dropdown_options_rect.bottom:
                    break
                    
                option_rect = pygame.Rect(self.dropdown_options_rect.x, option_y, 
                                        self.dropdown_options_rect.width, self.dropdown_item_height)
                
                # Highlight current instrument
                if instrument == current_instrument:
                    pygame.draw.rect(self.screen, self.BLUE, option_rect)
                    text_color = self.WHITE
                else:
                    text_color = self.BLACK
                
                # Draw text
                text = self.tiny_font.render(instrument, True, text_color)
                self.screen.blit(text, (option_rect.x + 5, option_rect.y + 2))
            
            # Draw scroll indicators if needed
            if len(instruments) > self.dropdown_visible_items:
                # Scroll up indicator
                if self.dropdown_scroll_offset > 0:
                    up_rect = pygame.Rect(self.dropdown_options_rect.right - 15, 
                                        self.dropdown_options_rect.y + 2, 10, 8)
                    pygame.draw.polygon(self.screen, self.DARK_GRAY, 
                                        [(up_rect.centerx, up_rect.y), 
                                        (up_rect.left, up_rect.bottom),
                                        (up_rect.right, up_rect.bottom)])
                
                # Scroll down indicator
                if self.dropdown_scroll_offset < max_scroll:
                    down_rect = pygame.Rect(self.dropdown_options_rect.right - 15, 
                                            self.dropdown_options_rect.bottom - 10, 10, 8)
                    pygame.draw.polygon(self.screen, self.DARK_GRAY,
                                        [(down_rect.centerx, down_rect.bottom),
                                        (down_rect.left, down_rect.y),
                                        (down_rect.right, down_rect.y)])
    
    def handle_dropdown_click(self, pos: tuple[int, int], instruments: list[str]) -> Optional[str]:
        """Handle mouse clicks on the dropdown. Returns selected instrument or None.
        
        Args:
            pos (tuple[int, int]): Mouse click position (x, y)
            instruments (list[str]): List of instrument names
        
        """
        mouse_x, mouse_y = pos
        
        # Click on help button
        if self.help_button_rect.collidepoint(mouse_x, mouse_y):
            self.help_visible = not self.help_visible
            return None
        
        # Click on dropdown button
        if self.dropdown_rect.collidepoint(mouse_x, mouse_y):
            self.dropdown_open = not self.dropdown_open
            return None
        
        # Click on dropdown options (if open)
        if self.dropdown_open and self.dropdown_options_rect.collidepoint(mouse_x, mouse_y):
            relative_y = mouse_y - self.dropdown_options_rect.y
            clicked_index = relative_y // self.dropdown_item_height
            
            # Adjust for scrolling
            actual_index = clicked_index + self.dropdown_scroll_offset
            
            if 0 <= clicked_index < self.dropdown_visible_items and actual_index < len(instruments):
                self.dropdown_open = False
                return instruments[actual_index]
        
        # Click outside dropdown - close it
        if self.dropdown_open:
            self.dropdown_open = False
        
        # Click outside help overlay - close help
        if self.help_visible and not (150 <= mouse_x <= 750 and 200 <= mouse_y <= 500):
            self.help_visible = False
        
        return None

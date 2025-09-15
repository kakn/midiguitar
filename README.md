# MIDI Guitar

A simple, clean MIDI guitar interface using column-based keyboard mapping.

## Features

- 🎸 **Column-based layout**: Each keyboard column represents a guitar fret
- 🎵 **Chord support**: Press multiple keys in same column to play chords
- 🌍 **Universal compatibility**: Standard QWERTY layout works on all keyboards

## Keyboard Layout

```
Fret:  0   1   2   3   4   5   6   7   8   9
G:     1   2   3   4   5   6   7   8   9   0
D:     Q   W   E   R   T   Y   U   I   O   P
A:     A   S   D   F   G   H   J   K   L   ;
E:     Z   X   C   V   B   N   M   ,   .   /
```

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Get a SoundFont file**:
   - Download any `.sf2` SoundFont file (we recommend FluidR3_GM.sf2 or GeneralUser GS)
   - Place it in the `data/` folder and name it `soundfont.sf2`
   - Or update `soundfont_path` in `src/midi_controller.py` to point to your file

3. **Run the application**:
   ```bash
   python main.py
   ```

4. **Play guitar**:
   - Each column = one fret (1qaz = fret 0, 2wsx = fret 1, etc.)
   - Press multiple keys in same column for chords
   - Use the dropdown to change instruments
   - ESC to quit

## Requirements

- Python 3.8+
- pygame
- pyfluidsynth
- pychord
- A SoundFont file (.sf2) for realistic instrument sounds
- MIDI output device (built-in on macOS, software synth recommended)

## Architecture

The code is cleanly modularized:

- `src/midi_controller.py` - MIDI output handling
- `src/keyboard_mapping.py` - Key-to-fret mapping logic  
- `src/guitar_display.py` - Visual interface rendering
- `src/guitar_app.py` - Main application orchestration
- `main.py` - Simple entry point

## To Do

- Fade out notes
- Scroll up for other strings / enable mouse input
- Add the interactive element (Guitar Hero style)
- Touch screen compatibility

## License

MIT License - see LICENSE file.
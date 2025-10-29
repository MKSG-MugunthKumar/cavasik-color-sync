# Cavasik DBus Color Sync - Development Documentation

This project was developed with assistance from Claude (Anthropic), an AI assistant.

## Project Overview

A Python script that automatically synchronizes the Cavasik audio visualizer colors with the currently playing music's album artwork in real-time using DBus communication.

## Technical Implementation

### Core Technologies
- **DBus**: Inter-process communication for MPRIS2 media player monitoring and Cavasik control
- **MPRIS2**: Standard media player interface for reading track metadata
- **ColorThief**: Color palette extraction from album artwork
- **Python GObject/GLib**: Event loop and DBus integration
- **HSV Color Manipulation**: Advanced color transformations for aesthetic schemes

### Architecture

```
┌─────────────────┐
│  Media Player   │ (Spotify, VLC, etc.)
│   (MPRIS2)      │
└────────┬────────┘
         │ DBus Signals
         ▼
┌─────────────────────────────────┐
│  cavasik-color-sync.py          │
│  ┌───────────────────────────┐  │
│  │ 1. Monitor MPRIS2         │  │
│  │ 2. Extract album art URL  │  │
│  │ 3. Download/read image    │  │
│  │ 4. Extract color palette  │  │
│  │ 5. Apply color scheme     │  │
│  │ 6. Generate RGB files     │  │
│  └───────────────────────────┘  │
└────────┬────────────────────────┘
         │ DBus Method Calls
         ▼
┌─────────────────┐
│    Cavasik      │
│   Visualizer    │
└─────────────────┘
```

### Key Challenges & Solutions

#### 1. File Format Discovery
**Challenge**: Initial implementation used XML format for color files, but Cavasik returned `false`.

**Solution**: Through source code analysis of Cavasik's `settings.py`, discovered the correct format is simple RGB text:
```
R,G,B
R,G,B
...
```

#### 2. Flatpak Sandbox Restrictions
**Challenge**: File paths in `/tmp/` were inaccessible to Flatpak Cavasik, causing `false` returns.

**Solution**: Used Flatpak's data directory: `~/.var/app/io.github.TheWisker.Cavasik/data/`

#### 3. DBus Colors Setting
**Challenge**: DBus calls failed even with correct file format and paths.

**Solution**: Discovered the `dbus-colors` setting must be enabled in Cavasik preferences:
```bash
flatpak run --command=gsettings io.github.TheWisker.Cavasik set io.github.TheWisker.Cavasik dbus-colors true
```

#### 4. Aesthetic Color Schemes
**Challenge**: Simple darkening of colors looked visually unappealing.

**Solution**: Implemented 4 distinct color schemes using HSV color space manipulation:
- **Dominant BG**: Solid background from most dominant color
- **Neon**: Complementary hue-shifted backgrounds for cyberpunk aesthetic
- **Black BG**: Pure black for maximum contrast
- **Gradient Reverse**: Inverted palette creates depth

### Color Scheme Implementation

Each scheme manipulates colors in HSV space for better perceptual results:

```python
# Example: Neon scheme
h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
h = (h + 0.5) % 1.0    # Shift to complementary hue
s = 0.6                 # Keep saturation for colored effect
v = 0.08                # Very dark
```

Benefits of HSV manipulation:
- Independent control of hue, saturation, brightness
- Perceptually uniform adjustments
- Easy hue shifting for complementary colors

### Cavasik DBus Interface

**Service**: `io.github.TheWisker.Cavasik`
**Object Path**: `/io/github/TheWisker/Cavasik`

**Methods**:
- `set_fg_colors(path: str) -> bool` - Set foreground colors
- `set_bg_colors(path: str) -> bool` - Set background colors

**Requirements**:
1. `dbus-colors` gsetting must be `true`
2. File path must be accessible to Flatpak sandbox
3. File must be in RGB format (R,G,B per line)
4. Return value indicates success/failure

### MPRIS2 Integration

Monitors `org.freedesktop.DBus.Properties.PropertiesChanged` signal on `/org/mpris/MediaPlayer2` path.

**Key Metadata**:
- `xesam:title` - Track title
- `mpris:artUrl` - Album art URL (can be `file://` or `http://`)

### File Structure

```
cavasik-dbus/
├── cavasik-color-sync.py       # Main script
├── test-dbus.py                # DBus connection test utility
├── alternative_color_schemes.py # Color scheme examples
├── requirements.txt            # Python dependencies
├── README.md                   # User documentation
└── CLAUDE.md                   # This file
```

## Development Process

### Iteration 1: Initial Implementation
- Basic MPRIS2 monitoring
- XML color file generation (incorrect format)
- Used `/tmp/` directory (Flatpak incompatible)

### Iteration 2: Format Correction
- Discovered correct RGB format via source code analysis
- Fixed file format to comma-separated RGB values

### Iteration 3: Flatpak Compatibility
- Identified sandbox restriction issue
- Migrated to Flatpak-accessible data directory

### Iteration 4: DBus Settings
- Discovered `dbus-colors` requirement
- Added documentation for enabling the setting

### Iteration 5: Aesthetic Improvements
- Initial 70% darkening looked too similar to foreground
- Experimented with 15% darkening
- Implemented dominant color solid background

### Iteration 6: Multiple Color Schemes
- Added 4 distinct color schemes
- Implemented configurable SETTINGS system
- HSV color space manipulation for better aesthetics

## Configuration System

The script uses a dual-layer configuration:

1. **COLOR_SCHEME**: String selector for active scheme
2. **SETTINGS**: Dict with per-scheme tunable parameters

This allows users to:
- Quickly switch schemes by changing one variable
- Fine-tune individual scheme parameters without understanding color math
- Create custom variations easily

## Testing Tools

### test-dbus.py
Validates:
- DBus connection to Cavasik
- Color file format and accessibility
- Method call success/failure

### alternative_color_schemes.py
- Examples of all color scheme implementations
- Standalone testing without running full script
- Educational reference for custom schemes

## Dependencies

- `dbus-python`: DBus communication
- `PyGObject`: GLib event loop integration
- `colorthief`: Color palette extraction
- `Pillow`: Image processing
- `requests`: HTTP album art fetching

## Future Enhancements

Potential improvements:
1. Command-line arguments for scheme selection
2. Real-time scheme switching via DBus interface
3. Config file support (YAML/TOML)
4. Album art caching for faster color extraction
5. Per-genre color scheme preferences
6. Smooth color transitions between tracks
7. Integration with pywal for system-wide theming

## Debugging Tips

**Issue**: Returns `false` on DBus calls
- Check: `dbus-colors` setting enabled
- Check: File path accessible to Flatpak
- Check: File format is RGB (not XML/hex)

**Issue**: No color changes on track change
- Check: MPRIS2 player is detected (`busctl --user list | grep mpris`)
- Check: Album art URL is present in metadata
- Monitor: `dbus-monitor --session "interface='org.mpris.MediaPlayer2.Player'"`

**Issue**: Script crashes on color extraction
- Check: Network connectivity (for HTTP album art)
- Check: Image format is supported by Pillow
- Check: File permissions for local album art

## License & Credits

Developed as an open-source integration tool for Cavasik.

**Cavasik**: https://github.com/TheWisker/Cavasik
**MPRIS2 Specification**: https://specifications.freedesktop.org/mpris-spec/latest/

---

*This documentation was created to help future developers understand the implementation details, design decisions, and potential improvements for this project.*

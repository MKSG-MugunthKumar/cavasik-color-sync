# Cavasik DBus Color Sync - AI Development Documentation

First read the README.md file for an overview of the project. Understand the troubleshooting sections before proceeding with troubleshooting.

## Key Constraints
  - **Small Indie Project** - do NOT over-engineer
  - Keep it simple and maintainable for a single developer

## Development Guidelines
  - Follow best practices for Python development
  - Ensure code is modular and maintainable
  - **Use version control** (e.g., Git) for all code changes
  - **Avoid unnecessary files**: User prefers minimal setup, no extra docs
  - **Document in CLAUDE.md**: Add context here, not scattered in comments
  - Write clear commit messages. Understand that this is an open source repository
  - Ensure dependency authors are clearly mentioned and credited (even if the licenses don't explicitly require it do so)

## Project Structure

```
cavasik-color-sync/
├── cavasik-color-sync.py       # Main script
├── test-dbus.py                # DBus testing utility
├── cavasik-color-sync.service  # Systemd user service file
├── requirements.txt            # Python dependencies
├── README.md                   # User documentation
├── CLAUDE.md                   # AI development context (this file)
└── LICENSE                     # GPL-3.0 license
```

## Development Environment Setup

1. **Python Version**: Python 3.x (tested on 3.9+)

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **System Requirements**:
   - DBus (usually pre-installed on Linux)
   - Cavasik (Flatpak recommended)
   - MPRIS2-compatible media player

4. **Testing Setup**:
   - Ensure Cavasik is running with DBus colors enabled
   - Start a media player (Spotify, VLC, etc.)
   - Run the script: `python cavasik-color-sync.py`

## Code Architecture

### Main Components

1. **Configuration Management** (lines 57-82):
   - YAML-based config at `~/.config/cavasik-color-sync/config.yaml`
   - Auto-creates default config on first run
   - Command-line args override config file

2. **DBus Integration**:
   - **MPRIS2 Monitoring**: Listens for `PropertiesChanged` signals from media players
   - **Cavasik Control**: Sends color updates via `set_fg_colors()` and `set_bg_colors()` methods
   - Uses `dbus.mainloop.glib` for event-driven architecture

3. **Color Processing Pipeline**:
   - Album art download → ColorThief palette extraction → HSV transformation → RGB file generation → DBus update
   - All transformations done in HSV color space for perceptual uniformity

4. **File Locations**:
   - **Color files**: `~/.var/app/io.github.TheWisker.Cavasik/data/` (Flatpak-accessible)
   - **Album art cache**: `/tmp/cavasik-color-sync/album_art/` (auto-cleaned on reboot)
   - **Logs**: `/tmp/cavasik-color-sync/cavasik-sync.log`
   - **Config**: `~/.config/cavasik-color-sync/config.yaml`

### Key Design Decisions

1. **Why HSV instead of RGB?**
   - Independent control of hue, saturation, brightness
   - Easy to create complementary colors (hue shift)
   - Perceptually uniform transformations
   - Avoids muddy darkening that happens with RGB multiplication

2. **Why /tmp for cache?**
   - Auto-cleaned on reboot (no manual cleanup needed)
   - Fast access
   - Prevents disk bloat from album art accumulation

3. **Why Flatpak data directory for color files?**
   - Flatpak sandbox security model restricts file access
   - `~/.var/app/io.github.TheWisker.Cavasik/data/` is guaranteed accessible
   - Avoids permission issues

4. **Event-driven architecture**:
   - Uses GLib main loop for efficient DBus signal handling
   - Non-blocking, low CPU usage when idle
   - Only processes on actual track changes

## Adding New Color Schemes

To add a new color scheme:

1. Add entry to `SETTINGS` dict with tuning parameters:
   ```python
   SETTINGS = {
       "your_scheme": {
           "fg_saturation_boost": 1.2,
           "fg_brightness_boost": 1.1,
           # ... other params
       },
   }
   ```

2. Add transformation logic in `apply_color_scheme()` function:
   ```python
   elif COLOR_SCHEME == "your_scheme":
       # Implement HSV transformations
       # Use colorsys.rgb_to_hsv() and colorsys.hsv_to_rgb()
   ```

3. Document in README.md's color scheme section
4. Update `--list-schemes` output

## Testing and Debugging

### Manual Testing

```bash
# Test DBus connection
python test-dbus.py

# Test with specific scheme
python cavasik-color-sync.py --scheme neon

# Monitor DBus traffic
dbus-monitor --session "interface='org.mpris.MediaPlayer2.Player'"
```

### Common Development Issues

1. **DBus method returns False**:
   - Check: Cavasik's `dbus-colors` setting
   - Check: File path accessibility to Flatpak
   - Check: RGB file format (not XML/hex)

2. **Color extraction fails**:
   - Verify image format with `file` command
   - Check network connectivity for HTTP URLs
   - Validate ColorThief installation

3. **No track changes detected**:
   - Verify MPRIS2 player running: `busctl --user list | grep mpris`
   - Check metadata contains `mpris:artUrl`
   - Monitor with `dbus-monitor`

### Useful Development Commands

```bash
# Check Cavasik DBus availability
busctl --user list | grep Cavasik

# Introspect Cavasik DBus interface
busctl --user introspect io.github.TheWisker.Cavasik /io/github/TheWisker/Cavasik

# View real-time logs
tail -f /tmp/cavasik-color-sync/cavasik-sync.log

# Test color file manually
busctl --user call io.github.TheWisker.Cavasik \
    /io/github/TheWisker/Cavasik \
    io.github.TheWisker.Cavasik \
    set_fg_colors s "$HOME/.var/app/io.github.TheWisker.Cavasik/data/test_colors.rgb"
```

## Dependencies and Credits

### Core Dependencies
- **dbus-python**: DBus communication (License: MIT/X11)
- **PyGObject**: GLib bindings for event loop (License: LGPL-2.1+)
- **colorthief**: Color palette extraction (License: MIT) - https://github.com/fengsp/color-thief-py
- **Pillow**: Image processing (License: HPND) - https://python-pillow.org/
- **requests**: HTTP album art fetching (License: Apache 2.0)
- **PyYAML**: Configuration file parsing (License: MIT)

### Integration Partners
- **Cavasik**: Audio visualizer by TheWisker (License: GPL-3.0+) - https://github.com/TheWisker/Cavasik
- **MPRIS2**: FreeDesktop media player standard - https://specifications.freedesktop.org/mpris-spec/latest/

## Contributing

When contributing:
1. Test with multiple media players (Spotify, VLC, etc.)
2. Verify Flatpak compatibility
3. Update README.md if adding user-facing features
4. Update this file (CLAUDE.md) if adding developer context
5. Keep commit messages clear and descriptive
6. Respect the "no over-engineering" principle

## License

This project uses **GPL-3.0-or-later** to align with Cavasik's licensing.
See [LICENSE](LICENSE) file for full text.

# Cavasik Color Sync

Automatically synchronizes Cavasik visualizer colors with currently playing music's album art in real-time.

## Features

- Monitors MPRIS2-compatible media players (Spotify, VLC, etc.)
- Extracts color palette from album cover art
- Updates Cavasik visualizer colors in real-time via DBus
- Works with Flatpak installations
- Multiple customizable color schemes

## Requirements

- Python 3
- Cavasik (Flatpak recommended) with DBus colors enabled
- MPRIS2-compatible media player

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Enable DBus colors in Cavasik:**
   - Open Cavasik → Press `Ctrl+P` → Enable "DBus Colors"
   - Or run: `flatpak run --command=gsettings io.github.TheWisker.Cavasik set io.github.TheWisker.Cavasik dbus-colors true`

3. **Run the script:**
   ```bash
   # Use default color scheme from config file
   python cavasik-color-sync.py

   # Or choose a specific scheme (overrides config)
   python cavasik-color-sync.py --scheme neon
   python cavasik-color-sync.py -s black_bg

   # List all available schemes
   python cavasik-color-sync.py --list-schemes
   ```

4. **Run in background:**
   ```bash
   # Using nohup
   nohup python3 cavasik-color-sync.py &

   # Or install as systemd service
   cp cavasik-color-sync.service ~/.config/systemd/user/
   systemctl --user daemon-reload
   systemctl --user enable --now cavasik-color-sync.service
   ```

5. **Play music!** The visualizer colors will automatically match your album art.

The script runs in the background and updates colors when:
- A new track starts playing
- Album art changes

## Configuration

The script uses a YAML configuration file located at:
- `$XDG_CONFIG_HOME/cavasik-color-sync/config.yaml` (usually `~/.config/cavasik-color-sync/config.yaml`)

The config file is automatically created on first run with default settings:

```yaml
color_scheme: dominant_bg
```

You can edit this file to change your preferred color scheme. Valid options:
- `dominant_bg` (default)
- `neon`
- `black_bg`
- `gradient_reverse`

Command-line arguments always override the config file.

## Directory Structure

The script uses the following directories:

```
~/.config/cavasik-color-sync/
└── config.yaml                    # Configuration file

~/.var/app/io.github.TheWisker.Cavasik/data/
├── cavasik_fg_colors.rgb         # Foreground color file (for Flatpak Cavasik)
└── cavasik_bg_colors.rgb         # Background color file (for Flatpak Cavasik)

/tmp/cavasik-color-sync/
├── album_art/                     # Downloaded album art cache
│   └── cover_*.jpg
└── cavasik-sync.log              # Log file
```

**Note:** Album art and logs are stored in `/tmp/cavasik-color-sync/` which is automatically cleaned on system reboot.

## Customization

### Changing Color Schemes

There are three ways to set your color scheme:

1. **Edit the config file** (persistent, recommended):
   ```bash
   # Edit ~/.config/cavasik-color-sync/config.yaml
   nano ~/.config/cavasik-color-sync/config.yaml
   ```
   Change `color_scheme: dominant_bg` to your preferred scheme.

2. **Use command-line arguments** (temporary override):
   ```bash
   # Use neon cyberpunk style
   python cavasik-color-sync.py --scheme neon

   # Use black background
   python cavasik-color-sync.py -s black_bg
   ```

3. **List all available schemes with descriptions**:
   ```bash
   python cavasik-color-sync.py --list-schemes
   ```

### Available Color Schemes

#### Quick Reference

| Scheme | Foreground | Background | Best For |
|--------|-----------|------------|----------|
| **dominant_bg** | All 5 colors, boosted saturation/brightness | Solid (darkened dominant color) | Most music, clean aesthetic |
| **neon** | Maximum saturation | Complementary colors (opposite hue) | Electronic, EDM, synthwave |
| **black_bg** | Enhanced brightness | Pure black | All genres, OLED screens |
| **gradient_reverse** | Normal gradient | Reversed gradient | Experimental looks |

#### Detailed Explanations

##### 1. dominant_bg (Default) ⭐

**How it works:**
```
Album: [Red🔴, Orange🟠, Yellow🟡, Green🟢, Blue🔵]
                    ↓
Background: Dark Red (solid)
Foreground: Enhanced [Red, Orange, Yellow, Green, Blue] gradient
```

**Technical:**
- Extracts 5 colors using ColorThief
- Takes color #1 (most dominant)
- Background: HSV conversion → Saturation × 0.6, Value × 0.08 (very dark)
- Foreground: All colors with Saturation × 1.4, Value × 1.3 (vibrant)

**Visual Effect:**
- Clean, unified look
- Background matches album theme
- High contrast without being jarring

**Use Cases:**
- General music listening
- Albums with cohesive color palettes
- Professional/clean aesthetic

##### 2. neon (Cyberpunk) 🌆

**How it works:**
```
Album: [Red🔴, Orange🟠, Yellow🟡, Green🟢, Blue🔵]
                    ↓
Background: [Cyan, Blue, Purple, Red, Orange] (hue-shifted +180°)
Foreground: Super vivid [Red, Orange, Yellow, Green, Blue]
```

**Technical:**
- Foreground: Saturation × 1.5, Value × 1.3 (maximum vividness)
- Background: Hue + 0.5 (shift 180° to complementary), Saturation 0.6, Value 0.08
- Creates color wheel opposites (Red → Cyan, Blue → Orange)

**Visual Effect:**
- High energy, vibrant
- Colors "pop" against contrasting background
- Cyberpunk/futuristic aesthetic

**Use Cases:**
- Electronic music (EDM, techno, house)
- Synthwave/retrowave albums
- Gaming sessions
- High-energy playlists

##### 3. black_bg (Classic) ⬛

**How it works:**
```
Album: [Red🔴, Orange🟠, Yellow🟡, Green🟢, Blue🔵]
                    ↓
Background: Pure black (0,0,0)
Foreground: Enhanced [Red, Orange, Yellow, Green, Blue]
```

**Technical:**
- Background: RGB (0, 0, 0) - no color
- Foreground: Saturation × 1.3, Value × 1.2 (enhanced but not extreme)

**Visual Effect:**
- Maximum contrast
- Colors stand out clearly
- Minimalist, classic look

**Use Cases:**
- Any music genre
- OLED screens (true black saves power)
- Minimalist setups
- When you want colors to be the focus

##### 4. gradient_reverse (Experimental) 🔄

**How it works:**
```
Album: [Red🔴, Orange🟠, Yellow🟡, Green🟢, Blue🔵]
                    ↓
Background: Dark [Blue, Green, Yellow, Orange, Red] (reversed)
Foreground: Enhanced [Red, Orange, Yellow, Green, Blue]
```

**Technical:**
- Foreground: Saturation × 1.2, Value × 1.1 (slight boost)
- Background: Reversed palette, RGB × 0.1 (very dark)
- Creates opposing gradient flow

**Visual Effect:**
- Visual "depth"
- Dynamic, moving feel
- Unique, experimental

**Use Cases:**
- Albums with varied color palettes
- Experimental music
- When you want something different
- Visual art projects

#### Choosing Your Scheme

**By Music Genre:**

| Genre | Recommended Scheme |
|-------|-------------------|
| Pop, Rock, Indie | `dominant_bg` or `black_bg` |
| Electronic, EDM, Synthwave | `neon` |
| Classical, Jazz, Acoustic | `black_bg` or `dominant_bg` |
| Hip-Hop, R&B | `black_bg` |
| Experimental, Ambient | `gradient_reverse` or `neon` |

**By Visual Preference:**

Want clean, cohesive look? → `dominant_bg`

Want maximum energy/vibrancy? → `neon`

Want simple, maximum contrast? → `black_bg`

Want something unique? → `gradient_reverse`

### Fine-Tuning

Each scheme has customizable settings in the `SETTINGS` dictionary:

```python
SETTINGS = {
    "dominant_bg": {
        "fg_saturation_boost": 1.4,    # 1.0 = normal, 1.5 = 50% more saturated
        "fg_brightness_boost": 1.3,    # 1.0 = normal, 1.3 = 30% brighter
        "bg_saturation": 0.6,          # 0-1 scale
        "bg_brightness": 0.08,         # Lower = darker (0-1 scale)
    },
    # ... more schemes
}
```

Adjust these values to create your perfect look!

### Technical: Color Space (HSV)

All schemes use HSV (Hue, Saturation, Value) color space for transformations:

- **Hue (H)**: Color tone (0-360° or 0-1)
  - 0° = Red, 120° = Green, 240° = Blue
  - Shifting hue creates different colors

- **Saturation (S)**: Color intensity (0-1)
  - 0 = Gray, 1 = Pure color
  - Boosting saturation makes colors more vivid

- **Value (V)**: Brightness (0-1)
  - 0 = Black, 1 = Full brightness
  - Reducing value darkens colors

**Why HSV?**
- Independent control of color properties
- Perceptually uniform adjustments
- Easy to create complementary colors
- Better than RGB for aesthetic transformations

## How it works

1. Loads configuration from `~/.config/cavasik-color-sync/config.yaml`
2. Listens for MPRIS2 `PropertiesChanged` signals on DBus
3. Extracts track metadata including album art URL
4. Downloads/reads the cover art image to `/tmp/cavasik-color-sync/album_art/`
5. Extracts a 5-color palette using ColorThief
6. Applies the selected color scheme transformation (dominant_bg, neon, black_bg, or gradient_reverse)
7. Creates RGB color files (one color per line: `R,G,B` format)
   - Foreground: `~/.var/app/io.github.TheWisker.Cavasik/data/cavasik_fg_colors.rgb`
   - Background: `~/.var/app/io.github.TheWisker.Cavasik/data/cavasik_bg_colors.rgb`
   - (Uses Flatpak-accessible directory for compatibility)
8. Sends colors to Cavasik via its DBus interface:
   - `io.github.TheWisker.Cavasik.set_fg_colors(path)`
   - `io.github.TheWisker.Cavasik.set_bg_colors(path)`
9. Logs all operations to `/tmp/cavasik-color-sync/cavasik-sync.log`

## Cavasik DBus Interface

The script uses the following DBus interface:

- **Service:** `io.github.TheWisker.Cavasik`
- **Object Path:** `/io/github/TheWisker/Cavasik`
- **Interface:** `io.github.TheWisker.Cavasik`
- **Methods:**
  - `set_fg_colors(path)` - Set foreground colors from RGB file
  - `set_bg_colors(path)` - Set background colors from RGB file

## Color File Format

Cavasik expects RGB color files with one color per line:

```
4,42,59
193,134,75
4,51,171
19,58,140
124,156,156
```

Each line contains comma-separated R,G,B values (0-255).

## Testing

Test the DBus connection and color setting:

```bash
python test-dbus.py
```

Test manually with busctl:

```bash
busctl --user call io.github.TheWisker.Cavasik \
    /io/github/TheWisker/Cavasik \
    io.github.TheWisker.Cavasik \
    set_fg_colors s "$HOME/.var/app/io.github.TheWisker.Cavasik/data/test_colors.rgb"
```

This should return `b true` if successful.

## Troubleshooting

### Enable DBus Colors in Cavasik

**IMPORTANT:** The DBus color feature must be enabled in Cavasik settings:

1. Open Cavasik
2. Press `Ctrl+P` or click menu → Preferences
3. Enable the **"DBus Colors"** setting

Verify it's enabled (for Flatpak):
```bash
flatpak run --command=gsettings io.github.TheWisker.Cavasik get io.github.TheWisker.Cavasik dbus-colors
```

Should return `true`. If not, enable it in Cavasik preferences.

### Common Issues

- **Returns `false` when setting colors**:
  - DBus colors setting is disabled in Cavasik (check preferences)
  - File path not accessible to Flatpak (use `~/.var/app/io.github.TheWisker.Cavasik/data/` for Flatpak installations)
- **No color changes**: Ensure Cavasik is running before starting the script
- **Script not responding**: Check that your media player supports MPRIS2 (most modern players do)
- **File not found errors**: Check album art URL and network connectivity
- **Check the log file**: View `/tmp/cavasik-color-sync/cavasik-sync.log` for detailed error messages

### Viewing Logs

```bash
# View the log file
cat /tmp/cavasik-color-sync/cavasik-sync.log

# Follow log in real-time
tail -f /tmp/cavasik-color-sync/cavasik-sync.log

# View systemd service logs
journalctl --user -u cavasik-color-sync.service -f
```

### Flatpak File Access

If you're running Cavasik as a Flatpak (recommended), color files must be in a location accessible to the sandbox:
- ✅ `~/.var/app/io.github.TheWisker.Cavasik/data/` - Used by this script
- ✅ `~/Documents/`, `~/Downloads/`, `~/Music/`, etc. - Default XDG directories
- ❌ `/tmp/` - Flatpak has its own `/tmp`
- ❌ Hidden files in `~/.cache/` - Blocked by Snap confinement

### DBus Monitoring & Debugging

**Monitor Cavasik DBus messages:**
```bash
dbus-monitor --session "sender='io.github.TheWisker.Cavasik'"
```

**Monitor MPRIS media player messages:**
```bash
dbus-monitor --session "interface='org.mpris.MediaPlayer2.Player'"
```

**Check if Cavasik is available on DBus:**
```bash
busctl --user list | grep -i cavasik
```

**Check active MPRIS media players:**
```bash
busctl --user list | grep -i mpris
```

**Introspect Cavasik DBus interface:**
```bash
busctl --user introspect io.github.TheWisker.Cavasik /io/github/TheWisker/Cavasik
```

**Monitor MPRIS metadata changes:**
```bash
dbus-monitor --session "type='signal',interface='org.freedesktop.DBus.Properties',member='PropertiesChanged',path='/org/mpris/MediaPlayer2'"
```

**GUI debugging tool (d-feet):**
```bash
sudo dnf install d-feet  # Fedora
d-feet  # Launch GUI to browse DBus services
```


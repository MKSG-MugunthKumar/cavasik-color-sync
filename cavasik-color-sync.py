#!/usr/bin/env python3
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from colorthief import ColorThief
from PIL import Image
import requests
from io import BytesIO
import colorsys
import argparse
import sys
import yaml
import hashlib

DBusGMainLoop(set_as_default=True)

# For Flatpak Cavasik, use a path accessible to the sandbox
# For system Cavasik, /tmp works fine
import os
import datetime

# Create working directory for all temporary files
WORK_DIR = "/tmp/cavasik-color-sync"
os.makedirs(WORK_DIR, exist_ok=True)

# For Flatpak, still need to use Flatpak data dir for color files
FLATPAK_DATA_DIR = os.path.expanduser("~/.var/app/io.github.TheWisker.Cavasik/data")
os.makedirs(FLATPAK_DATA_DIR, exist_ok=True)

# Color files in Flatpak directory (Cavasik needs access to these)
FG_COLOR_FILE = os.path.join(FLATPAK_DATA_DIR, "cavasik_fg_colors.rgb")
BG_COLOR_FILE = os.path.join(FLATPAK_DATA_DIR, "cavasik_bg_colors.rgb")

# Album art cache in /tmp/cavasik-dbus
ALBUM_ART_DIR = os.path.join(WORK_DIR, "album_art")
os.makedirs(ALBUM_ART_DIR, exist_ok=True)

# Log file in /tmp/cavasik-dbus
LOG_FILE = os.path.join(WORK_DIR, "cavasik-sync.log")

# Config file location
XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "cavasik-color-sync")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")

def log(message):
    """Log messages to both console and log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_message + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

def load_config():
    """Load configuration from YAML file"""
    default_config = {
        "color_scheme": "dominant_bg"
    }

    if not os.path.exists(CONFIG_FILE):
        # Create default config
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False)
        log(f"Created default config at {CONFIG_FILE}")
        return default_config

    try:
        with open(CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)
            if config is None:
                config = default_config
            # Ensure color_scheme exists
            if "color_scheme" not in config:
                config["color_scheme"] = "dominant_bg"
            return config
    except Exception as e:
        log(f"Error loading config: {e}, using defaults")
        return default_config

# ==================== CONFIGURATION ====================
# Choose your color scheme style:
# "dominant_bg"     - Solid background from dominant color, vibrant gradient foreground (default)
# "neon"            - Maximum saturation cyberpunk style with complementary backgrounds
# "black_bg"        - Pure black background for maximum contrast
# "gradient_reverse" - Reversed color palette for background

COLOR_SCHEME = "neon"

# Fine-tune settings for each scheme
SETTINGS = {
    "dominant_bg": {
        "fg_saturation_boost": 1.4,  # Boost foreground saturation (1.0 = no change, 1.5 = 50% more)
        "fg_brightness_boost": 1.3,  # Boost foreground brightness
        "bg_saturation": 0.6,  # Background color saturation (0-1)
        "bg_brightness": 0.28,  # Background darkness (lower = darker)
    },
    "neon": {
        "fg_saturation_boost": 1.5,  # Maximum saturation for neon effect
        "fg_brightness_boost": 1.3,  # Bright bars
        "bg_hue_shift": 0.5,  # Shift to complementary colors (0.5 = opposite)
        "bg_saturation": 0.6,  # Keep saturation for colored background
        "bg_brightness": 0.18,  # Very dark
    },
    "black_bg": {
        "fg_saturation_boost": 1.3,  # Boost saturation
        "fg_brightness_boost": 1.2,  # Boost brightness
        # Background is pure black (0,0,0)
    },
    "gradient_reverse": {
        "fg_saturation_boost": 1.2,  # Slight boost
        "fg_brightness_boost": 1.1,  # Slight boost
        "bg_brightness": 0.3,  # Reversed palette darkness
    },
}
# ======================================================


def extract_colors(image_path_or_url):
    """Extract color palette from cover art"""
    try:
        # Generate a unique filename based on the URL/path
        url_hash = hashlib.md5(image_path_or_url.encode()).hexdigest()[:12]
        temp_path = os.path.join(ALBUM_ART_DIR, f"cover_{url_hash}.jpg")

        # Download/copy image
        if image_path_or_url.startswith("http"):
            response = requests.get(image_path_or_url, timeout=5)
            img = Image.open(BytesIO(response.content))
        else:
            path = image_path_or_url.replace("file://", "")
            img = Image.open(path)

        # Save to our working directory
        img.save(temp_path)

        color_thief = ColorThief(temp_path)
        # Get palette of 3-5 colors for gradient
        palette = color_thief.get_palette(color_count=5, quality=1)

        return palette
    except Exception as e:
        log(f"Error extracting colors: {e}")
        return None


def create_color_files(colors):
    """Create color files in Cavasik's RGB format (one color per line: R,G,B)"""

    # Route to the selected color scheme
    if COLOR_SCHEME == "dominant_bg":
        return create_dominant_bg(colors)
    elif COLOR_SCHEME == "neon":
        return create_neon(colors)
    elif COLOR_SCHEME == "black_bg":
        return create_black_bg(colors)
    elif COLOR_SCHEME == "gradient_reverse":
        return create_gradient_reverse(colors)
    else:
        log(f"Unknown COLOR_SCHEME: {COLOR_SCHEME}, using dominant_bg")
        return create_dominant_bg(colors)


def create_dominant_bg(colors):
    """Solid background from dominant color, vibrant gradient foreground"""
    settings = SETTINGS["dominant_bg"]

    # Use first color (most dominant from ColorThief) as solid background
    dominant_r, dominant_g, dominant_b = colors[0]

    # Make background very dark version of dominant color
    h, s, v = colorsys.rgb_to_hsv(dominant_r / 255, dominant_g / 255, dominant_b / 255)
    s = s * settings["bg_saturation"]
    v = v * settings["bg_brightness"]
    bg_r, bg_g, bg_b = colorsys.hsv_to_rgb(h, s, v)

    # Solid background - same color for all gradient positions
    bg_content = f"{int(bg_r * 255)},{int(bg_g * 255)},{int(bg_b * 255)}\n" * len(
        colors
    )

    with open(BG_COLOR_FILE, "w") as f:
        f.write(bg_content)

    # Enhanced foreground with all colors
    fg_content = ""
    for r, g, b in colors:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        s = min(1.0, s * settings["fg_saturation_boost"])
        v = min(1.0, v * settings["fg_brightness_boost"])
        fg_r, fg_g, fg_b = colorsys.hsv_to_rgb(h, s, v)
        fg_content += f"{int(fg_r * 255)},{int(fg_g * 255)},{int(fg_b * 255)}\n"

    with open(FG_COLOR_FILE, "w") as f:
        f.write(fg_content)

    return FG_COLOR_FILE, BG_COLOR_FILE


def create_neon(colors):
    """Neon/cyberpunk style - super vibrant foreground, complementary colored background"""
    settings = SETTINGS["neon"]

    # Maximum saturation and brightness for foreground
    fg_content = ""
    for r, g, b in colors:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        s = min(1.0, s * settings["fg_saturation_boost"])
        v = min(1.0, v * settings["fg_brightness_boost"])
        fg_r, fg_g, fg_b = colorsys.hsv_to_rgb(h, s, v)
        fg_content += f"{int(fg_r * 255)},{int(fg_g * 255)},{int(fg_b * 255)}\n"

    with open(FG_COLOR_FILE, "w") as f:
        f.write(fg_content)

    # Complementary colored background (hue-shifted)
    bg_content = ""
    for r, g, b in colors:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        h = (h + settings["bg_hue_shift"]) % 1.0  # Shift to complementary
        s = settings["bg_saturation"]
        v = settings["bg_brightness"]
        bg_r, bg_g, bg_b = colorsys.hsv_to_rgb(h, s, v)
        bg_content += f"{int(bg_r * 255)},{int(bg_g * 255)},{int(bg_b * 255)}\n"

    with open(BG_COLOR_FILE, "w") as f:
        f.write(bg_content)

    return FG_COLOR_FILE, BG_COLOR_FILE


def create_black_bg(colors):
    """Pure black background for maximum contrast"""
    settings = SETTINGS["black_bg"]

    # Enhanced foreground
    fg_content = ""
    for r, g, b in colors:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        s = min(1.0, s * settings["fg_saturation_boost"])
        v = min(1.0, v * settings["fg_brightness_boost"])
        fg_r, fg_g, fg_b = colorsys.hsv_to_rgb(h, s, v)
        fg_content += f"{int(fg_r * 255)},{int(fg_g * 255)},{int(fg_b * 255)}\n"

    with open(FG_COLOR_FILE, "w") as f:
        f.write(fg_content)

    # Pure black background
    bg_content = "0,0,0\n" * len(colors)

    with open(BG_COLOR_FILE, "w") as f:
        f.write(bg_content)

    return FG_COLOR_FILE, BG_COLOR_FILE


def create_gradient_reverse(colors):
    """Reversed color palette for background creates interesting contrast"""
    settings = SETTINGS["gradient_reverse"]

    # Enhanced foreground
    fg_content = ""
    for r, g, b in colors:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        s = min(1.0, s * settings["fg_saturation_boost"])
        v = min(1.0, v * settings["fg_brightness_boost"])
        fg_r, fg_g, fg_b = colorsys.hsv_to_rgb(h, s, v)
        fg_content += f"{int(fg_r * 255)},{int(fg_g * 255)},{int(fg_b * 255)}\n"

    with open(FG_COLOR_FILE, "w") as f:
        f.write(fg_content)

    # Reversed and darkened palette for background
    bg_content = ""
    for r, g, b in reversed(colors):
        bg_r = int(r * settings["bg_brightness"])
        bg_g = int(g * settings["bg_brightness"])
        bg_b = int(b * settings["bg_brightness"])
        bg_content += f"{bg_r},{bg_g},{bg_b}\n"

    with open(BG_COLOR_FILE, "w") as f:
        f.write(bg_content)

    return FG_COLOR_FILE, BG_COLOR_FILE


def set_cavasik_colors(fg_path, bg_path):
    """Set Cavasik colors via DBus"""
    try:
        bus = dbus.SessionBus()
        cavasik = bus.get_object(
            "io.github.TheWisker.Cavasik", "/io/github/TheWisker/Cavasik"
        )
        interface = dbus.Interface(cavasik, "io.github.TheWisker.Cavasik")

        # Set foreground colors
        fg_result = interface.set_fg_colors(fg_path)
        log(f"  set_fg_colors returned: {fg_result}")

        # Set background colors
        bg_result = interface.set_bg_colors(bg_path)
        log(f"  set_bg_colors returned: {bg_result}")

        if fg_result and bg_result:
            log("Colors set successfully!")
        else:
            log("Warning: Color setting may have failed")

    except Exception as e:
        log(f"Error setting Cavasik colors: {e}")


def properties_changed(interface, changed, invalidated):
    """Called when MPRIS properties change"""
    if "Metadata" in changed:
        metadata = changed["Metadata"]
        if "mpris:artUrl" in metadata:
            art_url = metadata["mpris:artUrl"]
            log(f"New track: {metadata.get('xesam:title', 'Unknown')}")
            log(f"Cover art: {art_url}")

            colors = extract_colors(art_url)
            if colors:
                log(f"Extracted {len(colors)} colors: {colors}")
                fg_path, bg_path = create_color_files(colors)
                set_cavasik_colors(fg_path, bg_path)


def main():
    """Main entry point with command-line argument parsing"""
    global COLOR_SCHEME

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Sync Cavasik visualizer colors with currently playing music album art",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available color schemes:
  dominant_bg      - Solid background from dominant color (default, clean look)
  neon             - Cyberpunk style with complementary backgrounds (high energy)
  black_bg         - Pure black background (maximum contrast, classic)
  gradient_reverse - Reversed gradient background (unique depth effect)

Configuration:
  Config file: {config_file}
  Edit the config file to set your preferred color scheme persistently.
  Command-line arguments override the config file.

Examples:
  %(prog)s                          # Use config file setting
  %(prog)s --scheme neon            # Override config, use neon style
  %(prog)s -s black_bg              # Override config, use black background
  %(prog)s --list-schemes           # List all available schemes
        """.format(config_file=CONFIG_FILE),
    )

    parser.add_argument(
        "-s",
        "--scheme",
        type=str,
        default=None,
        choices=["dominant_bg", "neon", "black_bg", "gradient_reverse"],
        help="Color scheme to use (overrides config file)",
    )

    parser.add_argument(
        "--list-schemes",
        action="store_true",
        help="List all available color schemes with descriptions",
    )

    args = parser.parse_args()

    # Handle --list-schemes
    if args.list_schemes:
        print("Available Color Schemes:\n")
        print("1. dominant_bg (default)")
        print("   - Solid background from most dominant album color")
        print("   - Vibrant gradient foreground")
        print("   - Clean, cohesive look")
        print()
        print("2. neon")
        print("   - Maximum saturation cyberpunk style")
        print("   - Complementary colored backgrounds (opposite hue)")
        print("   - Best for: Electronic, synthwave, EDM")
        print()
        print("3. black_bg")
        print("   - Pure black background")
        print("   - Maximum contrast")
        print("   - Classic, minimalist aesthetic")
        print()
        print("4. gradient_reverse")
        print("   - Reversed color palette for background")
        print("   - Creates visual depth")
        print("   - Experimental, unique look")
        print()
        sys.exit(0)

    # Load config file
    config = load_config()

    # Set color scheme: command-line overrides config file
    if args.scheme:
        COLOR_SCHEME = args.scheme
        log(f"Using color scheme from command-line: {COLOR_SCHEME}")
    else:
        COLOR_SCHEME = config.get("color_scheme", "dominant_bg")
        log(f"Using color scheme from config: {COLOR_SCHEME}")

    log(f"Config file: {CONFIG_FILE}")
    log(f"Log file: {LOG_FILE}")
    log(f"Working directory: {WORK_DIR}")

    # Monitor all MPRIS players
    bus = dbus.SessionBus()
    bus.add_signal_receiver(
        properties_changed,
        signal_name="PropertiesChanged",
        dbus_interface="org.freedesktop.DBus.Properties",
        path="/org/mpris/MediaPlayer2",
    )

    log("Monitoring for media changes...")
    log("Press Ctrl+C to stop")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        log("\nStopped monitoring")
        sys.exit(0)


if __name__ == "__main__":
    main()

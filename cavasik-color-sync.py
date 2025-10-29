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

DBusGMainLoop(set_as_default=True)

# For Flatpak Cavasik, use a path accessible to the sandbox
# For system Cavasik, /tmp works fine
import os

FLATPAK_DATA_DIR = os.path.expanduser("~/.var/app/io.github.TheWisker.Cavasik/data")
os.makedirs(FLATPAK_DATA_DIR, exist_ok=True)

FG_COLOR_FILE = os.path.join(FLATPAK_DATA_DIR, "cavasik_fg_colors.rgb")
BG_COLOR_FILE = os.path.join(FLATPAK_DATA_DIR, "cavasik_bg_colors.rgb")

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
        if image_path_or_url.startswith("http"):
            response = requests.get(image_path_or_url, timeout=5)
            img = Image.open(BytesIO(response.content))
        else:
            path = image_path_or_url.replace("file://", "")
            img = Image.open(path)

        temp_path = "/tmp/cover_temp.jpg"
        img.save(temp_path)

        color_thief = ColorThief(temp_path)
        # Get palette of 3-5 colors for gradient
        palette = color_thief.get_palette(color_count=5, quality=1)

        return palette
    except Exception as e:
        print(f"Error extracting colors: {e}")
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
        print(f"Unknown COLOR_SCHEME: {COLOR_SCHEME}, using dominant_bg")
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
        print(f"  set_fg_colors returned: {fg_result}")

        # Set background colors
        bg_result = interface.set_bg_colors(bg_path)
        print(f"  set_bg_colors returned: {bg_result}")

        if fg_result and bg_result:
            print("Colors set successfully!")
        else:
            print("Warning: Color setting may have failed")

    except Exception as e:
        print(f"Error setting Cavasik colors: {e}")


def properties_changed(interface, changed, invalidated):
    """Called when MPRIS properties change"""
    if "Metadata" in changed:
        metadata = changed["Metadata"]
        if "mpris:artUrl" in metadata:
            art_url = metadata["mpris:artUrl"]
            print(f"New track: {metadata.get('xesam:title', 'Unknown')}")
            print(f"Cover art: {art_url}")

            colors = extract_colors(art_url)
            if colors:
                print(f"Extracted {len(colors)} colors: {colors}")
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

Examples:
  %(prog)s                          # Use default (dominant_bg)
  %(prog)s --scheme neon            # Use neon cyberpunk style
  %(prog)s -s black_bg              # Use black background
  %(prog)s --list-schemes           # List all available schemes
        """,
    )

    parser.add_argument(
        "-s",
        "--scheme",
        type=str,
        default="dominant_bg",
        choices=["dominant_bg", "neon", "black_bg", "gradient_reverse"],
        help="Color scheme to use (default: dominant_bg)",
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

    # Set color scheme from command-line
    COLOR_SCHEME = args.scheme
    print(f"Using color scheme: {COLOR_SCHEME}")

    # Monitor all MPRIS players
    bus = dbus.SessionBus()
    bus.add_signal_receiver(
        properties_changed,
        signal_name="PropertiesChanged",
        dbus_interface="org.freedesktop.DBus.Properties",
        path="/org/mpris/MediaPlayer2",
    )

    print("Monitoring for media changes...")
    print("Press Ctrl+C to stop")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("\nStopped monitoring")
        sys.exit(0)


if __name__ == "__main__":
    main()

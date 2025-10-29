#!/usr/bin/env python3
"""Test script to verify Cavasik DBus communication"""
import dbus
import sys
import os

# Use Flatpak-accessible directory
FLATPAK_DATA_DIR = os.path.expanduser("~/.var/app/io.github.TheWisker.Cavasik/data")
FG_COLOR_FILE = os.path.join(FLATPAK_DATA_DIR, "cavasik_fg_colors.rgb")
BG_COLOR_FILE = os.path.join(FLATPAK_DATA_DIR, "cavasik_bg_colors.rgb")

def test_cavasik_connection():
    """Test if we can connect to Cavasik via DBus"""
    try:
        bus = dbus.SessionBus()
        cavasik = bus.get_object(
            "io.github.TheWisker.Cavasik",
            "/io/github/TheWisker/Cavasik"
        )
        interface = dbus.Interface(cavasik, "io.github.TheWisker.Cavasik")

        print("✓ Successfully connected to Cavasik DBus interface")
        return interface
    except dbus.exceptions.DBusException as e:
        print(f"✗ Failed to connect to Cavasik: {e}")
        print("  Make sure Cavasik is running!")
        return None

def test_set_colors(interface, fg_path=FG_COLOR_FILE, bg_path=BG_COLOR_FILE):
    """Test setting colors"""
    try:
        print(f"\nTesting color setting:")
        print(f"  FG file: {fg_path}")
        print(f"  BG file: {bg_path}")

        # Test foreground colors
        result_fg = interface.set_fg_colors(fg_path)
        print(f"  set_fg_colors() returned: {result_fg}")

        # Test background colors
        result_bg = interface.set_bg_colors(bg_path)
        print(f"  set_bg_colors() returned: {result_bg}")

        if result_fg and result_bg:
            print("✓ Colors set successfully!")
        else:
            print("✗ Color setting may have failed (check Cavasik logs)")

    except Exception as e:
        print(f"✗ Error setting colors: {e}")

def check_color_files(fg_path=FG_COLOR_FILE, bg_path=BG_COLOR_FILE):
    """Verify color files exist and are in correct RGB format"""
    all_ok = True

    for path in [fg_path, bg_path]:
        try:
            with open(path, 'r') as f:
                content = f.read().strip()
                lines = content.split('\n')

                # Check format: each line should be R,G,B
                valid = all(len(line.split(',')) == 3 for line in lines if line)

                if valid:
                    print(f"✓ Color file exists and is valid: {path}")
                    print(f"  Contains {len(lines)} colors")
                else:
                    print(f"✗ Color file format incorrect (expected R,G,B format)")
                    all_ok = False
        except FileNotFoundError:
            print(f"✗ Color file not found: {path}")
            all_ok = False

    return all_ok

if __name__ == "__main__":
    print("=== Cavasik DBus Test ===\n")

    # Check color files
    files_ok = check_color_files()

    # Test DBus connection
    interface = test_cavasik_connection()

    # If connected and files exist, test setting colors
    if interface and files_ok:
        test_set_colors(interface)

    print("\n=== Test Complete ===")

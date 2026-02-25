#!/usr/bin/env python3
"""
YouTube Music VLC Player Setup Script
Automatically installs dependencies and sets up the player
"""

import subprocess
import sys
import os

# Make script executable if on posix system
if os.name == 'posix':
    try:
        os.chmod(__file__, 0o755)
    except:
        pass

def run_command(cmd, description):
    """Run a command and handle output"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False, e.stderr

def check_python():
    """Check Python version"""
    print("📋 Checking Python version...")
    if sys.version_info < (3, 6):
        print("❌ Python 3.6 or higher is required")
        print(f"   Your version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_vlc():
    """Check if VLC is installed"""
    print("\n📋 Checking for VLC...")
    try:
        result = subprocess.run(["vlc", "--version"], capture_output=True, text=True)
        if result.returncode == 0 or "VLC media player" in result.stdout:
            print("✅ VLC is installed")
            return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    print("❌ VLC is not installed or not in PATH")
    print("   Please install VLC from https://www.videolan.org/vlc/")
    return False

def install_python_deps():
    """Install Python dependencies"""
    success, _ = run_command(
        "pip install -r requirements.txt",
        "Installing Python dependencies"
    )
    return success

def install_yt_dlp():
    """Install yt-dlp if not in PATH"""
    print("\n📋 Checking for yt-dlp...")
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ yt-dlp is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    print("⚠️ yt-dlp not found in PATH, installing via pip...")
    return run_command(
        "pip install yt-dlp",
        "Installing yt-dlp"
    )[0]

def create_desktop_shortcut():
    """Create desktop shortcut (optional)"""
    print("\n🖼️ Would you like to create a desktop shortcut?")
    choice = input("Create shortcut? (y/N): ").strip().lower()

    if choice not in ['y', 'yes']:
        return True

    success = False
    script_path = os.path.abspath(__file__)
    dir_path = os.path.dirname(script_path)
    player_script = os.path.join(dir_path, "ytb_music_player.py")

    if os.name == 'posix':
        # macOS/Linux
        if sys.platform == 'darwin':
            # macOS - create Automator app
            success = create_macos_shortcut(player_script)
        else:
            # Linux - create .desktop file
            success = create_linux_shortcut(player_script)
    elif os.name == 'nt':
        # Windows - create batch file and shortcut
        success = create_windows_shortcut(player_script)

    if success:
        print("✅ Desktop shortcut created successfully")
    else:
        print("❌ Failed to create desktop shortcut")

    return True

def create_macos_shortcut(player_script):
    """Create macOS desktop shortcut"""
    try:
        app_name = "YouTube Music VLC Player"
        app_dir = f"{os.path.expanduser('~')}/Applications/{app_name}.app"

        # Create Automator app structure
        os.makedirs(os.path.join(app_dir, "Contents", "MacOS"), exist_ok=True)

        # Create shell script
        script_content = f'''#!/bin/bash
cd "{os.path.dirname(player_script)}"
python3 "{player_script}" "$@"
'''

        script_path = os.path.join(app_dir, "Contents", "MacOS", "run.sh")
        with open(script_path, 'w') as f:
            f.write(script_content)

        os.chmod(script_path, 0o755)

        # Create Info.plist
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>run.sh</string>
    <key>CFBundleName</key>
    <string>{app_name}</string>
    <key>CFBundleIdentifier</key>
    <string>com.youtubemusicvlc.player</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
</dict>
</plist>
'''

        plist_path = os.path.join(app_dir, "Contents", "Info.plist")
        with open(plist_path, 'w') as f:
            f.write(plist_content)

        return True
    except Exception as e:
        print(f"Error creating macOS shortcut: {e}")
        return False

def create_linux_shortcut(player_script):
    """Create Linux desktop shortcut"""
    try:
        desktop_file = f"{os.path.expanduser('~')}/.local/share/applications/youtube-music-vlc.desktop"

        content = f'''[Desktop Entry]
Name=YouTube Music VLC Player
Comment=Play YouTube Music via VLC
Exec=gnome-terminal -- python3 "{player_script}"
Icon=vlc
Terminal=true
Type=Application
Categories=AudioVideo;Player;
'''

        with open(desktop_file, 'w') as f:
            f.write(content)

        os.chmod(desktop_file, 0o644)
        return True
    except Exception as e:
        print(f"Error creating Linux shortcut: {e}")
        return False

def create_windows_shortcut(player_script):
    """Create Windows desktop shortcut"""
    try:
        # Create batch file
        batch_content = f'''@echo off
cd /d "{os.path.dirname(player_script)}"
python "{player_script}"
pause
'''

        batch_path = os.path.join(os.path.dirname(player_script), "ytb_music_player.bat")
        with open(batch_path, 'w') as f:
            f.write(batch_content)

        # Create shortcut (requires pywin32)
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(f"{os.path.expanduser('~')}\Desktop\YouTube Music VLC Player.lnk")
            shortcut.Targetpath = batch_path
            shortcut.WorkingDirectory = os.path.dirname(player_script)
            shortcut.IconLocation = "vlc.exe,0"
            shortcut.save()
            return True
        except ImportError:
            print("⚠️ pywin32 not installed, skipping shortcut creation")
            print("   Created batch file at:", batch_path)
            return True
    except Exception as e:
        print(f"Error creating Windows shortcut: {e}")
        return False

def main():
    """Main setup function"""
    print("🎵 YouTube Music VLC Player Setup")
    print("=" * 50)

    # Check Python version
    if not check_python():
        sys.exit(1)

    # Check VLC
    if not check_vlc():
        print("\nℹ️ You can continue with setup but VLC must be installed manually")
        choice = input("Continue anyway? (y/N): ").strip().lower()
        if choice not in ['y', 'yes']:
            sys.exit(1)

    # Install dependencies
    success = install_python_deps()

    # Install yt-dlp if needed
    install_yt_dlp()

    # Make script executable
    player_script = os.path.join(os.path.dirname(__file__), "ytb_music_player.py")
    if os.name == 'posix':
        os.chmod(player_script, 0o755)

    # Optional desktop shortcut
    create_desktop_shortcut()

    print("\n🎉 Setup completed!")
    print("=" * 50)
    print("\n🚀 To start using the player:")
    print(f"   cd {os.path.dirname(__file__)}")
    print("   python ytb_music_player.py --search 'your query'")
    print("\n📖 For more information, see README.md")
    print("\nℹ️ Note: You may need to restart your terminal for changes to take effect")

if __name__ == '__main__':
    main()

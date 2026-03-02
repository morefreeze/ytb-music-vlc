#!/usr/bin/env python3
"""
YouTube Music Player via VLC
Play YouTube Music directly from command line using VLC and yt-dlp

Version: 1.2.0

Optional Dependencies:
- keyboard: For TUI space selection functionality
"""

import os
import sys
import subprocess
import argparse
import tempfile
import tempfile
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time

# Try to import rich, gracefully fall back if not available
try:
    from rich.console import Console
    from rich.text import Text
    has_rich = True
except ImportError:
    has_rich = False

# Simple color support for terminals without rich
class SimpleColor:
    BOLD = '\033[1m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'

    @staticmethod
    def print_bold_cyan(text):
        print(f"{SimpleColor.BOLD}{SimpleColor.CYAN}{text}{SimpleColor.RESET}")

    @staticmethod
    def print_green(text):
        print(f"{SimpleColor.GREEN}{text}{SimpleColor.RESET}")

    @staticmethod
    def print_yellow(text):
        print(f"{SimpleColor.BOLD}{SimpleColor.YELLOW}{text}{SimpleColor.RESET}")

    @staticmethod
    def print_magenta(text):
        print(f"{SimpleColor.MAGENTA}{text}{SimpleColor.RESET}")

def get_ytdlp_path():
    """Find yt-dlp executable"""
    for path in os.environ['PATH'].split(os.pathsep):
        candidate = os.path.join(path, 'yt-dlp')
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
    candidate = os.path.join(os.path.dirname(sys.executable), 'yt-dlp')
    if os.path.exists(candidate) and os.access(candidate, os.X_OK):
        return candidate
    return None

def get_vlc_path():
    """Find VLC executable"""
    for path in os.environ['PATH'].split(os.pathsep):
        candidate = os.path.join(path, 'vlc')
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
    # Check common locations on macOS
    common_locations = [
        '/Applications/VLC.app/Contents/MacOS/VLC',
        '/usr/local/bin/vlc',
        '/opt/homebrew/bin/vlc'
    ]
    for candidate in common_locations:
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None

def extract_stream_url(url, quality='bestaudio', cookies=None, browser=None, ytdlp_path=None):
    """Extract stream URL using yt-dlp"""
    ytdlp = ytdlp_path or get_ytdlp_path()
    if not ytdlp:
        print("❌ Error: yt-dlp not found in PATH", file=sys.stderr)
        return None

    cmd = [
        ytdlp,
        '--ignore-config',
        '-f', quality,
        '--get-url',
        '--no-playlist',
        url
    ]

    cookie_file = handle_cookies_auth(ytdlp, browser, cookies, cmd)
    if cookie_file:
        cmd.extend(['--cookies', cookie_file])

    try:
        # Add a timeout to the subprocess call
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("❌ Error: yt-dlp command timed out while extracting stream URL.", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Error extracting stream: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return None

def extract_video_info(url, cookies=None, browser=None, ytdlp_path=None):
    """Extract video metadata using yt-dlp"""
    ytdlp = ytdlp_path or get_ytdlp_path()
    if not ytdlp:
        print("❌ Error: yt-dlp not found in PATH", file=sys.stderr)
        return None

    cmd = [
        ytdlp,
        '--ignore-config',
        '-j',
        '--no-playlist',
        url
    ]

    cookie_file = handle_cookies_auth(ytdlp, browser, cookies, cmd)
    if cookie_file:
        cmd.extend(['--cookies', cookie_file])

    try:
        # Add a timeout to the subprocess call
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print("❌ Error: yt-dlp command timed out while extracting video info.", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Error extracting info: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return None

def play_with_vlc(stream_url, video_title, vlc_args=None):
    """Play stream with VLC"""
    vlc = get_vlc_path()
    if not vlc:
        print("❌ Error: VLC not found in PATH", file=sys.stderr)
        return False

    cmd = [
        vlc,
        '--play-and-exit',
        '--meta-title', video_title,
        '--no-video-title-show',
        '--quiet',
        '--no-spu',
        stream_url
    ]

    if vlc_args:
        cmd.extend(vlc_args)

    try:
        # Start VLC process
        process = subprocess.Popen(cmd)
        process.wait()
        return process.returncode == 0
    except KeyboardInterrupt:
        print("\n⏹️ Playback interrupted by user")
        if process.poll() is None:
            process.terminate()
        return True
    except Exception as e:
        print(f"❌ Error playing stream: {e}", file=sys.stderr)
        return False

def handle_cookies_auth(ytdlp_path, browser, cookies, cmd):
    """Handles cookie authentication by exporting from browser or using a file."""
    cookie_file = None
    if browser:
        temp_cookie_file = os.path.join(tempfile.gettempdir(), f"ytb_music_cookies_{browser.replace(':', '_')}.txt")
        
        try:
            cookie_export_cmd = [
                ytdlp_path, '--cookies-from-browser', browser, '--cookies', temp_cookie_file
            ]
            subprocess.run(cookie_export_cmd, check=True, timeout=20, capture_output=True)
            cookie_file = temp_cookie_file
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            if os.path.exists(temp_cookie_file) and os.path.getsize(temp_cookie_file) > 0:
                cookie_file = temp_cookie_file
            else:
                cmd.extend(['--cookies-from-browser', browser])
    elif cookies:
        cookie_file = cookies
        
    return cookie_file

def search_music(query, max_results=5, cookies=None, browser=None, include_videos=False, debug=False):
    """Search YouTube Music and return results"""
    import time
    start_time = time.time()

    ytdlp = get_ytdlp_path()
    if not ytdlp:
        print("❌ Error: yt-dlp not found in PATH", file=sys.stderr)
        return None

    cmd = [
        ytdlp,
        '--ignore-config',
        '-j',
        '--no-playlist',
        '--flat-playlist',
        '--skip-download',
        '--no-check-certificate',
        '--no-warnings',
        '--no-check-formats',
        '--lazy-playlist',
        '--simulate',
        '--retries', '3',
        '--fragment-retries', '2',
        '--socket-timeout', '10',
        '--buffer-size', '16K'
    ]

    if debug:
        cmd.append('--verbose')

    cmd.extend([f'ytsearch{max_results}:{query}', '--default-search', 'ytsearch'])

    cookie_file = handle_cookies_auth(ytdlp, browser, cookies, cmd)
    if cookie_file:
        cmd.extend(['--cookies', cookie_file])

    try:
        if debug:
            print(f"ℹ️ Executing command: {' '.join(cmd)}")
        
        # Add a timeout to the subprocess call
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)

        if debug and result.stderr:
            print(f"--- yt-dlp debug output (stderr) ---\n{result.stderr}\n------------------------------------")
        
        if result.returncode != 0:
            if not debug and result.stderr:
                pass

        results = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    filtered = {
                        'id': data.get('id'),
                        'title': data.get('title'),
                        'uploader': data.get('uploader'),
                        'duration': data.get('duration', 0),
                        'view_count': data.get('view_count', 0),
                        'webpage_url': data.get('webpage_url'),
                        'url': data.get('url')
                    }
                    results.append(filtered)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse JSON line: {e}")
                    print(f"   Line content: {repr(line)}")
                    continue

        search_time = time.time() - start_time
        print(f"✅ Search completed in {search_time:.2f} seconds")
        print(f"🔍 Found {len(results)} results")

        return results[:max_results]
    except subprocess.TimeoutExpired:
        print("❌ Error: yt-dlp command timed out after 60 seconds. This might be a network issue or a problem with yt-dlp itself.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return None

def extract_playlist_urls(playlist_url, cookies=None, browser=None, ytdlp_path=None):
    """Extract all video URLs from a playlist"""
    ytdlp = ytdlp_path or get_ytdlp_path()
    if not ytdlp:
        print("❌ Error: yt-dlp not found in PATH", file=sys.stderr)
        return None

    cmd = [
        ytdlp,
        '--ignore-config',
        '-j',
        '--flat-playlist',
    ]

    cookie_file = handle_cookies_auth(ytdlp, browser, cookies, cmd)
    if cookie_file:
        cmd.extend(['--cookies', cookie_file])

    cmd.append(playlist_url)

    try:
        # Add a timeout to the subprocess call
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video = json.loads(line)
                    videos.append(video)
                except json.JSONDecodeError:
                    continue
        return videos
    except subprocess.TimeoutExpired:
        print("❌ Error: yt-dlp command timed out while extracting playlist URLs.", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Error extracting playlist: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return None


def generate_m3u_playlist(tracks, output_path):
    """Generate M3U playlist file from tracks"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for track in tracks:
            duration = track.get('duration', 0)
            title = track.get('title', 'Unknown Title')
            stream_url = track.get('stream_url', track.get('url'))
            if stream_url:
                f.write(f'#EXTINF:{duration},{title}\n')
                f.write(f'{stream_url}\n')


def parse_m3u_playlist(playlist_path):
    """Parse M3U playlist file and return tracks"""
    tracks = []
    with open(playlist_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF:'):
            # Parse duration and title
            parts = line.split('#EXTINF:')[1].split(',', 1)
            duration = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
            title = parts[1].strip() if len(parts) > 1 else 'Unknown Title'

            # Next line should be the URL
            if i + 1 < len(lines):
                url = lines[i+1].strip()
                if url and not url.startswith('#'):
                    tracks.append({
                        'title': title,
                        'duration': duration,
                        'url': url
                    })
                    i += 1  # Skip the URL line
        i += 1
    return tracks


def parse_xspf_playlist(playlist_path):
    """Parse XSPF playlist file and return tracks"""
    tracks = []

    try:
        tree = ET.parse(playlist_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"❌ Error parsing XSPF playlist: {e}")
        return None

    # Define the namespace
    ns = {'xspf': 'http://xspf.org/ns/0/'}

    # Find all track elements
    track_elements = root.findall('.//xspf:track', ns)

    for track in track_elements:
        location = track.find('xspf:location', ns)
        title = track.find('xspf:title', ns)
        duration = track.find('xspf:duration', ns)
        creator = track.find('xspf:creator', ns)

        track_info = {}
        if location is not None:
            track_info['url'] = location.text
        if title is not None:
            track_info['title'] = title.text
        if duration is not None and duration.text:
            # Convert from milliseconds to seconds
            track_info['duration'] = int(int(duration.text) / 1000)
        if creator is not None:
            track_info['uploader'] = creator.text
            track_info['creator'] = creator.text

        if track_info.get('url'):
            tracks.append(track_info)

    return tracks


def load_playlist(playlist_path):
    """Load and parse playlist file (supports M3U and XSPF formats)"""
    if not os.path.exists(playlist_path):
        print(f"❌ Playlist file not found: {playlist_path}")
        return None

    # Determine file format based on extension
    if playlist_path.lower().endswith('.xspf'):
        return parse_xspf_playlist(playlist_path)
    elif playlist_path.lower().endswith('.m3u') or playlist_path.lower().endswith('.m3u8'):
        return parse_m3u_playlist(playlist_path)
    else:
        print(f"❌ Unsupported playlist format: {playlist_path}")
        print("ℹ️ Supported formats: XSPF (.xspf), M3U (.m3u, .m3u8)")
        return None


def generate_xspf_playlist(tracks, output_path):
    """Generate XSPF playlist file from tracks"""
    # Create the playlist root element
    playlist = ET.Element('playlist', version='1', xmlns='http://xspf.org/ns/0/')

    # Add playlist title
    title = ET.SubElement(playlist, 'title')
    title.text = 'YouTube Music Playlist'

    # Add track list
    track_list = ET.SubElement(playlist, 'trackList')

    for track in tracks:
        track_elem = ET.SubElement(track_list, 'track')

        # Add track location
        location = ET.SubElement(track_elem, 'location')
        location.text = track.get('stream_url')

        # Add track title
        title_elem = ET.SubElement(track_elem, 'title')
        title_elem.text = track.get('title', 'Unknown Title')

        # Add track duration if available (convert to milliseconds)
        duration = track.get('duration', 0)
        if duration:
            duration_elem = ET.SubElement(track_elem, 'duration')
            duration_elem.text = str(duration * 1000)

        # Add artist if available
        artist = track.get('uploader') or track.get('creator')
        if artist:
            creator = ET.SubElement(track_elem, 'creator')
            creator.text = artist

    # Prettify the XML output
    rough_string = ET.tostring(playlist, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)


def pre_extract_stream_urls(tracks, args):
    """Pre-extract stream URLs for all tracks in playlist"""
    extracted_tracks = []
    total_tracks = len(tracks)

    for i, track in enumerate(tracks, 1):
        print(f"🔍 Extracting stream URL for track {i}/{total_tracks}...")

        # Get the video URL
        video_url = track.get('webpage_url') or track.get('url')
        if not video_url:
            print(f"❌ No URL found for track {i}, skipping...")
            continue

        # Extract stream URL
        stream_url = extract_stream_url(video_url, args.quality, args.cookies, args.browser)

        if stream_url:
            # Add stream URL to track info
            track['stream_url'] = stream_url
            extracted_tracks.append(track)

            # Show track info with coloring
            title = track.get('title', 'Unknown Title')
            if has_rich:
                console = Console()
                console.print(f"   ✅ [green]{title}[/green]")
            else:
                print(f"   ✅ ", end="")
                SimpleColor.print_green(title)
        else:
            print(f"   ❌ Failed to extract stream URL, skipping...")

    return extracted_tracks


def play_playlist_with_vlc(tracks, args, vlc_args):
    """Play tracks using a proper VLC playlist file"""
    import tempfile
    import os

    # Pre-extract stream URLs
    print("\n🔄 Pre-extracting stream URLs for all tracks...")
    tracks_with_streams = pre_extract_stream_urls(tracks, args)

    if not tracks_with_streams:
        print("❌ No valid tracks to play")
        return False

    print(f"\n✅ Successfully extracted stream URLs for {len(tracks_with_streams)}/{len(tracks)} tracks")

    # Create temporary playlist file
    playlist_suffix = '.xspf' if args.playlist_format == 'xspf' else '.m3u'
    with tempfile.NamedTemporaryFile(mode='w', suffix=playlist_suffix, delete=False, encoding='utf-8') as f:
        temp_playlist = f.name

    try:
        # Generate playlist in the requested format
        if args.playlist_format == 'xspf':
            generate_xspf_playlist(tracks_with_streams, temp_playlist)
        else:
            generate_m3u_playlist(tracks_with_streams, temp_playlist)

        print(f"\n🎵 Generated {args.playlist_format.upper()} playlist with {len(tracks_with_streams)} tracks")

        # Save playlist if requested
        if args.save_playlist:
            save_path = args.save_playlist
            if os.path.exists(save_path):
                save_path = handle_duplicate_file(save_path)
                if not save_path:
                    print("ℹ️ Save operation cancelled by user")
                else:
                    if args.playlist_format == 'xspf':
                        generate_xspf_playlist(tracks_with_streams, save_path)
                    else:
                        generate_m3u_playlist(tracks_with_streams, save_path)
                    print(f"💾 Playlist saved to {save_path}")
            else:
                if args.playlist_format == 'xspf':
                    generate_xspf_playlist(tracks_with_streams, save_path)
                else:
                    generate_m3u_playlist(tracks_with_streams, save_path)
                print(f"💾 Playlist saved to {save_path}")

        # Launch VLC with the playlist
        vlc = get_vlc_path()
        cmd = [vlc, '--play-and-exit']
        cmd.extend(vlc_args)

        # Add shuffle and repeat options to VLC if requested - this shuffles playback order after selection/sorting
        if args.shuffle:
            cmd.extend(['--shuffle'])
        if args.repeat:
            cmd.extend(['--repeat'])

        cmd.append(temp_playlist)

        print("\n▶️ Starting VLC with playlist...")
        print(f"🎵 Total tracks: {len(tracks_with_streams)}")
        if args.shuffle:
            print("🔀 Playback will be shuffled")
        if args.repeat:
            print("🔁 Playback will repeat")
        print("\nPress Ctrl+C to stop playback")
        print("-" * 50)

        try:
            # Start VLC process
            process = subprocess.Popen(cmd)
            process.wait()
            return process.returncode == 0 or process.returncode == -2  # -2 for SIGINT
        except KeyboardInterrupt:
            print("\n⏹️ Playback interrupted by user")
            if process.poll() is None:
                process.terminate()
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error playing playlist: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Clean up temporary playlist
        if os.path.exists(temp_playlist):
            os.unlink(temp_playlist)

def handle_duplicate_file(file_path):
    """Handle duplicate files by prompting user for action"""
    while True:
        print(f"⚠️ File already exists: {file_path}")
        print("What would you like to do?")
        print("1. Overwrite existing file")
        print("2. Save with auto-incremented suffix (e.g., filename_1.ext)")
        print("3. Cancel save operation")

        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == '1':
            # Overwrite
            return file_path
        elif choice == '2':
            # Auto-increment suffix
            base, ext = os.path.splitext(file_path)
            counter = 1
            new_path = f"{base}_{counter}{ext}"
            while os.path.exists(new_path):
                counter += 1
                new_path = f"{base}_{counter}{ext}"
            print(f"📝 Will save as: {new_path}")

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
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import rich, gracefully fall back if not available
try:
    from rich.console import Console
    from rich.text import Text
    has_rich = True
except ImportError:
    has_rich = False

def process_track_info(entry, include_videos=False):
    """Process individual track information from search results"""
    try:
        data = json.loads(entry)

        # Skip videos if not included
        duration = data.get('duration')
        if not include_videos and duration is not None and duration > 3600:
            return None

        filtered = {
            'id': data.get('id'),
            'title': data.get('title'),
            'uploader': data.get('uploader'),
            'duration': data.get('duration', 0),
            'view_count': data.get('view_count', 0),
            'webpage_url': data.get('webpage_url'),
            'url': data.get('url')
        }
        return filtered
    except json.JSONDecodeError:
        return None

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

def extract_stream_url(url, quality='best', cookies=None, browser=None, ytdlp_path=None, debug=False):
    """Extract stream URL using yt-dlp"""
    ytdlp = ytdlp_path or get_ytdlp_path()
    if not ytdlp:
        print("❌ Error: yt-dlp not found in PATH", file=sys.stderr)
        return None

    # Use a more flexible format selector that works with current YouTube restrictions
    if quality == 'bestaudio':
        format_spec = 'bestaudio[ext=m4a]/bestaudio/best'
    elif quality == 'worstaudio':
        format_spec = 'worstaudio[ext=m4a]/worstaudio/worst'
    else:
        format_spec = quality

    cmd = [
        ytdlp,
        '--ignore-config',
        '--remote-components', 'ejs:github',
        '-f', format_spec,
        '--get-url',
        '--no-playlist',
        url
    ]

    if browser:
        cmd.extend(['--cookies-from-browser', browser])
    elif cookies:
        cmd.extend(['--cookies', cookies])

    if debug:
        print(f"\n[DEBUG] === Stream URL Extraction ===")
        print(f"[DEBUG] URL: {url}")
        print(f"[DEBUG] Quality: {quality}")
        print(f"[DEBUG] Format spec: {format_spec}")
        print(f"[DEBUG] Command: {' '.join(cmd)}")
        print(f"[DEBUG] Starting extraction...")

    try:
        # Add a timeout to the subprocess call
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)

        if debug:
            print(f"[DEBUG] Extraction successful")
            print(f"[DEBUG] Stream URL length: {len(result.stdout.strip())} characters")

        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("❌ Error: yt-dlp command timed out while extracting stream URL.", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        if debug:
            print(f"[DEBUG] Extraction failed with exit code: {e.returncode}")
            print(f"[DEBUG] Error output: {e.stderr}")
        print(f"❌ Error extracting stream: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return None

def extract_video_info(url, cookies=None, browser=None, ytdlp_path=None, debug=False):
    """Extract video metadata using yt-dlp"""
    ytdlp = ytdlp_path or get_ytdlp_path()
    if not ytdlp:
        print("❌ Error: yt-dlp not found in PATH", file=sys.stderr)
        return None

    cmd = [
        ytdlp,
        '--ignore-config',
        '--remote-components', 'ejs:github',
        '-j',
        '--no-playlist',
        url
    ]

    if browser:
        cmd.extend(['--cookies-from-browser', browser])
    elif cookies:
        cmd.extend(['--cookies', cookies])

    if debug:
        print(f"\n[DEBUG] === Video Info Extraction ===")
        print(f"[DEBUG] URL: {url}")
        print(f"[DEBUG] Command: {' '.join(cmd)}")
        print(f"[DEBUG] Starting extraction...")

    try:
        # Add a timeout to the subprocess call
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)

        if debug:
            print(f"[DEBUG] Extraction successful")
            print(f"[DEBUG] Response size: {len(result.stdout)} characters")

        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print("❌ Error: yt-dlp command timed out while extracting video info.", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        if debug:
            print(f"[DEBUG] Extraction failed with exit code: {e.returncode}")
            print(f"[DEBUG] Error output: {e.stderr}")
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
        '--remote-components', 'ejs:github',
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

    if browser:
        cmd.extend(['--cookies-from-browser', browser])
    elif cookies:
        cmd.extend(['--cookies', cookies])

    try:
        if debug:
            print(f"\n[DEBUG] === Search Operation ===")
            print(f"[DEBUG] Query: '{query}'")
            print(f"[DEBUG] Max results: {max_results}")
            print(f"[DEBUG] Include videos: {include_videos}")
            print(f"[DEBUG] Command: {' '.join(cmd)}")
            print(f"[DEBUG] Starting search...")

        # Add a timeout to the subprocess call
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)

        if debug and result.stderr:
            print(f"[DEBUG] yt-dlp stderr output:\n{result.stderr}")

        if result.returncode != 0:
            if debug:
                print(f"[DEBUG] yt-dlp exit code: {result.returncode}")
            if not debug and result.stderr:
                pass

        # Get raw entries from output
        entries = []
        for line in result.stdout.strip().split('\n'):
            if line:
                entries.append(line)

        search_time = time.time() - start_time
        if debug:
            print(f"[DEBUG] Search completed in {search_time:.2f} seconds")
            print(f"[DEBUG] Found {len(entries)} raw results")
        print(f"✅ Search completed in {search_time:.2f} seconds")
        print(f"🔍 Found {len(entries)} results")

        # Return raw entries for parallel processing later
        return entries[:max_results]
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
        '--remote-components', 'ejs:github',
        '-j',
        '--flat-playlist'
    ]

    if browser:
        cmd.extend(['--cookies-from-browser', browser])
    elif cookies:
        cmd.extend(['--cookies', cookies])

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
            # Use stream_url if available, otherwise fall back to url
            stream_url = track.get('stream_url') or track.get('url')
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

        # Add track location - use stream_url if available, otherwise fall back to url
        location = ET.SubElement(track_elem, 'location')
        location.text = track.get('stream_url') or track.get('url')

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
        if args.debug:
            print(f"\n[DEBUG] === Pre-extraction for track {i} ===")
            print(f"[DEBUG] Track: {track.get('title', 'Unknown')}")
            print(f"[DEBUG] URL: {video_url}")
        stream_url = extract_stream_url(video_url, args.quality, args.cookies, args.browser, debug=args.debug)

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

            if args.debug:
                print(f"[DEBUG] Stream URL: {stream_url[:100]}...")
        else:
            print(f"   ❌ Failed to extract stream URL, skipping...")

    return extracted_tracks


def play_playlist_with_vlc(tracks, args, vlc_args):
    """Play tracks using a proper VLC playlist file"""
    import tempfile
    import os

    # Pre-extract stream URLs for all tracks
    print("\n🔄 Pre-extracting stream URLs for all tracks...")

    # Use ThreadPoolExecutor for parallel stream URL extraction
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def extract_single_track(track_info):
        """Extract stream URL for a single track"""
        import time
        start_time = time.time()

        video_url = track_info.get('webpage_url') or track_info.get('url')
        if not video_url:
            return None

        # Extract stream URL using the updated function
        if args.debug:
            print(f"\n[DEBUG] === Parallel extraction for track ===")
            print(f"[DEBUG] Track: {track_info.get('title', 'Unknown')}")
            print(f"[DEBUG] URL: {video_url}")
        stream_url = extract_stream_url(video_url, args.quality, args.cookies, args.browser, debug=args.debug)

        if args.debug:
            elapsed = time.time() - start_time
            print(f"[DEBUG] Extracting stream URL for '{track_info.get('title', 'Unknown')}' took {elapsed:.2f}s")

        if stream_url:
            track_info['stream_url'] = stream_url
            if args.debug:
                print(f"[DEBUG] Successfully extracted stream URL: {stream_url[:100]}...")
            return track_info
        return None

    # Extract stream URLs in parallel
    tracks_with_streams = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all tasks
        future_to_track = {executor.submit(extract_single_track, track): track for track in tracks}

        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_track), 1):
            result = future.result()
            if result:
                tracks_with_streams.append(result)
                title = result.get('title', 'Unknown Title')
                if has_rich:
                    console = Console()
                    console.print(f"   ✅ [green]{title}[/green]")
                else:
                    print(f"   ✅ ", end="")
                    SimpleColor.print_green(title)

            # Show progress
            print(f"🔍 Extracting stream URL for track {i}/{len(tracks)}...")

    if not tracks_with_streams:
        print("\n❌ No valid tracks to play")
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

        # Debug: Print tracks being added to playlist and save playlist content
        if args.debug:
            print(f"\n[DEBUG] === Playlist Contents ===")
            for i, track in enumerate(tracks_with_streams, 1):
                stream_url = track.get('stream_url')
                url = track.get('url')
                title = track.get('title', 'Unknown')
                print(f"[DEBUG] Track {i}: {title}")
                print(f"[DEBUG]   Stream URL: {stream_url[:100] if stream_url else 'None'}")
                print(f"[DEBUG]   Fallback URL: {url[:100] if url else 'None'}")

            # Save playlist content to debug file
            debug_playlist_path = temp_playlist + '.debug'
            with open(temp_playlist, 'r', encoding='utf-8') as f:
                playlist_content = f.read()
            with open(debug_playlist_path, 'w', encoding='utf-8') as f:
                f.write(playlist_content)
            print(f"[DEBUG] Playlist saved to: {debug_playlist_path}")

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
            return new_path
        elif choice == '3':
            # Cancel
            return None
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")


def select_tracks_with_space(results):
    """Create a rich TUI for selecting YouTube Music tracks similar to create_video_list_ui"""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time

        console = Console()

        # Store selection state - default to no tracks selected
        selected = set()
        current_index = 0

        # Preloading state (removed from UI)
        preloaded_tracks = {}
        preloading_progress = {"current": 0, "total": len(results)}
        preloading_active = True

        def preload_track(track_info, index):
            """Preload stream URL for a single track"""
            video_url = track_info.get('webpage_url') or track_info.get('url')
            if not video_url:
                return index, None

            # Simulate extraction (replace with actual extraction)
            # For now, just mark as preloaded
            return index, True

        def create_track_table():
            """Create and update the track selection table with selection column"""
            table = Table(show_header=True, header_style="bold cyan", show_lines=True)
            table.add_column("Select", style="bold", width=8)
            table.add_column("#", style="dim", width=4)
            table.add_column("Track Title", style="white", no_wrap=False)
            table.add_column("Artist", style="cyan", width=20)
            table.add_column("Duration", style="magenta", width=10)
            table.add_column("Views", style="green", width=12)
            table.add_column("Status", style="bold", width=15)

            for i, track in enumerate(results):
                title = track.get('title', 'Unknown Title')
                artist = track.get('uploader', 'Unknown Artist')

                # Format duration
                duration = track.get('duration')
                if duration is not None:
                    duration_int = int(duration)
                    minutes = duration_int // 60
                    seconds = duration_int % 60
                    duration_str = f"{minutes}:{seconds:02d}"
                else:
                    duration_str = "N/A"

                # Format view count
                view_count = track.get('view_count')
                if view_count:
                    if view_count >= 1000000:
                        views_str = f"{view_count/1000000:.1f}M"
                    elif view_count >= 1000:
                        views_str = f"{view_count/1000:.1f}K"
                    else:
                        views_str = str(view_count)
                else:
                    views_str = "N/A"

                # Selection indicator
                select_indicator = "[green]✓[/green]" if i in selected else "[white]□[/white]"

                status = ""
                if i == current_index:
                    status = "[bold yellow]◄[/bold yellow]"  # Cursor indicator

                if i in selected:
                    status += "[bold green]SELECTED[/bold green]"
                else:
                    status += "[dim]Unselected[/dim]"

                table.add_row(select_indicator, str(i + 1), title, artist, duration_str, views_str, status)

            return table

        def update_display(preloading_status=""):
            """Update the display with current state"""
            console.clear()

            # Header
            header = Panel.fit(
                "[bold cyan]🎵 YouTube Music Selection Interface[/bold cyan]\n"
                f"[bold yellow]Found {len(results)} tracks. Use arrow keys to navigate, space to toggle, a to select all, Enter to confirm, Q to quit.[/bold yellow]",
                border_style="cyan",
            )
            console.print(header)
            console.print()

            # Track table
            table = create_track_table()
            console.print(table)

            # Footer with instructions
            footer_text = f"[bold]Selected:[/bold] {len(selected)}/{len(results)} | "
            footer_text += "[bold green]Space:[/bold green] Toggle | "
            footer_text += "[bold blue]A:[/bold blue] Select All | "
            footer_text += "[bold blue]Enter:[/bold blue] Confirm | "
            footer_text += "[bold red]Q:[/bold red] Quit"

            # Add preloading status if provided
            if preloading_status:
                footer_text += f"\n[bold yellow]{preloading_status}[/bold yellow]"

            footer = Panel(
                footer_text,
                border_style="green",
            )
            console.print(footer)

        # Start preloading in background
        def start_preloading():
            """Start preloading tracks in background"""
            nonlocal preloading_active

            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit all tasks
                futures = []
                for i, track in enumerate(results):
                    future = executor.submit(preload_track, track, i)
                    futures.append(future)

                # Process completed tasks
                for future in as_completed(futures):
                    if not preloading_active:
                        break
                    index, _ = future.result()
                    preloading_progress["current"] += 1
                    # Preloading progress removed from UI

            preloading_active = False

        # Initial display
        update_display()

        # Start preloading in background thread
        import threading
        preload_thread = threading.Thread(target=start_preloading, daemon=True)
        preload_thread.start()

        # Keyboard handling
        import sys
        import termios
        import tty
        import select

        def get_key():
            """Get a single keypress"""
            try:
                # Save current terminal settings
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                tty.setraw(sys.stdin.fileno())

                # Read key
                ch = sys.stdin.read(1)

                # Handle special keys
                if ch == '\x1b':  # Escape sequence
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        ch3 = sys.stdin.read(1)
                        if ch3 in 'ABCD':  # Arrow keys
                            return {'[A': 'up', '[B': 'down', '[C': 'right', '[D': 'left'}.get('[' + ch3, '')
                        elif ch3 == 'H':  # Home
                            return 'home'
                        elif ch3 == 'F':  # End
                            return 'end'

                return ch.lower()
            except Exception:
                return ''
            finally:
                # Restore terminal settings
                try:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                except:
                    pass

        # Main interaction loop
        while True:
            key = get_key()

            if key == 'q':
                preloading_active = False
                return None
            elif key == '\n' or key == '\r':  # Enter key for confirmation
                preloading_active = False
                if selected:
                    return [results[i] for i in sorted(selected)]
                return None
            elif key == 'a':
                # Toggle select all
                if len(selected) == len(results):
                    selected.clear()
                else:
                    selected = set(range(len(results)))
                update_display()
            elif key == ' ' :  # Space key for toggle
                if current_index not in selected:
                    selected.add(current_index)
                else:
                    selected.remove(current_index)
                update_display()
            elif key == 'up':
                current_index = max(0, current_index - 1)
                update_display()
            elif key == 'down':
                current_index = min(len(results) - 1, current_index + 1)
                update_display()
            elif key == 'home':
                current_index = 0
                update_display()
            elif key == 'end':
                current_index = len(results) - 1
                update_display()

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled.[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red]TUI failed: {e}[/red]")
        console.print("[yellow]Falling back to CLI mode...[/yellow]")
        return create_simple_cli_interface(results)


def create_simple_cli_interface(results):
    """Simple CLI fallback interface"""
    if has_rich:
        from rich.console import Console
        from rich.table import Table
        from rich.prompt import Prompt
        
        console = Console()

        console.print("\n[bold cyan]SIMPLE CLI SELECTION[/bold cyan]")
        console.print(f"Found {len(results)} tracks. Please select which ones to play:")
        console.print("[bold]Instructions:[/bold]")
        console.print("- Enter track numbers separated by commas (e.g., 1,3,5)")
        console.print("- Enter 'all' to select all tracks")
        console.print("- Press Enter with no input to select none")
        console.print("- Enter 'q' to quit")
        console.print()

        # Display track list
        table = Table(show_header=True, header_style="bold cyan", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Track Title", style="white", no_wrap=False)
        table.add_column("Artist", style="cyan", width=20)
        table.add_column("Duration", style="magenta", width=10)
        table.add_column("Views", style="green", width=12)

        for i, track in enumerate(results, 1):
            title = track.get('title', 'Unknown Title')
            artist = track.get('uploader', 'Unknown Artist')
            
            # Format duration
            duration = track.get('duration')
            if duration:
                duration_int = int(duration)
                minutes = duration_int // 60
                seconds = duration_int % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "N/A"

            # Format view count
            view_count = track.get('view_count')
            if view_count:
                if view_count >= 1000000:
                    views_str = f"{view_count/1000000:.1f}M"
                elif view_count >= 1000:
                    views_str = f"{view_count/1000:.1f}K"
                else:
                    views_str = str(view_count)
            else:
                views_str = "N/A"

            table.add_row(str(i), title, artist, duration_str, views_str)

        console.print(table)

        while True:
            user_input = Prompt.ask("\nYour selection").strip().lower()

            if user_input == 'q':
                return None

            if not user_input:
                console.print("No tracks selected.")
                return None

            if user_input == 'all':
                return results

            try:
                # Parse comma-separated numbers
                selected_indices = []
                for part in user_input.split(','):
                    part = part.strip()
                    if part:
                        index = int(part)
                        if 1 <= index <= len(results):
                            selected_indices.append(index - 1)  # Convert to 0-based
                        else:
                            console.print(f"[red]Invalid track number: {index}[/red]")
                            break
                else:
                    # All indices are valid
                    selected_tracks = [results[i] for i in selected_indices]
                    console.print(f"[green]Selected {len(selected_tracks)} tracks.[/green]")
                    return selected_tracks

            except ValueError:
                console.print("[red]Invalid input. Please enter numbers separated by commas, or 'all', or leave empty.[/red]")
    else:
        # Fallback for systems without rich
        print("\nSIMPLE CLI SELECTION")
        print(f"Found {len(results)} tracks. Please select which ones to play:")
        print("Instructions:")
        print("- Enter track numbers separated by commas (e.g., 1,3,5)")
        print("- Enter 'all' to select all tracks")
        print("- Press Enter with no input to select none")
        print("- Enter 'q' to quit")
        print()

        # Display track list
        print("{:<4} {:<50} {:<20} {:<10} {:<12}".format("#", "Track Title", "Artist", "Duration", "Views"))
        print("-" * 100)
        
        for i, track in enumerate(results, 1):
            title = track.get('title', 'Unknown Title')
            artist = track.get('uploader', 'Unknown Artist')
            
            # Format duration
            duration = track.get('duration')
            if duration:
                duration_int = int(duration)
                minutes = duration_int // 60
                seconds = duration_int % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "N/A"

            # Format view count
            view_count = track.get('view_count')
            if view_count:
                if view_count >= 1000000:
                    views_str = f"{view_count/1000000:.1f}M"
                elif view_count >= 1000:
                    views_str = f"{view_count/1000:.1f}K"
                else:
                    views_str = str(view_count)
            else:
                views_str = "N/A"

            print("{:<4} {:<50} {:<20} {:<10} {:<12}".format(str(i), title[:47] + '...' if len(title) > 47 else title, 
                                                             artist[:17] + '...' if len(artist) > 17 else artist, 
                                                             duration_str, views_str))

        while True:
            user_input = input("\nYour selection: ").strip().lower()

            if user_input == 'q':
                return None

            if not user_input:
                print("No tracks selected.")
                return None

            if user_input == 'all':
                return results

            try:
                # Parse comma-separated numbers
                selected_indices = []
                for part in user_input.split(','):
                    part = part.strip()
                    if part:
                        index = int(part)
                        if 1 <= index <= len(results):
                            selected_indices.append(index - 1)  # Convert to 0-based
                        else:
                            print(f"Invalid track number: {index}")
                            break
                else:
                    # All indices are valid
                    selected_tracks = [results[i] for i in selected_indices]
                    print(f"Selected {len(selected_tracks)} tracks.")
                    return selected_tracks

            except ValueError:
                print("Invalid input. Please enter numbers separated by commas, or 'all', or leave empty.")


def main():
    """Main function that initializes argparse and handles program flow"""
    parser = argparse.ArgumentParser(
        description="YouTube Music Player via VLC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://www.youtube.com/watch?v=dQw4w9WgXcQ
  %(prog)s --search "上海交响乐团" -b "chrome:Profile 5" --max-results 3

  Advanced usage:
  %(prog)s --search "上海交响乐团" --include-videos --sort views --shuffle --save-playlist "shanghai_symphony.xspf"

  Troubleshooting format errors:
  %(prog)s <url> -q worstaudio  # Use lowest quality if bestaudio fails
        """
    )
    
    # Create a group for primary sources (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('url', nargs='?', help='YouTube Music URL (video, track, album, or playlist)')
    group.add_argument('-s', '--search', help='Search YouTube Music by query')
    group.add_argument('--load-playlist', help='Load and play from existing playlist file')

    parser.add_argument('-q', '--quality', default='best',
                       help='Stream quality preference (best, bestaudio, worstaudio, or format code)')
    parser.add_argument('-c', '--cookies', help='Path to cookies file for premium access')
    parser.add_argument('-b', '--browser', help='Extract cookies from browser (e.g., "chrome", "firefox:Profile 5")')
    parser.add_argument('--no-video', action='store_true',
                       help='Force audio-only playback even if video is available')
    parser.add_argument('--fullscreen', action='store_true',
                       help='Start VLC in fullscreen mode (when video is available)')
    parser.add_argument('--volume', type=int, help='Set initial volume (0-100)')
    parser.add_argument('--max-results', type=int, default=10,
                       help='Maximum search results to show (default: 10)')
    parser.add_argument('--list-formats', action='store_true',
                       help='List available formats and exit')
    parser.add_argument('--shuffle', action='store_true',
                       help='Shuffle playlist playback order after selection and sorting')
    parser.add_argument('--repeat', action='store_true',
                       help='Repeat playlist playback')
    parser.add_argument('--playlist-start', type=int, default=0,
                       help='Start playlist at specified index (0-based)')
    parser.add_argument('--playlist-end', type=int,
                       help='End playlist at specified index (0-based)')
    parser.add_argument('--save-playlist', help='Save generated playlist to file')
    parser.add_argument('--playlist-format', choices=['m3u', 'xspf'], default='xspf',
                       help='Playlist format for saving or temporary playlists (default: xspf)')
    parser.add_argument('--sort', choices=['views', 'duration', 'upload_date'],
                       help='Sort search results by specified field (views: highest to lowest, duration: longest to shortest, upload_date: newest to oldest)')
    parser.add_argument('--include-videos', action='store_true',
                       help='Include YouTube videos in search results (not just music tracks). Will still extract audio for playback.')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode for yt-dlp.')

    args = parser.parse_args()

    # Check dependencies
    if not get_ytdlp_path():
        print("❌ Error: yt-dlp is required but not found. Please install it first:")
        print("  pip install yt-dlp")
        sys.exit(1)

    if not get_vlc_path():
        print("❌ Error: VLC is required but not found. Please install it first:")
        print("  macOS: brew install vlc or download from https://www.videolan.org/vlc/")
        print("  Linux: sudo apt install vlc")
        print("  Windows: Download from https://www.videolan.org/vlc/")
        sys.exit(1)

    # Handle playlists
    playlist_videos = None

    # Handle loaded playlist
    if args.load_playlist:
        print(f"📂 Loading playlist from: {args.load_playlist}")
        playlist_videos = load_playlist(args.load_playlist)
        if not playlist_videos:
            print(f"❌ Failed to load playlist from {args.load_playlist}")
            sys.exit(1)
        print(f"✅ Loaded playlist with {len(playlist_videos)} tracks")

        # Apply shuffle - this shuffles playback order after selection/sorting if requested - this shuffles playback order after selection/sorting
        if args.shuffle:
            import random
            random.shuffle(playlist_videos)
            print("🔀 Playlist shuffled")

    # Check if we have playlist from search results
    elif args.search and 'selected_indices' in locals() and len(selected_indices) > 1:
        # This case should already be handled in the search selection logic
        pass
    elif args.url and ('playlist?list=' in args.url or '/playlist?' in args.url):
        print(f"📋 Fetching playlist: {args.url}")
        playlist_videos = extract_playlist_urls(args.url, args.cookies, args.browser)
        if not playlist_videos:
            print("❌ Failed to extract playlist")
            sys.exit(1)
        print(f"📝 Found {len(playlist_videos)} videos in playlist")

        # Apply shuffle - this shuffles playback order after selection/sorting
        if args.shuffle:
            import random
            random.shuffle(playlist_videos)
            print("🔀 Playlist shuffled")

        # Apply start/end indices
        start_idx = args.playlist_start
        end_idx = args.playlist_end if args.playlist_end is not None else len(playlist_videos) - 1

        if start_idx < 0 or start_idx >= len(playlist_videos):
            print(f"❌ Invalid start index. Must be between 0 and {len(playlist_videos) - 1}")
            sys.exit(1)

        if end_idx < start_idx or end_idx >= len(playlist_videos):
            print(f"❌ Invalid end index. Must be between {start_idx} and {len(playlist_videos) - 1}")
            sys.exit(1)

        playlist_videos = playlist_videos[start_idx:end_idx + 1]
        print(f"🎵 Playing videos {start_idx} to {end_idx} (total: {len(playlist_videos)})")

    elif args.search:
        if args.include_videos:
            print(f"🔍 Searching YouTube (including videos) for: {args.search}")
            results = search_music(args.search, args.max_results, args.cookies, args.browser, include_videos=True, debug=args.debug)
        else:
            print(f"🔍 Searching YouTube Music for: {args.search}")
            results = search_music(args.search, args.max_results, args.cookies, args.browser, debug=args.debug)

        if not results:
            print("❌ No results found")
            print("ℹ️ This may be because:")
            print("   - YouTube is requiring sign-in verification")
            print("   - Your browser cookies are not accessible")
            print("   - Your network IP is blocked by YouTube")
            sys.exit(1)

        # Process entries in parallel when showing results
        if results:
            print(f"📊 Processing {len(results)} results...")
            processed_results = []
            with ThreadPoolExecutor(max_workers=min(5, len(results))) as executor:
                # Submit all tasks
                future_to_entry = {executor.submit(process_track_info, entry, args.include_videos): entry for entry in results}

                # Process completed tasks with progress display
                completed = 0
                total = len(results)

                for future in as_completed(future_to_entry):
                    completed += 1
                    track_info = future.result()
                    if track_info:
                        processed_results.append(track_info)

                    # Show progress
                    if has_rich and total > 1:
                        print(f"✅ Processed {completed}/{total} tracks\r", end='')
                    elif total > 1:
                        print(f"✅ Processed {completed}/{total} tracks\r", end='')

                # Clear progress line
                if total > 1:
                    print(" " * 50 + "\r", end='')

            results = processed_results

        # Filter out None entries if any
        results = [r for r in results if r is not None]
        if not results:
            print("❌ Valid search results found after filtering")
            sys.exit(1)

        # Sort results if requested - this only affects display order
        if args.sort:
            print(f"📊 Sorting results by: {args.sort}")
            if args.sort == 'views':
                # Sort by view count (highest to lowest)
                results.sort(key=lambda x: x.get('view_count', 0), reverse=True)
            elif args.sort == 'duration':
                # Sort by duration (longest to shortest)
                results.sort(key=lambda x: x.get('duration', 0), reverse=True)
            elif args.sort == 'upload_date':
                # Sort by upload date (newest to oldest)
                results.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
                # Fallback to release_timestamp if upload_date is not available
                if not all(r.get('upload_date') for r in results):
                    results.sort(key=lambda x: x.get('release_timestamp', 0), reverse=True)

        # Check if rich is available for TUI
        if has_rich:
            print("Launching interactive selection interface...")
            selected_tracks = select_tracks_with_space(results)
            if selected_tracks and len(selected_tracks) > 0:
                # Create playlist from selected tracks
                playlist_videos = []
                for track in selected_tracks:
                    playlist_videos.append({
                        'webpage_url': track.get('webpage_url') or track.get('url'),
                        'title': track.get('title', 'Unknown Title')
                    })
                print(f"\n▶️ Selected {len(playlist_videos)} tracks to play as playlist")
            else:
                # If user cancelled selection (q key), exit directly
                print("\nNo tracks selected. Exiting...")
                sys.exit(0)
        else:
            # For non-rich environments, use CLI interface directly
            selected_tracks = create_simple_cli_interface(results)
            if selected_tracks and len(selected_tracks) > 0:
                # Create playlist from selected tracks
                playlist_videos = []
                for track in selected_tracks:
                    playlist_videos.append({
                        'webpage_url': track.get('webpage_url') or track.get('url'),
                        'title': track.get('title', 'Unknown Title')
                    })
                print(f"\n▶️ Selected {len(playlist_videos)} tracks to play as playlist")
            else:
                print("No tracks selected. Exiting...")
                sys.exit(0)
    else:
        url = args.url

    # Cleanup unnecessary variables
    if 'selected_indices' in locals():
        del selected_indices
    if 'selected' in locals():
        del selected

    if args.list_formats:
        print("🔍 Fetching available formats...")
        info = extract_video_info(url, args.cookies)
        if not info:
            sys.exit(1)

        print("\n📊 Available Formats:")
        print("-" * 100)
        print(f"{'ID':<5} {'Type':<10} {'Codec':<20} {'Bitrate':<10} {'Quality'}")
        print("-" * 100)

        for fmt in info.get('formats', []):
            if fmt.get('acodec') == 'none':
                continue

            fmt_id = fmt.get('format_id', 'N/A')
            if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                fmt_type = 'video+audio'
            else:
                fmt_type = 'audio only'

            acodec = fmt.get('acodec', 'none')
            if fmt.get('abr'):
                bitrate = f"{fmt.get('abr')}k"
            else:
                bitrate = 'N/A'

            quality = fmt.get('format_note', 'N/A')
            print(f"{fmt_id:<5} {fmt_type:<10} {acodec:<20} {bitrate:<10} {quality}")

        sys.exit(0)

    # Prepare VLC arguments
    vlc_args = []
    if args.no_video:
        vlc_args.extend(['--no-video'])
    if args.fullscreen:
        vlc_args.extend(['--fullscreen'])
    if args.volume is not None:
        vlc_args.extend(['--volume', str(args.volume)])

    # Handle playlist playback
    if playlist_videos:
        # Use the new proper playlist playback system
        success = play_playlist_with_vlc(playlist_videos, args, vlc_args)

        if success:
            print("\n✅ Playlist playback completed successfully")
        else:
            print("\n❌ Playlist playback failed")
            sys.exit(1)

    else:
        # Check if we need to initialize url
        if 'url' not in locals() or url is None:
            # This can happen if playlist_videos is None but no url was set
            print("❌ No playback source selected or found")
            sys.exit(1)

        # Single track playback
        # Check if we need to save as playlist
        if args.save_playlist:
            # Create a single-track playlist
            print(f"\n💾 Saving single track as playlist to {args.save_playlist}")

            # Get video info for metadata
            info = extract_video_info(url, args.cookies, args.browser, debug=args.debug)
            if not info:
                info = {'title': 'Unknown Title', 'webpage_url': url}

            # Add stream URL to info
            stream_url = extract_stream_url(url, args.quality, args.cookies, args.browser)
            if not stream_url:
                print("❌ Failed to extract stream URL")
                sys.exit(1)
            info['stream_url'] = stream_url

            # Save playlist in requested format
            save_path = args.save_playlist
            if os.path.exists(save_path):
                save_path = handle_duplicate_file(save_path)
                if not save_path:
                    print("ℹ️ Save operation cancelled by user")
                    # Still proceed with playback
                    print("\n▶️ Starting playback...")
                    success = play_with_vlc(stream_url, info.get('title', 'YouTube Music'), vlc_args)
                    return

            if args.playlist_format == 'xspf':
                generate_xspf_playlist([info], save_path)
            else:
                generate_m3u_playlist([info], save_path)
            print(f"✅ Playlist saved to {save_path}")

            # Playback after saving
            print("\n▶️ Starting playback...")
            if args.debug:
                print(f"[DEBUG] Playing stream URL: {stream_url[:100]}...")
            success = play_with_vlc(stream_url, info.get('title', 'YouTube Music'), vlc_args)
        else:
            # Normal single track playback
            # Extract stream URL
            print("🔍 Extracting stream URL...")
            stream_url = extract_stream_url(url, args.quality, args.cookies, args.browser, debug=args.debug)

            if not stream_url:
                print("❌ Failed to extract stream URL")
                sys.exit(1)

            # Get video title for VLC metadata
            info = extract_video_info(url, args.cookies, args.browser, debug=args.debug)
            video_title = info.get('title', 'YouTube Music') if info else 'YouTube Music'

            # Print with appropriate coloring
            if has_rich:
                console = Console()
                console.print(f"▶️ Now playing: [bold cyan]{video_title}[/bold cyan]")
            else:
                print(f"▶️ Now playing: ", end="")
                SimpleColor.print_bold_cyan(video_title)
            print(f"🎵 Stream URL: {stream_url[:100]}...")
            if args.debug:
                print(f"[DEBUG] Full stream URL: {stream_url}")
            print("\nPress Ctrl+C to stop playback")
            print("-" * 50)

            # Start playback
            success = play_with_vlc(stream_url, video_title, vlc_args)

        if success:
            print("\n✅ Playback completed successfully")
        else:
            print("\n❌ Playback failed or was interrupted")
            sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

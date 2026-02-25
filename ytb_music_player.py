#!/usr/bin/env python3
"""
YouTube Music Player via VLC
Play YouTube Music directly from command line using VLC and yt-dlp
"""

import os
import sys
import subprocess
import argparse
import tempfile
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

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

def extract_stream_url(url, quality='bestaudio', cookies=None, browser=None):
    """Extract stream URL using yt-dlp"""
    ytdlp = get_ytdlp_path()
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

    if browser:
        browser_parts = browser.split(':', 1)
        if len(browser_parts) == 2:
            cmd.extend(['--cookies-from-browser', f'{browser_parts[0]}:{browser_parts[1].strip()}'])
        else:
            cmd.extend(['--cookies-from-browser', browser])
    elif cookies:
        cmd.extend(['--cookies', cookies])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error extracting stream: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return None

def extract_video_info(url, cookies=None, browser=None):
    """Extract video metadata using yt-dlp"""
    ytdlp = get_ytdlp_path()
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

    if browser:
        browser_parts = browser.split(':', 1)
        if len(browser_parts) == 2:
            cmd.extend(['--cookies-from-browser', f'{browser_parts[0]}:{browser_parts[1].strip()}'])
        else:
            cmd.extend(['--cookies-from-browser', browser])
    elif cookies:
        cmd.extend(['--cookies', cookies])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
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

def search_music(query, max_results=5, cookies=None, browser=None, include_videos=False):
    """Search YouTube Music and return results"""
    ytdlp = get_ytdlp_path()
    if not ytdlp:
        print("❌ Error: yt-dlp not found in PATH", file=sys.stderr)
        return None

    cmd = [
        ytdlp,
        '--ignore-config',
        '-j',
        '--no-playlist'
    ]

    if include_videos:
        # Search for all YouTube content (music and videos)
        cmd.extend([f'ytsearch{max_results}:{query}', '--default-search', 'ytsearch'])
    else:
        # Search specifically for YouTube Music tracks
        cmd.extend([f'youtube Music:{query}', '--default-search', 'ytsearch'])
        cmd.extend(['--extract-audio', '--audio-format', 'mp3'])  # These flags help prioritize audio tracks

    if browser:
        browser_parts = browser.split(':', 1)
        if len(browser_parts) == 2:
            cmd.extend(['--cookies-from-browser', f'{browser_parts[0]}:{browser_parts[1].strip()}'])
        else:
            cmd.extend(['--cookies-from-browser', browser])
    elif cookies:
        cmd.extend(['--cookies', cookies])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # ytsearch returns multiple JSON objects, one per line
        results = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return results
    except subprocess.CalledProcessError as e:
        print(f"❌ Error searching: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return None

def extract_playlist_urls(playlist_url, cookies=None, browser=None):
    """Extract all video URLs from a playlist"""
    ytdlp = get_ytdlp_path()
    if not ytdlp:
        print("❌ Error: yt-dlp not found in PATH", file=sys.stderr)
        return None

    cmd = [
        ytdlp,
        '--ignore-config',
        '-j',
        '--flat-playlist',
        '--no-playlist'
    ]

    if browser:
        browser_parts = browser.split(':', 1)
        if len(browser_parts) == 2:
            cmd.extend(['--cookies-from-browser', f'{browser_parts[0]}:{browser_parts[1].strip()}'])
        else:
            cmd.extend(['--cookies-from-browser', browser])
    elif cookies:
        cmd.extend(['--cookies', cookies])

    cmd.append(playlist_url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video = json.loads(line)
                    videos.append(video)
                except json.JSONDecodeError:
                    continue
        return videos
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

        # Add shuffle and repeat options to VLC if requested
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


def main():
    parser = argparse.ArgumentParser(
        description='YouTube Music Player via VLC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Play a YouTube Music track:
    %(prog)s https://music.youtube.com/watch?v=abc123

  Play a YouTube playlist:
    %(prog)s https://www.youtube.com/playlist?list=abc123
    %(prog)s https://music.youtube.com/playlist?list=abc123

  Search and play:
    %(prog)s --search "Taylor Shake It Off"

  Search and sort by views (most popular first):
    %(prog)s --search "chill lo-fi" --sort views

  Search and sort by duration (longest first):
    %(prog)s --search "classical music" --sort duration

  Search and save results to playlist with duplicate handling:
    %(prog)s --search "80s hits" --save-playlist my_80s_hits.xspf --sort views

  Search YouTube including videos (will still extract audio):
    %(prog)s --search "lo-fi hip hop radio" --include-videos

  Play with higher quality audio:
    %(prog)s https://music.youtube.com/watch?v=abc123 --quality "bestaudio[abr>192]/bestaudio"

  Play with cookies for premium access:
    %(prog)s https://music.youtube.com/watch?v=abc123 --cookies ~/.config/youtube-dl/cookies.txt

  Play using Chrome browser cookies:
    %(prog)s https://music.youtube.com/watch?v=abc123 --browser chrome
    %(prog)s https://music.youtube.com/watch?v=abc123 --browser "chrome:Profile 5"
        """
    )

    # Create a group for primary sources (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('url', nargs='?', help='YouTube Music URL (video, track, album, or playlist)')
    group.add_argument('-s', '--search', help='Search YouTube Music by query')
    group.add_argument('--load-playlist', help='Load and play from existing playlist file')

    parser.add_argument('-q', '--quality', default='bestaudio',
                       help='Stream quality preference (default: bestaudio)')
    parser.add_argument('-c', '--cookies', help='Path to cookies file for premium access')
    parser.add_argument('-b', '--browser', help='Extract cookies from browser (e.g., "chrome", "firefox:Profile 5")')
    parser.add_argument('--no-video', action='store_true',
                       help='Force audio-only playback even if video is available')
    parser.add_argument('--fullscreen', action='store_true',
                       help='Start VLC in fullscreen mode (when video is available)')
    parser.add_argument('--volume', type=int, help='Set initial volume (0-100)')
    parser.add_argument('--max-results', type=int, default=15,
                       help='Maximum search results to show (default: 15)')
    parser.add_argument('--list-formats', action='store_true',
                       help='List available formats and exit')
    parser.add_argument('--shuffle', action='store_true',
                       help='Shuffle playlist before playing')
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

        # Apply shuffle if requested
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

        # Apply shuffle
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
            results = search_music(args.search, args.max_results, args.cookies, args.browser, include_videos=True)
        else:
            print(f"🔍 Searching YouTube Music for: {args.search}")
            results = search_music(args.search, args.max_results, args.cookies, args.browser)

        if not results:
            print("❌ No results found")
            print("ℹ️ This may be because:")
            print("   - YouTube is requiring sign-in verification")
            print("   - Your browser cookies are not accessible")
            print("   - Your network IP is blocked by YouTube")
            sys.exit(1)

        # Filter out None entries if any
        results = [r for r in results if r is not None]
        if not results:
            print("❌ Valid search results found after filtering")
            sys.exit(1)

        # Sort results if requested
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

        print("\n🎵 Search Results:")
        print("-" * 80)
        for i, result in enumerate(results, 1):
            title = result.get('title', 'Unknown Title')
            channel = result.get('uploader', 'Unknown Artist')
            duration = result.get('duration', 0)
            views = result.get('view_count', 0)

            # Format duration
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "N/A"

            # Format views
            if views >= 1000000:
                views_str = f"{views/1000000:.1f}M"
            elif views >= 1000:
                views_str = f"{views/1000:.1f}K"
            else:
                views_str = str(views)

            # Print with appropriate coloring
            if has_rich:
                console = Console()
                console.print(f"{i:2d}. [bold cyan]{title}[/bold cyan]")
                console.print(f"    Artist: [green]{channel}[/green]")
                console.print(f"    Duration: [yellow]{duration_str}[/yellow] | Views: [magenta]{views_str}[/magenta]")
            else:
                print(f"{i:2d}. ", end="")
                SimpleColor.print_bold_cyan(title)
                print(f"    Artist: ", end="")
                SimpleColor.print_green(channel)
                print(f"    Duration: ", end="")
                SimpleColor.print_yellow(duration_str)
                print(f" | Views: ", end="")
                SimpleColor.print_magenta(views_str)
            print()

        # Let user select
        while True:
            try:
                selection = input(f"Select tracks to play (space-separated numbers like '1 3 5', 'all' for all, 'q' to quit): ").strip()
                if selection.lower() == 'q':
                    sys.exit(0)
                if selection.lower() == 'all':
                    # Play all search results as a playlist
                    playlist_urls = []
                    for result in results:
                        url = result.get('webpage_url') or result.get('url')
                        playlist_urls.append(url)
                    print(f"\n▶️ Selected all {len(playlist_urls)} tracks to play as playlist")
                    # Create a temporary playlist dictionary
                    playlist_videos = []
                    for result in results:
                        playlist_videos.append({
                            'webpage_url': result.get('webpage_url') or result.get('url'),
                            'title': result.get('title', 'Unknown Title')
                        })
                    break

                # Parse space-separated numbers
                selected_indices = list(map(int, selection.split()))
                if len(selected_indices) > 1:
                    # Multiple selection - create playlist
                    playlist_urls = []
                    for idx in selected_indices:
                        if 1 <= idx <= len(results):
                            index = idx - 1
                            selected = results[index]
                            playlist_urls.append(selected.get('webpage_url') or selected.get('url'))
                    print(f"\n▶️ Selected {len(playlist_urls)} tracks to play as playlist")
                    # Create a temporary playlist dictionary
                    playlist_videos = []
                    for idx in selected_indices:
                        if 1 <= idx <= len(results):
                            index = idx - 1
                            result = results[index]
                            playlist_videos.append({
                                'webpage_url': result.get('webpage_url') or result.get('url'),
                                'title': result.get('title', 'Unknown Title')
                            })
                    break
                else:
                    # Single selection
                    index = selected_indices[0] - 1
                    if 0 <= index < len(results):
                        selected = results[index]
                        url = selected.get('webpage_url') or selected.get('url')
                        # Print selection with appropriate coloring
                        selected_title = selected.get('title', 'Unknown Title')
                        if has_rich:
                            console = Console()
                            console.print(f"\n▶️ Selected: [bold cyan]{selected_title}[/bold cyan]")
                        else:
                            print("\n▶️ Selected: ", end="")
                            SimpleColor.print_bold_cyan(selected_title)
                        break
                    print(f"Please enter a number between 1 and {len(results)}")
            except ValueError:
                print("Invalid input. Please enter space-separated numbers, 'all', or 'q'")

        # Handle single selection case (fallback)
        if not playlist_videos and 'selected' in locals():
            selected_title = selected.get('title', 'Unknown Title')
            url = selected.get('webpage_url') or selected.get('url')
            if has_rich:
                console = Console()
                console.print(f"\n▶️ Selected: [bold cyan]{selected_title}[/bold cyan]")
            else:
                print("\n▶️ Selected: ", end="")
                SimpleColor.print_bold_cyan(selected_title)
        elif not playlist_videos:
            # No valid selection made
            print("❌ No valid selection made")
            sys.exit(1)
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
            info = extract_video_info(url, args.cookies, args.browser)
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
            success = play_with_vlc(stream_url, info.get('title', 'YouTube Music'), vlc_args)
        else:
            # Normal single track playback
            # Extract stream URL
            print("🔍 Extracting stream URL...")
            stream_url = extract_stream_url(url, args.quality, args.cookies, args.browser)

            if not stream_url:
                print("❌ Failed to extract stream URL")
                sys.exit(1)

            # Get video title for VLC metadata
            info = extract_video_info(url, args.cookies, args.browser)
            video_title = info.get('title', 'YouTube Music') if info else 'YouTube Music'

            # Print with appropriate coloring
            if has_rich:
                console = Console()
                console.print(f"▶️ Now playing: [bold cyan]{video_title}[/bold cyan]")
            else:
                print(f"▶️ Now playing: ", end="")
                SimpleColor.print_bold_cyan(video_title)
            print(f"🎵 Stream URL: {stream_url[:100]}...")
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

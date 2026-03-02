# YouTube Music VLC Player

Version: 1.2.0

A command-line tool to search, stream, and play YouTube Music using VLC media player. This tool provides a seamless way to enjoy YouTube Music with proper playlist support and full VLC integration.

## Features

- 🎵 **Search YouTube Music**: Search for songs, artists, albums, or playlists
- 📋 **Playlist Support**: Create, save, and load playlists in XSPF or M3U format
- 🎬 **Full VLC Integration**: Load playlists directly into VLC with complete playlist management
- ⚡ **Bulk Stream Extraction**: Pre-extract stream URLs for entire playlists
- 🎛️ **Playback Controls**: Support for shuffle, repeat, volume control, and audio-only mode
- 🎨 **Colorful Output**: Beautiful terminal output with rich text formatting
- 📱 **Cookie Support**: Use browser cookies or cookie files for premium access
- 🔀 **Search Results Sorting**: Sort results by views, duration, or upload date
- 💾 **Duplicate File Handling**: Smart handling of duplicate filenames when saving playlists
- 🛡️ **EJS Challenge Support**: Automatically handles YouTube's EJS challenges using yt-dlp's remote components
- 🎯 **Flexible Selection**: Select multiple tracks using comma or space-separated numbers

## Prerequisites

Before using YouTube Music VLC Player, you need to install the following dependencies:

### Required Dependencies

1. **Python 3.6+**: https://www.python.org/downloads/
2. **yt-dlp**: A powerful YouTube downloader
3. **VLC Media Player**: https://www.videolan.org/vlc/

### Optional Dependencies

- **rich**: For enhanced terminal output with colors and formatting (recommended)

## Installation

### 1. Install Required Software

### 2. Install Optional Features

For improved terminal formatting (highly recommended):
```bash
pip install rich
```

#### macOS
```bash
# Install VLC using Homebrew
brew install vlc yt-dlp

# Or download VLC manually from https://www.videolan.org/vlc/
```

#### Linux
```bash
# Debian/Ubuntu
sudo apt update
sudo apt install vlc python3-pip

# Install yt-dlp
pip3 install yt-dlp
```

#### Windows
```bash
# Install VLC from https://www.videolan.org/vlc/
# Install Python from https://www.python.org/downloads/

# Install yt-dlp using pip
pip install yt-dlp
```

### 2. Install Python Dependencies

```bash
# Install rich for better output (recommended)
pip install rich
```

### 3. Download the Player

```bash
# Clone or download this repository
cd ytb-music-vlc

# Make the script executable
chmod +x ytb_music_player.py
```

## Quick Start

### Selection Mode

**Number Selection Mode**:
- Enter space-separated numbers to select multiple tracks (e.g., `1 3 5`)
- Type `all` to select all tracks
- Type `q` to quit

### Search and Play Music

```bash
# Search for a song
python ytb_music_player.py --search "Rick Astley Never Gonna Give You Up"

# Search with more results
python ytb_music_player.py --search "Taylor Swift" --max-results 10
```

### Play from YouTube URLs

```bash
# Play a single video
python ytb_music_player.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Play a playlist
python ytb_music_player.py "https://www.youtube.com/playlist?list=PLzMcBGfZo4-mP7qA9cagf68V06sko5otr"
```

### Playlist Management

```bash
# Save search results as a playlist
python ytb_music_player.py --search "80s music" --max-results 5 --save-playlist 80s_music.xspf

# Load and play from a saved playlist
python ytb_music_player.py --load-playlist 80s_music.xspf --shuffle --repeat

# Convert playlist format (M3U to XSPF)
python ytb_music_player.py --load-playlist old_playlist.m3u --save-playlist new_playlist.xspf
```

### Advanced Playback Options

```bash
# Audio-only mode (no video)
python ytb_music_player.py --search "lofi hip hop" --no-video

# Set custom volume
python ytb_music_player.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --volume 75

# High-quality audio
python ytb_music_player.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --quality "bestaudio[abr>192]/bestaudio"

# Shuffle and repeat playlist
python ytb_music_player.py "https://www.youtube.com/playlist?list=PLzMcBGfZo4-mP7qA9cagf68V06sko5otr" --shuffle --repeat
```

### Cookie Support for Premium Access

```bash
# Use cookies from Chrome browser
python ytb_music_player.py --search "Taylor Swift" --browser chrome

# Use cookies from specific Chrome profile
python ytb_music_player.py --search "Taylor Swift" --browser "chrome:Profile 2"

# Use cookie file
python ytb_music_player.py --search "Taylor Swift" --cookies ~/.config/youtube-dl/cookies.txt
```

## Usage Examples

### Search and Play Multiple Songs

```bash
python ytb_music_player.py --search "Queen greatest hits" --max-results 5
```

When prompted, select tracks to play:
- Enter `1 3 5` to play tracks 1, 3, and 5
- Enter `all` to play all search results
- Enter `q` to quit

Note: You can also use comma-separated numbers (e.g., `1,3,5`) for selection.

### Create and Manage Playlists

```bash
# Create a playlist from multiple search results
python ytb_music_player.py --search "classic rock" --max-results 10 --save-playlist classic_rock.xspf

# Play with shuffle and repeat
python ytb_music_player.py --load-playlist classic_rock.xspf --shuffle --repeat

# Play specific range from playlist
python ytb_music_player.py --load-playlist classic_rock.xspf --playlist-start 2 --playlist-end 6
```

### Audio-Only Playback

```bash
# Perfect for background music
python ytb_music_player.py --search "lofi study beats" --no-video --volume 60
```

## Command Line Options

```
usage: ytb_music_player.py [-h] [-s SEARCH] [--load-playlist LOAD_PLAYLIST]
                           [-q QUALITY] [-c COOKIES] [-b BROWSER] [--no-video]
                           [--fullscreen] [--volume VOLUME]
                           [--max-results MAX_RESULTS] [--list-formats]
                           [--shuffle] [--repeat]
                           [--playlist-start PLAYLIST_START]
                           [--playlist-end PLAYLIST_END]
                           [--save-playlist SAVE_PLAYLIST]
                           [--playlist-format {m3u,xspf}]
                           [--sort {views,duration,upload_date}]
                           [--include-videos] [--debug]
                           [url]

YouTube Music Player via VLC

positional arguments:
  url                   YouTube Music URL (video, track, album, or playlist)

options:
  -h, --help            show this help message and exit
  -s SEARCH, --search SEARCH
                        Search YouTube Music by query
  --load-playlist LOAD_PLAYLIST
                        Load and play from existing playlist file
  -q QUALITY, --quality QUALITY
                        Stream quality preference (default: bestaudio)
  -c COOKIES, --cookies COOKIES
                        Path to cookies file for premium access
  -b BROWSER, --browser BROWSER
                        Extract cookies from browser (e.g., "chrome",
                        "firefox:Profile 5")
  --no-video            Force audio-only playback even if video is available
  --fullscreen          Start VLC in fullscreen mode (when video is available)
  --volume VOLUME       Set initial volume (0-100)
  --max-results MAX_RESULTS
                        Maximum search results to show (default: 10)
  --list-formats        List available formats and exit
  --shuffle             Shuffle playlist playback order after selection and
                        sorting
  --repeat              Repeat playlist playback
  --playlist-start PLAYLIST_START
                        Start playlist at specified index (0-based)
  --playlist-end PLAYLIST_END
                        End playlist at specified index (0-based)
  --save-playlist SAVE_PLAYLIST
                        Save generated playlist to file
  --playlist-format {m3u,xspf}
                        Playlist format for saving or temporary playlists
                        (default: xspf)
  --sort {views,duration,upload_date}
                        Sort search results by specified field (views: highest
                        to lowest, duration: longest to shortest, upload_date:
                        newest to oldest)
  --include-videos      Include YouTube videos in search results (not just
                        music tracks). Will still extract audio for playback.
  --debug               Enable debug mode for yt-dlp.
```

## Troubleshooting

### Common Issues

1. **YouTube Sign-in Required Error**
   ```
   ℹ️ This may be because:
   - YouTube is requiring sign-in verification
   - Your browser cookies are not accessible
   - Your network IP is blocked by YouTube
   ```
   **Solution**: Use the `--browser` or `--cookies` option to provide authentication

2. **Stream Extraction Failed**
   **Solution**: Check your internet connection, try using cookies, or wait and try again later

3. **VLC Not Found Error**
   **Solution**: Install VLC and ensure it's in your system PATH

4. **yt-dlp Not Found Error**
   **Solution**: Install yt-dlp using pip or package manager

5. **EJS Challenge Errors**
   The player automatically handles YouTube's EJS challenges using yt-dlp's remote components feature. If you encounter issues:
   - Ensure you have the latest version of yt-dlp: `pip install --upgrade yt-dlp`
   - Check your internet connection (remote components are downloaded from GitHub)
   - Try using cookie authentication for better success rates

### Cookie Troubleshooting

If you're having issues with cookie authentication:

1. **Chrome**: Ensure Chrome is closed when using `--browser chrome`
2. **Firefox**: Make sure Firefox is not running in private mode
3. **Cookie Files**: Use a tool like `Get cookies.txt LOCALLY` browser extension to export cookies

## Contributing

Contributions are welcome! If you find bugs or have feature requests, please open an issue or submit a pull request.

## License

This project is open source and available under the MIT License.

## Disclaimer

This tool is for personal use only. Please respect YouTube's terms of service and copyright laws when using this tool. The developer is not responsible for any misuse of this software.

## Credits

- **yt-dlp**: For powerful YouTube media extraction
- **VLC**: For robust media playback capabilities
- **rich**: For beautiful terminal output formatting
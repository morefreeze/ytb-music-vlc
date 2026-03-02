# YouTube Music VLC 播放器

版本：1.2.0

一个命令行工具，用于搜索、串流和播放 YouTube Music，使用 VLC 媒体播放器。该工具提供了一种无缝的方式来享受 YouTube Music，支持完整的播放列表功能和 VLC 集成。

## 功能特性

- 🎵 **搜索 YouTube Music**：搜索歌曲、艺术家、专辑或播放列表
- 📋 **播放列表支持**：创建、保存和加载 XSPF 或 M3U 格式的播放列表
- 🎬 **完整 VLC 集成**：直接将播放列表加载到 VLC 中，并支持完整的播放列表管理
- ⚡ **批量串流提取**：为整个播放列表预提取串流 URL
- 🎛️ **播放控制**：支持随机播放、重复播放、音量控制和纯音频模式
- 🎨 **彩色输出**：美观的终端输出，支持富文本格式
- 📱 **Cookie 支持**：使用浏览器 cookie 或 cookie 文件获取高级访问权限
- 🔀 **搜索结果排序**：按观看次数、时长或上传日期对结果进行排序
- 💾 **重复文件处理**：保存播放列表时智能处理重复文件名
- 🛡️ **EJS 挑战支持**：使用 yt-dlp 的远程组件自动处理 YouTube 的 EJS 挑战
- 🎯 **灵活选择**：使用逗号或空格分隔的数字选择多个音轨

## 前提条件

在使用 YouTube Music VLC 播放器之前，您需要安装以下依赖项：

### 必需依赖项

1. **Python 3.6+**：https://www.python.org/downloads/
2. **yt-dlp**：强大的 YouTube 下载器
3. **VLC 媒体播放器**：https://www.videolan.org/vlc/

### 可选依赖项

- **rich**：增强的终端输出格式（推荐）

## 安装

### 1. 安装必需软件

### 2. 安装可选功能

为了改进终端格式（强烈推荐）：
```bash
pip install rich
```

#### macOS
```bash
# 使用 Homebrew 安装 VLC
brew install vlc yt-dlp

# 或从 https://www.videolan.org/vlc/ 手动下载 VLC
```

#### Linux
```bash
# Debian/Ubuntu
sudo apt update
sudo apt install vlc python3-pip

# 安装 yt-dlp
pip3 install yt-dlp
```

#### Windows
```bash
# 从 https://www.videolan.org/vlc/ 安装 VLC
# 从 https://www.python.org/downloads/ 安装 Python

# 使用 pip 安装 yt-dlp
pip install yt-dlp
```

### 3. 下载播放器

```bash
# 克隆或下载此仓库
cd ytb-music-vlc

# 使脚本可执行
chmod +x ytb_music_player.py
```

## 快速开始

### 选择模式

**数字选择模式**：
- 输入空格分隔的数字以选择多个音轨（例如 `1 3 5`）
- 输入 `all` 以选择所有音轨
- 输入 `q` 以退出

注意：您也可以使用逗号分隔的数字进行选择（例如 `1,3,5`）。

### 搜索和播放音乐

```bash
# 搜索歌曲
python ytb_music_player.py --search "Rick Astley Never Gonna Give You Up"

# 搜索更多结果
python ytb_music_player.py --search "Taylor Swift" --max-results 10
```

### 从 YouTube URL 播放

```bash
# 播放单个视频
python ytb_music_player.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# 播放播放列表
python ytb_music_player.py "https://www.youtube.com/playlist?list=PLzMcBGfZo4-mP7qA9cagf68V06sko5otr"
```

### 播放列表管理

```bash
# 将搜索结果保存为播放列表
python ytb_music_player.py --search "80s music" --max-results 5 --save-playlist 80s_music.xspf

# 从保存的播放列表加载并播放
python ytb_music_player.py --load-playlist 80s_music.xspf --shuffle --repeat

# 转换播放列表格式（M3U 到 XSPF）
python ytb_music_player.py --load-playlist old_playlist.m3u --save-playlist new_playlist.xspf
```

### 高级播放选项

```bash
# 仅音频模式（无视频）
python ytb_music_player.py --search "lofi hip hop" --no-video

# 设置自定义音量
python ytb_music_player.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --volume 75

# 高质量音频
python ytb_music_player.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --quality "bestaudio[abr>192]/bestaudio"

# 随机播放和重复播放列表
python ytb_music_player.py "https://www.youtube.com/playlist?list=PLzMcBGfZo4-mP7qA9cagf68V06sko5otr" --shuffle --repeat
```

### Cookie 支持以获取高级访问权限

```bash
# 使用 Chrome 浏览器的 cookie
python ytb_music_player.py --search "Taylor Swift" --browser chrome

# 使用特定 Chrome 配置文件的 cookie
python ytb_music_player.py --search "Taylor Swift" --browser "chrome:Profile 2"

# 使用 cookie 文件
python ytb_music_player.py --search "Taylor Swift" --cookies ~/.config/youtube-dl/cookies.txt
```

## 使用示例

### 搜索并播放多首歌曲

```bash
python ytb_music_player.py --search "Queen greatest hits" --max-results 5
```

出现提示时，选择要播放的音轨：
- 输入 `1 3 5` 以播放音轨 1、3 和 5
- 输入 `all` 以播放所有搜索结果
- 输入 `q` 以退出

注意：您也可以使用逗号分隔的数字进行选择（例如 `1,3,5`）。

### 创建和管理播放列表

```bash
# 从多个搜索结果创建播放列表
python ytb_music_player.py --search "classic rock" --max-results 10 --save-playlist classic_rock.xspf

# 随机播放和重复播放
python ytb_music_player.py --load-playlist classic_rock.xspf --shuffle --repeat

# 从播放列表播放特定范围
python ytb_music_player.py --load-playlist classic_rock.xspf --playlist-start 2 --playlist-end 6
```

### 仅音频播放

```bash
# 完美的背景音乐
python ytb_music_player.py --search "lofi study beats" --no-video --volume 60
```

### 高级搜索和排序

```bash
# 按观看次数排序并包含视频
python ytb_music_player.py --search "piano music" --sort views --include-videos --max-results 10

# 按时长排序（最长优先）
python ytb_music_player.py --search "ambient music" --sort duration --no-video

# 按上传日期排序（最新优先）
python ytb_music_player.py --search "new releases" --sort upload_date --max-results 20
```

## 命令行选项

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

## 故障排除

### 常见问题

1. **YouTube 需要登录错误**
   ```
   ℹ️ 这可能是因为：
   - YouTube 需要登录验证
   - 您的浏览器 cookie 无法访问
   - 您的网络 IP 被 YouTube 阻止
   ```
   **解决方案**：使用 `--browser` 或 `--cookies` 选项提供身份验证

2. **串流提取失败**
   **解决方案**：检查您的互联网连接，尝试使用 cookie，或稍后重试

3. **未找到 VLC 错误**
   **解决方案**：安装 VLC 并确保它在您的系统 PATH 中

4. **未找到 yt-dlp 错误**
   **解决方案**：使用 pip 或包管理器安装 yt-dlp

5. **EJS 挑战错误**
   播放器使用 yt-dlp 的远程组件功能自动处理 YouTube 的 EJS 挑战。如果遇到问题：
   - 确保您有最新版本的 yt-dlp：`pip install --upgrade yt-dlp`
   - 检查您的互联网连接（远程组件从 GitHub 下载）
   - 尝试使用 cookie 身份验证以获得更好的成功率

### Cookie 故障排除

如果您在使用 cookie 身份验证时遇到问题：

1. **Chrome**：使用 `--browser chrome` 时确保 Chrome 已关闭
2. **Firefox**：确保 Firefox 不在隐私模式下运行
3. **Cookie 文件**：使用 `Get cookies.txt LOCALLY` 浏览器扩展等工具导出 cookie

## 贡献

欢迎贡献！如果您发现错误或希望请求新功能，请打开 issue 或提交 pull request。

## 许可证

此项目是开源的，可在 MIT 许可证下使用。

## 免责声明

此工具仅供个人使用。使用此工具时，请尊重 YouTube 的服务条款和版权法。开发者不对本软件的任何滥用负责。

## 致谢

- **yt-dlp**：用于强大的 YouTube 媒体提取
- **VLC**：用于强大的媒体播放功能
- **rich**：用于美观的终端输出格式

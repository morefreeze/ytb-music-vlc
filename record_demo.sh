#!/bin/bash
# Terminal recording script for creating demo GIF
# Requirements: ffmpeg, terminal-notifier (optional)

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎬 Terminal Demo Recorder${NC}"
echo "=============================="

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg is not installed. Please install it first:"
    echo "   brew install ffmpeg"
    exit 1
fi

# Default values
OUTPUT_DIR="$(pwd)"
DURATION=""
RESOLUTION="1280x720"
FRAMERATE=15
QUALITY=25

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -d|--duration)
            DURATION="-t $2"
            shift 2
            ;;
        -r|--resolution)
            RESOLUTION="$2"
            shift 2
            ;;
        -f|--framerate)
            FRAMERATE="$2"
            shift 2
            ;;
        -q|--quality)
            QUALITY="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -o, --output DIR      Output directory (default: current directory)"
            echo "  -d, --duration SEC    Recording duration in seconds"
            echo "  -r, --resolution WxH  Recording resolution (default: 1280x720)"
            echo "  -f, --framerate FPS   Framerate (default: 15)"
            echo "  -q, --quality Q       Quality 1-50, lower is better (default: 25)"
            echo "  -h, --help            Show this help"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 -d 30 -o ~/Desktop"
            echo "  $0 -r 1920x1080 -f 30"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create output filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="${OUTPUT_DIR}/terminal_demo_${TIMESTAMP}.gif"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo -e "${YELLOW}📋 Recording Settings:${NC}"
echo "   Output: $OUTPUT_FILE"
echo "   Resolution: $RESOLUTION"
echo "   Framerate: $FRAMERATE fps"
echo "   Quality: $QUALITY"
if [ -n "$DURATION" ]; then
    echo "   Duration: ${DURATION#-t } seconds"
fi
echo ""

# Countdown
echo -e "${GREEN}Starting recording in...${NC}"
for i in 3 2 1; do
    echo -e "${YELLOW}$i...${NC}"
    sleep 1
done

echo -e "${GREEN}🔴 Recording started!${NC}"
echo "Press Ctrl+C to stop recording"
echo ""

# Record the screen
# Get the terminal window ID
TERMINAL_WINDOW=$(osascript -e 'tell application "Terminal" to get id of front window' 2>/dev/null || echo "")

if [ -n "$TERMINAL_WINDOW" ]; then
    # Use screencapture with specific window
    ffmpeg -f avfoundation -i "default" \
           -vf "scale=$RESOLUTION" \
           -r $FRAMERATE \
           -pix_fmt rgb24 \
           $DURATION \
           -y "$OUTPUT_FILE" 2>/dev/null &
else
    # Fallback: record entire screen
    ffmpeg -f avfoundation -i "1" \
           -vf "scale=$RESOLUTION" \
           -r $FRAMERATE \
           -pix_fmt rgb24 \
           $DURATION \
           -y "$OUTPUT_FILE" 2>/dev/null &
fi

FFMPEG_PID=$!

# Wait for recording to finish
trap "kill $FFMPEG_PID 2>/dev/null" EXIT

wait $FFMPEG_PID

# Check if file was created
if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
    echo -e "${GREEN}✅ Recording saved!${NC}"
    echo "   File: $OUTPUT_FILE"
    echo "   Size: $FILE_SIZE"

    # Open the file
    if command -v open &> /dev/null; then
        open "$OUTPUT_FILE"
    fi
else
    echo -e "❌ Recording failed"
    exit 1
fi

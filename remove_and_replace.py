#!/usr/bin/env python3
"""Remove select_tracks_with_space function and replace with rich-based version"""

import re

# Read the file
with open('ytb_music_player.py', 'r') as f:
    lines = f.readlines()

# Find the start and end of select_tracks_with_space function
start_line = None
end_line = None

for i, line in enumerate(lines):
    if line.startswith('def select_tracks_with_space'):
        start_line = i
    elif start_line is not None and line.startswith('def ') and not line.startswith('def select'):
        end_line = i
        break

if start_line is None:
    print("ERROR: Could not find select_tracks_with_space function")
    exit(1)

if end_line is None:
    end_line = len(lines)

print(f"Found select_tracks_with_space at lines {start_line+1} to {end_line}")

# Create the new function using rich
new_function = '''def select_tracks_with_space(results):
    """Allow user to select multiple tracks using rich TUI"""
    if not has_rich:
        print("❌ rich module is required for TUI selection. Please install it with 'pip install rich'")
        return None

    console = Console()
    selected = set()
    current_index = 0
    max_index = len(results) - 1

    def get_table():
        table = Table(
            title="🎵 Search Results - Use ↑/↓ to navigate, SPACE to select, ENTER to confirm",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Select", width=6)
        table.add_column("Title", style="bold")
        table.add_column("Artist", style="green")
        table.add_column("Duration", style="yellow")

        for i, result in enumerate(results):
            title = result.get('title', 'Unknown Title')
            channel = result.get('uploader', 'Unknown Artist')
            duration = result.get('duration', 0)

            if duration:
                minutes = int(duration) // 60
                seconds = int(duration) % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "N/A"

            # Selection indicator
            select_indicator = ""
            if i in selected:
                select_indicator = "✅"
            elif i == current_index:
                select_indicator = "👉"

            # Row styling based on selection
            if i == current_index:
                table.add_row(
                    f"{i+1}",
                    select_indicator,
                    title,
                    channel,
                    duration_str,
                    style="bold cyan"
                )
            elif i in selected:
                table.add_row(
                    f"{i+1}",
                    select_indicator,
                    title,
                    channel,
                    duration_str,
                    style="green"
                )
            else:
                table.add_row(
                    f"{i+1}",
                    select_indicator,
                    title,
                    channel,
                    duration_str
                )

        return table

    with Live(get_table(), console=console, screen=True, refresh_per_second=4) as live:
        while True:
            try:
                # Use readchar for cross-platform single character input
                key = readchar.readchar()

                if key == readchar.key.UP:
                    current_index = max(0, current_index - 1)
                elif key == readchar.key.DOWN:
                    current_index = min(max_index, current_index + 1)
                elif key == ' ':
                    if current_index in selected:
                        selected.remove(current_index)
                    else:
                        selected.add(current_index)
                elif key == readchar.key.ENTER or key == '\r' or key == '\n':
                    if selected:
                        break
                    else:
                        console.print("[yellow]⚠️ No tracks selected. Please select at least one track.[/yellow]")
                        time.sleep(1)
                elif key == 'q' or key == readchar.key.ESC:
                    return None

                live.update(get_table())

            except KeyboardInterrupt:
                return None

    if not selected:
        return None

    # Return sorted selection
    sorted_selection = sorted(selected)
    return [results[i] for i in sorted_selection]

'''

# Remove old function and insert new one
new_lines = lines[:start_line] + [new_function] + lines[end_line:]

# Write back
with open('ytb_music_player.py', 'w') as f:
    f.writelines(new_lines)

print(f"✅ Successfully replaced select_tracks_with_space function")
print(f"   - Removed {end_line - start_line} lines")
print(f"   - Added {len(new_function.split(chr(10)))} lines")

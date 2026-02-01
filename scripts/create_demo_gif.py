#!/usr/bin/env python3
"""Create animated demo GIF for Talkie using Pillow."""

from PIL import Image, ImageDraw, ImageFont
import os

# Terminal-style colors
BG = (13, 17, 23)  # #0d1117
PROMPT = (48, 209, 88)  # Green
TEXT = (201, 209, 217)  # Light gray
KEY = (121, 192, 255)  # Blue for JSON keys
VALUE = (255, 166, 87)  # Orange for numbers
STRING = (230, 230, 230)  # White for strings

WIDTH, HEIGHT = 700, 400
FONT_SIZE = 14

def create_frame(text_lines, frame_num=0):
    """Create a single frame with terminal output."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", FONT_SIZE)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()
    
    y = 20
    line_height = 18
    
    for i, line in enumerate(text_lines):
        if line.startswith("$ "):
            color = PROMPT
        elif '"' in line and ":" in line:
            color = KEY
        elif any(c.isdigit() for c in line):
            color = VALUE
        else:
            color = TEXT
        
        draw.text((20, y), line[:80], fill=color, font=font)
        y += line_height
    
    return img

def main():
    frames_data = [
        ["$ talkie get https://jsonplaceholder.typicode.com/posts/1", ""],
        ["$ talkie get https://jsonplaceholder.typicode.com/posts/1", "", "HTTP/1.1 200 OK"],
        ["$ talkie get https://jsonplaceholder.typicode.com/posts/1", "", "HTTP/1.1 200 OK", "Content-Type: application/json", ""],
        ["$ talkie get https://jsonplaceholder.typicode.com/posts/1", "", "HTTP/1.1 200 OK", "Content-Type: application/json", "", "{", '  "userId": 1,'],
        ["$ talkie get https://jsonplaceholder.typicode.com/posts/1", "", "HTTP/1.1 200 OK", "Content-Type: application/json", "", "{", '  "userId": 1,', '  "id": 1,', '  "title": "sunt aut facere...",', '  "body": "quia et suscipit..."', "}"],
    ]
    
    frames = [create_frame(lines) for lines in frames_data]
    
    # Add final frame for longer display
    for _ in range(5):
        frames.append(frames[-1].copy())
    
    output_path = os.path.join(os.path.dirname(__file__), "..", "docs", "images", "demo.gif")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=400,
        loop=0,
    )
    print(f"Created {output_path}")

if __name__ == "__main__":
    main()

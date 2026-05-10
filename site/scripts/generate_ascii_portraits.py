#!/usr/bin/env python3
"""
Generate ASCII art portraits for Signal terminal crew profiles.
Usage: python3 generate_ascii_portraits.py
Output: crew_ascii_portraits.json
"""

import json
import os
from PIL import Image
from pathlib import Path

# Character set: dark → light (works well on green-on-black CRT)
CHARS = " .:-=+*#%@"

# Source image directories (checked in order)
IMAGE_DIRS = [
    "/Users/jeremy/Documents/current_projects/the_ephergent_projects/ephergent_blog_v1/content/images/characters",
    "/Users/jeremy/Documents/current_projects/the_ephergent_projects/ARCHIVE/ephergent_blog_season02/content/images/characters",
    "/Users/jeremy/Documents/current_projects/the_ephergent_projects/ARCHIVE/MCP_servers/assets/images/characters",
    "/Users/jeremy/Documents/current_projects/the_ephergent_projects/ARCHIVE/pixels_papercraft/assets/characters_profile_images",
]

# Slug → filename mappings (not all characters have images)
SLUG_MAP = {
    "pixel-paradox": "pixel_paradox.png",
    "a1": "a1_assistant.png",
    "clive": "clive_stapler_informant.png",
    "mochi": None,  # no image — will use placeholder
    "meatball": "meatball_rottweiler.png",
    "nano": "nano_informant.png",
    "baron-klaus": "baron_klaus_von_gnomendorf.png",
    "luminara": "luminara_usha.png",
    "signal-the-narrator": None,  # meta character — no portrait
    "barry-kowalski": None,  # no image found
    "om-kai": "om_kai.png",
    "zephyr-glitch": "zephyr_glitch.png",
}


def find_image(filename: str) -> str | None:
    for d in IMAGE_DIRS:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            return path
    return None


def image_to_ascii(img_path: str, width: int = 36) -> str:
    height = width // 2
    img = Image.open(img_path).convert("L").resize((width, height))
    pixels = list(img.getdata())
    rows = [pixels[i * width:(i + 1) * width] for i in range(height)]
    return "\n".join(
        "".join(CHARS[min(p // 16, len(CHARS) - 1)] for p in row) for row in rows
    )


def generate_portraits():
    portraits = {}

    # Placeholder art for characters without images
    portraits["mochi"] = (
        "     .-----.     \n"
        "   .'  .-.  '.   \n"
        "  /   (o)(o)  \\  \n"
        " |  .-------.  | \n"
        " |  |  ===  |  | \n"
        "  \\ |       | /  \n"
        "   |       |    \n"
        "   '-------'     "
    )
    portraits["barry-kowalski"] = (
        "   .--------.    \n"
        "  /  .----.  \\   \n"
        "  |  |    |  |   \n"
        "  |  |    |  |   \n"
        "   \\ |    | /    \n"
        "   | '----' |    \n"
        "   |  ____  |    \n"
        "   |__|  |__|    "
    )
    portraits["signal-the-narrator"] = (
        "  .__:____::__   \n"
        " /   |    |   \\  \n"
        "|    |    |    | \n"
        "|    |    |    | \n"
        "|____|    |____| \n"
        " \\______________/ \n"
        "   \\________/     \n"
        "    |      |      "
    )

    for slug, filename in SLUG_MAP.items():
        if slug in portraits:
            continue  # skip placeholders
        if filename is None:
            continue
        path = find_image(filename)
        if path:
            portraits[slug] = image_to_ascii(path)
            print(f"  {slug}: {path}")
        else:
            print(f"  {slug}: NOT FOUND — {filename}")
    return portraits


if __name__ == "__main__":
    print("Scanning for character portraits...")
    portraits = generate_portraits()

    output = {
        "meta": {
            "width": 36,
            "chars": CHARS,
            "description": "ASCII art portraits for Signal terminal. 36 chars wide."
        },
        "portraits": portraits
    }

    out_path = os.path.join(os.path.dirname(__file__), "crew_ascii_portraits.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nWritten: {out_path}")
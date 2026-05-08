#!/usr/bin/env python3
"""
Generate EPUB ebook for The Ephergent - all 3 seasons consolidated.
Dark sci-fi aesthetic with terminal green text on black background.
"""

import zipfile
import os
import re
from pathlib import Path

# Base paths
BASE_DIR = Path("/home/debian/Documents/code_repos/the_ephergent_grand_plan")
EPISODES_DIR = BASE_DIR / "phase_04_episodes"
OUTPUT_PATH = BASE_DIR / "the_ephergent.epub"

# Episode file mapping: (season_dir, pattern) -> chapter_number
SEASONS = [
    ("season01", "S01E{:02d}_*.md", 1),
    ("season02", "S02E{:02d}_*.md", 11),
    ("season03", "S03E{:02d}_*.md", 21),
]

def natural_sort_key(s):
    """Sort string with numbers naturally."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(s))]

def find_episode_files():
    """Find all 30 episode files, sorted by episode number."""
    episodes = []
    
    for season_dir, file_pattern, start_chapter in SEASONS:
        season_path = EPISODES_DIR / season_dir
        if not season_path.exists():
            print(f"Warning: {season_path} not found")
            continue
        
        # Build glob pattern: S01E*.md, S02E*.md, S03E*.md
        prefix = file_pattern[:3]  # S01, S02, S03
        for f in sorted(season_path.glob(f"{prefix}E*.md"), key=natural_sort_key):
            if f.name.startswith("."):
                continue
            # Extract episode number from filename
            match = re.search(r'E(\d{2})_', f.name)
            if match:
                ep_num = int(match.group(1))
                chapter_num = start_chapter + ep_num - 1
                episodes.append((chapter_num, f))
    
    return sorted(episodes, key=lambda x: x[0])

def extract_title_and_content(markdown_text):
    """Extract title and content from markdown, converting to HTML."""
    lines = markdown_text.strip().split('\n')
    
    title = "Untitled"
    content_lines = []
    in_content = False
    
    for i, line in enumerate(lines):
        if i == 1 and line.startswith('# ') and not in_content:
            title = line[2:].strip()
            in_content = True
            continue
        if i >= 2:
            in_content = True
        if in_content:
            content_lines.append(line)
    
    content = '\n'.join(content_lines)
    
    # Convert markdown to basic HTML
    html = markdown_to_html(content)
    
    return title, html

def markdown_to_html(text):
    """Convert basic markdown to HTML."""
    html_lines = []
    
    for line in text.split('\n'):
        # Skip empty lines that are just whitespace
        stripped = line.strip()
        
        if not stripped:
            html_lines.append('<p></p>')
            continue
        
        # Headers
        if stripped.startswith('#### '):
            html_lines.append(f'<h4>{escape_html(stripped[5:])}</h4>')
        elif stripped.startswith('### '):
            html_lines.append(f'<h3>{escape_html(stripped[4:])}</h3>')
        elif stripped.startswith('## '):
            html_lines.append(f'<h2>{escape_html(stripped[3:])}</h2>')
        elif stripped.startswith('# '):
            html_lines.append(f'<h1>{escape_html(stripped[2:])}</h1>')
        # Horizontal rule
        elif stripped == '---' or stripped == '***' or stripped == '___':
            html_lines.append('<hr/>')
        # List items
        elif stripped.startswith('- ') or stripped.startswith('* '):
            html_lines.append(f'<li>{process_inline(stripped[2:])}</li>')
        # Numbered lists
        elif re.match(r'^\d+\. ', stripped):
            match = re.match(r'^(\d+)\. (.*)', stripped)
            if match:
                html_lines.append(f'<li>{process_inline(match.group(2))}</li>')
        # Blockquotes
        elif stripped.startswith('> '):
            html_lines.append(f'<blockquote>{process_inline(stripped[2:])}</blockquote>')
        # Emphasis and inline code
        else:
            html_lines.append(f'<p>{process_inline(stripped)}</p>')
    
    return '\n'.join(html_lines)

def process_inline(text):
    """Process inline markdown elements."""
    # Process code spans first (don't want to mangle them)
    result = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Bold
    result = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', result)
    
    # Italic
    result = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', result)
    
    # Strikethrough
    result = re.sub(r'~~([^~]+)~~', r'<s>\1</s>', result)
    
    return escape_html(result)

def escape_html(text):
    """Escape HTML special characters."""
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;'))

def generate_chapter_html(chapter_num, title, content):
    """Generate a complete XHTML chapter file."""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{escape_html(title)}</title>
    <style type="text/css">
        body {{
            background-color: #0a0a0a;
            color: #00ff41;
            font-family: "Courier New", Courier, monospace;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
        }}
        h1 {{
            color: #00ff41;
            border-bottom: 1px solid #00ff41;
            padding-bottom: 10px;
            font-size: 1.4em;
        }}
        h2 {{
            color: #00cc33;
            font-size: 1.2em;
        }}
        h3 {{
            color: #00aa2a;
            font-size: 1.1em;
        }}
        h4 {{
            color: #008822;
            font-size: 1em;
        }}
        p {{
            margin: 12px 0;
        }}
        blockquote {{
            border-left: 3px solid #00ff41;
            padding-left: 15px;
            margin-left: 10px;
            color: #00cc33;
            font-style: italic;
        }}
        code {{
            background-color: #1a1a1a;
            padding: 2px 6px;
            border-radius: 3px;
            color: #ffcc00;
        }}
        strong {{
            color: #ffffff;
        }}
        em {{
            color: #00dd55;
        }}
        li {{
            margin: 5px 0;
        }}
        hr {{
            border: none;
            border-top: 1px solid #00ff41;
            margin: 20px 0;
        }}
        a {{
            color: #00ffaa;
            text-decoration: none;
        }}
    </style>
</head>
<body>
<h1>{escape_html(title)}</h1>
{content}
</body>
</html>'''

def generate_toc_ncx(chapters):
    """Generate NCX navigation file."""
    nav_points = []
    for num, title, _ in chapters:
        nav_points.append(f'''    <navPoint id="navpoint-{num}" playOrder="{num}">
        <navLabel><text>{escape_html(title)}</text></navLabel>
        <content src="chapter{num:02d}.xhtml"/>
    </navPoint>''')
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="the-ephergent"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle><text>The Ephergent</text></docTitle>
    <navMap>
{chr(10).join(nav_points)}
    </navMap>
</ncx>'''

def generate_content_opf(chapters):
    """Generate OPF manifest and spine."""
    manifest_items = []
    spine_items = []
    
    # Cover
    manifest_items.append('<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
    manifest_items.append('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
    
    for num, _, _ in chapters:
        manifest_items.append(f'<item id="chapter{num}" href="chapter{num:02d}.xhtml" media-type="application/xhtml+xml"/>')
        spine_items.append(f'<itemref idref="chapter{num}"/>')
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="the-ephergent">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>The Ephergent</dc:title>
        <dc:creator>Jeremy</dc:creator>
        <dc:language>en</dc:language>
        <dc:identifier id="the-ephergent">the-ephergent</dc:identifier>
        <meta property="dcterms:modified">2026-05-01T00:00:00Z</meta>
    </metadata>
    <manifest>
{chr(10).join(manifest_items)}
    </manifest>
    <spine toc="ncx">
{chr(10).join(spine_items)}
    </spine>
</package>'''

def generate_container():
    """Generate container.xml."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''

def generate_cover_html():
    """Generate a dark sci-fi cover page."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>The Ephergent - Cover</title>
    <style type="text/css">
        body {
            background-color: #0a0a0a;
            color: #00ff41;
            font-family: "Courier New", Courier, monospace;
            text-align: center;
            margin: 0;
            padding: 40px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        h1 {
            font-size: 2.5em;
            color: #00ff41;
            text-shadow: 0 0 10px #00ff41;
            margin-bottom: 10px;
            letter-spacing: 5px;
        }
        .subtitle {
            font-size: 1.2em;
            color: #00cc33;
            margin-bottom: 40px;
        }
        .signal {
            color: #00ffaa;
            font-size: 1em;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .description {
            color: #008822;
            max-width: 500px;
            line-height: 1.8;
            margin-top: 30px;
        }
        .seasons {
            margin-top: 40px;
            color: #00aa2a;
        }
    </style>
</head>
<body>
    <h1>THE EPHERGENT</h1>
    <p class="subtitle">A Retrocausality Sci-Fi Universe</p>
    <p class="signal">[ TRANSMISSION RECEIVED ]</p>
    <p class="description">
        The Ephergent is a signal—a retrocausal transmission from a future intelligence reaching backward through time. 
        When the Department of Reality Maintenance crumbles, data analyst Pixel Paradox finds herself broadcast into a void 
        between worlds, piloting a lifeboat through an ocean of static with her crew: an espresso machine with ancient memories, 
        a bronze robot poet, and a dog who understands frequencies humans cannot hear.
    </p>
    <p class="seasons">Three Seasons • Thirty Chapters</p>
</body>
</html>'''

def create_epub():
    """Create the EPUB file."""
    print("Finding episode files...")
    episodes = find_episode_files()
    
    if len(episodes) < 30:
        print(f"Warning: Found only {len(episodes)} episodes (expected 30)")
    
    print(f"Found {len(episodes)} episodes")
    
    # Process episodes
    chapters = []
    for chapter_num, filepath in episodes:
        print(f"Processing Chapter {chapter_num}: {filepath.name}")
        content = filepath.read_text(encoding='utf-8')
        title, html_content = extract_title_and_content(content)
        chapters.append((chapter_num, title, html_content))
    
    print("\nGenerating EPUB...")
    
    # Create EPUB
    with zipfile.ZipFile(OUTPUT_PATH, 'w', zipfile.ZIP_DEFLATED) as epub:
        # mimetype must be first, uncompressed
        epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        
        # META-INF/container.xml
        epub.writestr('META-INF/container.xml', generate_container())
        
        # EPUB/content.opf
        epub.writestr('EPUB/content.opf', generate_content_opf(chapters))
        
        # EPUB/toc.ncx
        epub.writestr('EPUB/toc.ncx', generate_toc_ncx(chapters))
        
        # Cover
        epub.writestr('EPUB/cover.xhtml', generate_cover_html())
        
        # Chapters
        for chapter_num, title, html_content in chapters:
            epub.writestr(f'EPUB/chapter{chapter_num:02d}.xhtml', 
                         generate_chapter_html(chapter_num, title, html_content))
    
    print(f"\nEPUB created successfully: {OUTPUT_PATH}")
    print(f"File size: {OUTPUT_PATH.stat().st_size:,} bytes")
    
    return str(OUTPUT_PATH)

if __name__ == "__main__":
    create_epub()

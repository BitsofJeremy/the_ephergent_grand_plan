---
name: ephergent-image-gen
description: Use when generating Ephergent comic art, character portraits, or scene illustrations via ComfyUI Flux on the LAN server.
author: rodan
license: MIT
platforms: [linux, macos, windows]
tags: [ephergent, flux, image-generation, ephergent-comics, character-art, lan-server]
related_skills: [the-ephergent]
---

# Ephergent Image Generation

Generate Ephergent comic art via ComfyUI Flux on Jeremy's LAN server.

## Server

- **URL:** `http://comfyui.nexus.home.test:8188`
- **GPU:** RTX 3060 12GB VRAM
- **Speed:** ~200ms/image (first run ~4 min model load)
- **Workflow:** `t2i_ephergent_comics_001.json`

## Generate an Image

```bash
WORKFLOW='/home/debian/Documents/code_repos/the_ephergent_grand_plan/source_archive/t2i_ephergent_comics_001.json'
UUID=$(python3 -c 'import uuid; print(uuid.uuid4().hex[:8])')

python3 - << 'EOF'
import json
with open(WORKFLOW) as f:
    wf = json.load(f)
wf['6']['inputs']['text'] = 'your prompt here'
wf['30']['inputs']['seed'] = 77   # or -1 for random
with open('/tmp/gen.json', 'w') as f:
    json.dump(wf, f)
print('READY')
EOF

curl -s -X POST "http://10.0.0.20:8188/prompt" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": $(cat /tmp/gen.json), \"client_id\": \"$UUID\"}"
```

Poll for completion:
```bash
sleep 5 && curl -s "http://10.0.0.20:8188/history/PROMPT_ID"
```

Download:
```bash
curl -s "http://10.0.0.20:8188/view?filename=ephergent_comics-NNN.png&subfolder=the_ephergent_rebuild&type=output" \
  -o /home/debian/Documents/code_repos/ephergent.com/assets/images/generated/ephergent_comics-NNN.png
```

## Workflow Stack

- **Model:** FLUX/flux1-dev-fp8.safetensors
- **LoRAs:** fluxlisimo v4 (0.7), Kenva_Style (0.6), creepy-cute-magical (0.3), Evangelion_Post-impact (0.8)
- **Sampler:** euler, 32 steps, cfg=1.0
- **Output:** 1024×1024 PNG

## Prompt Structure

```
[STYLE CHAIN], cinematic [SHOT TYPE], [SUBJECT], [SETTING], [LIGHTING], [EMOTIONAL TONE]
```

**Always prepend:**
```
p0st_1mp4ct style, ArsMJStyle, Kenva, fluxlisimo,
```

**Always append:**
```
A digitally illustrated drawing in stylized 3D anime manga style with painterly cel-shading and hand-drawn textures, featuring volumetric lighting with soft watercolor-like gradients, dynamic comic book halftone patterns, realistic depth of field and atmospheric perspective, soft ambient occlusion shadows, cinematic rim lighting, subsurface scattering effects, realistic material textures and fabric physics, while maintaining clean manga lineart with NPR non-photorealistic rendering and traditional anime color palettes enhanced by atmospheric haze
```

## Character Prompts (Quick Reference)

### Pixel Paradox
```
p0st_1mp4ct style, ArsMJStyle, Kenva, fluxlisimo, cinematic medium shot portrait, young 24 year old woman journalist and accidental starship captain, fiery red hair in asymmetrical punk cut, bright curious green eyes, wearing weathered brown leather jacket with silver Art Nouveau buckles, vintage band tee, silver-framed goggles with teal lenses, sturdy exploration boots, steam rising from espresso cup in hand, warm amber ship interior lighting, electric pink broadcast glow, the Ephergent bridge with brass fittings and holographic displays
```

### A1 / The Ship
```
p0st_1mp4ct style, ArsMJStyle, Kenva, fluxlisimo, cinematic medium shot, ancient quantum espresso machine that is also a living starship, warm brass and copper body with holographic displays flickering with probability vectors, protective parental presence, coffee steam rising in patterns that suggest dimensional coordinates, soft indigo ship interior lighting, the Ephergent bridge visible behind, stoic British formality, a vessel that is also a home
```

### Clive
```
p0st_1mp4ct style, ArsMJStyle, Kenva, fluxlisimo, cinematic medium shot portrait, knee-high robot with a glowing sphere head in warm blue-white light, wearing a battered fedora (gift from Barry), expressive light patterns pulsing in rhythmic sequences, noir oracle energy, the weight of 90 years of institutional memory, detective presence
```

### Mochi
```
p0st_1mp4ct style, ArsMJStyle, Kenva, fluxlisimo, cinematic medium shot, Shiba Inu with warm orange and white coat, alert pointed ears, bright curious eyes, blue tactical vest with patches and signal receiver, standing at alert with head tilted, cosmic detector energy, warm amber lighting, no dialogue just warm glow pulses
```

### Meatball
```
p0st_1mp4ct style, ArsMJStyle, Kenva, fluxlisimo, cinematic medium shot, orange corgi with barrel chest, short sturdy legs, large orange-and-white coat, black nose, large pointed ears moving independently, thick tail, warm amber engine room lighting, soft golden glow from nearby espresso machine, loyal presence
```

## Check Server Status

```bash
curl -s http://10.0.0.20:8188/system_stats   # VRAM free = model loaded
curl -s http://10.0.0.20:8188/queue            # empty = idle
```

## Common Issues

- **First run slow (~4 min):** Normal — model loading from disk into VRAM
- **Counter collision:** Always poll `/history/{id}` for actual filename
- **cfg=1.0 is correct for Flux** — don't increase
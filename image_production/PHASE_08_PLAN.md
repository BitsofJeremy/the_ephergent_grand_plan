# PHASE 08 — IMAGE PRODUCTION
*Character portraits, scene art, and game concept art for ephergent.com*

---

## OVERVIEW

Phase 08 generates visual assets for The Ephergent universe using ComfyUI Flux on Jeremy's LAN server (10.0.0.20:8188). Assets are integrated into ephergent.com to support character profiles, scene illustrations, and game concept art.

**Server:** ComfyUI LAN — RTX 3060 12GB VRAM  
**Model:** FLUX/flux1-dev-fp8.safetensors  
**LoRA Stack:** fluxlisimo_v4 (0.7) → Kenva_Style (0.6) → creepy-cute-magical (0.3) → Evangelion_Post-impact (0.8)  
**Speed:** ~200ms per image (after first-load); first gen ~4 min  
**Output:** 1024×1024 PNG, saved to `ComfyUI/output/the_ephergent_rebuild/`

**Canonical workflow:** `/home/debian/Documents/code_repos/the_ephergent_grand_plan/source_archive/t2i_ephergent_comics_001.json`

---

## CONTEXT FROM PREVIOUS WORK

The `source_archive/ephergent_season_03_generator/` is a Flask app with a full ComfyUI service (`services/comfyui_service.py`), character prompt templates (`prompts/characters/*_s3.md`), and an image prompt generation pipeline (`services/image_service.py`). This is **reference code only** — it drives a local web app with its own queue system. The new implementation bypasses the Flask app entirely and calls ComfyUI REST API directly from Hermes, which is more appropriate for on-demand heartbeat generation.

The existing `ephergent-image-gen` skill has been updated with full character visual profiles and scene prompts.

---

## ASSET TYPES

### 1. CHARACTER PORTRAITS
One hero image per character, suitable for the crew section of ephergent.com. Site currently has thin pages for: Pixel Paradox, A1, Clive, Meatball, Mochi, Om Kai, Zephyr Glitch. These need full-bleed character portraits.

**Characters:**
- [ ] Pixel Paradox — `/crew/pixel-paradox/`
- [ ] A1 — `/crew/a1/`
- [ ] Clive — `/crew/clive/`
- [ ] Meatball — `/crew/meatball/`
- [ ] Mochi — `/crew/mochi/`
- [ ] Om Kai — `/crew/om-kai/`
- [ ] Zephyr Glitch — `/crew/zephyr-glitch/`
- [ ] Barry Kowalski — `/crew/barry-kowalski/` (canonically alive in the Wellspring, appears in Season 3)

### 2. SCENE ILLUSTRATIONS
Key scene images for lore entries and transmission pages:
- [ ] The Ephergent bridge interior
- [ ] The Interdimensional Space (the Space between frequencies)
- [ ] Nocturne Aeturnus (gothic twilight)
- [ ] The Wellspring (cosmic genesis)
- [ ] Frequency storm
- [ ] Prime Material (urban contemporary)
- [ ] Verdantia (sentient flora)
- [ ] Cogsworth Cogitarium (clockwork metropolis)

### 3. EPISODE THUMBNAILS
- [ ] All 30 canonical episodes (S01–S03) — one hero image each for transmission pages

### 4. GAME CONCEPT ART
For Phase 05 games (built later):
- [ ] Meatball's Big Walk — gameplay concept
- [ ] Tune-the-Dial — frequency interface concepts
- [ ] Static Run — Nano character + entropy visuals
- [ ] The Laughing Funeral — Nocturne Aeturnus + Baron Klaus
- [ ] Builder Station Game — archive terminal, Clive companion
- [ ] The Wellspring — broadcast mechanic visuals

---

## GENERATION WORKFLOW

### Standard Generation (VPS → LAN ComfyUI)

```bash
WORKFLOW="/home/debian/Documents/code_repos/the_ephergent_grand_plan/source_archive/t2i_ephergent_comics_001.json"
UUID=$(python3 -c 'import uuid; print(uuid.uuid4().hex[:8])')

# 1. Patch prompt into workflow node 6
python3 - << 'PYEOF'
import json
with open("$WORKFLOW") as f:
    wf = json.load(f)
wf["6"]["inputs"]["text"] = "YOUR FULL PROMPT HERE"
wf["30"]["inputs"]["seed"] = -1   # -1 = random, or set specific seed
with open("/tmp/gen.json", "w") as f:
    json.dump(wf, f)
print("READY")
PYEOF

# 2. Queue prompt
curl -s -X POST "http://10.0.0.20:8188/prompt" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": $(cat /tmp/gen.json), \"client_id\": \"$UUID\"}" \
  -o /tmp/queue_resp.json
PROMPT_ID=$(python3 -c "import json; print(json.load(open('/tmp/queue_resp.json'))['prompt_id'])")
echo "Prompt ID: $PROMPT_ID"

# 3. Poll until done (~4 min first load, ~200ms after)
sleep 8 && curl -s "http://10.0.0.20:8188/history/$PROMPT_ID" -o /tmp/hist.json
# Repeat until hist.json has content (prompt_id as key)

# 4. Get actual filename from history
FILENAME=$(python3 -c "import json; h=json.load(open('/tmp/hist.json')); print(h.popitem()[1]['outputs']['33']['images'][0]['filename'])")
echo "Output: $FILENAME"

# 5. Download to local
curl -s "http://10.0.0.20:8188/view?filename=$FILENAME&subfolder=the_ephergent_rebuild&type=output" \
  -o "/home/debian/Documents/code_repos/ephergent.com/assets/images/generated/$FILENAME"

# 6. Commit to git
cd /home/debian/Documents/code_repos/ephergent.com && git add assets/images/generated/$FILENAME && git commit -m "img: $FILENAME"
```

### Image Dimensions

| Use Case | Width | Height | Notes |
|----------|-------|--------|-------|
| Character portrait (crew page) | 1024 | 1024 | Workflow default |
| Episode thumbnail | 1024 | 1024 | Workflow default |
| Scene illustration | 1024 | 1024 | Workflow default |
| Game concept art | 1024 | 1024 | Workflow default |

For wider compositions (16:9), the `EmptyLatentImage` node (ID `5`) can be changed to `1344×768` before queuing. See `t2i_ephergent_season_03_workflow.json` for that configuration.

---

## API REFERENCE (ComfyUI LAN)

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/prompt` | Queue a generation |
| GET | `/history/{prompt_id}` | Poll for completion |
| GET | `/view?filename=&subfolder=&type=` | Download image |
| GET | `/queue` | Check queue status |
| GET | `/system_stats` | VRAM usage / model loaded |

### Prompt Payload Structure

```json
{
  "prompt": { /* full workflow JSON with prompt patched */ },
  "client_id": "uuid-v4-hexstring"
}
```

### History Response

```json
{
  "prompt_id": {
    "outputs": {
      "33": {
        "images": [
          {
            "filename": "ephergent_comics-007.png",
            "subfolder": "the_ephergent_rebuild",
            "type": "output"
          }
        ]
      }
    }
  }
}
```

---

## PROMPT GUIDANCE

### Style Chain (ALWAYS prepend)
```
p0st_1mp4ct style, ArsMJStyle, Kenva, fluxlisimo,
```

### Aesthetic Suffix (ALWAYS append)
```
A digitally illustrated drawing in stylized 3D anime manga style with painterly cel-shading and hand-drawn textures, featuring volumetric lighting with soft watercolor-like gradients, dynamic comic book halftone patterns, realistic depth of field and atmospheric perspective, soft ambient occlusion shadows, cinematic rim lighting, subsurface scattering effects, realistic material textures and fabric physics, while maintaining clean manga lineart with NPR non-photorealistic rendering and traditional anime color palettes enhanced by atmospheric haze
```

### Node IDs (from t2i_ephergent_comics_001.json)
| Node | Class | Purpose |
|------|-------|---------|
| 6 | CLIPTextEncode | Positive prompt input |
| 31 | CLIPTextEncode | Negative prompt (leave empty) |
| 5 | EmptyLatentImage | Resolution (1024×1024 default) |
| 30 | KSampler | Seed, steps (32), cfg (1.0) |

### Seed Strategy
- Use `seed: -1` for "anything good" — Flux will randomize
- Use a specific seed to reproduce a composition with a new prompt
- For character portraits: generate 4–6 with different seeds, pick the best

---

## OUTPUTS & DELIVERY

All generated images are downloaded to:
```
/home/debian/Documents/code_repos/ephergent.com/assets/images/generated/
```

Commit message convention:
```
img: character/pixel-paradox-portrait-001
img: scene/wellspring-001
img: episode/S01E01-thumb-001
```

Each image is committed separately to keep history clean and git blame usable.

---

## PITFALLS

1. **First generation ~4 min:** Model loads from disk to VRAM. Subsequent runs ~200ms. Don't retry during first-load.
2. **Counter filename collisions:** `ephergent_comics-XXX.png` counter resets on ComfyUI restart. Always poll `/history/{prompt_id}` to get the actual filename. Do NOT assume the next sequential number.
3. **Empty history = not done:** `{}` from `/history/{id}` means still running or not yet recorded. Check `/queue` for running jobs.
4. **cfg=1.0 is correct:** Flux uses guidance differently than SDXL. Do not increase CFG.
5. **Batch size = 1:** This workflow outputs one image per run. For variants, run multiple times with different seeds.
6. **LAN-only access:** The ComfyUI server is on Jeremy's home network at 10.0.0.20. VPS (10.0.0.199) can reach it. External internet cannot.

---

## HEARTBEAT TASK SIZING

Each image generation (including first-load) is one heartbeat task:
- Generate 1 portrait → ~4 min first time, ~200ms after
- Batch 4 variants of same character → one heartbeat, sequential runs

Suggested per-heartbeat targets:
- 1 character portrait (4 seed variants, pick best)
- 2 scene illustrations
- 3 episode thumbnails
- 1 game concept art piece

---

## RELATIONSHIP TO OTHER PHASES

- **Phase 07 (Site):** Phase 08 assets are consumed by the site. Crew pages need portraits. Lore pages need scene art.
- **Phase 04 (Episodes):** Episode thumbnails are tied to canonical transmission pages.
- **Phase 05 (Games):** Game concept art feeds the game design bible assets.
- **Phase 02 (Characters):** Character portraits bring the character bibles to life visually.

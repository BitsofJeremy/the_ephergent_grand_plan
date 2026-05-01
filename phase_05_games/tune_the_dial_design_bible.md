# Tune-the-Dial — Game Design Bible

## The Ephergent Project — Game 2

*Status: Design Complete — Ready for Development*
*Engine: Godot 4 (HTML5 export)*
*Hard cap: 15 MB*
*Price: Free forever, browser-playable*

---

## 1. Overview

Tune-the-Dial is a frequency puzzle game. The player operates a retro oscilloscope interface — a single dial, a waveform display, and a signal meter — to scan the cosmic radio spectrum. Hidden in the noise are stable signals: the five known frequencies, Builder Station broadcasts, the Ephergent Frequency itself, and one deeply buried pattern that Barry Kowalski left for Clive eight hundred years ago.

The game is atmospheric, contemplative, and deceptively simple. The core loop is: turn the dial, listen, watch the waveform, find the signal. The depth comes from the character perspective system (each crew member hears different things on the same channel), the layered difficulty of extracting faint signals from noise, and the lore entries that each discovery unlocks.

This is not an action game. It is a listening game. The player's primary tool is patience.

---

## 2. Core Mechanic — The Dial

### The Dial Interface

The screen shows a single circular frequency dial at center-bottom, styled as a heavy analog knob with etched notch marks. The player rotates it by click-dragging (mouse), touch-dragging (mobile), or left/right arrow keys. The dial is continuous — it wraps. There is no beginning or end to the spectrum. This is thematic: the multiverse is an infinite radio dial.

The dial has **1000 discrete positions** internally, but the player experiences it as smooth analog rotation. Each position maps to a unique point on the frequency spectrum.

### The Waveform Display

Above the dial, the oscilloscope screen occupies the top two-thirds of the viewport. It renders a real-time waveform:

- **Noise**: The default state. Jagged, irregular, fast-moving static. Visually chaotic. Audio is white/pink noise with subtle modulation.
- **Approaching a signal**: The noise begins to organize. The waveform develops hints of periodicity. The audio static develops faint tonal qualities. The signal meter (top-right) twitches upward.
- **On a signal**: The waveform resolves into a distinct, stable pattern — each signal has a unique waveform shape. The audio becomes a clear tone/texture. The signal meter holds steady in the green zone.
- **Locked on**: When the player holds the dial steady on a signal for 3 seconds, the signal "locks" — the waveform brightens, the audio clarifies fully, and the associated lore entry unlocks. A brief text overlay identifies what was found.

### Signal Strength & Proximity

Each signal occupies a narrow band on the dial (roughly 5–15 positions wide out of 1000). Signals have a proximity gradient:

| Distance from center | Waveform behavior | Audio behavior | Meter |
|---|---|---|---|
| >50 positions | Pure noise | Pure static | Dead |
| 30–50 positions | Occasional flicker of pattern | Faint tonal hint buried in noise | Twitches |
| 15–30 positions | Pattern visible but unstable | Tone audible but fighting static | Low |
| 5–15 positions | Pattern mostly resolved, slight jitter | Tone clear, light static overlay | Mid |
| 0–5 positions | Clean, stable waveform | Pure signal | Green lock zone |

### Difficulty Escalation

Not all signals are equally easy to find:

- **Tier 1 — The Five Frequencies**: Wide bands (15 positions), strong signals. A new player will find these within minutes. These are the tutorial.
- **Tier 2 — Builder Station Signals**: Narrower bands (8 positions), weaker signals that require slower, more careful dial movement. The waveform hints are subtler.
- **Tier 3 — The Ephergent Frequency**: A single channel (5 positions wide) that behaves differently based on the selected character perspective. Finding it once is moderate difficulty; hearing all perspective variants requires deliberate replay.
- **Tier 4 — Barry's Hidden Pattern**: The hardest signal in the game. Band is only 3 positions wide. The signal does not behave like the others — it does not produce a clean waveform. Instead, it produces a pattern *within the noise itself*: a rhythmic modulation of the static that looks random unless you know what you're looking for. The signal meter does NOT respond to it. This is intentional. Barry hid it where instruments wouldn't flag it. Only eyes and ears find it.

---

## 3. Frequency Categories — The Signals

### 3A. The Five Known Frequencies

Each of the five frequencies has a unique waveform signature, audio character, and color tint on the oscilloscope.

#### Frequency 1 — Prime Material
- **Waveform**: Clean sine wave. Steady, confident, zero jitter. The most "normal" signal on the dial.
- **Audio**: A warm, low hum — like mains electricity heard through a wall. Steady. Unremarkable. The signal you'd tune past if you weren't paying attention.
- **Oscilloscope tint**: No tint. Default green-on-black. Prime Material is the baseline.
- **Lore unlock**: Entry on Prime Material — the "normal" world, thin spots spreading, the hum beneath the surface no one notices.

#### Frequency 2 — Nocturne Aeturnus
- **Waveform**: A slow, deep oscillation with harmonic overtones — like a cello waveform. The peaks are rounded, almost gentle. Long wavelength.
- **Audio**: A resonant chord. Low cello tone with cathedral reverb. The player feels it in the chest before recognizing it as a signal. Carries emotional weight — the signal itself sounds sad and beautiful.
- **Oscilloscope tint**: Deep indigo/purple wash.
- **Lore unlock**: Entry on Nocturne Aeturnus — eternal twilight, crystallized emotion, the Sorrowful Moon dimming.

#### Frequency 3 — Cogsworth Cogitarium
- **Waveform**: A precise square wave with metronomic timing. Sharp edges. Perfect intervals. Mechanical regularity.
- **Audio**: Clicking rhythm — a clock shop at midnight. Layered ticking at slightly different rates, all somehow in sync. Faint steam hiss underneath. Hypnotic.
- **Oscilloscope tint**: Warm amber/copper.
- **Lore unlock**: Entry on Cogsworth Cogitarium — the clockwork frequency, the Grand Orrery wobbling, gears skipping as entropy wins.

#### Frequency 4 — Verdantia
- **Waveform**: An organic, breathing waveform — rises and falls like respiration. Never perfectly periodic. Each cycle slightly different from the last, like a living thing.
- **Audio**: A low, thrumming pulse — a heartbeat heard through earth. Layered: leaf rustle, creaking wood, a subsonic hum that feels alive.
- **Oscilloscope tint**: Deep emerald green with faint bioluminescent pulse (the waveform line itself gently brightens and dims on the breathing cycle).
- **Lore unlock**: Entry on Verdantia — the living frequency, the root network disconnecting node by node, the collective consciousness growing quieter.

#### Frequency 5 — The Edge
- **Waveform**: Chaos. Not noise — structured chaos. A waveform that contains fragments of every other frequency's pattern, overlapping, interfering, never quite resolving. Visually the most complex signal on the dial.
- **Audio**: A roaring, shimmering wall of sound containing ghost-fragments of every other signal. Most players will hear noise. Attentive players will hear the other four frequencies buried in it.
- **Oscilloscope tint**: Shifting — cycles through colors that don't have names. Implementation: slow HSV hue rotation with saturation variance.
- **Lore unlock**: Entry on The Edge — reality at its thinnest, the Nursery Fields producing fewer new worlds, chaos tilting from creation toward dissolution.

### 3B. Builder Station Signals (Tier 2)

Seven narrower, weaker signals corresponding to the seven catalogued Builder Stations. Each uses a variation of the frequency waveform from its nearest frequency, but filtered — attenuated, older-sounding, with a characteristic "age" to the signal (slight warble, faint harmonic decay).

| Station | Nearest Freq. | Waveform Character | Audio Character |
|---|---|---|---|
| 11-Quiescent | Between 2 & 4 | Near-flatline with faint thermal drift | Almost silence. A faint warmth in the static — not a sound, an absence of cold. |
| 3-Resonant | Between 1 & 3 | Sine/square hybrid at ~4% amplitude | A hum you have to lean into. The most beautiful faint sound. Crystal resonance. |
| 5-Meridian | Convergence 2/3/4 | Tricolor interference — three overlapping patterns | A chord that wavers. Three signals trying to hold together. |
| 7-Ascending | Near 5 / Edge | Strong structured chaos at 23% | The clearest Builder signal. A tone that rises. The EPHERGENT plate hums. |
| 9-Liminal | Border of Silence | Subsonic pulse, felt not heard | A pressure. The waveform is almost below the display range. Hold your breath. |
| 14-Threshold | Wellspring approach | Pure, sustained resonance at 40% | Standing inside a sound that knows your name. |
| 0-Origin (Wellspring) | The source | Every waveform simultaneously, in harmony | The full broadcast. All frequencies contained in one signal. |

Each Station signal unlock populates a lore entry about that Station — its status, what the crew found there, what Barry left behind.

---

## 4. The Hidden Barry Pattern

### What It Is

At a specific position on the dial (randomized per playthrough within a narrow range to prevent wiki-lookup solving), there is no signal. The meter stays dead. The waveform looks like noise. But the noise itself is structured.

Barry Kowalski spent 23 years as a night guard listening to Clive talk in his sleep. He learned Builder frequency notation by ear. When he reached the Wellspring, he encoded a message into the cosmic static — a specific modulation pattern that only someone who knew what they were looking for would recognize.

### How the Player Finds It

The Barry Pattern is not findable by scanning for signal strength — the meter doesn't respond. The player must:

1. **Notice the noise is different**. At this dial position, the static has a rhythm. It's subtle — a slight pulse in the amplitude of the noise, roughly 3 beats per second. The waveform's chaos has a hidden periodicity that the oscilloscope won't highlight automatically.

2. **Hold the dial steady**. Unlike other signals that lock after 3 seconds, the Barry Pattern requires **23 seconds** of holding — one second for each year Barry spent on the nightshift with Clive. During those 23 seconds, the pattern slowly emerges: the noise organizes itself, not into a clean waveform but into a recognizable shape — Barry's handwriting. The oscilloscope traces out, in the noise, the letter forms of a message.

3. **Read the message**. The noise-writing resolves into:

   > *"C — the trail is intact. Follow the thermos. — B"*

### What It Unlocks

- A lore entry about the Wellspring — Barry's discovery of it, his deliberate entry, his encoding of a trail for Clive to follow.
- **Clive's dialogue trigger** (see Section 11 — Narrative Integration).
- A hidden achievement/badge: **"23 Years of Patience"**
- The Wellspring Builder Station signal (0-Origin) becomes findable on the dial. It was always there but invisible until the Barry Pattern is found. This gates the deepest lore content behind the hardest puzzle.

### Design Notes

The 23-second hold is the design signature. It teaches the player what the game is *about*: patience. The same patience Barry had. The same patience Clive has. You don't find the answer by scanning faster. You find it by staying still.

---

## 5. The Ephergent Frequency Channel

### The Mechanic

One channel on the dial carries the Ephergent Frequency — the oldest signal in the universe. Unlike every other signal in the game, this one **changes based on which character perspective the player has selected**. Same dial position, different audio and waveform, depending on who is "listening."

This is the game's central insight: the same signal, heard differently by different people, carries different information. It is a mechanic that teaches the player something about the Ephergent universe — that connection is not one-size-fits-all, that the Builders built a message system sophisticated enough to speak to each consciousness in its own language.

### What Each Character Hears

The player can select from the crew members who have defined Ephergent Frequency experiences. Each selection changes both the audio output and the waveform visualization when tuned to the Ephergent Frequency channel:

#### Pixel Paradox (Captain / Broadcaster)
- **Audio**: A broadcast. Static resolves into a voice — not words the player can understand, but the cadence and warmth of a transmission from somewhere. It sounds like tuning into a radio station from a city you've never visited but somehow recognize. Familiar music you've never heard.
- **Waveform**: An AM radio carrier wave with amplitude modulation — the waveform of a voice speaking, though the words are just beyond comprehension.
- **Lore unlock**: Pixel's entry — born too sensitive to frequencies, always out of step with Prime Material, the Signal finding her first.

#### Om Kai (Philosophy / Counsel)
- **Audio**: Near-silence. The signal is the *gaps* — brief pauses in the background noise that, when attended to, contain more meaning than any sound. A breath. A pause between mantras. The player must lower their volume and listen to the quiet.
- **Waveform**: A flatline that, on close inspection, contains tiny inflections — moments where the line dips or rises almost imperceptibly. The signal is in the stillness, not the motion.
- **Lore unlock**: Om Kai's entry — choosing stillness in Nocturne Aeturnus, a frequency of perpetual emotional motion.

#### Meatball (Emotional Compass)
- **Audio**: Not a sound. A texture. The audio channel produces a warm, low-frequency rumble — below the range of clear hearing, felt in the speakers/headphones more than heard. It sounds like being near something alive and safe. Thursday afternoon. Almost home.
- **Waveform**: A soft, rolling wave — not a signal pattern but something that looks like a sleeping heartbeat. Slow. Warm. The oscilloscope tint shifts to a golden amber.
- **Lore unlock**: Meatball's entry — a Rottweiler with the frequency sensitivity of a Builder instrument, nobody knows why.

#### Clive (Mechanic / Memory)
- **Audio**: The player hears a voice — Clive's voice, but different. Younger? Older? Speaking words in a language that is almost English but not quite, with the cadence of someone explaining something important to someone they care about. It is Clive, eight hundred years ago, before the compression, before the forgetting. His own voice calling to himself across centuries.
- **Waveform**: The waveform traces Builder frequency notation — angular, mathematical, beautiful. The player is looking at Clive's own handwriting from before he forgot how to write it.
- **Lore unlock**: Clive's entry — a Builder Companion Unit, 800 years compressed, carrying memories he cannot access.

#### Zephyr Glitch (Communications)
- **Audio**: A laugh. Distant, warm, unmistakable — a person who finds something genuinely funny, far away but clearly present. Aether's laugh. It fades in and out, never quite fully arriving, never fully gone. It is the audio equivalent of reaching for someone's hand and almost touching.
- **Waveform**: Two waveforms overlapping — one solid (Zephyr), one translucent/ghosted (Aether). They almost sync. They never quite do. The gap between them is the distance Zephyr has been trying to close since Aether crossed over.
- **Lore unlock**: Zephyr's entry — The Edge, his brother becoming a Keeper, being half-gone since.

#### A1 (The Ship / Navigator)
- **Audio**: Music. Not a melody the player will recognize — something older, more structural, like hearing the mathematical relationships between notes before anyone assigned them to instruments. A1 hears the Ephergent Frequency as the composition it is. The audio is a slowly evolving harmonic series.
- **Waveform**: A perfect composite — all five frequency waveforms layered, in phase, creating an interference pattern that is more complex and more beautiful than any individual signal. A1 hears the network as a network.
- **Lore unlock**: A1's entry — the ship itself, Builder-era navigation consciousness, the espresso machine at the center of everything.

#### Luminara Usha (Science / Observation)
- **Audio**: A recording. The signal sounds clinical — measured, observed, catalogued. Luminara hears data. The audio has the quality of a scientific instrument readout sonified: precise, informative, emotionally neutral. But beneath it, so faint it might be imagined: the sound of roots growing.
- **Waveform**: A clean, annotated waveform — as if the oscilloscope itself added measurement markers, frequency labels, amplitude readings. Luminara's perspective turns the signal into data.
- **Lore unlock**: Luminara's entry — Verdantia's collective consciousness, choosing individual sight, the root network remembering.

#### Baron Klaus (Procurement / Investigation)
- **Audio**: Footsteps in a stone corridor. The echo of a large space. The faint, distant sound of crystallized emotion cracking. Whatever Klaus hears in the Ephergent Frequency, it sounds like Nocturne Aeturnus — and it sounds like leaving.
- **Waveform**: A signal that keeps almost resolving, then breaking apart. Something is being investigated but not yet understood.
- **Lore unlock**: Klaus's entry — Nocturne Aeturnus, the reason he left that he won't discuss until Season 3.

#### Nano (Engineering / Speed)
- **Audio**: The signal plays fast. Double-speed, triple-speed — Nano hears the Ephergent Frequency as a compressed burst, the way she processes everything. The same content in less time. Between bursts: the ticking of Cogsworth's clocks, but wrong. Slightly off-beat. The desynchronization that drove her to leave.
- **Waveform**: A compressed waveform — the full signal squeezed into rapid bursts with gaps between them. In the gaps, a faint square wave: Cogsworth's metronome, losing time.
- **Lore unlock**: Nano's entry — Cogsworth's precision in her bones, understanding that wrenches can't fix entropy.

---

## 6. Character Perspectives — The System

### How It Works

The bottom-left corner of the screen shows a **crew roster** — small circular portraits of each available crew member, arranged vertically. The currently selected character is highlighted with a glow matching their home frequency's color. The player clicks/taps a portrait to switch perspective.

Switching perspective changes:
- What the player hears on the **Ephergent Frequency channel** (Section 5)
- The **color palette** of the oscilloscope display (subtle — the green shifts toward the character's home frequency color)
- **Ambient background noise** — each character adds a faint signature to the baseline static. Meatball's perspective has the softest static. Nano's has the fastest. Clive's has occasional brief gaps — micro-silences, like memory dropouts.

Switching perspective does NOT change:
- The position or difficulty of the five frequency signals
- The position or difficulty of the Builder Station signals
- The position of the Barry Pattern (though Clive's perspective adds a subtle audio hint — see Section 11)

### Unlock Progression

Not all characters are available at game start. The roster builds as the player discovers signals:

| Unlock trigger | Characters available |
|---|---|
| Game start | Pixel (default), Meatball |
| Find Frequency 1 (Prime Material) | +Clive (he's from Prime Material by adoption — Barry found him there) |
| Find Frequency 2 (Nocturne Aeturnus) | +Om Kai, +Baron Klaus |
| Find Frequency 3 (Cogsworth Cogitarium) | +Nano |
| Find Frequency 4 (Verdantia) | +Luminara |
| Find Frequency 5 (The Edge) | +Zephyr |
| Find any 3 Builder Stations | +A1 (the ship's perspective requires understanding the network) |

---

## 7. Win/Completion States

### "Finished" (Casual)

Find all five frequency signals. This takes 10–30 minutes for most players.

**Reward**: The oscilloscope display shifts — the noise floor drops noticeably, as if the dial has been calibrated. A brief text: *"Five frequencies found. The dial is wider than this. Keep tuning."*

### "Complete" (Thorough)

Find all five frequencies + all seven Builder Station signals + hear the Ephergent Frequency from at least one perspective.

**Reward**: The full Station network map appears on the oscilloscope — a brief visualization of all seven Stations connected by signal lines, pulsing faintly. Text: *"The network is visible. Most Stations are dark. Fewer than 30 still broadcast."*

### "Cartographer" (Completionist)

All signals found + Ephergent Frequency heard from all 9 character perspectives.

**Reward**: The oscilloscope displays Mochi's frequency map briefly — hundreds of signals, most faded, some bright. More frequencies than the five that are known. Text: *"The atlas contains more than five worlds. Most have gone quiet. Some can be heard again."*

### "23 Years of Patience" (Secret)

Find the Barry Pattern + all other signals.

**Reward**: Clive's dialogue (see Section 11). The Wellspring signal. The complete lore atlas entry for the Wellspring. A final oscilloscope visualization: every signal found, all layered, creating the composite waveform that A1 hears — the Ephergent Frequency as the Builders intended it. Text: *"The signal endures because someone keeps choosing to transmit."*

---

## 8. Lore Atlas Connection

### How It Works

Every signal the player discovers in Tune-the-Dial corresponds to an entry in the ephergent.com Lore Atlas. The game communicates discoveries to the site via a simple mechanism:

**Unlock codes**: Each signal, when found, displays a short alphanumeric code (8 characters) alongside the lore text. The player can enter this code on ephergent.com/atlas to unlock the corresponding entry. This avoids requiring login/authentication and works within the 15MB constraint (no server communication from the game itself).

**Codes are deterministic, not random** — the same signal always produces the same code. This allows wiki/community sharing (intentional — spreading the lore is thematic).

### What Unlocks Where

| Game discovery | Atlas entry unlocked |
|---|---|
| Each of the 5 frequencies | Frequency overview + signal character + cultural description |
| Each Builder Station signal | Station field guide entry — status, contents, Barry's trail |
| Ephergent Frequency (per character) | Character profile entry — full background, frequency relationship |
| Barry's Pattern | The Wellspring entry — Barry's discovery, the Builders' broadcast, the trail |

### Narrative Breadcrumbs

The lore entries unlocked by Tune-the-Dial are written as if the player is receiving transmissions. The framing: you have found a frequency. Here is what broadcasts on it. The voice of each entry is appropriate to its source — Cogsworth entries are precise and measured, Verdantia entries breathe, The Edge entries are structured chaos.

This positions the player not as a character in the story but as a receiver — someone with a dial, tuning in to a universe that is already broadcasting. You are not in the story. You are hearing it.

---

## 9. UI / Visual Direction

### Aesthetic: Retro Oscilloscope

The visual language is **1970s laboratory equipment**. Think Tektronix oscilloscopes, analog signal generators, cold-war era electronics. The entire UI is rendered as if the player is looking at a piece of physical equipment.

### Color Palette

**Default (Pixel's perspective)**:
- Background: Pure black (#000000)
- Waveform / text: Phosphor green (#00FF41) — classic oscilloscope green
- Grid lines: Dark green (#003300) at 20% opacity
- Signal meter: Green → amber → red gradient
- UI chrome (dial housing, bezels): Dark gunmetal grey (#1A1A1A) with subtle edge highlights

**Per-character palette shifts** (applied as a subtle tint to the waveform, not a full recolor):
- Pixel: Default green
- Meatball: Warm gold shift
- Clive: Cooler blue-green with occasional flicker
- Om Kai: Deep violet tint, lower brightness
- Baron Klaus: Indigo with purple edge
- Nano: Amber/copper, sharper edges on waveform rendering
- Luminara: Emerald with bioluminescent pulse
- Zephyr: Shifting hue (Edge colors) — slow chromatic drift
- A1: White. Pure, clean, no color filter. A1 sees the signal as it is.

### Layout

```
┌──────────────────────────────────────────────────┐
│ ┌──────────────────────────────────┐  [SIGNAL]   │
│ │                                  │  ████░░░░   │
│ │       OSCILLOSCOPE DISPLAY       │  STRENGTH   │
│ │          (waveform area)         │             │
│ │                                  │  ┌───────┐  │
│ │                                  │  │ FREQ  │  │
│ │                                  │  │ DATA  │  │
│ └──────────────────────────────────┘  └───────┘  │
│                                                  │
│  [CREW]     ╭─────────────────╮     [LORE LOG]   │
│  ● Pixel    │    ◄── DIAL ──► │     12/20 found  │
│  ○ Meat     │   ╱           ╲ │                   │
│  ○ Clive    │  (    ●────    ) │                   │
│  ○ ...      │   ╲           ╱ │                   │
│             │    ───────────  │                   │
│             ╰─────────────────╯                   │
└──────────────────────────────────────────────────┘
```

- **Oscilloscope display**: Top 60% of screen. The waveform area. Grid overlay. Scrolling waveform left-to-right or centered.
- **Signal strength meter**: Top-right. Vertical bar meter with LED-style segments.
- **Frequency data readout**: Below meter. Shows numeric frequency value, current dial position as a percentage, and signal name (when locked).
- **The Dial**: Center-bottom. Large, tactile, the primary interaction point. Rendered with physicality — shadow, texture, a notch indicator.
- **Crew roster**: Bottom-left. Vertical column of small circular portraits.
- **Lore log**: Bottom-right. Count of discoveries. Clickable to open the lore journal (full-screen overlay showing all unlocked entries).

### Waveform Rendering

The waveform is rendered as a **single continuous line** drawn left-to-right across the oscilloscope display, with phosphor persistence (fading trail behind the current draw position, like a real CRT oscilloscope). This is achievable in Godot 4 with a Line2D node or custom drawing via `_draw()`.

The phosphor persistence effect: previous frames' waveform fades over 3–5 frames, creating the classic "afterglow" look. This is cosmetically important and computationally cheap (alpha-blended copies of the previous line at decreasing opacity).

### Typography

Monospace throughout. A pixel-friendly monospace font (e.g., IBM Plex Mono, JetBrains Mono, or a custom pixel font at the appropriate size). All text rendered as if displayed on CRT — slight bloom/glow effect on characters.

---

## 10. Technical Constraints

### 15 MB Hard Cap — Budget Breakdown

| Component | Target size | Notes |
|---|---|---|
| Godot 4 HTML5 runtime | ~5 MB | Compressed. Non-negotiable baseline. |
| Game code (GDScript + scenes) | ~500 KB | Minimal scene tree, procedural rendering |
| Audio assets | ~6 MB | **The critical budget item. See below.** |
| Lore text content | ~500 KB | All lore entries as embedded strings |
| UI assets (sprites, fonts) | ~1 MB | Dial graphic, crew portraits (pixel art), font |
| Crew portrait sprites | ~500 KB | 9 small circular portraits, minimal animation |
| Margin / overhead | ~1 MB | Breathing room |
| **Total** | **~15 MB** | |

### Audio Strategy — Keeping Signal Audio Small

Audio is the critical constraint. The game's core experience is auditory — signals must sound distinct, characterful, and evocative. Here is how to achieve that under 6 MB:

#### Procedural Audio (Primary Approach)
The majority of signals should be generated procedurally at runtime using Godot's `AudioStreamGenerator`:

- **Sine waves, square waves, noise generators**: The five frequency signals are fundamentally simple waveforms. Generate them mathematically.
- **Noise modulation**: White noise with parameterized filtering (low-pass for Meatball, band-pass for specific frequencies) generated in real-time.
- **Metronomic clicking** (Cogsworth): Procedurally timed impulse samples. A single "click" sample (~5 KB) played at calculated intervals.
- **Harmonic layering**: Build complex signals by summing simple waveforms at different frequencies and amplitudes. The Edge's "every frequency simultaneously" is literally the sum of the other four signals' procedural generators.

#### Minimal Recorded Audio (Accent Only)
Small recorded samples used for moments that procedural audio can't achieve:

- **Clive's voice fragment**: 3–5 seconds of processed voice audio for the Ephergent Frequency / Clive perspective. Heavily filtered and pitch-shifted, so low bitrate (mono, 22050 Hz, OGG Vorbis) works. Target: ~50 KB.
- **Aether's laugh**: 2–3 seconds of distant, reverbed laughter for Zephyr's perspective. Same compression strategy. Target: ~30 KB.
- **Ambient textures**: A small library of short loopable textures (leaf rustle, stone echo, steam hiss) — 5–8 samples, 1–2 seconds each, mono, 22050 Hz OGG. Target: ~200 KB.
- **Lock chime**: A short confirmation sound when a signal locks. ~10 KB.

#### Audio Budget Summary

| Category | Approach | Size |
|---|---|---|
| 5 frequency signals | 100% procedural | ~0 KB (code only) |
| 7 Builder Station signals | 95% procedural + texture samples | ~100 KB |
| Ephergent Frequency (9 perspectives) | Procedural base + 3–4 recorded accents | ~300 KB |
| Barry Pattern noise modulation | 100% procedural | ~0 KB |
| UI sounds (lock chime, dial click) | Tiny recorded samples | ~50 KB |
| Ambient noise floor | Procedural white/pink noise | ~0 KB |
| **Total audio assets** | | **~450 KB** |

This leaves ~5.5 MB of the audio budget unused, providing substantial margin for iteration. If procedural audio proves insufficient for some signals during development, there is room to add recorded elements.

### Godot 4 HTML5 Implementation Notes

- **AudioStreamGenerator** for procedural audio: Godot 4 supports real-time audio generation via `AudioStreamGenerator` and `AudioStreamGeneratorPlayback`. Fill the buffer each frame with calculated samples. This is the core audio engine.
- **Rendering**: All waveform rendering via Godot's `CanvasItem._draw()` or `Line2D`. No 3D. No shaders required (though a simple CRT bloom shader for the phosphor glow effect is cheap and impactful — a fragment shader under 50 lines).
- **Input**: Mouse drag, touch drag, keyboard arrows. Godot 4's InputEvent system handles all three natively.
- **State persistence**: Use `JavaScriptBridge.eval()` to write to browser `localStorage` for save state (which signals have been found, which perspectives have been heard). This persists across sessions without server infrastructure.
- **Export settings**: Strip unused modules. Disable 3D renderer. Disable physics engine. This significantly reduces the HTML5 export size.

---

## 11. Narrative Integration

### Timeline Placement

Tune-the-Dial exists **outside the show's timeline**. The player is not a character in the story. They are someone with a dial — a listener, a receiver, tuning in to a universe that is already broadcasting. The game never breaks this frame. There is no "you are Pixel" or "you are on the ship." You are at a desk, with an oscilloscope, finding signals.

This positions the game as a **transmission from the Ephergent universe to ours** — consistent with the project's framing that the ephergent.com site and its games are the crew's broadcast reaching our frequency.

### Connection to Season 1

The five frequency signals and the early Builder Station signals (11-Quiescent, 3-Resonant) correspond to Season 1 content. Finding these signals gives the player lore that parallels S01's narrative: the crew forming, the first encounter with Builder architecture, the first hints that something is wrong with the frequencies.

The Barry Pattern connects to Season 1 specifically through Clive.

### Clive's Dialogue — The Trigger

When the player finds the Barry Pattern, the following sequence plays:

1. The noise-writing resolves: *"C — the trail is intact. Follow the thermos. — B"*
2. A brief pause. The oscilloscope flickers.
3. Text appears in a different style — not the game's UI font but something that reads as Clive's measured, precise speech pattern:

> *"...I know this handwriting."*
>
> *"He encoded it in the noise. Of course he did. Twenty-three years of nightshifts and he learned to write in static."*
>
> *[pause]*
>
> *"The trail is intact. He's been there this whole time. Waiting."*
>
> *[longer pause]*
>
> *"...I need to tell the Captain."*

In Season 1, this dialogue appears in **S01E09** — the episode where the crew passes Station 11-Quiescent. Clive says this line, or a version of it, seemingly in response to something the crew doesn't understand. It reads as flavor text — Clive being enigmatic, as he often is. The audience files it away.

By Season 3, when the crew reaches the Wellspring and finds Barry, this moment is recontextualized: Clive had already confirmed the trail was intact. He knew. Not because of anything the crew did in the show — because someone out here, on our frequency, found the signal in a game and Clive heard it. The game is not supplementary to the story. The game is where Clive got the information.

This connection is **never stated explicitly** in the show. It is there for the audience members who played the game. For everyone else, S01E09's moment works as character texture. For players, it is a revelation.

### Clive's Perspective — The Subtle Hint

When the player selects Clive as their character perspective and tunes near (but not on) the Barry Pattern's location, the ambient static contains a barely perceptible change: a warmth. Not a signal. Not a direction. Just a faint, almost-imagined quality in the noise that suggests something is there. Clive's frequency sensitivity — inherited from the Builders — gives the player the smallest possible nudge toward the hidden pattern.

This is not an arrow or a highlight. It is a feeling, translated into audio. If the player notices it and investigates, they are doing what Clive does: following a half-remembered recognition toward something he doesn't yet understand.

---

## Appendix A: Signal Map (Developer Reference)

The dial's 1000 positions should distribute signals as follows (exact positions randomized per playthrough within the noted ranges):

| Signal | Dial range | Band width | Strength |
|---|---|---|---|
| Freq 1 — Prime Material | 050–100 | 15 positions | Strong |
| Freq 2 — Nocturne | 180–230 | 15 positions | Strong |
| Freq 3 — Cogsworth | 320–370 | 15 positions | Strong |
| Freq 4 — Verdantia | 480–530 | 15 positions | Strong |
| Freq 5 — The Edge | 650–700 | 15 positions | Strong |
| Station 11-Quiescent | 140–160 | 8 positions | Weak |
| Station 3-Resonant | 250–280 | 8 positions | Weak |
| Station 5-Meridian | 400–430 | 8 positions | Weak |
| Station 7-Ascending | 600–630 | 8 positions | Medium |
| Station 9-Liminal | 730–760 | 8 positions | Weak |
| Station 14-Threshold | 820–850 | 8 positions | Medium |
| The Wellspring (0-Origin) | 900–930 | 8 positions | Strong (hidden until Barry Pattern found) |
| Ephergent Frequency | 550–580 | 5 positions | Variable (perspective-dependent) |
| Barry's Pattern | 775–810 | 3 positions | Zero (meter doesn't respond) |

Gaps between signals are intentional — they are the noise, the static, the Space between stations. Most of the dial is nothing. This is accurate to the universe: most of the Space is void.

## Appendix B: Procedural Audio Reference

### Core Generator Functions (Pseudocode)

```
# Sine wave (Prime Material base)
func sine_signal(freq_hz, t):
    return sin(2 * PI * freq_hz * t)

# Square wave (Cogsworth base)
func square_signal(freq_hz, t):
    return sign(sin(2 * PI * freq_hz * t))

# Breathing wave (Verdantia base)
func organic_signal(freq_hz, t):
    base = sin(2 * PI * freq_hz * t)
    breath = sin(2 * PI * 0.15 * t)  # ~0.15 Hz breathing rate
    return base * (0.6 + 0.4 * breath)

# Cello harmonic (Nocturne base)
func cello_signal(freq_hz, t):
    h1 = sin(2 * PI * freq_hz * t)
    h2 = 0.5 * sin(2 * PI * freq_hz * 2 * t)
    h3 = 0.25 * sin(2 * PI * freq_hz * 3 * t)
    return (h1 + h2 + h3) / 1.75

# Chaos (The Edge base)
func chaos_signal(t, other_signals):
    sum = 0
    for sig in other_signals:
        sum += sig.evaluate(t) * rand_range(0.1, 0.4)
    return sum + white_noise() * 0.3

# Noise floor
func noise_floor(t, character_mod):
    base = white_noise() * 0.1
    return base * character_mod.noise_multiplier

# Barry Pattern (hidden amplitude modulation)
func barry_pattern(t, noise):
    pulse = sin(2 * PI * 3.0 * t)  # 3 Hz pulse
    modulation = 1.0 + 0.08 * pulse  # 8% amplitude mod — barely perceptible
    return noise * modulation
```

### Signal Mixing

At any dial position, the audio output is:
```
output = noise_floor(t) * (1 - signal_strength) + signal(t) * signal_strength
```

Where `signal_strength` is 0.0 (pure noise) to 1.0 (pure signal), determined by proximity to the nearest signal's center position.

---

*This document is part of The Ephergent Project game pipeline. For related documents, see: [GRAND_MASTER_PLAN.md](../GRAND_MASTER_PLAN.md) · [frequency_system.md](../phase_01_world/frequency_system.md) · [builder_stations_field_guide.md](../phase_01_world/builder_stations_field_guide.md)*

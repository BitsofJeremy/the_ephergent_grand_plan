# STATIC RUN — Game Design Bible

**Game 3 in The Ephergent Pipeline**  
**Status**: Pre-production  
**Character**: Nano  
**Genre**: Endless Runner  
**Engine**: Phaser.js (recommended — see §10)  
**Size Constraint**: 15MB hard cap  

---

## 1. Overview

Static Run is an endless runner set in the Space between frequencies. The player controls Nano — engineer, speedster, the only person who can outrun the machines she builds — as she sprints through collapsing interstitial corridors while entropy fragments chase her.

The game is about how long, not whether.

You can always outrun them. The entropy fragments will never catch Nano if the player keeps moving. There is no death by catching. There is death by obstacle — by losing momentum, by hesitating, by slowing down long enough that the corridor collapses around you. The fragments are the pressure. The obstacles are the threat. Speed is the answer, and Nano has always known this.

The game works as a standalone arcade experience: pick up, run, score, repeat. Underneath, for the obsessive, there is a secret — torn pages from Barry's notebook, carried by entropy fragments, readable only if you slow down just enough. The complete text, collected across many runs, spells out a coordinate. Finding it is optional. Finding it changes what the running means.

---

## 2. Character: Nano

### Who She Is

Nano is from Cogsworth Cogitarium — Frequency 3. Clockwork world. Brass and copper and gears the size of buildings. Cogsworth produces precise engineers who work slowly, methodically, with micron-level tolerance. Nano understood precision. She also understood something her home frequency couldn't accommodate: entropy doesn't wait.

She left because she could not slow down, and Cogsworth could not speed up.

### How She Moves

Nano does not walk. Walking is what you do when you've given up on arriving in time. In-game, she runs with a forward lean, copper-red hair flattened back, jumpsuit pockets rattling with tools. Her animation should feel like a frame from a film running slightly faster than the projector intended — kinetic, barely contained.

**Idle state** (pre-run, menu): She vibrates. Shifts weight foot to foot. Turns a small component in her fingers. She cannot be still.

**Running state**: Compact, efficient stride. Arms pump close to the body. Boots hit hard — reinforced soles, designed for this. As speed escalates, her form tightens. She doesn't flail. She gets more precise.

**Death state**: Not a collapse. A stutter — like a film splice. She stops, the corridor closes, static consumes the frame. Quick. No drama. Nano wouldn't want drama.

### What She Says

Nano talks fast, incomplete sentences, mid-thought. The game uses minimal text, but what exists follows her voice:

- Run start: *"— right, going —"*
- Speed milestone: *"Faster. Good. Keep it —"*
- Near miss: *"— three centimeters, recalibrating —"*
- Barry fragment spotted: *"...wait. That's not — that's not entropy."*
- Death: *"— insufficient."* (spoken matter-of-factly, not defeated)

---

## 3. Core Mechanic

### Controls

**Two-button game.** Designed for mobile tap and keyboard alike.

| Input | Action |
|---|---|
| Tap / Spacebar / Up | Jump (tap = short hop, hold = full jump) |
| Swipe Down / Down Arrow / S | Slide (ducks under overhead obstacles) |

Nano runs automatically. The player does not control horizontal speed — speed escalates on a fixed curve. The player controls vertical positioning: jump or slide to avoid obstacles.

**No lateral movement.** This is a single-lane runner. Simplicity is the point. The complexity is in timing, not in choice paralysis.

### Speed Escalation

Speed increases on a logarithmic curve — fast gains early, diminishing increases over time, approaching but never reaching a theoretical maximum.

| Phase | Time | Speed | Feel |
|---|---|---|---|
| **Warm-up** | 0–15s | 1.0x–1.5x | Comfortable. Learn the controls. |
| **Jog** | 15–45s | 1.5x–2.5x | Obstacles appear more frequently. |
| **Sprint** | 45–90s | 2.5x–4.0x | Reaction windows tighten. This is where most runs end. |
| **Overdrive** | 90–180s | 4.0x–5.5x | Expert territory. Obstacles layer. |
| **Redline** | 180s+ | 5.5x–6.5x (cap) | The game at its fastest. Survival here is the high score. |

The speed curve is tuned so that a skilled player's average run lasts 60–90 seconds. Exceptional runs exceed 3 minutes. The leaderboard tail stretches toward 5+.

### Scoring

- **Primary score**: Distance (meters). Clean and comparable.
- **Bonus**: Near-miss multiplier. Clearing an obstacle with <10px margin grants a 1.1x multiplier for the next 3 seconds. Stacks up to 1.5x. Rewards precision — Cogsworth would approve.
- **No coins.** No collectibles littering the track. The run is clean. The only collectible is Barry's fragments, and those are rare.

### Obstacle Types

Obstacles are generated procedurally within hand-designed pattern templates. Templates are selected based on current speed phase and weighted for variety.

| Obstacle | Action | Visual |
|---|---|---|
| **Static Wall** | Jump | A vertical band of dense static, waist-high. Solid. Brass frame corroded by entropy. |
| **Overhang** | Slide | A drooping section of corridor ceiling. Clockwork gears frozen mid-rotation, hanging low. |
| **Gap** | Jump (long) | The corridor floor drops away. Empty static below. Requires a held jump. |
| **Double** | Jump then slide (or vice versa) | Two obstacles in rapid sequence. Tests reaction chaining. Appears from Sprint phase onward. |
| **Stutter** | Timing | The corridor visually glitches — a frame skip. The next obstacle arrives 0.2s earlier than the rhythm suggests. Disrupts pattern recognition. Appears from Overdrive onward. |

---

## 4. Entropy Fragment Types

Entropy fragments occupy the background, chasing Nano from behind. They are not obstacles — they are atmosphere and pressure. The player cannot interact with them except for one special type (§5). They fill the space behind Nano, and if she stops, they fill the space she's in.

### Fragment Behaviors

**Chasers** — The baseline. Amorphous static shapes that tumble forward in Nano's wake. They maintain a fixed distance behind her; as speed increases, they crowd closer but never overtake. They are the visual representation of "you must keep moving." Rendered as smeared pixel clusters, trailing static artifacts like a corrupted video signal.

**Blockers** — Stationary entropy formations that appear in the corridor. Not obstacles the player dodges — these are background elements that narrow the visual corridor, increasing claustrophobia. As the run progresses, more blockers appear, making the corridor feel tighter even though the playable lane doesn't change. Dark, dense, gear-shaped but broken — Cogsworth machinery consumed by the Drift.

**Pattern Fragments** — Rare. These move in recognizable patterns: sine waves, figure-eights, spirals. They are entropy that hasn't fully decohered — remnants of the frequencies they consumed, still carrying the ghost of structure. They appear beautiful and wrong simultaneously. Rendered with faint color traces: a blue shimmer (Luminara's frequency), a green pulse (Verdania), amber glow (Cogsworth). These are the Drift in miniature — the thing Nano is running from is made of the things she's running to protect.

**Swarm Fragments** — Appear during Overdrive and Redline phases. Dozens of tiny fragments that behave like a murmuration — flocking, splitting, reforming. They fill the upper or lower portion of the corridor, creating visual noise that makes reading obstacles harder. Not a direct threat. A distraction. Entropy doesn't just chase you; it tries to make you lose focus.

### Visual Design Direction

All entropy fragments share a visual language:

- **Base**: Pixel noise. Static. The thing you see when a signal fails.
- **Color**: Predominantly greyscale with desaturated color bleeds. The colors come from consumed frequencies — entropy carries the ghost of what it's eaten.
- **Motion**: Jittery. Frame-skipping. They don't move smoothly; they stutter between positions like a buffering stream. This contrasts with Nano's smooth, precise movement.
- **Edge treatment**: No clean edges. Fragments bleed into the background. They are the background asserting itself into the foreground.

### What They Represent

The entropy fragments are the Drift made visible. In the larger Ephergent universe, the Drift is the slow desynchronization of all frequencies — the thing the Builder Stations were meant to prevent, the thing Barry spent twenty-three years trying to understand. In Static Run, the Drift is not a concept. It is the thing behind you. It is always there. It is always gaining, not because it's faster than you, but because it doesn't need to be. It just needs to be patient.

Nano can outrun it. She always can. But outrunning is not solving, and somewhere in the static behind her, there might be a message from the one person who tried to solve it.

---

## 5. Barry's Notebook Page Easter Egg

### The Mechanic

One entropy fragment, encountered rarely, does not look like entropy. It looks like a torn page from a notebook — cream-colored, with handwritten text, edges singed by static. It appears among the chasers behind Nano, tumbling with the rest, but visually distinct: warmer, lighter, recognizably paper.

**Trigger**: The fragment has a ~3% chance of appearing per run, checked once per run at a random point between 30s and 120s into the run. It appears behind Nano, slightly closer than the other chasers.

**Default behavior**: If the player does nothing special, the fragment tumbles past and is consumed by the static behind. Gone. No penalty. Most players won't notice it on early runs.

**Special interaction**: If the player maintains current speed without jumping or sliding for 2.5 seconds after the fragment appears (running alongside it), the fragment drifts forward to Nano's position. It slows. It steadies. For 1.5 seconds, a few words of handwritten text become legible on the page before it dissolves into static.

This is the tension: running alongside means you cannot dodge obstacles for 2.5 seconds. The game does not pause obstacle generation. The player must judge whether the corridor ahead is clear enough to risk it. Sometimes it isn't. Sometimes the page appears right before a wall, and you have to choose: the page or the run.

### The Fragments

There are **23 unique notebook page fragments** — one for each year Barry searched.

Each fragment contains a short phrase in Barry's handwriting. The phrases are cryptic in isolation but form a coherent message when assembled. The player does not know how many fragments exist or what order they belong in.

**Fragment texts** (in canonical order, though the player encounters them randomly):

| # | Text | Note |
|---|---|---|
| 1 | *"The stations were never"* | — |
| 2 | *"separate. They were"* | — |
| 3 | *"one instrument."* | — |
| 4 | *"I traced the resonance"* | — |
| 5 | *"pattern back to"* | — |
| 6 | *"its origin point."* | — |
| 7 | *"Not a place."* | — |
| 8 | *"A frequency."* | — |
| 9 | *"Bearing:"* | First coordinate element |
| 10 | *"7"* | — |
| 11 | *"7"* | — |
| 12 | *"."* | — |
| 13 | *"3"* | — |
| 14 | *"Resonance:"* | Second coordinate element |
| 15 | *"1"* | — |
| 16 | *"1"* | — |
| 17 | *"9"* | — |
| 18 | *"."* | — |
| 19 | *"4"* | — |
| 20 | *"If you are reading this"* | — |
| 21 | *"you are fast enough"* | — |
| 22 | *"to matter."* | — |
| 23 | *"— B."* | Barry's sign-off |

**The complete message**: *"The stations were never separate. They were one instrument. I traced the resonance pattern back to its origin point. Not a place. A frequency. Bearing: 77.3 Resonance: 119.4 If you are reading this you are fast enough to matter. — B."*

**The coordinate** — Bearing 77.3, Resonance 119.4 — is a Builder-era navigation format. It points to a location in the Space between frequencies: the Wellspring. This coordinate appears nowhere else in The Ephergent's public-facing content. Static Run is the only place it exists. Players who complete the collection have discovered something that connects to Season 2's narrative and the larger mystery of Barry's search.

### Collection System

- Fragments are tracked in localStorage (browser) or save file (GB Studio).
- The collection screen is accessed from the main menu: a visual notebook page, torn and reassembled, with collected fragments appearing in their canonical positions and missing fragments shown as static smears.
- Duplicate fragments can appear. Collecting a duplicate shows the same text — no penalty, no reward. The game does not tell you it's a duplicate until you see the collection screen unchanged.
- **No hint system.** The game does not tell you how many fragments exist, how many you've found, or that a coordinate is forming. The player discovers the pattern or they don't.

---

## 6. The Philosophy

*"The game is about how long, not whether."*

### What This Means Mechanically

There is no winning. There is no final level, no boss, no ending screen that says "Congratulations." The run always ends. Entropy always catches up — not because it's faster, but because the corridor is finite and your attention is finite and eventually you'll clip a wall or miss a slide and the static will close in.

The game asks: how long can you keep going? And then it asks: is "how long" the right question?

### What This Means for Nano

Nano's entire character is built on speed as survival strategy. She runs because if she stops, she'll see how much has already been lost. Cogsworth's Grand Orrery is desynchronizing. The frequencies are drifting apart. Entropy is winning the long game, and Nano's answer is to be faster than the long game.

Static Run is Nano's psyche made playable. The endless corridor is her worldview: keep moving, don't stop, don't look back. The entropy fragments are the thing she knows is true but won't examine — that speed without direction is just elaborate avoidance.

### What This Means for The Ephergent

The series' central theme: entropy is not the enemy. The Drift is not a disease to cure. It is the natural state of a universe in motion, and the answer is not to outrun it but to find the frequency that harmonizes with it.

Static Run embodies the question before the answer. Nano hasn't learned this yet. The player, running, hasn't learned it either. But Barry's notebook pages — the ones you can only read by slowing down — are the first whisper of it. The coordinate they spell out points to the Wellspring, which is the answer. But you can only find the answer by doing the thing Nano is afraid of: not stopping, but running alongside instead of away.

The mechanic IS the theme. Running alongside the entropy fragment is mechanically identical to slowing down — you sacrifice evasion time, you accept risk. But narratively, you are choosing to match entropy's pace instead of fleeing it. This is the lesson Nano learns by Season 3. The game teaches it to the player first.

---

## 7. Visual Direction

### The Corridor

The run takes place in the Space between frequencies — the interstitial void the Ephergent traverses. This is not a physical place. It is the absence of frequency, rendered as a collapsing corridor.

**Aesthetic**: Cogsworth-adjacent. The corridor's structure evokes clockwork architecture — brass-colored beams, gear-tooth patterns in the walls, mechanical ribbing overhead — but decayed. Corroded. Frozen mid-rotation. This is what Cogsworth's precision looks like when entropy has had its way with it. The beautiful machinery of a Builder Station, rotting in the space between.

**Color palette**:
- **Corridor**: Deep bronze, tarnished brass, oxidized copper greens. Warm metallics gone cold.
- **Background**: Black with static grain. The void is not empty; it fizzes.
- **Nano**: Warm amber highlights (her eyes, her hair, tool glints). She is the brightest thing on screen.
- **Entropy**: Greyscale with desaturated color bleeds. Cold against the warm corridor.

**Parallax**: Three layers minimum.
1. **Foreground**: The playable corridor floor and immediate obstacles. Sharp, readable.
2. **Midground**: Corridor walls, structural elements, blockers. Slightly darker, slight motion blur at high speeds.
3. **Background**: The void. Static. Entropy swarms. Deep parallax, slow scroll. This layer never changes speed — the void doesn't care how fast you run.

### Nano's Sprite

Pixel art. Small — 32x32 or 48x48 maximum. She reads as: compact figure, copper-red hair, amber eye-glint, dark jumpsuit, heavy boots. Her silhouette is distinctive even at speed: the forward lean, the close-pumping arms, the hair blown back.

**Animation frames**:
- Run cycle: 6–8 frames. Snappy, not fluid — she's mechanical in her precision.
- Jump: 3 frames (launch, apex, land). Tight. No hang time.
- Slide: 3 frames (drop, slide, recover). Low, fast, boots-first.
- Death: 2 frames (stutter, static). Abrupt.

### Entropy Fragment Visuals

Rendered as pixel-noise clusters with distinct silhouettes per type:
- **Chasers**: Amorphous blobs, trailing static tails. Jittery movement.
- **Blockers**: Angular, gear-shaped. Recognizably mechanical but broken.
- **Pattern Fragments**: Smooth curves, faint color traces. The most "beautiful" fragments.
- **Swarm**: Individual fragments are 4x4 pixel dots. Collective movement creates the visual.
- **Barry's Page**: Cream rectangle, visible handwriting scrawl, singed edges. Unmistakably different from everything else on screen. Warm. Paper-like. Wrong, in a way that draws the eye.

### Resolution

Target: 320x180 native resolution, scaled up. This gives a clean pixel-art aesthetic while keeping asset sizes minimal. At 4x scale, renders at 1280x720 for desktop.

---

## 8. Audio Direction

### Music

**Approach**: Single procedural music track that responds to speed phase.

- **Warm-up**: Minimal. A ticking clock — Cogsworth's heartbeat. Steady, mechanical, metronomic. Quarter notes. Simple.
- **Jog**: The clock gains layers. A bass pulse joins. Syncopation enters. The tick becomes a rhythm.
- **Sprint**: Full driving beat. Electronic, mechanical, relentless. Think: a clockwork mechanism running at double speed. The precision is still there but the urgency has overtaken it.
- **Overdrive**: The beat distorts slightly. The clock-tick is still audible underneath but the layers are compressing. Static crackle enters the mix as a percussive element.
- **Redline**: Maximum intensity. The music and the static are nearly indistinguishable. The ticking is frantic. The player should feel the music pushing them.

**Key constraint**: One continuous track with intensity layers, not separate tracks per phase. This keeps file size minimal and avoids audible transitions. Cross-fade between layers is handled by the engine.

**Size budget**: ~800KB for music (compressed OGG, layered stems).

### Sound Effects

Minimal, precise, mechanical. Every sound should feel like it comes from Cogsworth.

| Sound | Description | Size Est. |
|---|---|---|
| **Footsteps** | Metallic taps. Quick, regular, pitch-shifting up with speed. | 20KB |
| **Jump** | A spring-loaded click. Mechanical. Not a "boing" — a calibrated release. | 10KB |
| **Slide** | Metal on metal. A brief grinding hiss. | 10KB |
| **Obstacle near-miss** | A sharp harmonic ping. Like flicking a tuning fork. Satisfying. | 8KB |
| **Death** | A mechanical failure sound — gears catching, a desynchronization crunch, then silence. | 15KB |
| **Entropy ambient** | Low static hiss. Constant. Increases in volume as fragments crowd closer. | 30KB (looped) |
| **Barry's page appear** | A warmth. A different texture. Like a radio finding a signal between stations. Brief, unmistakable. | 12KB |
| **Barry's page reading** | The static drops. Near-silence. A faint mechanical ticking — slower than the music. Intimate. | 15KB |

**Total SFX budget**: ~120KB

---

## 9. Progression System

### High Scores

- **Local leaderboard**: Top 10 runs stored in localStorage. Distance + date.
- **Personal best**: Prominently displayed on the main menu. This is the number to beat.
- **No online leaderboard.** The game is free, browser-based, and light. An online leaderboard adds server infrastructure, moderation burden, and scope. The game doesn't need it. Your competition is yourself.

### Speed Phase Badges

On first reaching each speed phase, the player earns a badge displayed on the main menu. Five badges total: Warm-up (automatic), Jog, Sprint, Overdrive, Redline. These serve as soft progression markers — "you have reached this level of skill."

### Barry's Collection

The notebook page collection (§5) is the only persistent cross-session progression. It is accessed from the main menu as "NOTEBOOK" — initially appearing as a blank, torn page. As fragments are collected, handwritten text fills in.

The collection screen does not sort fragments by order of discovery. It assembles them in canonical order. The player sees the message forming, with gaps, over time. This creates a puzzle-adjacent experience: *what are the missing words?*

**Completion reward**: When all 23 fragments are collected, the notebook page is complete. The coordinate pulses faintly. Tapping/clicking the coordinate triggers a brief sequence:

1. The screen fills with static.
2. The static resolves into a Builder-era navigation display.
3. The coordinate appears: **Bearing 77.3 / Resonance 119.4**
4. Text, in Nano's voice: *"— that's not random. That's a location. Barry, you absolute — that's the Wellspring."*
5. The display fades. The main menu returns. The notebook now has a small gear icon in the corner — Cogsworth's mark. Permanent.

This is a narrative reward. It connects to Season 2 of The Ephergent. It gives completionists a piece of lore that no other game, transmission, or episode provides. The coordinate is real within the fiction. Nano is the one who finds it, and the player is the reason she can.

### Unlockables

Minimal. The game is about the run, not about unlocking things. Two optional visual unlocks:

1. **Cogsworth Trail** (reach Overdrive): Nano leaves faint gear-tooth impressions in the corridor floor behind her as she runs. Cosmetic only.
2. **Entropy Echo** (reach Redline): After death, a brief replay shows the last 5 seconds of the run from the entropy fragments' perspective — the corridor rushing toward the camera, Nano a small bright figure ahead. A reversal. Cosmetic only.

---

## 10. Technical Constraints

### 15MB Hard Cap

All Ephergent games must be browser-playable and under 15MB. Static Run, as the simplest game in the pipeline, should target well under this.

### Engine Recommendation: Phaser.js

**Phaser.js is recommended over GB Studio.** Rationale:

| Factor | Phaser.js | GB Studio |
|---|---|---|
| **Output size** | ~500KB framework + assets. Total easily under 5MB. | ROM output is small, but the web player adds overhead. ~2–3MB minimum. |
| **Endless runner support** | Native. Procedural generation, parallax scrolling, physics — all built-in or trivial to implement. | Possible but against the grain. GB Studio is scene-based, not designed for infinite scrolling. Workarounds required. |
| **Procedural content** | Full JavaScript. Generate obstacle patterns, fragment spawns, and speed curves in code. | Limited scripting. Procedural generation is constrained by the GBVM scripting engine. |
| **Audio layering** | Web Audio API. Layer stems, cross-fade, respond to game state. Straightforward. | 4-channel audio. Authentic but severely limited. No dynamic layering. |
| **Barry's page mechanic** | Trivial. Render text on a sprite, animate opacity, track collection in localStorage. | Complex. Text rendering is dialogue-box-based. Custom text-on-sprite would require significant workarounds. |
| **Mobile support** | Touch input native. Responsive canvas. Works on phones without modification. | Designed for gamepad/keyboard. Touch requires additional wrapper. |
| **Developer familiarity** | JavaScript/TypeScript. Standard web development. | Proprietary IDE + GBVM. Learning curve for the specific toolchain. |

GB Studio's charm is its aesthetic — Game Boy authenticity. But Static Run's visual direction (Cogsworth brass, colored entropy fragments, parallax void) exceeds the Game Boy's palette and resolution constraints. Phaser gives us the aesthetic we need at the size we need.

### Size Budget Breakdown

| Component | Estimated Size |
|---|---|
| **Phaser.js framework** (minified) | 500KB |
| **Game code** (minified) | 80KB |
| **Sprite sheets** (Nano, obstacles, fragments) | 200KB |
| **Tileset** (corridor, parallax layers) | 150KB |
| **Music** (layered OGG stems) | 800KB |
| **Sound effects** | 120KB |
| **Fonts** (1 pixel font, 1 handwriting font for Barry) | 50KB |
| **UI assets** (menu, badges, notebook screen) | 100KB |
| **Total** | **~2MB** |

Under 15MB by a wide margin. This leaves room for polish, additional visual effects, or higher-resolution assets if desired. The game should ship lean.

### Hosting

Static files. Deploy alongside the Ephergent site (Astro 5 + Tailwind 3). The game loads in an `<iframe>` or a dedicated route. No server-side logic. All state is client-side localStorage.

---

## 11. Lore Connection

### Where Static Run Sits in The Ephergent

Static Run is Game 3 of three games in the Ephergent pipeline. Each game maps to a crew member and a narrative thread:

1. **Meatball's Big Walk** — Cozy point-and-click. Meatball. Barry's coffee mug. *"Smells like: looking for something."*
2. **Tune-the-Dial** — Frequency puzzle. The Ephergent Frequency. Barry's hidden frequency signature. Clive's confirmation.
3. **Static Run** — Endless runner. Nano. Barry's notebook pages. The coordinate.

Together, the three games form a scavenger hunt across formats. Each contributes a piece of Barry's trail:
- Meatball's Big Walk: The emotional trace. Barry was here. He was looking.
- Tune-the-Dial: The signal. Barry left a frequency. Clive recognized it.
- Static Run: The location. Barry encoded where to go. Nano decoded it by running.

### What the Coordinate Unlocks

**Bearing 77.3 / Resonance 119.4** — the Wellspring's location in Builder-era navigation. This information feeds into Season 2's narrative:

- Players who complete Static Run's collection before Season 2 airs will recognize the coordinate when Nano delivers it to the crew in-episode. They knew before the characters did.
- The Ephergent site (phase_07) will include a hidden input field — visually buried, not advertised — where entering the coordinate unlocks a lore page about the Wellspring. This page contains information not available in any episode: Builder-era technical specifications, the original purpose of the frequency network, and a message from Barry to whoever found his trail.

### The Thematic Bridge

Static Run teaches the player the lesson Nano learns across three seasons: speed is necessary but insufficient. You can outrun entropy. You cannot out-speed understanding. The notebook pages require patience from a game about velocity. The coordinate requires collection from a game about single runs. The answer is in the running, but only if you're paying attention to what you're running past.

Nano's game is the one that asks: what if the thing chasing you is carrying the thing you need?

---

## Appendix A: Development Priority

**Phase 1 — Core loop** (MVP):
- Nano runs. Obstacles appear. Speed escalates. Death happens. Score records.
- This is a playable game. Ship it.

**Phase 2 — Polish**:
- Entropy fragments (visual only, background).
- Parallax corridor.
- Music layers.
- Speed phase badges.

**Phase 3 — Barry's Pages**:
- Fragment appearance system.
- Alongside-running mechanic.
- Collection screen.
- Coordinate completion sequence.

**Phase 4 — Integration**:
- Deploy to Ephergent site.
- Connect coordinate unlock to site's hidden lore page.
- Test cross-session persistence.

Each phase produces a shippable increment. Phase 1 is the game. Everything after is depth.

---

## Appendix B: Key Reference Quotes

From the Grand Master Plan:
> *"Run. Entropy fragments chase you. You can always outrun them. The game is about how long, not whether."*

From Nano's character bible:
> *"She is precise AND fast. This is unusual for Cogsworth Cogitarium."*

> *"Walking is what you do when you've given up on arriving in time."*

> *"Her central tension: she can outrun the entropy that chases everything, but she cannot outrun the question of what she's running toward."*

> *"Nano's game is the one that requires patience from a character defined by speed. Finding Barry's trail means slowing down just enough to read what entropy is carrying."*

---

*Static Run. Nano runs. The entropy follows. Somewhere in the static, there's a page with your name on it. You just have to be fast enough to find it and patient enough to read it.*

*— right, going —*

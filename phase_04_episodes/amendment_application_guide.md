# Amendment Application Guide

## The Ephergent Project | Phase 4 — Mechanical Amendment Instructions

*For use by LLM agents or human editors applying amendments to the 37 existing episodes.*

**Source documents:**
- Amendment Log: `phase_04_episodes/amendment_log.md`
- Locked Rules: `GRAND_MASTER_PLAN.md` lines 607–625
- Character Bibles: `phase_02_characters/`
- Episode files: `source_archive/rebuild/ephergent_stories/`

---

# Part 1: Global Find-and-Replace Patterns

These seven Common Amendments (CA-1 through CA-7) apply to **every existing episode**. Execute them in order — CA-1 first (most complex), then CA-2 through CA-7 (progressively simpler).

---

## CA-1: Clive — Stapler → Robot

**Locked Rule**: *"Clive is a knee-high robot with a glowing sphere head and a fedora — not a stapler."*

**Affected episodes** (16): S01E01, S01E04, S01E05, S01E06, S01E07, S01E08, S01E09, S01E13, S02E03, S02E05, S03E01, S03E02, S03E03, S03E07, S03E11, S03E12

### 1A: Simple Term Replacements

These regex patterns handle straightforward swaps. Apply case-insensitively where noted.

| Search Pattern (regex) | Replacement | Notes |
|------------------------|-------------|-------|
| `\bstapler\b` | `robot` | Context-dependent — see 1B below |
| `\bSwingline\b` | *(delete entire phrase containing it)* | No Swingline equivalent exists |
| `\bbinding fluid\b` | `coolant` or `internal fluid` | Rare — check context |

### 1B: Context-Dependent Replacements

These cannot be done with simple find-replace. Each requires reading the surrounding sentence.

#### Identity/Description References

**Pattern**: Clive described AS a stapler.

| Original Text (example) | Replacement |
|--------------------------|-------------|
| "My stapler, Clive — ancient orange Swingline, been at that desk since before I was born" (S01E01 line 22) | "My desk companion, Clive — a knee-high robot with a glowing sphere for a head and a battered fedora, been at that desk since before I was born" |
| "sentient stapler" (S01E03, S01E04, S03E02, S03E07, S03E11) | "knee-high robot" or "small robot" — match the register of the surrounding prose |
| "ancient orange Swingline" | "ancient Builder-alloy robot" or remove entirely — replace with patina/bronze/weathered description |
| "a stapler and a barrel-chested detective" (S03E02) | "a small robot and a barrel-chested detective" |
| "for a stapler" (S03E11) | "for a robot his size" |
| "staplers don't cry" (S03E11) | "robots don't cry" |
| "Clive — her orange Swingline stapler" (S01E01 line 32) | "Clive — a knee-high robot of ancient bronze alloy, his glowing sphere head topped with a weathered fedora" |

**Rule**: Every time the word "stapler" appears within 50 words of "Clive," it MUST be replaced. No exceptions.

#### Communication Method Replacements

**Pattern**: Clive communicates via staple patterns / firing staples.

This is the most complex replacement. Clive's canonical communication methods are:
1. **Light patterns** from his glowing sphere head (primary)
2. **Fedora adjustments** (emotional emphasis)
3. **Glow changes** — brightening, dimming, color shifts (blue-white normal; warm flickers during memory)
4. **Chest core pulses** — heartbeat rhythm changes
5. **Verbal speech** — Clive CAN speak; he has a gravelly, laconic voice

| Original Pattern | Replacement |
|------------------|-------------|
| "Clive staples: *MESSAGE*" | "Clive's sphere head pulsed: *MESSAGE*" or simply use dialogue: Clive said, "MESSAGE" |
| "Clive staples slowly, deliberately, into the console surface" (S01E01 line 78) | "Clive's sphere dimmed, then pulsed slowly, deliberately" |
| "staple patterns" (as communication) | "light patterns" or "glow patterns" |
| "staple-pattern poetry" / "staple-pattern cipher" (S03E07, S03E12) | "light-pattern poetry" / "glow-pattern cipher" |
| "Clive staples: *BROADCAST. SOMEONE MIGHT HEAR.*" (S01E01 line 112) | "Clive's glow brightened: *BROADCAST. SOMEONE MIGHT HEAR.*" — or use dialogue |
| "staple pattern embedded in the lattice" (S03E02) | "glow pattern embedded in the lattice" or "light-pattern signature burned into the lattice" |
| "Clive staples a terse observation" (S01E03) | "Clive's sphere flashed a terse observation" or "Clive said flatly," |
| "His staple patterns near Meridian-7 spell out..." (S03E04) | "His light-pattern signature near Meridian-7 traces out..." |
| "staple patterns that evening spell out Barry's name, over and over" (S03E02) | "his glow that evening pulsed Barry's name, over and over" |

**Rule**: Wherever Clive "staples" as a verb, replace with either (a) a light/glow pattern action or (b) spoken dialogue. Prefer dialogue for messages with actual words. Prefer light patterns for non-verbal emotional communication.

#### Physical Action Replacements

**Pattern**: Clive picked up, tucked into pocket, etc. (as small object).

| Original | Replacement |
|----------|-------------|
| "stuffed Clive in my jacket" (S01E01 line 26) | "Clive scrambled up onto my shoulder" or "Clive kept pace beside me, his short legs a blur" |
| "tucks Clive into her jacket pocket" (S01E01 line 54) | "Clive clambers aboard the lifeboat" — he is knee-high, he walks |
| "Clive — sits in his usual spot" (as desk object) | "Clive — stands at his usual post" (he is a robot, he stands) |

**Rule**: Clive is knee-high (~60cm/2ft). He walks, stands, climbs. He is NOT carried in pockets. He may ride on a console, sit on a shelf, or stand beside the crew. He has hands and can grip surfaces.

#### Staple-Adjacent Vocabulary

| Term | Replacement | Context |
|------|-------------|---------|
| "springs" (in Clive context) | "servos" or "joints" | Mechanical internals |
| "binding fluid" | "coolant" or omit | Very rare |
| "harmonic anchor staples" (S01E03) | "harmonic anchor points" or "resonance pins" | Technical context |
| "staple points" | "light-pattern markers" | Navigation/trail context |

---

## CA-2: "Dimension" → "Frequency"

**Locked Rule**: *"Dimensions are called 'frequencies' — never 'dimensions,' 'planes,' or 'realms' in-universe."*

**Affected episodes** (11): S01E01 (3), S01E02 (1), S01E03 (20!), S01E04 (8), S01E05 (5), S01E07 (1), S01E08 (1), S01E09 (1), S01E10 (1), S03E01 (1), S03E08 (1)

### 2A: Simple Replacements

| Search (regex) | Replacement | Scope |
|----------------|-------------|-------|
| `\bdimension\b` | `frequency` | All in-universe narration and dialogue |
| `\bdimensions\b` | `frequencies` | All in-universe narration and dialogue |
| `\bdimensional\b` | `frequency-based` or `cross-frequency` | Context-dependent |
| `\bdimension-crossing\b` | `frequency-crossing` | Direct swap |

### 2B: Compound Phrases

| Original Phrase | Replacement |
|-----------------|-------------|
| "plant dimension" (S01E05) | "plant frequency" |
| "clockwork dimension" (S01E04, S01E05) | "clockwork frequency" |
| "gothic dimension" (S01E03) | "gothic frequency" |
| "another dimension" | "another frequency" |
| "other dimension" | "other frequency" |
| "an actual other dimension" (S01E03) | "an actual other frequency" |
| "dimension painted in perpetual twilight" (S01E03) | "frequency painted in perpetual twilight" |
| "dimensional earthquake" (S01E03) | "frequency earthquake" or "frequency rupture" |
| "the dimension's name" (S01E03) | "the frequency's name" |
| "mapped dimension" (S03E01) | "mapped frequency" |
| "takes on a new dimension" (S03E08) | Rephrase — this is an English idiom, not in-universe terminology. Replace with "takes on new depth" or "takes on new significance" |

### 2C: Exceptions — DO NOT Replace

- **Frontmatter/metadata** uses of "dimension" describing the concept for external readers — acceptable
- **English idiom** "a new dimension" meaning "a new aspect" — rephrase to avoid the word entirely
- **"Interdimensional"** — see CA-3 (handled as part of "Interdimensional Sea" → "Interdimensional Space")

### 2D: S01E03 Special Case

S01E03 (`ephergent_S01E03.md`, maps to new S01E04 "When the Moon Stopped Weeping") has **20 instances** — the highest count. This episode requires a full read-through. Many are in Pixel's dialogue/narration where she's still learning terminology. In early Season 1, Pixel might USE "frequency" awkwardly — she's learning the word. This is fine. Just ensure the WORD is "frequency" even if the character is uncertain about the concept.

---

## CA-3: "The Sea" → "The Space"

**Locked Rule**: *"The Space between frequencies is called 'the Space' or 'the Interdimensional Space' — never 'the Sea'."*

**Affected episodes** (17+): S01E01, S01E02, S01E04, S01E07, S01E08, S01E09, S01E10, S01E11, S01E12, S01E13, S02E04, S02E05, S02E07, S02E08, S02E09, S03E10, S03E12

### 3A: Direct Replacements

| Search (regex) | Replacement |
|----------------|-------------|
| `Interdimensional Sea` | `Interdimensional Space` |
| `the Sea` (when referring to the medium between frequencies) | `the Space` |
| `\bthe Sea\b` (capitalized, referring to the medium) | `the Space` |

**CRITICAL**: "the Sea" as a proper noun (capitalized "Sea") referring to the medium between frequencies MUST be replaced. Lowercase "sea" in normal English usage (e.g., "a sea of stars" as metaphor) may be left IF it does not refer to the Interdimensional Space. When in doubt, replace.

### 3B: Frontmatter Location Fields

| Original | Replacement |
|----------|-------------|
| `location: "... Interdimensional Sea"` | `location: "... Interdimensional Space"` |
| `location: "... the Sea"` | `location: "... the Space"` |
| `location: "... Deep Sea"` | `location: "... Deep Space"` or `location: "... Deep Interdimensional Space"` |

### 3C: Nautical Metaphor Replacements

When the text uses ocean/nautical language TO DESCRIBE THE SPACE, replace with spatial vocabulary. When nautical language describes something else (an actual ocean on a frequency-world), leave it.

| Nautical Term (in Space context) | Replacement Options |
|----------------------------------|---------------------|
| "sailed" / "sailing" | "traveled" / "navigated" / "crossed" |
| "waves" (of the Space) | "currents" / "fluctuations" / "ripples" (energy context) |
| "ocean" (the Space) | "expanse" / "void" / "medium" |
| "shore" / "shores" | "edge" / "boundary" / "threshold" |
| "tide" / "tides" | "drift" / "pull" / "current" |
| "surface" (of the Sea) | "boundary" / "outer layer" |
| "depths" (of the Sea) | "depths" (acceptable) or "deep Space" |
| "currents" | Keep — "currents" works for energy flows in Space |
| "dark water" (S01E06) | "dark void" or "dark expanse" |
| "The Sea swallows it whole" (S01E01) | "The Space swallows it whole" |
| "spat the Form 27-B out" (S01E05) | "ejected the Form 27-B" or keep if the ship is the subject |
| "eddy where currents...cancel each other out" (S03E07) | Keep "eddy" and "currents" — these work as physics metaphors for energy flows |

**Rule**: "Currents," "ripples," "fluctuations," and "eddies" are acceptable Space vocabulary. "Sailed," "waves," "ocean," "shore," and "tide" are NOT.

### 3D: Episode Title Updates

Two episode titles contain "Sea":
- **S01E16**: "The Signal and the Sea" → **"The Signal and the Space"** (or keep if creator decides — flag for review)
- **S03E10**: "Where the Sea Learns to Sing" → **"Where the Space Learns to Sing"** (or keep — flag for review)

Update both the title in frontmatter AND any in-text references to the title.

### 3E: Summary Field Updates

Many episode summaries in frontmatter contain "Sea" or "Interdimensional Sea." Apply the same replacements to summary text.

---

## CA-4: Mochi Insertion (ALL 37 Episodes)

**Locked Rule**: *"Mochi doesn't speak. Mochi doesn't have complex emotions. Mochi is warm, simple, and holds one enormous secret."*  
**Architecture Requirement**: Mochi warming cue in every episode.

**Mochi is absent from ALL 37 existing episodes.** Every episode needs at least one Mochi beat added.

### 4A: Who Is Mochi (Reference for Insertion)

- Dome-shaped Builder artifact, head-sized (~6-8 inches diameter)
- Carried in Pixel's satchel/jacket or sitting on a console near Pixel
- Communicates via: **color** (core glow), **vibration** (felt through contact), **warmth** (radiating)
- Color language: pink = content, blue = detection, green = confirmation, orange = caution, red = danger, purple = ancient/Builder recognition, white = maximum attention, dim/flicker = distress
- Does NOT speak. Does NOT have complex emotions. Does NOT make decisions.
- Reacts to the Ephergent Frequency like a compass to north

### 4B: Mochi Beat Templates

Use these templates, customized to each episode's context. Insert ONE per episode minimum. Insert at a moment that is quiet, transitional, or emotionally resonant — never during action peaks.

#### Template M1: Passive Warming (default — use when nothing special is happening)
```
In Pixel's satchel, Mochi pulsed a faint pink — warmth radiating through the fabric against Pixel's hip. She didn't notice. She never did, yet.
```

#### Template M2: Builder/Ancient Detection (use near Builder tech, old stations, relics)
```
Mochi's core shifted to purple, a slow swirl that brightened the inside of Pixel's bag. The warmth intensified — not uncomfortable, but insistent, the way a compass needle insists on north.
```

#### Template M3: Danger/Distress (use during threats, Drift encounters, system failures)
```
Mochi dimmed. Not flickered — dimmed, the glow retreating inward like something pulling a blanket over its head. The warmth faded from Pixel's satchel, leaving a pocket of cold where comfort had been.
```

#### Template M4: Frequency Resonance (use when the Ephergent Frequency is heard)
```
Mochi's core flared blue — a single, sharp pulse that Pixel felt through her jacket like a second heartbeat. Then it settled. Whatever Mochi had detected, the detection was over before anyone could name it.
```

#### Template M5: Emotional Scene Accompaniment (use during crew bonding, grief, revelation)
```
Mochi glowed steady green. No pulse, no shift — just a sustained warmth that radiated through the satchel and into the silence, as if confirming something no one had said aloud.
```

### 4C: Per-Episode Mochi Insertion Points

For each existing episode, the recommended insertion point and template:

#### Season 1

| Episode (source file) | Insertion Point | Template | Specific Note |
|----------------------|-----------------|----------|---------------|
| S01E01 (`ephergent_S01E01.md`) | After Pixel grabs equipment and runs — during the lifeboat launch | M1 → M4 | Mochi warms in pocket from the very first moment. Pixel attributes warmth to adrenaline. During lifeboat engine startup, Mochi flares blue (first Ephergent Frequency beat). |
| S01E02 (`ephergent_S01E02.md`) | During the sub-basement archive exploration | M2 | Mochi warms near Builder-derived equipment in deepest level. |
| S01E03 (`ephergent_S01E03.md`) → new S01E04 | During the emotional crystal market scene | M5 → M2 | Luminara-Mochi touch moment — amber pulse matching joy crystals. |
| S01E04 (`ephergent_S01E04.md`) → new S01E05 | During the Grand Chronometer scene | M4 | Mochi pulse synchronized with the Chronometer's tone. |
| S01E05 (`ephergent_S01E05.md`) → new S01E06 | During root network interference | M2 → M5 | Mochi glows green; plants lean toward Pixel. |
| S01E06 (`ephergent_S01E06.md`) → new S01E07 | During the Edge distortion scene | M4 | Mochi flares when A1 hears the song. |
| S01E07 (`ephergent_S01E07.md`) → new S01E08 | During ship awakening sequence | M4 (intense) | Full-cabin light pulse during ship power-on. Biggest Mochi moment of early S01. |
| S01E08 (`ephergent_S01E08.md`) → new S01E09 | Evening scene, ship settling | M1 | Steady glow; A1 notes temperature anomaly in his logs. |
| S01E09 (`ephergent_S01E09.md`) → new S01E11 | Eye of the frequency storm | M4 (brightest S01 moment) | Three-second white-gold flare. Painful to look at. Crew reacts: "What was THAT?" Returns to normal. |
| S01E10 (`ephergent_S01E10.md`) → new S01E12 | During Veranth memory loss scenes | M3 | First Mochi dimming — contrast to E11 flare. |
| S01E11 (`ephergent_S01E11.md`) → new S01E14 | During toll negotiation with Voss | M1 (cautious) | Cautious warmth — Mochi reading Voss. |
| S01E12 (`ephergent_S01E12.md`) → new S01E15 | Debris field / dead world discovery | M3 | Mourning-blue glow. |
| S01E13 (`ephergent_S01E13.md`) → new S01E16 | During the crew vote | M5 | Approval pulse during vote. |

#### Season 2

| Episode (source file) | Insertion Point | Template | Specific Note |
|----------------------|-----------------|----------|---------------|
| S02E01 (`ephergent_S02E01.md`) → new S02E02 | During deep frequency song sequence | M4 | Counter-tone harmonizing with Canticle's broadcast. First Mochi sound since S01E13 dead zone. |
| S02E02 (`ephergent_S02E02.md`) → new S02E03 | Near relay hardware | M2 | Warmth near Barry's old signal hardware. |
| S02E03 (`ephergent_S02E03.md`) → new S02E04 | During Chromatica's fading colors | M3 | Dimming — parallel to S01E12 Veranth. |
| S02E04 (`ephergent_S02E04.md`) → new S02E12 | During broker meeting | M1 | Background warmth; strengthens near broker's old relics. |
| S02E05 (`ephergent_S02E05.md`) → new S02E06 | During toll passage | M2 | Illuminating dormant Builder patterns in corridor. |
| S02E07 (`ephergent_S02E07.md`) → new S02E08 | During journal reading | M2 | Warming near Aether's journals/relay architecture. |
| S02E08 (`ephergent_S02E08.md`) → new S02E11 | During storm crisis | M3 → M4 | Dims during storm, then spikes when ghost signal peaks. |
| S02E09 (`ephergent_S02E09.md`) | Drift content merged into S02E11 | — | See S02E11 above. |
| S02E10 (`ephergent_S02E10.md`) | Absorbed into S02E15 (NEW) | — | N/A — episode content relocates. |
| S02E12 (`ephergent_S02E12.md`) → new S02E16 | Season finale, pre-vote | M5 → M4 | Mochi warming near Stations responding; peaks during vote. |

#### Season 3

| Episode (source file) | Insertion Point | Template | Specific Note |
|----------------------|-----------------|----------|---------------|
| S03E01 | Arrival at unmapped zone | M1 → M2 | Warming; shifts purple near Builder-adjacent signals. |
| S03E02 | Frequency Graveyard discovery | M3 | Dimming among dead frequencies. |
| S03E03 | Lighthouse/threshold scene | M2 (intense) | Crystal responds to Station 14's broadcast. |
| S03E04 | Philosophical discussion scene | M5 | Steady green during Om Kai's observation. |
| S03E05 | Silence/compression scene | M1 | Barely perceptible warmth in the silence. |
| S03E06 | Midpoint identity scene | M4 | Pulse during "Ephergent" word completion. |
| S03E07 | Ship graveyard / seeker gathering | M2 | Warming near ancient ship Builder-tech. |
| S03E08 | **Map release (canonical)** | M4 (maximum) | Atlas opens — Mochi's defining S03 moment. Core blazes white. Hundreds of frequencies visible. |
| S03E09 | Barry reunion | M5 | Steady, warm, near-constant. Home frequency. |
| S03E10 | Wellspring arrival | M4 (near-constant) | Near-constant warmth at Wellspring. |
| S03E11 | Broadcast preparation | M5 | Steady accompaniment; warming near Builder message translation. |
| S03E12 | Final broadcast | M4 → M5 | Near-constant warmth throughout. Most extraordinary Mochi presence of the series. |

---

## CA-5: A1 Coffee Flavor Insertion

**Locked Rule**: *"A1's coffee flavor is noted in every scene where A1 is present."*

**Affected episodes** (A1 present, zero coffee): S01E12, S02E03, S02E06, S02E07, S02E08, S03E02

### 5A: Coffee Flavor Language Guide

A1's coffee reflects his processing/emotional state. Use these flavor associations:

| A1's State | Coffee Flavor Description |
|------------|--------------------------|
| Normal/calm | "rich, steady espresso — dark roast, no surprises" |
| Alert/analyzing | "sharp, bright — almost citric, like the coffee was paying attention" |
| Scared/stressed | "burnt static — acrid, over-extracted, the taste of a machine running too hot" |
| Confident/proud | "rich chocolate undertones, smooth, like the coffee knew it was good" |
| Near Builder material | "unfamiliar ancient flavors — something floral that predated agriculture, a sweetness with no earthly name" |
| Grief/loss | "thin, bitter — barely coffee at all, like the machine had forgotten how" |
| Wonder/discovery | "layered — flavors shifting with each sip, as if the espresso couldn't decide what it wanted to be" |
| Near Wellspring/origin | "tastes like memory — arrival — home" |

### 5B: Coffee Beat Templates

#### Template C1: Scene-opening coffee (natural, unobtrusive)
```
A1 produced an espresso without being asked. It tasted [FLAVOR] — [ONE-SENTENCE EMOTIONAL CONTEXT].
```

#### Template C2: Mid-scene coffee note (woven into action)
```
The espresso A1 had brewed earlier sat cooling on the console, its aroma [DESCRIPTOR] — [FLAVOR NOTE that mirrors the scene's emotion].
```

#### Template C3: Character-reaction coffee (another character notices)
```
Pixel took a sip and paused. The coffee tasted [FLAVOR]. She glanced at A1's chrome surface. Whatever he was processing, it was showing in the brew.
```

### 5C: Per-Episode Coffee Insertion Points

| Episode (source) | New Slot | A1 Context | Recommended Flavor | Insertion Point |
|------------------|----------|------------|-------------------|-----------------|
| S01E12 (`ephergent_S01E12.md`) | S01E15 | Dead world / debris field crisis | Thin, bitter — grief | Early in episode when crew first processes the wreckage |
| S02E03 (`ephergent_S02E02.md`) | S02E03 | Signal relay analysis | Sharp, analytical | During A1's signal analysis scene |
| S02E06 (`ephergent_S02E05.md`) | S02E06 | Cogsworth Gate / toll politics | Layered — political complexity | During toll negotiation prep |
| S02E07 (`ephergent_S02E07.md`) | S02E08 | Aether's journals discovery | Ancient flavors — Builder-adjacent | During journal reading scenes |
| S02E08 (`ephergent_S02E08.md`) | S02E11 | Storm / frequency crisis | Burnt static — stressed systems | During storm crisis peak |
| S03E02 (`ephergent_S03E02.md`) | S03E02 | Frequency Graveyard | Thin, nearly flavorless — mourning | During Boneyard exploration |

---

## CA-6: Ephergent Frequency Beat Insertion

**Architecture Requirement**: The Ephergent Frequency is heard briefly in every episode.

### 6A: What the Frequency Is

The Ephergent Frequency is the Builders' original signal — a hum/tone/melody that predates all current civilizations. It is embedded in Builder technology, Station broadcasts, and the background radiation of the Space. It is subtle, usually below conscious perception. When characters hear it, each hears something different.

### 6B: Frequency Beat Templates

#### Template F1: Environmental hum (most common — use as default)
```
Beneath the [AMBIENT SOUND], something hummed. Not mechanical — older than mechanical. A tone that sat at the edge of hearing, felt more than perceived. [CHARACTER] [noticed/didn't notice]. It was gone before anyone could name it.
```

#### Template F2: A1 detection (technical)
```
A1's sensors flagged an anomaly in the ambient frequency — a carrier tone underneath the [LOCAL SIGNAL], predating it by centuries. He logged it. Filed it. Didn't mention it to the crew. Not yet.
```

#### Template F3: Meatball reaction (simple, animal)
```
Meatball's ears perked. He tilted his head, listening to something below the range of human hearing — a low, sustained note that made his tail wag once, slowly, before the sound passed.
```

#### Template F4: Character-specific hearing (for climactic moments)
```
The Frequency broke through — clear, sustained, unmistakable. [CHARACTER] heard [WHAT THEY HEARD]. It lasted [DURATION] seconds, and then it was gone, leaving [EMOTIONAL RESIDUE].
```

### 6C: Per-Episode Frequency Notes

Refer to the Amendment Log's per-episode "Architecture-Specific Amendments" for the exact Frequency beat mandated for each episode. The per-episode section (Part 2 below) includes these instructions.

---

## CA-7: Barry Trail — Reframing

**Locked Rule**: *"Barry Kowalski is alive. He is in the Wellspring. He left a trail."* and *"Barry's notes, when found, are never dramatic. They're methodical. That's what makes them devastating."*

### 7A: Language Replacements

| Original Framing | Corrected Framing |
|------------------|-------------------|
| "Barry Kowalski disappeared decades ago" (S01E01) | "Barry Kowalski walked into the Space decades ago" or "went looking for the source" |
| "disappeared" (Barry context) | "left" / "departed" / "went ahead" |
| "vanished into the Sea" (S01E01) | "went into the Space" / "followed a signal into the Space" |
| "missing partner" (S03E02) | "old partner" — Barry is not missing, he left a trail |
| "Barry would've laughed" (S03E11) | "Barry laughed" — he is PRESENT in S03E09+ |
| Memorial language in S03E12 ("A seed. Somewhere... something of Barry Kowalski will take root") | Replace with Barry PRESENT: he is there, thermos in hand, alive, working, methodical |
| "didn't stop" (as ominous/lost framing) | Reframe as deliberate: "kept going" / "followed the trail forward" |

### 7B: Barry Tone Guide

- Barry is **alive, deliberate, methodical, mildly annoyed** at how long it took them
- His notes are **technical, careful, observational** — not poetic or dramatic
- His trail is **intentional** — he MEANT to leave breadcrumbs
- His thermos is always present. His handwriting is neat. His data is organized.
- He is a night guard who understood more than anyone gave him credit for

### 7C: S03E09–S03E12 Critical Note

Barry is FOUND in S03E09. **All episodes S03E09 through S03E12 must reference Barry as PRESENT, not past tense.** Any existing memorial language in S03E11 and S03E12 must be rewritten with Barry physically there.

---

# Part 2: Per-Episode Specific Amendments

For episodes requiring more than global pattern replacements ("Major Amend" and episodes with architecture-specific insertions). Episodes marked "Minor Amend" need only the CA-1 through CA-7 global patterns above, plus the specific notes below.

---

## Season 1

### S01E01 — "The Day the Dial Broke" (source: `ephergent_S01E01.md`)
**Status**: Minor Amend | **New Slot**: S01E01 (same)

**Global patterns to apply**: CA-1 (9 stapler instances), CA-2 (3 dimension), CA-3 (4 bare Sea + 5 Interdimensional Sea), CA-4 (Mochi), CA-7 (Barry reframe)

**Specific insertions**:
1. **Clive wall-panel pause** — Insert during lifeboat console scene (after line ~60). Clive is placed on the console. His glow dims, his surface hums against the panel: "something feels familiar." Don't explain.
2. **Mochi first appearance** — Insert when Pixel grabs her belongings. Mochi is in a satchel/pocket. Pixel feels warmth, attributes to adrenaline.
3. **Ephergent Frequency first beat** — Insert during lifeboat engine startup. The engine hum has an undertone that doesn't match any mechanical frequency. A1 notices but files it.
4. **Barry reframe** — Lines ~140, ~154: Replace "disappeared" and "vanished" with deliberate departure language.

---

### S01E02 — "Ruins, Ripples, and Really Nervous Dinosaurs" (source: `ephergent_S01E02.md`)
**Status**: Minor Amend | **New Slot**: S01E02 (same)

**Global patterns**: CA-2 (1 dimension), CA-3 (2 Sea), CA-4 (Mochi), CA-5 (verify coffee — present but check flavor)

**Specific insertions**:
1. **Barry's personnel file** — Insert in archive scene background: "B. Kowalski — Night Security, Sub-Level 3, 23 years service"
2. **Clive doorway pause** — At a locked floor, glow brightens: "Efficient architecture."
3. **Mochi warmth** — Tied to Builder-derived equipment in deepest sub-basement.
4. **Ephergent Frequency** — Low hum from sub-basement deepest corridor, too low for human hearing; Meatball's ears perk.

---

### S01E04 (new) ← S01E03 "When the Moon Stopped Weeping" (source: `ephergent_S01E03.md`)
**Status**: Minor Amend | **New Slot**: S01E04

**Global patterns**: CA-1 (4 stapler, incl. "sentient stapler"), CA-2 (20 dimension — HIGHEST COUNT), CA-3 (4 Interdimensional Sea), CA-4 (Mochi)

**Specific insertions**:
1. **Clive navigation detour** — Reroutes past distant Builder Station outer marker (angular, dark, enormous). His glow dims. He says nothing.
2. **Luminara-Mochi moment** — Amber pulse matching Nocturne Aeturnus joy crystals.
3. **Ephergent Frequency** — Emotional crystal markets hum at frequency harmonizing with A1's engines.
4. **CA-2 bulk operation** — This episode needs ALL 20 "dimension" instances replaced. Do a full pass.

---

### S01E05 (new) ← S01E04 "The Clockwork Unraveling" (source: `ephergent_S01E04.md`)
**Status**: Minor Amend | **New Slot**: S01E05

**Global patterns**: CA-1 (2 stapler), CA-2 (8 dimension), CA-3 (2 Interdimensional Sea), CA-4 (Mochi)

**Specific insertions**:
1. **Clive hands-know moment** — His hands move to correct calibration settings before his conscious mind catches up.
2. **Mochi chronometer sync** — Pulse synchronized with Grand Chronometer.
3. **Professor Chronos line** — "The original calibration predates recorded history."
4. **Ephergent Frequency** — Grand Chronometer emits pure tone that hangs 3 seconds longer than physics allows. Om Kai: *"That sound is older than this place."*

---

### S01E06 (new) ← S01E05 "Root and Branch" (source: `ephergent_S01E05.md`)
**Status**: Minor Amend | **New Slot**: S01E06

**Global patterns**: CA-1 (2 stapler), CA-2 (5 dimension), CA-3 (2 Interdimensional Sea), CA-4 (Mochi)

**Specific insertions**:
1. **Clive stillness** — In interference field, observes "architecture" in the Root Network.
2. **Mochi green glow** — Plants lean toward Pixel.
3. **Zephyr-Barry parallel** — Zephyr's line about his brother echoes Barry's situation.
4. **Ephergent Frequency** — Root Network's lowest point produces subsonic pulse matching DRM sub-basement hum from E02. A1 logs it. Clive notices A1 logging it.

---

### S01E07 (new) ← S01E06 "The Song at the Edge of Everything" (source: `ephergent_S01E06.md`)
**Status**: **Major Amend** | **New Slot**: S01E07

**Global patterns**: CA-1 (3 stapler), CA-2 (1 dimension), CA-3 (3 Interdimensional Sea), CA-4 (Mochi)

**CRITICAL insertion — new scene required**:
1. **Clive-A1 private scene** — Late at night. Clive on A1's console. A1 brews an espresso — warm, sweet, flavored with something Clive recognizes and A1 doesn't consciously remember making. Clive: *"You remember, don't you?"* Quiet. No dramatic music. Insert as a new section after the main action resolves, before the closing.
2. **Ephergent Frequency** — The song A1 hears IS the Frequency at its clearest yet. Through The Edge's distortion it sounds alien. Only Clive recognizes it.

---

### S01E08 (new) ← S01E07 "That Which Emerges" (source: `ephergent_S01E07.md`)
**Status**: Minor Amend | **New Slot**: S01E08

**Global patterns**: CA-1 (1 stapler), CA-2 (1 "dimension-crossing"), CA-3 (9 Sea!), CA-4 (Mochi)

**Specific insertions**:
1. **Clive hull-sync** — Hand on hull during ship awakening, his glow syncs with the power-up sequence.
2. **Ship naming beat** — Clive: *"Name it whatever feels true."* → Pixel names it "Ephergent" → Clive: *"That'll do."* (weighted pause)
3. **Mochi full-cabin pulse** — During ship awakening, Mochi blazes. Brightest S01 moment to this point.
4. **Coffee ring** — On bridge console. Barry was here. Don't explain.
5. **Ephergent Frequency** — When ship fully powers on, every surface hums with the Frequency — clear, sustained, unmistakable — then fades to background.

---

### S01E09 (new) ← S01E08 "Learning to Be Large" (source: `ephergent_S01E08.md`)
**Status**: Minor Amend | **New Slot**: S01E09

**Global patterns**: CA-1 (1 stapler), CA-3 (9+ Sea), CA-4 (Mochi)

**Specific insertions**:
1. **Clive engine room familiarity** — Knows the layout intuitively. "I've been somewhere shaped like this."
2. **Charging alcove discovery** — Setup for Barry's Desk (S01E10 new episode).
3. **Mochi steady glow** — A1 notes temperature anomaly.
4. **Luminara grounding moment** — Documentation as therapy.
5. **Ephergent Frequency** — At night, ship hums. Pixel half-awake thinks it sounds like a lullaby.

---

### S01E11 (new) ← S01E09 "The Sound That Wants to Come Home" (source: `ephergent_S01E09.md`)
**Status**: **Major Amend** | **New Slot**: S01E11

**Global patterns**: CA-1 (2 stapler), CA-2 (1 dimension), CA-3 (5 Sea + 3 Interdimensional Sea), CA-4 (Mochi)

**CRITICAL insertions**:
1. **Mochi three-second flare** — Brightest Mochi moment of Season 1. White-gold, painful to look at, exactly three seconds. Crew reacts: *"What was THAT?"* Mochi returns to normal. Insert during the eye of the frequency storm.
2. **Clive coordinates** — Silently notes coordinates on his data pad, slips it into a compartment unseen. Insert after the storm passes.
3. **Clive line** — *"Every signal matters."*
4. **Ephergent Frequency** — In the eye of the storm, audible to everyone simultaneously. A1: *"Did you all hear that?"* Everyone heard it. Nobody heard the same thing.

---

### S01E12 (new) ← S01E10 "The Color of Forgetting" (source: `ephergent_S01E10.md`)
**Status**: Minor Amend | **New Slot**: S01E12

**Global patterns**: CA-2 (1 dimension), CA-3 (1 Sea + 2 Interdimensional Sea), CA-4 (Mochi), CA-5 (A1 present, NO coffee — ADD)

**Specific insertions**:
1. **Clive line** — *"Keep showing up."*
2. **Mochi dimming** — First time Mochi dims (contrast to E11 flare).
3. **Luminara echo** — *"Someone has to remember."*
4. **A1 coffee** — Currently missing entirely. Add thin, grief-flavored espresso.
5. **Ephergent Frequency** — When Pixel broadcasts Veranth's story, the transmission carries an undertone — the Frequency woven into her voice without her knowing.

---

### S01E14 (new) ← S01E11 "Toll Roads and Trade Winds" (source: `ephergent_S01E11.md`)
**Status**: Minor Amend | **New Slot**: S01E14

**Global patterns**: CA-3 (8 Sea + 4 Interdimensional Sea), CA-4 (Mochi)

**Specific insertions**:
1. **Squeeze-Bot "C" designation** — Slips and calls Clive something starting with "C." Clive's glow flickers — recognition.
2. **Barry reference** — Someone mentions "night guard type, thirty years back."
3. **Mochi cautious warmth** — Reading Voss.
4. **Ephergent Frequency** — Shimmer Strait phase-shifter beacons emit maintenance tone with the Frequency underneath.

---

### S01E15 (new) ← S01E12 "Wreckage and Will" (source: `ephergent_S01E12.md`)
**Status**: **Major Amend** | **New Slot**: S01E15

**Global patterns**: CA-2 (2 dimension), CA-3 (4 Sea + 1 Interdimensional Sea), CA-4 (Mochi), CA-5 (A1 present, NO coffee — ADD)

**Specific insertions**:
1. **Klaus recognizes Clive's age** — First time anyone sees Clive as ancient, not just old.
2. **Barry's logbook** — Entry in the library. Methodical. Technical. Devastating in its normalcy.
3. **Mochi mourning-blue** — Glow.
4. **Pixel command authority** — Reinforce Pixel making command decisions under crisis without consulting committee.
5. **A1 coffee** — Add. Thin, bitter — the machine barely trying.
6. **Ephergent Frequency** — Dead world's last signal contains a fragment. A1 logs it. Clive dims his glow for three seconds — mourning.

---

### S01E16 (new) ← S01E13 "The Signal and the Sea" (source: `ephergent_S01E13.md`)
**Status**: **Major Amend** | **New Slot**: S01E16

**Global patterns**: CA-1 (3 stapler), CA-3 (6 Sea + 1 Interdimensional Sea), CA-4 (Mochi)

**CRITICAL insertions**:
1. **Title update** — Consider "The Signal and the Space" per CA-3 locked rule. Flag for creator decision.
2. **Clive finale line** — At the very end, after the vote, almost throwaway: *"The Builders called this home. They were right to."* First time Clive says "Builders." No one reacts.
3. **Barry's relay** — The distress signal's sub-frequency characteristics match Barry's relay. Don't reveal — plant for S02 connection.
4. **Mochi approval pulse** — During crew vote.
5. **Ephergent Frequency** — Heard clearly by every crew member simultaneously for the first time. Each hears differently: Pixel: broadcast, A1: song, Clive: voice, Meatball: heartbeat, Zephyr: brother, Om Kai: silence, Luminara: shutter click, Klaus: bell.

---

## Season 2

### S02E02 (new) ← S02E01 "The Singing Deep" (source: `ephergent_S02E01.md`)
**Status**: Minor Amend + Relocate | **New Slot**: S02E02

**Global patterns**: CA-3 (2 Interdimensional Sea), CA-4 (Mochi)

**Specific insertions**:
1. **Clive sensory echo** — Harmony he's heard before. Glow shifts for 2 seconds.
2. **Barry notebook margin note** — Frequencies beyond the five.
3. **Mochi counter-tone** — Harmonizing with Canticle's broadcast.
4. **Soften first-discovery framing** — They've just come from a Builder Station in S02E01 (new).
5. **Ephergent Frequency** — Woven into Canticle's deepest musical layers.

---

### S02E03 (new) ← S02E02 "Signal and Noise" (source: `ephergent_S02E02.md`)
**Status**: Minor Amend + Relocate | **New Slot**: S02E03

**Global patterns**: CA-1 (1 stapler), CA-4 (Mochi), CA-5 (A1 present, NO coffee — ADD)

**Specific insertions**:
1. **Barry's hardware** — Old signal amplification hardware at relay point.
2. **Clive involuntary Builder word** — At a junction. Zephyr hears it, writes it down. Neither discusses.
3. **Mochi warmth** — Near Barry's hardware.
4. **Ephergent Frequency** — Undertone in relay network — the Frequency is using their infrastructure.
5. **A1 coffee** — Add. Sharp, analytical flavor.

---

### S02E04 (new) ← S02E03 "Every Color Was a Name" (source: `ephergent_S02E03.md`)
**Status**: Minor Amend + Relocate | **New Slot**: S02E04

**Global patterns**: CA-3 (2 Interdimensional Sea + 1 Sea), CA-4 (Mochi)

**Specific insertions**:
1. **Barry notebook entry** — Frequency-dependent life and Builders' purpose.
2. **Clive "located grief"** — Watching something he built fail to protect what it was meant to.
3. **Mochi dimming** — Parallel to S01E12 Veranth.
4. **Zephyr ghost signal** — In Chromatica's noise.
5. **Emotional weight** — Crew has just seen the Station. They know what was supposed to prevent this.

---

### S02E06 (new) ← S02E05 "The Toll at Cogsworth Gate" (source: `ephergent_S02E05.md`)
**Status**: Minor Amend + Relocate | **New Slot**: S02E06

**Global patterns**: CA-1 (1 stapler), CA-4 (Mochi), CA-5 (A1 present, NO coffee — ADD)

**Specific insertions**:
1. **Builder transit corridor** — Clive's navigation featured.
2. **Toll-keeper Barry reference** — Mentions a solo traveler matching Barry's description.
3. **Mochi Builder patterns** — Illuminating dormant patterns.
4. **Ephergent Frequency** — Amplification in the corridor.
5. **A1 coffee** — Add. Layered flavors — political complexity.

---

### S02E08 (new) ← S02E07 "The Journals of the Lost Brother" (source: `ephergent_S02E07.md`)
**Status**: **Major Amend** + Relocate | **New Slot**: S02E08

**Global patterns**: CA-3 (2 Interdimensional Sea + 1 Sea), CA-4 (Mochi), CA-5 (A1 present, NO coffee — ADD)

**Specific insertions**:
1. **Aether "Ephergent" reference** — Journals should reference the concept. Aether encountered it independently.
2. **Zephyr filtered reaction** — Through E07 revelation. He has a word now.
3. **Barry-Aether parallel** — Both followed same signals to same places.
4. **Clive relay recognition** — "They point the same direction."
5. **A1 coffee** — Add. Ancient Builder-adjacent flavors near the journals.
6. **Mochi warming** — Near journals and relay architecture.

---

### S02E11 (new) ← S02E08 + S02E09 "Three Voices in the Storm" (source: `ephergent_S02E08.md` + `ephergent_S02E09.md`)
**Status**: **Major Amend** + Relocate + Merge | **New Slot**: S02E11

**Global patterns**: CA-3 (1 Interdimensional Sea), CA-4 (Mochi), CA-5 (A1 present, NO coffee — ADD)

**Merge instructions**:
- Primary structure from S02E08 (storm crisis)
- Integrate Drift-acceleration content from S02E09 ("The Season Theory")
- Om Kai's "sandcastles at high tide" observation goes HERE

**Specific insertions**:
1. **Barry failure timeline chart** — Found in earlier notebooks.
2. **Clive network-sensation** — During the storm.
3. **Ghost signal spike** — In the storm.
4. **A1 coffee** — Add. Burnt static — stressed.
5. **Mochi** — Dims during storm, spikes when ghost signal peaks.

---

### S02E12 (new) ← S02E04 "The Broker at the Edge of Static" (source: `ephergent_S02E04.md`)
**Status**: **Major Amend** + Relocate | **New Slot**: S02E12

**Global patterns**: CA-3 (2 Interdimensional Sea + 1 Sea), CA-4 (Mochi)

**Specific insertions**:
1. **Broker knew Barry** — Recognition scene with Clive.
2. **Silence Zone geography** — Sets up Station 9-Liminal for E13.
3. **Zephyr ghost signal** — Strongest here.
4. **REMOVE Aether name-drop** — Broker mentions "strange signals," NOT Aether specifically. Protects E15 payoff.
5. **Mochi warming, A1 coffee** — Add.

---

### S02E16 (new) ← S02E12 "The Surge" → "The Signal and the Source" (source: `ephergent_S02E12.md`)
**Status**: **Major Amend** + Relocate + Rename | **New Slot**: S02E16

**Global patterns**: CA-3 (4 Interdimensional Sea), CA-4 (Mochi)

**Major changes**:
1. **Rename** — "The Surge" → "The Signal and the Source" (frontmatter title field + all references)
2. **Expand to full finale** — Current episode needs expansion.
3. **Clive open statement** — Most vulnerable moment of the season. Insert new scene.
4. **Barry page-47 note** — *"See you at the source. Bring coffee. Mine's terrible."*
5. **Zephyr's calm sentence** about Aether.
6. **Stations responding** — To crew's passage.
7. **Vote structure** — Must echo S01E16's vote. Same structure, deeper stakes.

---

## Season 3

### S03E01 — "Where the Frequencies Have No Name" (source: `ephergent_S03E01.md`)
**Status**: **Major Amend** | **New Slot**: S03E01

**Global patterns**: CA-1 (1 stapler), CA-2 (1 dimension), CA-3 (3 Interdimensional Sea), CA-4 (Mochi)

**Specific insertions**:
1. **S02 handoff threads** — Clive's open navigation, Zephyr's calm certainty, crew's post-confrontation trust.
2. **Season 3 register** — Establish quieter emotional tone.
3. **Pixel "Ephergent" moment** — She says the word aloud. It sounds different than S01.
4. **Clive four-note phrase** — Humming: *"I've been here before. Or somewhere shaped like here."*
5. **Mochi warming, A1 coffee** — Add.

---

### S03E02 — "The Boneyard of Beautiful Things" (source: `ephergent_S03E02.md`)
**Status**: **Major Amend** | **New Slot**: S03E02

**Global patterns**: CA-1 (2 stapler), CA-3 (implied Sea), CA-4 (Mochi), CA-5 (A1 present, NO coffee — ADD), CA-7 (Barry "staple patterns" → robot equivalent)

**Specific insertions**:
1. **Clive S03 register** — Not shock but steady grief.
2. **Barry trail** — Notebook measurements (NOT "staple patterns" — replace with light-pattern signatures or notebook entries).
3. **Luminara "Ephergent" understanding** — Transformation.
4. **Deepen loss-Wellspring connection**.
5. **A1 coffee** — Add. Thin, nearly flavorless — mourning.
6. **Mochi dimming** — Among dead frequencies.

---

### S03E03 — "The Lighthouse Keeps No One" → "The Threshold" (source: `ephergent_S03E03.md`)
**Status**: **Major Amend (effective REPLACE)** | **New Slot**: S03E03

**Global patterns**: CA-1 (1 stapler), CA-3 (2 Interdimensional Sea), CA-4 (Mochi)

**Major change**: **Replace primary plot** with Station 14-Threshold content.
1. **Rename** — "The Lighthouse Keeps No One" → "The Threshold"
2. **New content** — Station 14, last Builder Station at near-original output. Keeper delivering Builders' farewell address for 800 years.
3. **Clive memory** — Remembers being built (penultimate memory).
4. **Existing home-calling subplot** — Absorb as Klaus subplot or relocate to S03E04.
5. **Mochi crystal response** — To Station 14's broadcast.

---

### S03E04 — "The Day That Loved Itself to Death" (source: `ephergent_S03E04.md`)
**Status**: Standard Amend | **New Slot**: S03E04

**Global patterns**: CA-4 (Mochi), CA-7 (Barry "staple patterns")

**Specific insertions**:
1. **Sharpen Wellspring/Builders' choice contrast**.
2. **Clive philosophical settling**.
3. **Om Kai "Ephergent" understanding** — Place here.
4. **Fix all Clive/Barry communication** — "staple patterns" → light-pattern signatures or notebook entries.

---

### S03E05 — "The Loudest Thing in the Room Is Nothing" (source: `ephergent_S03E05.md`)
**Status**: Standard Amend | **New Slot**: S03E05

**Global patterns**: CA-3 (2 Interdimensional Sea), CA-4 (Mochi)

**Specific insertions**:
1. **Barry notebook wisdom** — About respecting refusal.
2. **Clive settling beat** — Compression-as-silence.
3. **Zephyr "Ephergent" understanding** — In the silence.
4. **Builders' invitation-not-commandment** — Connection.
5. **Mochi warming, A1 coffee** — Add.

---

### S03E06 — "My Brother the Broadcast" (source: `ephergent_S03E06.md`)
**Status**: **Major Amend** | **New Slot**: S03E06

**Global patterns**: CA-4 (Mochi)

**Specific insertions**:
1. **"Ephergent" revelation** — Lands for ALL remaining crew (Klaus, Nano, Meatball, A1).
2. **Clive recognition** — Of his own approaching reunion.
3. **Barry signal detection**.
4. **Midpoint pivot** — After this, the word is complete and crew identity is claimed.
5. **Mochi warming, A1 coffee** — Add.

---

### S03E07 — "Every Ship That Ever Sailed This Far" (source: `ephergent_S03E07.md`)
**Status**: **Major Amend** | **New Slot**: S03E07

**Global patterns**: CA-1 (2 stapler, incl. "staple-pattern cipher"), CA-3 (4 Interdimensional Sea), CA-4 (Mochi)

**Specific insertions**:
1. **Baron Klaus Nocturne revelation** — Episode's emotional spine. Klaus opens up about his secret.
2. **Om Kai response** — To Klaus.
3. **A1 competitive humor** — About other ships. Preserve.
4. **Fix "staple-pattern cipher"** → "light-pattern cipher" or "glow-pattern cipher."
5. **Mochi warming, A1 coffee** — Add.

---

### S03E08 — "Compost and Constellations" → "The Atlas Opens" (source: `ephergent_S03E08.md`)
**Status**: **Major Amend** | **New Slot**: S03E08

**Global patterns**: CA-2 (1 dimension — IDIOMATIC, rephrase), CA-4 (Mochi)

**Major change**: **Replace primary plot** with Mochi's map release.
1. **Rename** — "Compost and Constellations" → "The Atlas Opens"
2. **Mochi atlas scene** — Canonically mandated. Core blazes white. Hundreds of frequencies visible. The defining Mochi moment of S03.
3. **Om Kai wisdom** — "Compost and constellations" integrates as thematic context for seeing dead and potential frequencies.
4. **CA-2 note** — "takes on a new dimension" is an English idiom → "takes on new depth."

---

### S03E09 — "The Ship That Remembered Tomorrow" → "Took You Long Enough" (source: `ephergent_S03E09.md`)
**Status**: **Major Amend** | **New Slot**: S03E09

**Global patterns**: CA-3 (1 Interdimensional Sea), CA-4 (Mochi)

**Major change**: **Replace primary plot** with the Barry reunion.
1. **Rename** — "The Ship That Remembered Tomorrow" → "Took You Long Enough"
2. **Barry's first words** — CANONICAL, use verbatim: *"Took you long enough. I left very clear directions."*
3. **Barry characterization** — NOT a rescue. He is alive, working, mildly annoyed.
4. **Existing ship content** — Absorb into S03E08 or this episode's early minutes.
5. **Mochi warming** — Near-constant. Home frequency.
6. **A1 coffee** — Extraordinary flavors near origin.

---

### S03E10 — "Where the Sea Learns to Sing" (source: `ephergent_S03E10.md`)
**Status**: **Major Amend** | **New Slot**: S03E10

**Global patterns**: CA-3 (2 Sea + title contains "Sea"), CA-4 (Mochi)

**Specific insertions**:
1. **Title update** — Consider "Where the Space Learns to Sing." Flag for creator decision.
2. **Builder broadcast** — Canonical Grand Master Plan content.
3. **Zephyr/Aether reunion** — At the Wellspring.
4. **Clive complete memory restoration** — The choice to forget.
5. **Barry-Clive partnership** — Resuming.
6. **Wellspring reframe** — It is a state/tuning, not a place with temptation. Remove "offering dissolution" language.
7. **Mochi** — Near-constant warmth at Wellspring.
8. **A1 coffee** — Tastes like memory, arrival, home.

---

### S03E11 — "Every Story Becomes a Seed" (source: `ephergent_S03E11.md`)
**Status**: **Major Amend** | **New Slot**: S03E11

**Global patterns**: CA-1 (3 stapler), CA-4 (Mochi), CA-7 (Barry memorial language — HE IS PRESENT)

**Major changes**:
1. **Barry is PRESENT** — Rewrite all past-tense/memorial Barry references. He is collaborating, not commemorated. "Barry would've laughed" → "Barry laughed."
2. **Broadcast preparation** — Each crew member translates the Builder message. Each translation IS their story becoming a seed.
3. **Nano calibration** — Her arc's culmination.
4. **Fix all 3 stapler instances** — "sentient stapler," "for a stapler," "staplers don't cry."
5. **Polyphonic structure** — Episode mirrors the broadcast: layered, each voice distinct.
6. **Mochi warming, A1 coffee** — Add.

---

### S03E12 — "The Signal Was Us All Along" (source: `ephergent_S03E12.md`)
**Status**: **Major Amend** | **New Slot**: S03E12

**Global patterns**: CA-1 (1 stapler), CA-3 (2 Sea + 6 Interdimensional Sea!), CA-4 (Mochi), CA-7 (Barry PRESENT)

**Major changes**:
1. **ALL canonical Grand Master Plan dialogue** — Pixel's final transmission verbatim, Meatball's howl.
2. **Full crew epilogue** — Add.
3. **Station 11-Quiescent flicker** — Add.
4. **Each character's broadcast contribution** — Complete.
5. **Barry is PRESENT** — Rewrite ALL memorial language. He's there with his thermos. "A seed. Somewhere..." passage → Barry is physically part of the broadcast.
6. **Fix "staple poetry" / "staple-pattern"** references → "light-pattern poetry" / "glow-pattern cipher."
7. **Fix ALL 8 Sea/Interdimensional Sea** instances → Space/Interdimensional Space.
8. **Mochi** — Near-constant warming throughout. Most extraordinary presence of the series.
9. **A1 coffee** — Most extraordinary of the series.
10. **Epilogue tone** — Hopeful, not naive. Drift does not reverse. Crew broadcasts, documents, keeps signal alive. That's enough. That's everything.

---

# Part 3: Episode Renumbering Map

## Season 1 Renumbering

| Old File | Old Number | → | New Number | New Title | Frontmatter Changes |
|----------|-----------|---|-----------|-----------|---------------------|
| `ephergent_S01E01.md` | S01E01 | → | S01E01 | The Day the Dial Broke | No number change |
| `ephergent_S01E02.md` | S01E02 | → | S01E02 | Ruins, Ripples, and Really Nervous Dinosaurs | No number change |
| — | — | → | S01E03 | The DRM Archive | **NEW EPISODE** |
| `ephergent_S01E03.md` | S01E03 | → | S01E04 | When the Moon Stopped Weeping | `episode: 3` → `episode: 4` |
| `ephergent_S01E04.md` | S01E04 | → | S01E05 | The Clockwork Unraveling | `episode: 4` → `episode: 5` |
| `ephergent_S01E05.md` | S01E05 | → | S01E06 | Root and Branch | `episode: 5` → `episode: 6` |
| `ephergent_S01E06.md` | S01E06 | → | S01E07 | The Song at the Edge of Everything | `episode: 6` → `episode: 7` |
| `ephergent_S01E07.md` | S01E07 | → | S01E08 | That Which Emerges | `episode: 7` → `episode: 8` |
| `ephergent_S01E08.md` | S01E08 | → | S01E09 | Learning to Be Large | `episode: 8` → `episode: 9` |
| — | — | → | S01E10 | Barry's Desk | **NEW EPISODE** |
| `ephergent_S01E09.md` | S01E09 | → | S01E11 | The Sound That Wants to Come Home | `episode: 9` → `episode: 11` |
| `ephergent_S01E10.md` | S01E10 | → | S01E12 | The Color of Forgetting | `episode: 10` → `episode: 12` |
| — | — | → | S01E13 | Meatball's Frequency | **NEW EPISODE** |
| `ephergent_S01E11.md` | S01E11 | → | S01E14 | Toll Roads and Trade Winds | `episode: 11` → `episode: 14` |
| `ephergent_S01E12.md` | S01E12 | → | S01E15 | Wreckage and Will | `episode: 12` → `episode: 15` |
| `ephergent_S01E13.md` | S01E13 | → | S01E16 | The Signal and the Sea* | `episode: 13` → `episode: 16` (*title may change) |

### Frontmatter update template (Season 1):
```yaml
# For each renumbered episode, change:
episode: [OLD_NUMBER]
# To:
episode: [NEW_NUMBER]
```

## Season 2 Renumbering

| Old File | Old Number | → | New Number | New Title | Frontmatter Changes |
|----------|-----------|---|-----------|-----------|---------------------|
| — | — | → | S02E01 | First Station | **NEW EPISODE** |
| `ephergent_S02E01.md` | S02E01 | → | S02E02 | The Singing Deep | `episode: 1` → `episode: 2` |
| `ephergent_S02E02.md` | S02E02 | → | S02E03 | Signal and Noise | `episode: 2` → `episode: 3` |
| `ephergent_S02E03.md` | S02E03 | → | S02E04 | Every Color Was a Name | `episode: 3` → `episode: 4` |
| — | — | → | S02E05 | The Library Between | **NEW EPISODE** |
| `ephergent_S02E05.md` | S02E05 | → | S02E06 | The Toll at Cogsworth Gate | `episode: 5` → `episode: 6` |
| — | — | → | S02E07 | The Word for What We Are | **NEW EPISODE** |
| `ephergent_S02E07.md` | S02E07 | → | S02E08 | The Journals of the Lost Brother | `episode: 7` → `episode: 8` |
| — | — | → | S02E09 | The Mochi Revelation | **NEW EPISODE** |
| — | — | → | S02E10 | The Keeper Wakes | **NEW EPISODE** |
| `ephergent_S02E08.md` + `ephergent_S02E09.md` | S02E08 + S02E09 | → | S02E11 | Three Voices in the Storm | `episode: 8` → `episode: 11` (merge) |
| `ephergent_S02E04.md` | S02E04 | → | S02E12 | The Broker at the Edge of Static | `episode: 4` → `episode: 12` |
| — | — | → | S02E13 | The Lighthouse | **NEW EPISODE** |
| — | — | → | S02E14 | You Knew | **NEW EPISODE** |
| — (absorbs `ephergent_S02E10.md`) | — | → | S02E15 | What Aether Left Behind | **NEW** (absorbs S02E10 content) |
| `ephergent_S02E12.md` | S02E12 | → | S02E16 | The Signal and the Source | `episode: 12` → `episode: 16`, `title: "The Surge"` → `title: "The Signal and the Source"` |
| `ephergent_S02E06.md` | S02E06 | → | **REMOVED** | The Laughing Funeral | Remove from S02 sequence |
| `ephergent_S02E11.md` | S02E11 | → | **REMOVED** | The Cost of Light | Remove from S02 sequence |

## Season 3 Renumbering

No position changes. All S03 episodes remain in their slots (S03E01–S03E12).

**Title changes only**:

| File | Old Title | New Title | Frontmatter Change |
|------|-----------|-----------|-------------------|
| `ephergent_S03E03.md` | The Lighthouse Keeps No One | The Threshold | `title:` update |
| `ephergent_S03E08.md` | Compost and Constellations | The Atlas Opens | `title:` update |
| `ephergent_S03E09.md` | The Ship That Remembered Tomorrow | Took You Long Enough | `title:` update |
| `ephergent_S03E10.md` | Where the Sea Learns to Sing | Where the Space Learns to Sing* | `title:` update (*pending creator decision) |

## Cross-Reference Updates

When episodes reference other episodes by number (e.g., "back in S01E03"), those references must be updated to the new numbering. Search each episode for patterns:

| Search Pattern (regex) | Action |
|------------------------|--------|
| `S01E03` (referring to "When the Moon Stopped Weeping") | → `S01E04` |
| `S01E04` (referring to "The Clockwork Unraveling") | → `S01E05` |
| `S01E05` (referring to "Root and Branch") | → `S01E06` |
| `S01E06` (referring to "The Song at the Edge") | → `S01E07` |
| `S01E07` (referring to "That Which Emerges") | → `S01E08` |
| `S01E08` (referring to "Learning to Be Large") | → `S01E09` |
| `S01E09` (referring to "The Sound That Wants to Come Home") | → `S01E11` |
| `S01E10` (referring to "The Color of Forgetting") | → `S01E12` |
| `S01E11` (referring to "Toll Roads and Trade Winds") | → `S01E14` |
| `S01E12` (referring to "Wreckage and Will") | → `S01E15` |
| `S01E13` (referring to "The Signal and the Sea") | → `S01E16` |
| `S02E01` (referring to "The Singing Deep") | → `S02E02` |
| `S02E02` (referring to "Signal and Noise") | → `S02E03` |
| `S02E03` (referring to "Every Color Was a Name") | → `S02E04` |
| `S02E04` (referring to "The Broker at the Edge of Static") | → `S02E12` |
| `S02E05` (referring to "The Toll at Cogsworth Gate") | → `S02E06` |
| `S02E07` (referring to "The Journals of the Lost Brother") | → `S02E08` |
| `S02E08` (referring to storm content) | → `S02E11` |
| `S02E09` (referring to Drift content) | → merged into `S02E11` |
| `S02E12` (referring to "The Surge") | → `S02E16` |

**Caution**: Some references to episode numbers may be in prose ("remember what happened in episode 3") rather than formal notation. Read context before replacing.

---

# Part 4: Verification Checklist

Run this checklist against **every amended episode** before marking it complete.

## Per-Episode Verification

### Locked Rule Compliance
- [ ] **No "dimension" in-universe** — Search for `\bdimension` (case-insensitive). Zero hits in dialogue/narration. Frontmatter metadata uses acceptable.
- [ ] **No "the Sea"** — Search for `\bSea\b` (capitalized). Zero hits referring to the Interdimensional Space. Check title, frontmatter location, summary, and body.
- [ ] **Clive is robot, not stapler** — Search for `\bstapl`. Zero hits. No "Swingline." No "binding fluid." Clive is described as knee-high robot with glowing sphere head and fedora.
- [ ] **Mochi appears at least once** — Search for `\bMochi\b`. At least one hit. Verify Mochi does not speak, has no complex emotions, and communicates only via warmth/glow/vibration.
- [ ] **A1's coffee noted when A1 present** — If A1 appears in the episode, search for `coffee|espresso|brew|roast`. At least one hit with flavor description.
- [ ] **Barry references are hopeful, not tragic** — Search for `\bBarry\b`. If found, verify: no "disappeared," no "vanished," no "lost," no memorial past tense (after S03E09: Barry is physically present).
- [ ] **Ephergent Frequency heard** — Verify at least one beat where the Frequency is perceived (hum, tone, undertone, melody, pulse).
- [ ] **Builders are not villains** — If Builders mentioned, verify they are framed as loving, deliberate, not malicious.
- [ ] **Drift is entropy, not villain** — If Drift mentioned, verify it is framed as sad inevitability, not antagonist.
- [ ] **Wellspring is state, not place** — If Wellspring mentioned (S03), verify it is framed as tuning/state, not a location that "offers" or "tempts."
- [ ] **Barry's notes are methodical** — If Barry's notes/entries appear, verify they are technical, careful, observational — not poetic or dramatic.

### Structural Compliance
- [ ] **Frontmatter episode number correct** — Matches the new numbering map.
- [ ] **Frontmatter title correct** — Matches the new title (if renamed).
- [ ] **Frontmatter location field clean** — No "Interdimensional Sea" or "Deep Sea."
- [ ] **Frontmatter summary clean** — No locked rule violations in summary text.
- [ ] **Cross-references updated** — Any mention of other episode numbers uses new numbering.
- [ ] **Featured characters list accurate** — Reflects any character additions (Mochi should be added to featured_characters if she appears).

### Continuity Compliance
- [ ] **Adjacent episode consistency** — Events referenced from previous/next episodes match the new episode ordering.
- [ ] **Character knowledge consistent** — Characters don't know things they shouldn't yet know at this point in the new order.
- [ ] **Emotional register matches season** — S01: discovery/wonder, S02: deepening/questioning, S03: settling/acceptance.

## Batch Verification Commands

Run these grep commands against the full amended episode directory to catch remaining violations:

```bash
# CA-1: Stapler references (should return ZERO results)
grep -rni "stapler\|staple\|swingline\|binding fluid" *.md

# CA-2: Dimension in-universe (review each hit — metadata OK, in-universe NOT OK)
grep -rni "\bdimension" *.md

# CA-3: Sea references (should return ZERO capitalized "Sea" referring to the Space)
grep -rn "\bSea\b\|Interdimensional Sea" *.md

# CA-4: Mochi presence (every file should have at least one hit)
for f in *.md; do echo -n "$f: "; grep -c "Mochi" "$f"; done

# CA-5: A1 + coffee check (files with A1 but no coffee)
for f in *.md; do
  a1=$(grep -c "\bA1\b" "$f")
  coffee=$(grep -ci "coffee\|espresso\|brew\|roast" "$f")
  if [ "$a1" -gt 0 ] && [ "$coffee" -eq 0 ]; then
    echo "WARNING: $f has A1 ($a1 mentions) but no coffee"
  fi
done

# CA-7: Barry + disappearance language
grep -rni "barry.*disappear\|barry.*vanish\|barry.*lost\|barry.*memorial\|barry.*would've" *.md
```

---

*Amendment Application Guide generated for Phase 4 Episode Amendment workflow. Each pattern, template, and instruction is designed for mechanical execution by an LLM agent or human editor.*

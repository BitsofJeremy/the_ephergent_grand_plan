# Artist Handoff — Meatball's Big Walk: Clive Visual Update

**Game**: Meatball's Big Walk (cozy point-and-click)
**Task**: Replace all Clive sprites. Add one new hotspot asset.
**Rule**: NO dialogue, hotspot text, or script changes. Visual assets only.

---

## 1. CLIVE — WHAT HE LOOKS LIKE NOW

Clive is a **knee-high Builder Companion Bot** (~2 ft / 60 cm tall). He is NOT a stapler.

| Feature | Detail |
|---|---|
| **Body** | Barrel-chested, stocky, dwarven proportions. Broad shoulders, thick limbs, low center of gravity. |
| **Material** | Unknown Builder alloy — shifts between deep bronze, aged copper-green, and shadow-grey depending on light. Heavy verdigris patina in every seam. Worn smooth at contact points. Warm-looking. |
| **Head** | Featureless glowing sphere (~6 in diameter) on a rotating neck mount. Glow shifts **blue-white** (NOT pink). No eyes, no mouth, no display. Expression is purely through tilt, angle, and glow intensity. |
| **Chest Core** | Circular glowing core (blue-white) visible through a lens opening, center chest. Pulses gently like a heartbeat. |
| **Fedora** | Weathered brown-grey, classic noir detective style, tilted rakish. Brim partially obscures the head glow, casting shadows. **The fedora is ALWAYS on.** It was Barry Kowalski's gift. |
| **Hands** | Articulated, thick-fingered, surprisingly dexterous. Fingertips worn smooth. Builder precision engineering. |
| **Surface** | Geometric Builder symbols across body — some faintly glow blue-white, some nearly worn away. Verdigris fills seams. Pitting from age. |
| **Movement** | Uncanny smooth — too precise to be human, too fluid to be mechanical. Deliberate, weighted footfalls. |

---

## 2. SCALE REFERENCE

```
  ┌───┐
  │   │  ← Crew member (~5'8")
  │   │
  │   │
  │   │
  ├───┤  ← Knee line
  │   │   ┌─.─┐  ← Fedora
  │   │   │(●)│  ← Glowing sphere head
  │   │   │▐█▌│  ← Barrel chest + core
  └───┘   └┘ └┘  ← Clive (~2 ft)
──────────────────
```

Clive's head (with fedora) reaches roughly knee-height on a standing crew member.

---

## 3. SPRITES TO UPDATE

Replace every Clive sprite in the game. The old stapler design is fully retired.

- **Clive idle** — all facing directions
- **Clive walking** — all facing directions
- **Clive interaction poses** (head tilt, fedora adjust, pointing, arms crossed)
- **Clive in scene backgrounds** — any location where Clive appears (bridge, corridors, A1's console area, etc.)
- **Clive portrait/dialogue box sprite** (if used)
- **Any inventory or UI icon** referencing Clive

Every scene/location in Meatball's Big Walk where Clive's sprite appears gets the new asset.

---

## 4. NEW HOTSPOT — BARRY'S COFFEE MUG

**Location**: On A1's console
**Asset needed**: A single coffee mug, sitting on the console surface. Worn, used, clearly someone's daily mug. Nothing fancy.
**Interaction**: Meatball can sniff it.
**Hotspot text** (already written, do not change):

> *"Smells like: looking for something. 23 years. Almost there."*

Sprite needed: the mug on the console (static, no animation required).

---

## 5. WHAT DOES NOT CHANGE

- ❌ No dialogue changes
- ❌ No hotspot text changes (except adding Barry's mug above)
- ❌ No GDScript changes
- ❌ No scene restructuring
- ❌ No changes to Meatball's sprites
- ❌ No changes to any other character's sprites

This is a **sprite swap + one new hotspot asset**. That's it.

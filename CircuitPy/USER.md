# Pocket Organist — User Guide

Quick reference for controls and features. Hold function buttons while using them; release to exit unless noted.

---

## Power

| Keys | Description |
|------|-------------|
| **Power** (hold ~0.5 s) | Turn off. Hold again ~0.5 s while off to turn back on (USB power). |

---

## Play modes

Select mode with **Shift** plus one modifier (only one at a time):

| Keys | Mode |
|------|------|
| **Shift + 3rd** | **Chord** — one chord per note key |
| **Shift + 5th** | **Melody** — single-note lines |
| **Shift + 7th** | **Drum** — GM drum hits on note keys |

Press a **note key** (C, D, E, F, G, A, B, …) to play. Release the note key to stop (chord/melody), or use other keys as below.

---

## Chord mode

| Keys | Description |
|------|-------------|
| **Note key** (hold) | Chord root; name and shape on display |
| **3rd** | Major/minor third (with **m**: sus2 / sus4) |
| **5th** | Perfect / aug / dim fifth (with **m**) |
| **7th** | Add or remove chord 7th |
| **m** | Minor (also affects 3rd/5th modifiers above) |
| **Key pressure** | Expression (CC11) on the held note |
| **Neighbour keys** (expr up/down rows) | Pitch bend while holding the root |
| **Strum comb** (12 pads) | While holding a note key: touch pads to sound stacked chord tones (instead of the auto-arpeggio if any pad is already held). Release the note key to stop |

---

## Melody mode

| Keys | Description |
|------|-------------|
| **Note keys** | Scale notes (respects capo) |
| **#** | Sharp on the current note |
| **Two adjacent keys** (quick double) | Sharp via slide between neighbours |
| **3rd** | One octave down |
| **5th** | One octave up |
| **Shift** | One octave up |
| **7th / m** (while a note sounds) | Pitch bend up / down |
| **Note key pressure** | Expression (CC11) on the sounding note |

Note names appear on the display while you play.

---

## Drum mode

| Keys | Description |
|------|-------------|
| **Note keys** | Drum sounds (name on display) |
| **Function keys** | Still work while a drum key is held |

---

## Volume

| Keys | Description |
|------|-------------|
| **Vol** (hold) | **Master volume** — tap **7th** or **m** (Up/Down) to adjust; harder press = larger step |
| **Shift** (tap while Vol held) | Switch between **master** and **channel** volume (live channels 0 and 1). **Shift + Vol** at entry starts in channel volume |
| | Channel volume blocked while a loop is recording |
| | While Vol is held, note keys and mode changes are ignored |

**Startup default:** master volume 75% (95/127); channel volume 100.

---

## Capo and global tuning

| Keys | Description |
|------|-------------|
| **Capo** (hold) | **Transpose** by semitones |
| **Note key** | Set capo to that key's pitch class |
| **#** (tap) | Toggle +1 semitone on the chosen step |
| **Shift** (tap while Capo held) | Switch between **capo** and **global tuning**. **Shift + Capo** at entry starts in tuning |
| **7th / m** (Up/Down, in tuning) | Raise or lower tuning (~1-7 cents per firm press) |
| **7th + m together** (in tuning) | Reset to **+0**; frozen until both are released |
| **Release Capo** | Exit; capo changes apply if you adjusted transpose during the session |

Reference pitch is A440 at 0. Tuning affects live play and loop playback. Capo = semitone shift; tuning = fine cent offset.

---

## Instrument

| Keys | Description |
|------|-------------|
| **Instr** (hold) | Choose MIDI instrument |
| **Note key** | Pick instrument **family** |
| **Shift** (tap while Instr held) | Switch between **low** and **high** instrument banks (eight families each). **Shift + Instr** at entry starts in the high bank |
| **Same or another note key** (second press) | Pick instrument within family; repeat same key to cycle |
| | Not available while recording a loop |

---

## Looper

| Keys | Description |
|------|-------------|
| **Loop** (hold) | Looper UI; empty slots glow **blue** (hint); recorded slots show red/green/orange status |
| **Note key** (empty slot) | Arm record on that track; metronome starts |
| **Note key** (tap again after release while arming) | Toggle **quick loop** mode (chord taps; metronome paused) |
| **Note key** (recorded track) | Toggle play/stop |
| **Note key** (hold >1.5 s on existing track) | Delete that loop |
| **#** (tap twice) | Tap tempo — two taps set BPM; metronome turns on |
| **7th / m** | BPM +5 / -5 (while in looper) |
| **5th** | Toggle metronome click (can stay on after leaving looper if enabled here or via tap tempo) |
| **Release Loop** | Leave looper |

Up to six loop slots on note keys. Each loop uses its own MIDI channel pair for recording.

---

## Tips

- While **Vol**, **Loop**, **Instr**, or **Capo** is held, actionable keys glow **blue** (left-hand controls and relevant note keys).
- While **Vol**, **Instr**, or **Capo** is held, a quick **Shift** tap switches sub-modes (master/channel, low/high bank, capo/tuning).
- **Shift** at entry still picks the alternate sub-mode; release **Shift** before tapping to switch again.
- **Vol**, **Instr**, and **Capo** UIs block accidental note input and mode changes while active.
- Mode name appears briefly on the display when you change **Shift + 3rd / 5th / 7th**.

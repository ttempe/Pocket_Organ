# Pocket Organist — Agent Guide

CircuitPython firmware for a portable MIDI chord organ with hall-effect keys, OLED display, and on-board or USB MIDI out. Targets **RP2040** (no FPU); current hardware revision is **V31** (`version.py`).

## Entry point

- `code.py` — bootstraps the app (typically `import pocket_organist`).
- `pocket_organist.py` — main application loop (`PocketOrgan` class).

## Module map

| Module | Role |
|--------|------|
| `board_po.py` | **Pin allocation and hardware constants only** — mux GPIO, ADC, buttons, display SPI, MIDI, strum I2C (`strum_i2c`, `STRUM_*`), calibration tables. Import as `import board_po as board`. |
| `mux.py` | MUX shift-register addressing, hall-sensor power (GP4), `vbat_read()` / `vusb_read()`. |
| `keyboard.py` | Hall-key scanning, chord/melody/drum modes, calibration helpers. |
| `display.py` | 128×64 SSD1306 via **displayio** (`auto_refresh=False`; call `disp.refresh()` after updates). |
| `battery.py` | OCV lookup SOC gauge; charging animation via `disp_bat_charging()`. |
| `polyphony.py` | Chord/melody/drum logic and MIDI note output. |
| `looper.py` | Loop recording/playback. |
| `midi.py` | MIDI message helpers (uses `board.midi`). |
| `backlight.py` | NeoPixel key backlight; `backlight_map` in `board_po.py` maps key index to pixel. |
| `bs8112a.py` | Holtek BS8112A-3 I2C driver; `read_keys()` → 12-bit pad mask. |
| `instr_names.py` | GM instrument name tables. |
| `version.py` | Board revision number. |

Legacy / test code lives in `misc/`.

**User-facing documentation:** [`USER.md`](USER.md) — key combinations and feature descriptions for musicians. Keep it in sync when changing UI or controls.

## Application features (agent summary)

| Area | Implementation notes |
|------|----------------------|
| **Modes** | `keyboard.mode`: chord / melody / drum via Shift+3rd/5th/7th. |
| **Volume** | Master vs channel; Shift+Vol at entry or Shift tap while Vol held (`_consume_shift_toggle`). `keyboard.ui_lock` during UI. Startup master = `127 * 75 // 100`. |
| **Capo / tuning** | `loop_capo_or_tune()` — Shift+Capo at entry or Shift tap toggles capo vs tuning. Capo: `polyphony.transpose`. Tuning: GS SysEx, `global_tuning_tenths`, peg*10, Up+Down reset. `ui_lock` throughout. |
| **Instrument** | `loop_instr()` — `high_bank` toggled by Shift tap while Instr held (Shift+Instr at entry = high bank). |
| **Metronome** | `metronome.user_wants` — persists click after looper exit when enabled via Fifth or tap tempo; auto-on from recording arm stops on exit unless `user_wants`. |
| **Looper** | In-memory `TrackStore`; CC7 baked at first note; `leave_looper()` / `apply_ui()` metronome cleanup. |
| **Melody expression** | CC11 on melody channel from key pressure; pitch bend from 7th/m keys. |
| **Display sliders** | `disp_slider()` always updates `text_zones[0].text` (dynamic titles e.g. tuning cents). |
| **Strumming** | 12-pad comb via BS8112A on I2C (GP7 SCL, GP6 SDA, addr 0x50). Hold chord root, touch pads for stacked chord tones; `keyboard.strum_keys` / `polyphony` note on/off. |

## Conventions

- **Always** `import board_po as board` — never bare `import board_po` or `from board_po import …` (except inside `board_po.py` itself).
- **GPIO stays in `board_po.py`**; mux addressing and sensor power live in `mux.py`.
- Hall sensor power: **GP4 high = off**, **GP4 low = on**. Power on before MUX/ADC reads; power off after.
- Display colors for shapes: use `0xFFFFFF` / `0x000000`, not small integers.
- Fonts: PCF in `fonts/`; preload with `font.load_glyphs()` (not dummy `Label`s).
- Battery icon: procedural `Rect` gauge at x=108 in the 8px status bar; persistent (do not clear in `Display.clear()`).
- Keep changes **minimal and focused**; match existing style; avoid drive-by refactors.

## Display layout

- Top **8 px**: status bar (latency ~x=24, battery gauge ~x=108).
- Bottom **56 px**: chord name (large font) or up to 3 lines (medium font) + tips zone.

## Battery

- Single-cell Li-ion (10440), OCV interpolation with **10% reserve** (display 0% at 10% true SOC).
- `battery.py` uses `mux.vbat_read()` / `mux.vusb_read()`; USB ≥ 4.5 V → charging animation.

## Hardware notes

- Analog keys via 3-line MUX + 2 ADCs; calibration in `board.keyb_min` / `board.keyb_range`.
- `keyboard.calibrate()` and `keyboard.test_power_settle()` for bring-up.
- Power: `board.power_off` (GP13), `board.force_on` (GP14).

## What not to do

- Do not commit unless explicitly asked.
- Do not move GPIO out of `board_po.py` or duplicate mux logic outside `mux.py`.
- Do not use `fill=0` on `Rect` borders (renders opaque black on OLED).
- Avoid `pop()`/`append()` on display objects in hot loops without manual refresh batching (causes flicker).

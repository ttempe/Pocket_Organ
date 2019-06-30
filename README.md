# Pocket Organ

A modern musical instrument instrument that fits in your pocket

Most instruments we play today are designed around the manufacturing constrains of hundreds of years ago.
Newer instruments are often electronic versions, with the same or similar user interface.

Really novel instruments are either:
1. excellent, but really exensive brand-name products that only a dedicated musician would buy (eg: the Roli Seaboard, the Dualo Du-Touch, the Hang steel drum, EWI electronic woodwind...)
2. cheap, but not good enough for a musician, lacking in depth and/or playability (eg: the roll-up keyboards, stylophone, Otamatone...)

It doesn't have to be that way, though.

The aim of this project is to develop a real music instrument that:
* is easier to learn and play than most instruments out there
* is so affordable that aspiring musicians would consider it
* has enough depth and expessivity that experienced musicians might appreciate it
* is convenient and versatile, fitting in your pocket and playable over a headphone or a MIDI toolchain.
* is widely available, ideally from multiple manufacturers, under the generic term "pocket organ".

# Hardware design

* The PCB design is published on: https://lceda.cn/ThomasTempe/Pocket_Musical_Instrument
 * The device is built around a micro-controller (currently AtMEGA 32u4) and single-chip MIDI synth (SAM2695).
 * The PCB is two-sided, but all the solderable components are on the same side. It is designed to use 0402 and QFN components, and is unfortunately not practical to home-etch or hand-solder ; however, you can order the PCB for a low price directly from https://szlcsc.com. If you have a China address, you can even have them do prototype pick-and-place soldering for most components (still requires SMT hand-soldering skills to finish, though). 
 * It has a LiPo battery that lasts a few hours, and a USB port for charging and playing.
* The enclosure is published on: https://a360.co/2Yl1HuQ
 * It is smaller but thicker than a smartphone (12.5*6*1.5cm)
 * It can be 3D-printed
* The device uses a silicone keypad for all push buttons
 * You can find a 3D model together with the enclosure, and 3D-print it, then use it to cast silicone
 * some of the keys are pressure-sensitive, using Velostat.
 * The process is partly documented here: https://www.instructables.com/id/Analog-Pressure-sensitive-Push-button/
* There is provision for an OLED display, that will feed back what the musician is playing (to ease the learning process). Not working yet, though.

# Musical design

This is work in progress. 
The most interesting part of this project is to develop a musically sound, progessive, easy-to-learn user interface for playing music.

Contrary to most instruments, the pocket organ plays chords by default.
A single-finger press gives a major chord. Chord modifier key combinations allow to change the shape of the chord.
A "melody" mode allows to play individual notes.
A looper allows to overlay sequences.
The note keys (Do~Si) are also pressure-sensitive. The best way to turn that into expression is still to be determined.

# Current status

* Software features are half-way through.
* Small-series (3D printed, hand-assembled) user testing has just begun as of June 2019.
* If you're interested in this project, please get in touch, as the building process is not fully documented yet.

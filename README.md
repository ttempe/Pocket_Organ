# Pocket Organ
A modern music instrument instrument that fits in your pocket

Most instruments we play today are designed around the manufacturing constrains of hundreds of years ago.
Newer instruments are often electronic versions, with the same or similar user interface.

Really novel instruments are either:
1. excellent, but really exensive brand-name products that only a dedicated musician would buy (eg: the Roli Seaboard, the Dualo Du-Touch...)
2. cheap, but not good enough for a musician, lacking in depth and/or playability (eg: the roll-up keyboards, stylophone...)

It doesn't have to be that way, though.

The aim of this project is to develop a real music instrument that:
* is easier to learn and play than most instruments out there
* is so affordable that aspiring musicians would consider it
* has enough depth and expessivity that experienced musicians might appreciate it
* is convenient and versatile, fitting in your pocket and playable over a headphone or a MIDI toolchain.
* is widely available, ideally from multiple manufacturers, under the generic term "pocket organ".

# Hardware design
The device is built around a micro-controller (currently AtMEGA 32u4) and single-chip MIDI synth (SAM2695).
It has a LiPo battery that lasts a few hours, and a USB port for charging and playing.
It is smaller but thicker than a smartphone (12.5*6*1.5cm)
It has a silicone keypad. Some of the keys are pressure-sensitive for expression control.
There is provision for a display, that will feed back what the musician is playing (to ease the learning process).

# Musical design
This is work in progress. 
The most interesting part of this project is to develop a musically sound, progessive, easy-to-learn user interface for playing music.

Contrary to most instruments, the pocket organ plays chords by default.
A single-finger press gives a major chord. Chord modifier key combinations allow to change the shape of the chord.
A "melody" mode allows to play individual notes.
A looper allows to overlay sequences.
The note keys (Do~Si) are also pressure-sensitive. The best way to turn that into expression is still to be determined.

# Current status
I have a working prototype (3D-printed enclosure).
Software features are half-way through.

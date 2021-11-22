# Pocket Organ

A modern musical instrument instrument that fits in your pocket

https://www.facebook.com/Thomass-pocket-organ-109581037453852

https://archive.org/details/hopeconf2020/20200730_0900_The_Pocket_Organ.mp4

Most instruments we play today are designed around the manufacturing constrains of hundreds of years ago.
Newer instruments are often electronic versions, with the same or similar user interface.

Really novel instruments are either:
1. excellent, but expensive small-volume brand-name products that only a dedicated musician would buy (eg: the Roli Seaboard, the Dualo Du-Touch, the Hang steel drum, the Sylphyo electronic woodwind, Artiphon Instrument 1, Jamstik ...)
2. cheap, but not good enough for a musician, lacking in depth and/or playability (eg: the roll-up keyboards, stylophone, Otamatone...)

It doesn't have to be that way, though.

The aim of this project is to develop a real musical instrument that:
* is easier to learn and play than most instruments out there
* is so affordable that aspiring musicians would consider it
* has enough depth and expessivity that experienced musicians might appreciate it
* is convenient and versatile, fitting in your pocket and playable over a headphone (includes a synthetizer) or a MIDI workstation.
* is widely available, ideally from multiple manufacturers, under the generic term "pocket organ".

See the general presentation: https://github.com/ttempe/Pocket_Organ/blob/master/Doc/2019-06-22%20Pocket%20Organ.pdf

![3D rendering of Pocket Organ V7](https://github.com/ttempe/Pocket_Organ/blob/master/Pictures/V7/V7_rendering_small.png)

# Hardware design

* The PCB design is published on: https://lceda.cn/ThomasTempe/Pocket_Musical_Instrument
 * The PCB is two-sided, but all the solderable components are on the same side. It is designed to use 0402 and QFN components, and is unfortunately not practical to home-etch or hand-solder ; however, you can order the PCB for a low price directly from https://szlcsc.com. If you have a China address, you can even have them do prototype pick-and-place soldering for most components (still requires SMT hand-soldering skills to finish, though). 
 * It has a LiPo battery that lasts a few hours, and a USB port for charging, and for MIDI over USB.
* The enclosure is published on: https://a360.co/2Yl1HuQ

# capacitive touch keys: prototypes V10+

I've basically restarted from scratch at the beginning of 2020. This branch has:
* capacitive touch keys, which I'm trying to make somehow analog (currently under experimentation)
* a STM32F405 microcontroller
* I've re-written the whole code in Micropython. See the "Py" directory

![Photo of V12 prototype](https://github.com/ttempe/Pocket_Organ/blob/master/Pictures/V12/V12_assembled.jpg)

As of August 2021, V18 is giving quite good keys sensing, expression (analog input on the note keys) and responsiveness.

# Pressure-sensitive: prototypes V6 to V9

This branch of the project culminated in functional prototypes.
The analog keys use a sheet of Velostat (a pressure-sensitive, conductive plastic) and a silicone keypad.

* The device is built around a micro-controller (currently AtMEGA 32u4) and single-chip MIDI synth (SAM2695).
* code is written in C++, for the Arduino IDE. See the "src" directory.
* It is smaller but thicker than a smartphone (12.5*6*1.5cm)
* The device uses a silicone keypad for all push buttons
 * You can find a 3D model together with the enclosure, and 3D-print it, then use it to cast silicone
 * The process is partly documented here: https://www.instructables.com/id/Analog-Pressure-sensitive-Push-button/
 
![Photo of V8 prototype](https://github.com/ttempe/Pocket_Organ/blob/master/Pictures/V7/V8_proto_small.PNG)
 
I've decided to move away from this principle, after:
* realizing that it would be a significant challenge to further lower the key mechanical resistance
* experiencing the Sylphyo's amazingly expressive capacitive touch keys.


# Musical design

This is still work in progress; and probably the most interesting part of the project.

You can play a lot of nice tunes on a piano; but they all require multiple fingers. If you come to a piano with just one finger, the result is likely to sound unpleasant.

In building the user interface, I'm trying to spare some fun for each level of play. This is why it will play chords by default. Chords are undemanding, gratifying, and you can probably find your favourite song on any tablatures repository.

More advanced play (playing one note at a time, adding expression, more exotic chord shapes...) are all there waiting for you to build up your dexterity and coordination; each step takes one more finger to play.

My ultimate goal is that the design of the instrument should progressively nudge the player on the first steps of his musical path. Each successive step should bring additional challenge, and more reward. After a few months, an assiduous player should feel confident to move to his second instrument. But if I've done my job right, the pocket organ will remain an instrument of choice.

# Features

* Under the right hand, there is one analog key for each note of the diatonic scale (Do~Si; plus a second Do). Half-tones are obtained by pressing down two adjacent notes. The keys are laid out such that notes separated by full tones are side-by-side (Do-Re-Mi, Fa-Sol-La-Si, Do).
* Under the left hand are chord shape keys, a "shift" key, and a volume slider.
* Lastly, there is a "strumming comb" slider at the bottom, that allows to easily play multiple notes of the current chord.

Additional features include:
* an 8-track looper (with color backlight codes under the note keys, similar to the Dualo Du-Touch)
* a small OLED display, to serve as a feedback loop. It will ease musical exploration and progressive disclosure by displaying the name of the note/chord being played, and name the features being used.
* function keys allow to select the instrument from the MIDI bank, tune the pitch, transpose, access the looper, and change to melody or drum pad mode.

# The end game

An Open Source Software is easy to publish: you just put it on GitHub, and call it a day. A hardware project means every single unit needs to be manufactured, ideally in a cost-effective way. 

My objective is to put 1 million devices in the hands of prospective players. That will take investment in manufacturing, distribution, and above all marketing, all things that are not in my realm.

I see myself as the person who will develop a product, then set the conditions right so that others may do the manufacturing and distribution. That means building a community, building the word-of-mouth, generating enthusiasthm and possibly looking for partners for distribution and marketing. And then, let them run away with it, and hopefully make money. The product will not reach its users unless someone makes money at every step of the process. I'm the only one who is expected to work for free. And maybe you, the supporter, the enthusiast, the player.

The project's open source nature may be a boon, or a hindrance. I might close back the source, strategically, if I think it can help someone else sell the product. Ultimately, it is better for it to be universally available as black-box commodity than open source on a dusty Github page.

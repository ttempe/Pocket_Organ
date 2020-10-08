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
* a STM32F405 MCU
* I've re-written the whole code in Micropython. See the "Py" directory

![Photo of V12 prototype](https://github.com/ttempe/Pocket_Organ/blob/master/Pictures/V12/V12_assembled.jpg)

As of October 2020, I have a working V14 protopype, but am not fully satisfied with the touch sensors (input is noisy and a little laggy). I am working on V15, which will feature a new capacitive sensor chip, as well as a strumming comb.

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

More advanced play (playing one note at a time, adding expression, more exotic chord shapes...) are all there waiting for you to build up your dexterity and coordination; they all take additional fingers to play.

My ultimate goal is that the design of the instrument should progressively, nudge the player on the first steps of his musical path. Each successive step should bring additional challenge, and more reward. After a few months, an assiduous player should feel confident to move to his second instrument. But if I've done my job right, the pocket organ will remain the instrument of choice for certain occasions.

# Features

Under the right hand, there is one analog key for each note of the diatonic scale (Do~Si), plus one Sharp key.

Under the left hand are chord shape keys, a "shift" key for playing notes and 2 to 3 sliders.

Additional features include:
* an 8-track looper (with color backlight codes under the note keys, similar to the Dualo Du-Touch)
* a small OLED display, to serve as a feedback loop. It will ease musical exploration by displaying the name of the note/chord being played, and name the features being used.
* function keys allow to select the instrument from the MIDI bank, tune, transpose, and possibly other features.

# The end game

This project is quite a moonshot. Reaching my goal means putting large numbers, maybe millions of instruments in the hands of prospective players. This means it will not stop at design and small-scale prototyping. The instrument will ultimately need to enter mass production.

I thoroughly enjoy the design and development phase. I have professional experience in the manufacturing industry, and live in China, where I can easily find suppliers. I will most likely end up building the first 100 on my kitchen table.

However, ultimately, the instrument will need to be produced at scale. It is not my goal, or my area of expertise, to run a manufacturing and distribution operation. Someone else will need to do that, most likely an established company. 

I currently plan to promote the project through social networking and crowdfunding, demonstrate the commercial potential, and hope for someone to pick it up (ideally multiple companies).
Its open source nature may be a boon, or a hindrance. I might close back the source, strategically, if I think it can help someone else sell the product. Ultimately, it is better for it to be universally available as black-box commodity than open source on a dusty Github page.

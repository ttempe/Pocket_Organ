
#ifndef HEADER_POCKET_ORGAN
  #define HEADER_POCKET_ORGAN

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define MIDI_SERIAL Serial1

/////////////////
//Choose output
//#define OUT_USB //Send Midi commands to the USB as a Midi device (with 32u4 or Arduino; use a computer as synth)
#define OUT_SERIAL //Send Midi commands on the serial line, to a Midi chip (embedded synth)

///////////////////
//Function buttons
#define B_SHARP  0
#define B_MIN    1 
#define B_7      2
#define B_SUS    3
#define B_AUG    4
#define B_VOL    5
#define B_INSTR  6
#define B_LOOP   7
#define B_RYTHM  8
#define B_MELODY_LOCK  8
#define B_MELODY 9 
#define B_PLUS   2
#define B_MINUS  4
#define B_ZERO   3
#define B_TRANSP 6
#define B_TUNE   7

//TODO
#define B_SUS2   8
#define B_ADD9   8
#define B_FAST   8

/////////////////
//MIDI codes
#define CHANNEL 0
#define MIDI_VOLUME 7
#define MIDI_BANK 0
#define MIDI_MODULATION 1
#define MIDI_EXPRESSION 0x0B
#define MIDI_EFFECT1 0x0C
#define MIDI_EFFECT2 0x0D
#define MIDI_ATTACK 0x49
#define MIDI_RELEASE 0x48
#define MIDI_DECAY 0x4B
#define MIDI_SOUND_VARIATION 0x46
#define MIDI_SOUND_TIMBRE 0x47
#define MIDI_BRIGHTNESS 0x4A
#define MIDI_VIBRATO_RATE 0x4C
#define MIDI_VIBRATO_DEPTH 0x4D
#define MIDI_PITCH_BEND 0xE0


/////////////////
//Global variables
extern Adafruit_SSD1306 display;
extern byte current_instrument;

/////////////////
//Digital buttons
#define NB_DB 10
static char DB[NB_DB] = {6, 12, 0, 10, 8, 7, 17, 16, 11, 5};


/////////////////
//EEPROM addresses

#define E_VOLUME 0
#define E_AB_CALIBRATION 1    //28 octets
#define E_LOOP_STATUS 30      //1 octet; which loops were recorded
#define E_LOOP_LENGTHS 32     //16 octets
#define E_LOOP_INSTRUMENTS 48 //8 octets


/////////////////
//I2C addresses

#define ADDR_EEPROM 0x50

/////////////////
//Prototypes
void playNote(byte pitch);
void chordPlayGuitar(char degree);
void chordUpdate(char vel);
void chordStop();


/////////////////
//Determine which notes to play simultaneously
//for a given chord
//Completely mimics guitar chords
static char guitarStrings[6] = {52, 57, 62, 67, 71, 76}; //MI LA RE SOL SI MI
static char guitarChords[7][7][6] = //7h, Maj/Min, degree*7, string*6
{ //About 320 octets of RAM
  //http://all-guitar-chords.com/guitar_chords_common.php
  {//Major 
    {0, 1, 0, 2, 3, -1},//Do
    {2, 3, 2, 0, -1, -1},//Re
    {0, 0, 1, 2, 2, 0}, //Mi
    {1, 1, 2, 3, -1, -1},//Fa
    {3, 0, 0, 0, 2, 3},//Sol
    {0, 2, 2, 2, 0, -1}, //La
    {2, 4, 4, 4, 2, -1} //Si
  },
  { //Minor
    {3, 1, 0, 1, 3, -1},//Do
    {1, 3, 2, 0, -1, -1},//Re
    {0, 0, 0, 2, 2, 0}, //Mi
    {1, 1, 1, 3, 3, 1}, //Fa
    {3, 3, 3, 5, 5, 3}, //Sol
    {0, 1, 2, 2, 0, -1}, //La
    {2, 3, 4, 4, 2, -1} //Si
  },
  { //Major7
    {0, 1, 3, 2, 3, -1}, //Do 
    {2, 1, 2, 0, -1, -1}, //Re
    {0, 0, 1, 0, 2, 0}, //Mi
    {1, 1, 2, 1, 3, 1}, //Fa
    {1, 0, 0, 0, 2, 3}, //Sol
    {0, 2, 0, 2, 0, -1}, //La
    {2, 0, 2, 1, 2, -1} //Si
  },
  { //Minor7
    {8, 8, 8, 8, 10, 8}, //Do 
    {1, 1, 2, 0, -1, -1}, //Re
    {0, 0, 0, 0, 2, 0}, //Mi
    {1, 1, 1, 1, 3, 1}, //Fa
    {3, 3, 3, 3, 5, 1}, //Sol
    {0, 1, 0, 2, 0, -1}, //La
    {2, 3, 2, 4, 2, -1} //Si
  },
  { //9
    {-1, 5, 7, 5, 7, 8},//Do
    {-1, 7, 9, 7, 9, 10},//Re
    {-1, 9, 11, 9, 11, 12},//Mi
    {-1, 10, 12, 10, 12, 13},//Fa
    {-1, 0, 2, 0, 2, 3}, //Sol
    {-1, 2, 4, 2, 4, 5}, //La
    {-1, 4, 6, 4, 6, 7}//Si
  },
  { //Sus4
    {8, 8, 10, 10, 10, 8}, //Do
    {10, 10, 12, 12, 12, 10}, //Re
    {0, 0, 2, 2, 2, 0}, //Mi
    {1, 1, 3, 3, 3, 1},//Fa
    {3, 3, 5, 5, 5, 3}, //Sol
    {5, 5, 7, 7, 7, 5}, //La
    {7, 7, 9, 9, 9, 7}//Si
  },
  { //Sus2
    {3, 3, 5, 5, 3, -1},//Do
    {5, 5, 7, 7, 5, -1},//Re
    {7, 7, 9, 9, 7, -1}, //Mi
    {8, 8, 10, 10, 8, -1}, //Fa
    {10, 10, 12, 12, 10, -1}, //Sol
    {0, 0, 2, 2, 0, -1}, //La
    {1, 1, 3, 3, 1, -1} //Si
  } 
};


#endif //HEADER_POCKET_ORGAN

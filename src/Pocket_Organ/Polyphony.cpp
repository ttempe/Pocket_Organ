#include "arduino.h"
#include "Polyphony.h"
#include "piano.h"
#include "Support.h"
#include "Looper.h"

///////////////////////////////////////////////
//Chords playing

Polyphony::Polyphony(Looper* l){
  myLooper = l;
}

void Polyphony::playNote(char pitch){
  notesQueue[queueToPlayI] = pitch;
  queueToPlayI++;
  queueToPlayI%=QUEUE;
  queuePlaying=1;
}

void Polyphony::chordStop(){
  setMidiControl(0xB0, 0x7B, 0x00, 0);
  queuePlaying=0;
  queueToPlayI=0;
  queuePlayedI=0;
  myLooper->recordNote(0xB0, 0x7B, 0x00);
}

void Polyphony::chordUpdate(char vel){
  static long lastT, velSpeedUp=0;
  unsigned long int t=micros();
  velSpeedUp += min((t-lastT)*(127-vel)/96,1000);
  if (queuePlaying){
    if (queuePlayedI!=queueToPlayI and t>=velSpeedUp*(not playingFast)+timeToPlay){
      noteOn(notesQueue[queuePlayedI], playingFast?92:64,0);
      myLooper->recordNoteOn(notesQueue[queuePlayedI], playingFast?92:64);
      queuePlayedI++;
      queuePlayedI%=QUEUE;
      timeToPlay = t+15000+10000*(not playingFast);
      velSpeedUp = 0;
    }
  }
  lastT=t;
}

void Polyphony::noteStop(char pitch){
  noteOff(pitch, 0);
  myLooper->recordNoteOff(pitch);
  
}

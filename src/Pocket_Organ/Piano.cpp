///////////////////////////////////////////////
//Piano chords generator

#include "arduino.h"
#include "piano.h"
#include "Polyphony.h"
#include "Pocket_Organ.h"

//Trick: The 3rd is defined by the "minor" button, but the 7th is defined by the scale
char key = 7; //Default to Sol

const char AB_notes[7] = {0, 2, 4, 5, 7, 9, 11};



void Piano::readModifierKeys(){
  b_minor      = not digitalRead(DB[B_MIN]);
  b_seventh    = not digitalRead(DB[B_7]);
  b_sus        = not digitalRead(DB[B_SUS]);
  b_aug        = not digitalRead(DB[B_AUG]);
  b_sharp      = not digitalRead(DB[B_SHARP]);
}

void Piano::playChordNotes(){
  P->playNote(tonic-12);//BASS
  P->playNote(tonic);
  P->playNote(third);
  P->playNote(fifth);
  if (seventh!=-1){
    P->playNote(seventh);
  }  
}

void Piano::chordPlay(char degree, char transpose){
  //read the kets
  readModifierKeys();

  //Process key combinations
  char minor = b_minor and not b_sus and not b_aug;
  char sus4 = b_sus and not b_minor;
  char sus2    = b_sus and b_minor; //Sus+Minor gines a Sus2 instead of a Sus4
  char aug = b_aug and not b_minor;
  char dim = b_aug and b_minor; //Augmented chord: press Aug. Diminished: press Aug+Aug
  
  //Compute the chord
  tonic   = (AB_notes[degree]+b_sharp)%12+60;
  third   = (tonic+4-minor+sus4-sus2*2)%12+60;
  fifth   = (tonic+7+aug-dim)%12+60;
  seventh = b_seventh?(tonic+10-b_minor)%12+60:-1;
  
  //play
  playChordNotes();

}


void Piano::chordRefresh(){

  //read the keys and check for changes
  char b_sharp_old = b_sharp;
  char b_minor_old  = b_minor;
  char b_seventh_old = b_seventh;
  char b_sus_old = b_sus;
  char b_aug_old = b_aug;
  readModifierKeys();
  
  if (b_sharp != b_sharp_old){
    playChordNotes();
  }
  if (b_seventh_old!=b_seventh){
    if (b_seventh){
      seventh = tonic+10-b_minor;
      P->playNote(seventh);
    } else{
      P->noteStop(seventh);
    }
  }
  if (b_sus_old != b_sus){
    P->noteStop(third);  
    char minor = b_minor and not b_sus and not b_aug;
    char sus4 = b_sus and not b_minor;
    char sus2 = b_sus and b_minor; //Sus+Minor gives a Sus2 instead of a Sus4
    third = tonic+4-minor+sus4-sus2*2;
    P->playNote(third);
  }
  if (b_aug_old != b_aug){
    P->noteStop(fifth);  
    char aug = b_aug and not b_minor;
    char dim = b_aug and b_minor; //Augmented chord: press Aug. Diminished: press Aug+Aug
    fifth   = tonic+7+aug-dim;
    P->playNote(fifth);
  }
}

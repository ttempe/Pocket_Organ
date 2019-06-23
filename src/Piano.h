///////////////////////////////////////////////
//Piano chords generator

#ifndef HEADER_PIANO
  #define HEADER_PIANO

#include "Polyphony.h"

class Piano {
  private:
    char tonic, third, fifth, seventh;
    char b_seventh, b_sus, b_aug, b_minor, b_sharp;
    void readModifierKeys();
    void playChordNotes();
    Polyphony *P;
  public:
    Piano(Polyphony *pp){
      P = pp;
    }
    void chordPlay(char degree, char transpose);
    void chordRefresh();
};


#endif //HEADER_PIANO

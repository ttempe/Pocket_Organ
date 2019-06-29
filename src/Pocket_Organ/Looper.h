///////////////////////////////////////////////
//Looper: record midi events into flash memory, then replay them

/* There are 16 MIDI channels
 * channels 0~8 are used (0=played directy, 1=Do, 2=Re, 3=Mi...)
 * 
 */

#ifndef HEADER_LOOPER
  #define HEADER_LOOPER

#include "Support.h"

#define NB_LOOPS 7

class Looper {
  public:
    Looper(); //constructor 
    
    char channel; //current channel
    char currentlyRecording;
    char statusAll[NB_LOOPS]; //0=not recorded; 1=recorded

    void displayStatus();
    void startRecording();
    void recordNote(char note);
    
};

#endif //HEADER_LOOPER

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
#define MEMORY_PER_LOOP 9362

class Looper {
    long unsigned int start[NB_LOOPS]; //Start address, in memory, of each loop
    long unsigned int finish[NB_LOOPS];//End address, in memory, of the recorded contents fro each loop
    
    char instruments[NB_LOOPS]; //selected MIDI instruments

    char currentlyRecording=-1; //channel#, 0=none, 1=Do, 2=Re...
    unsigned char recorded; //one bit per channel, 0=not recorded; 1=recorded. 1=Do, 2=Re, 4=Mi...
    unsigned char playing;  //one bit per channel, 0=not playing; l=playing. 1=Do, 2=Re, 4=Mi...

    unsigned long int loopStartTime; //time of start of loop, modulo maxLoopDuration
    unsigned long int maxLoopDuration, recordingStartedTime;

  public:
    Looper(); //constructor 
    void displayStatus(); //display through 
    void startRecording(char channel);
    void stopRecording();
    void deleteRecord(char channel);
    void togglePlay(char channel); //start or stop playing a given channel
    void recordNote(char note, char vel);
    
};

#endif //HEADER_LOOPER

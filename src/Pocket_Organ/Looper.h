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

    byte recorded; //one bit per channel, 0=not recorded; 1=recorded. 1=Do, 2=Re, 4=Mi...
    byte playing;  //one bit per channel, 0=not playing; l=playing. 1=Do, 2=Re, 4=Mi...

    unsigned long int loopStartTime; //time of start of loop, modulo maxLoopDuration
    unsigned long int maxLoopDuration, recordingStartedTime;

  public:
    char currentlyRecording=-1; //channel#, -1=none, 0=Do, 1=Re...
    Looper(); //constructor 
    void displayStatus(); //display through SR key backlight
    void startRecording(char channel);
    void stopRecording();
    bool isRecorded(byte loop);
    void deleteRecord(byte channel);
    void togglePlay(byte channel); //start or stop playing a given channel
    void recordNote(char note, char vel);
    
};

#endif //HEADER_LOOPER

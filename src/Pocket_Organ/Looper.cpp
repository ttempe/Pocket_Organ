///////////////////////////////////////////////
//Looper: record midi events into flash memory, then replay them

/* TODO:
    change non-loop channel to something else
    record expression
    blink the key while recording a loop?
    Change the "playing" status only when releasing the "loop" button
    Test memory overrun or timeout conditions
    Make sure all instruments stop playing when the user interrupts loop playback
    Round off user timing errors 
    Handle the case where the player changes the instrument while recording a loop
    Playback now stops when entering melody mode
    Set MaxLoopDuration according to the longest loop currently playing
    When enabling a loop while another was playing, check that the playing of all past events doesn't make sound
*/


#include "arduino.h"
#include "Looper.h"
#include "Pocket_Organ.h"
#include <EEPROM.h>

///////////////////////////////////////////////
//Constructor
Looper::Looper() {
  maxLoopDuration = 0;
  for (byte i = 0; i < NB_LOOPS; i++) {
    start[i] = MEMORY_PER_LOOP * i;
    //EEPROM.get(E_LOOP_LENGTHS   + 2 * i, finish[i]);
    //EEPROM.get(E_LOOP_DURATIONS + 4 * i, duration[i]);
    maxLoopDuration=max(maxLoopDuration, duration[i]);
  }
  //EEPROM.get(E_LOOP_STATUS, recorded);
};

///////////////////////////////////////////////
//User Interface & control

void Looper::displayStatus() {
  //Green: recorded
  //Orange: playing (assumes recorded)
  //Red: recording
  byte recording = (-1 < currentlyRecording) ? 1 << currentlyRecording : 0;
  byte red = playing | recording;
  byte green = recorded & (~recording);
  SR_map(green, red);
}

void Looper::startRecording(char channel) {
  if (currentlyRecording != -1) { //don't record two tracks at once
    return ;
  }
  CONSOLE.print("Start recording channel "); CONSOLE.println((byte)channel);

  currentlyRecording = channel;
  recordingStartedTime = 0; //will set the t=0 when playing the 1st button

  //record instrument
  ST_write5(start[channel], 0, 0xC0 | channel, 0, current_instrument);
  finish[currentlyRecording]=5;
}

void Looper::stopRecording() {
  if (currentlyRecording == -1) { //check we were actually recording something
    return;
  }
  CONSOLE.print("Stop recording channel "); CONSOLE.print((byte)currentlyRecording);  CONSOLE.print(" ("); CONSOLE.print(finish[currentlyRecording]); CONSOLE.println(" bytes written)");
  recorded += 1 << currentlyRecording;
  EEPROM.update(E_LOOP_STATUS, recorded);
  EEPROM.update(E_LOOP_LENGTHS   + 2 * currentlyRecording, finish[currentlyRecording]);
  EEPROM.update(E_LOOP_DURATIONS + 4 * currentlyRecording, duration[currentlyRecording]);
  currentlyRecording = -1;

  maxLoopDuration=0;
  for (byte i=0; i<NB_LOOPS; i++){
    maxLoopDuration=max(maxLoopDuration, duration[i]);
  }
}

void Looper::deleteRecord(byte channel) {
  CONSOLE.print("Deleting record "); CONSOLE.println(channel);
  playing = playing & ~(1 << channel);
  recorded = recorded & ~(1 << channel);
  finish[channel] = 0;
  EEPROM.update(E_LOOP_STATUS, recorded);
}


void Looper::recordNoteOn(byte note, byte vel) {
  recordNote(0x90, note, vel);
}

void Looper::recordNoteOff(byte note) {
  recordNote(0x80, note, 0);
}

void Looper::recordNote(byte control, byte note, byte vel) {
  unsigned long int newTime, now;
  now = millis();
  if (-1 == currentlyRecording) { //ignore
    return;
  }

  if (not recordingStartedTime) {
    //TODO: In case we have other loops playing already, set the start of play
    if (playing){
      CONSOLE.println("reusing previous start");
      recordingStartedTime = loopStartTime;
    } else {
      CONSOLE.println("recording anew");
      recordingStartedTime = now;
    }
  } /*else if ((now - recordingStartedTime) & 0xFFF80000) { //Manage timer overrun TODO: review
    stopRecording();
    return;
  }*/
  if (finish[currentlyRecording] + 5 < MEMORY_PER_LOOP) {
    CONSOLE.print("Loop "); CONSOLE.print((byte)currentlyRecording); 
    if(control==0x90){
      CONSOLE.print(" recording note on "); 
    } else if (control==0x80){
      CONSOLE.print(" recording note off "); 
    } else {
      CONSOLE.print(" recording control "); 
    }
    CONSOLE.print((byte)note); CONSOLE.print(" at "); CONSOLE.print(((float)((millis() - recordingStartedTime))) / 1000); CONSOLE.print("s, (addr: "); CONSOLE.print(start[currentlyRecording]); CONSOLE.print("+"); CONSOLE.print(finish[currentlyRecording]); CONSOLE.print("); finish[i] = ");CONSOLE.print(finish[currentlyRecording]);CONSOLE.print("\n");

    ST_write5(  start[currentlyRecording] + finish[currentlyRecording], 
                now - recordingStartedTime, 
                control | currentlyRecording, note, vel);
    finish[currentlyRecording] += 5;
    
  } else {
    CONSOLE.println("memory overrun");
  }
}


bool Looper::isRecorded(byte i) {
  return recorded & (1 << i);
}

///////////////////////////////////////////////
//Playback

void Looper::togglePlay(byte i) {
  if (isRecorded(i)) {
    playing = playing ^ (1 << i);
  }
  /*TODO: review*/
    if (playing){
    readingCursor[i]=0;
    loopStartTime = millis();
    }
}

void Looper::playbackLoop() {
  //Each call takes <12ms on an 8MHz ATMega (V8)
  unsigned long int nextTime;
  byte data1, data2, data3;

  if (playing and (millis() - loopStartTime)>maxLoopDuration){ //loop at the end of the longest recording
    loopStartTime += maxLoopDuration;
    CONSOLE.print("Looping! maxLoopDuration = ");CONSOLE.println(maxLoopDuration);
    for (char i=0; i<NB_LOOPS; i++){
      readingCursor[i]=0;
    }
  }
  for (byte l = 0; l < NB_LOOPS; l++) {

    if (playing & (1 << l)) {
      ST_read5((readingCursor[l] + start[l]), &nextTime, &data1, &data2, &data3);
      /*CONSOLE.print("Read from ST pos ");CONSOLE.print((readingCursor[l] + start[l])*5);
      CONSOLE.print("; next time: ");CONSOLE.print((float)nextTime/1000);
      CONSOLE.print("s; data: ");CONSOLE.print(data1, HEX);
      CONSOLE.print(" ");CONSOLE.print(data2, HEX);
      CONSOLE.print(" ");CONSOLE.print(data3, HEX);
      CONSOLE.println("");*/

      CONSOLE.print("PlaybackLoop: ");
      CONSOLE.print("Pos="); CONSOLE.print(readingCursor[l] + start[l]);
      CONSOLE.print("; Now?="); CONSOLE.print(nextTime <= (millis() - loopStartTime) % maxLoopDuration);
      CONSOLE.print("; Current time="); CONSOLE.print((millis() - loopStartTime) % maxLoopDuration);
      CONSOLE.print("; Target time="); CONSOLE.print(nextTime );
      CONSOLE.print("; Maxloop duration="); CONSOLE.print(maxLoopDuration);
      CONSOLE.print("; Track continuing?="); CONSOLE.println(readingCursor[l] < (start[l] + finish[l]));
      //    char buf[256];sprintf(buf, "(%d) readingCurstor: %d<%d+%d", l, readingCursor[l], start[l], finish[l]);CONSOLE.println(buf);
     
    if (nextTime <= (millis() - loopStartTime) % maxLoopDuration and readingCursor[l] < start[l] + finish[l] ) { //Time for this one
      /*if (readingCursor[l]<start[l]+finish[l]){ //play in loop; TODO: only for short loops; and add time to the timestamp 
        //divide the duration of this loop by the longest loop; round to the closest integer; add the corresponding fraction of the longest loop to the timestamp
        readingCursor[l] = start[l];
      }*/
      CONSOLE.print("Playing loop "); CONSOLE.print(l); 
      CONSOLE.print(",pos="); CONSOLE.print(readingCursor[l] + start[l]);
      CONSOLE.print("; Current time="); CONSOLE.print((millis() - loopStartTime) % maxLoopDuration);
      CONSOLE.print("; Target time="); CONSOLE.print(nextTime );
      CONSOLE.print(",data: "); CONSOLE.print(data1, HEX);
      CONSOLE.print(", "); CONSOLE.print(data2, HEX);
      CONSOLE.print(", "); CONSOLE.println(data3, HEX);
      readingCursor[l] += 5;
      sendMidi(data1, data2, data3);
      //TODO: Manage loops that are shorter than others?
      }
    }
  }
}

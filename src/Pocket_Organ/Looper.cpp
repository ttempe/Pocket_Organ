///////////////////////////////////////////////
//Looper: record midi events into flash memory, then replay them

/* TODO:
    record instrument selection
    record expression
    blink the key while recording a loop?
    Change the "playing" status only when releasing the "loop" button
    Test memory overrun or timeout conditions
    Make sure all instruments stop playing when the user interrupts loop playback
    Round off user timing errors 
    Handle the case where the player changes the instrument while recording a loop
    Playback now stops when entering melody mode
*/


#include "arduino.h"
#include "Looper.h"
#include "Pocket_Organ.h"
#include <EEPROM.h>

///////////////////////////////////////////////
//Constructor
Looper::Looper() {
  for (byte i = 0; i < NB_LOOPS; i++) {
    start[i] = MEMORY_PER_LOOP * i;
    EEPROM.get(E_LOOP_LENGTHS + 2 * i, finish[i]);
    EEPROM.get(E_LOOP_INSTRUMENTS + i, instruments[i]);
  }
  EEPROM.get(E_LOOP_STATUS, recorded);
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
  Serial.print("Start recording channel "); Serial.println((byte)channel);

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
  Serial.print("Stop recording channel "); Serial.print((byte)currentlyRecording);  Serial.print(" ("); Serial.print(finish[currentlyRecording]); Serial.println(" bytes written)");
  recorded += 1 << currentlyRecording;
  EEPROM.update(E_LOOP_STATUS, recorded);
  EEPROM.update(E_LOOP_LENGTHS + 2 * currentlyRecording, finish[currentlyRecording]);
  EEPROM.update(E_LOOP_INSTRUMENTS + currentlyRecording, instruments[currentlyRecording]);
  currentlyRecording = -1;
  maxLoopDuration = millis() - recordingStartedTime;
}

void Looper::deleteRecord(byte channel) {
  Serial.print("Deleting record "); Serial.println(channel);
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
      Serial.println("reusing previous start");
      recordingStartedTime = loopStartTime;
    } else {
      Serial.println("recording anew");
      recordingStartedTime = now;
    }
  } /*else if ((now - recordingStartedTime) & 0xFFF80000) { //Manage timer overrun TODO: review
    stopRecording();
    return;
  }*/
  if (finish[currentlyRecording] + 5 < MEMORY_PER_LOOP) {
    Serial.print("Loop "); Serial.print((byte)currentlyRecording); 
    if(control==0x90){
      Serial.print(" recording note on "); 
    } else if (control==0x80){
      Serial.print(" recording note off "); 
    } else {
      Serial.print(" recording control "); 
    }
    Serial.print((byte)note); Serial.print(" at "); Serial.print(((float)((millis() - recordingStartedTime))) / 1000); Serial.print("s, (addr: "); Serial.print(start[currentlyRecording]); Serial.print("+"); Serial.print(finish[currentlyRecording]); Serial.print("); finish[i] = ");Serial.print(finish[currentlyRecording]);Serial.print("\n");

    ST_write5(  start[currentlyRecording] + finish[currentlyRecording], 
                now - recordingStartedTime, 
                control | currentlyRecording, note, vel);
    finish[currentlyRecording] += 5;
    
  } else {
    Serial.println("memory overrun");
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
  //Each call takes 9~11ms on an 8MHz ATMega (V8)
  unsigned long int nextTime;
  byte data1, data2, data3;

  if ((millis() - loopStartTime)>maxLoopDuration){ //loop at the end of the longest recording
    loopStartTime += maxLoopDuration;
    for (char i=0; i<NB_LOOPS; i++){
      readingCursor[i]=start[i];
    }
  }
  for (byte l = 0; l < NB_LOOPS; l++) {
    ST_read5((readingCursor[l] + start[l]), &nextTime, &data1, &data2, &data3);

    if (playing & (1 << l)) {
      /*Serial.print("Read from ST pos ");Serial.print((readingCursor[l] + start[l])*5);
      Serial.print("; next time: ");Serial.print((float)nextTime/1000);
      Serial.print("s; data: ");Serial.print(data1, HEX);
      Serial.print(" ");Serial.print(data2, HEX);
      Serial.print(" ");Serial.print(data3, HEX);
      Serial.println("");*/
/*
      Serial.print("PlaybackLoop: ");
      Serial.print("Pos="); Serial.print(readingCursor[l] + start[l]);
      Serial.print("; Now?="); Serial.print(nextTime <= (millis() - loopStartTime) % maxLoopDuration);
      Serial.print("; Current time="); Serial.print((millis() - loopStartTime) % maxLoopDuration);
      Serial.print("; Target time="); Serial.print(nextTime );
      Serial.print("; Maxloop duration="); Serial.print(maxLoopDuration);
      Serial.print("; Track continuing?="); Serial.println(readingCursor[l] < (start[l] + finish[l]));
      //    char buf[256];sprintf(buf, "(%d) readingCurstor: %d<%d+%d", l, readingCursor[l], start[l], finish[l]);Serial.println(buf);
  */    
    }
    if (nextTime <= (millis() - loopStartTime) % maxLoopDuration and readingCursor[l] < start[l] + finish[l] ) { //Time for this one
      readingCursor[l] += 5;
      /*if (readingCursor[l]<start[l]+finish[l]){ //play in loop; TODO: only for short loops; and add time to the timestamp 
        //divide the duration of this loop by the longest loop; round to the closest integer; add the corresponding fraction of the longest loop to the timestamp
        readingCursor[l] = start[l];
      }*/
      if (playing & (1 << l)) { //this loop is playing
        Serial.print("Playing loop "); Serial.print(l); 
        Serial.print(", "); Serial.print(data1, HEX);
        Serial.print(", "); Serial.print(data2, HEX);
        Serial.print(", "); Serial.println(data3, HEX);
        sendMidi(data1, data2, data3);
        //TODO: Manage loops that are shorter than others?
      }
    }
  }
}

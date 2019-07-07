///////////////////////////////////////////////
//Looper: record midi events into flash memory, then replay them

#include "arduino.h"
#include "Looper.h"
#include "Pocket_Organ.h"
#include <EEPROM.h>

Looper::Looper(){
  char i;
  unsigned long int a;
  //TODO: load from EEPROM
  for (i=0; i<NB_LOOPS; i++){
    start[i]=a;
    a+=MEMORY_PER_LOOP;
    EEPROM.get(E_LOOP_LENGTHS+2*i, finish[i]);
    EEPROM.get(E_LOOP_INSTRUMENTS+i, instruments[i]);
  }
  EEPROM.get(E_LOOP_STATUS, recorded);
};

void Looper::displayStatus(){
  //Green: recorded
  //Orange: playing (assumes recorded)
  //Red: recording
  unsigned char recording = currentlyRecording?1 <<(currentlyRecording-1):0;
  unsigned char red = playing | recording;
  unsigned char green = recorded & (~recording);
  SR_map(green, red);
}

void Looper::startRecording(char channel){
  Serial.print("Start recording channel "); Serial.println(channel);
  deleteRecord(channel);
  currentlyRecording = channel;
  recordingStartedTime = 0; //will set the t=0 when playing the 1st button
}

void Looper::stopRecording(){
  Serial.print("Start recording channel "); Serial.print(currentlyRecording);  Serial.print(" (");Serial.print(finish[currentlyRecording]);Serial.println(" bytes written)");
  //TODO: save to EEPROM storage
  currentlyRecording = -1;
}

void Looper::deleteRecord(char channel){
  if (playing>>channel&0x1){
    togglePlay(channel);
  }
  finish[channel] = start[channel];
}

void Looper::recordNote(char note, char vel){
  unsigned long int newTime;
  if (-1 == currentlyRecording){
    return;
  }
  if (not recordingStartedTime){
    //TODO: handle the case where we have loops recorded already
    recordingStartedTime = millis();
  }
  if (finish[currentlyRecording]+5<MEMORY_PER_LOOP){
    ST_write5(start[currentlyRecording]+finish[currentlyRecording], ((millis()-recordingStartedTime)>>3)&0xFFFF, 0x90|currentlyRecording, note, vel);
    finish[currentlyRecording]+=5;
  }
}

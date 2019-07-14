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
  byte recording = (-1<currentlyRecording)?1 <<currentlyRecording:0;
  byte red = playing | recording;
  byte green = recorded & (~recording);
  SR_map(green, red);
}

void Looper::startRecording(char channel){
  if (currentlyRecording != -1){//don't record two tracks at once
    return ;
  }
  Serial.print("Start recording channel "); Serial.println((byte)channel);
  deleteRecord(channel);
  currentlyRecording = channel;
  recordingStartedTime = 0; //will set the t=0 when playing the 1st button
}

void Looper::stopRecording(){
  if (currentlyRecording == -1){ //check we were actually recording something
    return;
  }
  Serial.print("Stop recording channel "); Serial.print((byte)currentlyRecording);  Serial.print(" (");Serial.print(finish[currentlyRecording]);Serial.println(" bytes written)");
  recorded += 1<<currentlyRecording;
  EEPROM.update(E_LOOP_STATUS, recorded);
  EEPROM.update(E_LOOP_LENGTHS+2*currentlyRecording, finish[currentlyRecording]);
  EEPROM.update(E_LOOP_INSTRUMENTS+currentlyRecording, instruments[currentlyRecording]);
  currentlyRecording = -1;
}

void Looper::deleteRecord(byte channel){
  playing = playing & ~(1<<channel);
  recorded = recorded & ~(1<<channel);
  EEPROM.update(E_LOOP_STATUS, recorded);
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

bool Looper::isRecorded(byte i){
  return recorded & (1<<i);
}

void Looper::togglePlay(byte i){
  if (isRecorded(i)){
    playing = playing ^ (1 << i);
  }
}

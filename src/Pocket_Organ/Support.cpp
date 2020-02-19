#include "arduino.h"
#include <EEPROM.h>
#include <Wire.h>
#include "Support.h"
#include "Pocket_Organ.h"

///////////////////////////////////////////////
//Note keys backlighting (through the shift registers)

//One clock pulse
void SR_clock(){
  digitalWrite(SR_CLK, HIGH);
  digitalWrite(SR_CLK, LOW);  
}


//turn off key backlighting
void SR_blank(){
  digitalWrite(SR_DATA, LOW);
  for (char i=0; i<17; i++){
    SR_clock();
  }
}

//Light exactly one key, green
void SR_one(char n){
  if (6==n){return;} //TODO: weird bug on V8, where Si gets almost full reading whenever its green LED is on
  SR_blank();
  digitalWrite(SR_DATA, HIGH);
  SR_clock();
  digitalWrite(SR_DATA, LOW);
  for (char i=0; i<=n*2; i++){
    SR_clock();
  }
}

//Light all keys according to the bit maps passed in arguments
//1=Do, 2=Re, 4=Mi...
void SR_map(unsigned char green, unsigned char red){
  for (char i=7; i>=0; i--){
    digitalWrite(SR_DATA, (red>>i)&1);
    SR_clock();
    digitalWrite(SR_DATA, (green>>i)&1);
    SR_clock();
  }
  SR_clock();
}

///////////////////////////////////////////////
//EEPROM storage (on i2c bus)

void ST_write1(unsigned long int addr, byte data){
  Wire.beginTransmission(ADDR_EEPROM);
  Wire.write(addr >> 8);
  Wire.write(addr & 0xFF);
  Wire.write(data);
  Wire.endTransmission();
}

void ST_write5(unsigned long int addr, unsigned long int timestamp, byte data1, byte data2, byte data3){
  //Serial.print("Writing to ");Serial.println(addr);
  Wire.beginTransmission(ADDR_EEPROM);
  Wire.write(addr >> 8);
  Wire.write(addr & 0xFF);
  Wire.write(((timestamp >>11)&255)); //record ~100th of seconds over 16 bits, so max duration is ~50 minutes
  Wire.write(((timestamp >> 3)&255));
  Wire.write(data1);
  Wire.write(data2);
  Wire.write(data3);
  Wire.endTransmission();
  delay(4);
}

void ST_write2(unsigned long int addr, int data){
  Wire.beginTransmission(ADDR_EEPROM);
  Wire.write(addr >> 8);
  Wire.write(addr & 0xFF);
  Wire.write(data >> 8);
  Wire.write(data & 0xFF);
  Wire.endTransmission();
}

byte ST_read1(unsigned long int addr){
  char rdata;
  Wire.beginTransmission(ADDR_EEPROM);
  Wire.write(addr >> 8);
  Wire.write(addr & 0xFF);
  Wire.endTransmission();
  Wire.beginTransmission(ADDR_EEPROM);
  Wire.requestFrom(0x50, 1);
  rdata = Wire.read();
  Wire.endTransmission();
  return rdata;
}

int ST_read2(unsigned long int addr){
  int rdata;
  Wire.beginTransmission(ADDR_EEPROM);
  Wire.write(addr >> 8);
  Wire.write(addr & 0xFF);
  Wire.endTransmission();
  Wire.beginTransmission(ADDR_EEPROM);
  Wire.requestFrom(0x50, 2);
  rdata = (int)Wire.read()*256+Wire.read();
  Wire.endTransmission();
  return rdata;
}

void ST_read5(unsigned long int addr, unsigned long int* timestamp, byte* data1, byte* data2, byte* data3){
  Wire.beginTransmission(0x50);
  Wire.write(addr >> 8);
  Wire.write(addr & 0xFF);
  Wire.endTransmission();
  Wire.beginTransmission(0x50);
  Wire.requestFrom(0x50, 5);
  *timestamp = ((unsigned long int)Wire.read()<<11)+((unsigned long int)Wire.read()<<3);
  *data1 = Wire.read();
  *data2 = Wire.read();
  *data3 = Wire.read();
  Wire.endTransmission();
}

///////////////////////////////////////////////
//Analog buttons

//input pin#, depressed value, released value
unsigned int AB_cal[7][3] = { 
{4,0,167},
{3,0,202},
{2,0,146},
{9,71,274},
{0,0,234},
{1,0,166},
{6,71,240}
}; 

const char AB_degrees[NB_AB] = { 0, 2, 4, 5, 7, 9, 11};//Do, Re, Mi, Fa, Sol, La, Si

char AB::degree(byte d){
  return AB_degrees[d];
}

int AB::readVal(byte i){
  return analogRead(AB_cal[i][0]);
}

/* //Normal code, that uses the calibration stored in EEPROM
unsigned char AB::readVel(byte i){
  //Read the velocity of analog key i
  //i is the key index (0~6), not the analog input's address
  //returns a pressure level between 0 (not pressed) and 126.
  const float thres=0.01;
  unsigned int r = analogRead(AB_cal[i][0]);
  r = max(AB_cal[i][1], min(r, AB_cal[i][2]));
  r = r - AB_cal[i][1];
  float p = r/(float)(AB_cal[i][2]-AB_cal[i][1]);
  p = max(0, p-thres)/(1-thres);
  unsigned char v = (unsigned char)(p*126);
  //if (v>126){v=0;}
  return v;
}*/

//quick and dirty code with hard-wired calibration, for board V10 with the pull-down resistors removed
//the readings are very consistent, so I'm removing the calibration
unsigned char AB::readVel(byte i){
  //Read the velocity of analog key i
  //i is the key index (0~6), not the analog input's address
  //returns a pressure level between 0 (not pressed) and 126.
  const float thres=0.01;
  unsigned int r = analogRead(AB_cal[i][0]);
  if (r>1018){
    return 0;
  }
  else {
    return min((1018-r)/4,126);
  }
}


void AB::init(){
  //Restore analog buttons calibration from EEPROM
  for (char i=0; i<NB_AB; i++){
    EEPROM.get(E_AB_CALIBRATION+i*4, AB_cal[i][1]);
    EEPROM.get(E_AB_CALIBRATION+i*4+2, AB_cal[i][2]);
    AB_cal[i][2]=max(AB_cal[i][2], AB_cal[i][1]+10);
  } 
}


char AB::get_keypad_press(bool sharp){
  //obtain a single keypress from the analog buttons keypad (incl. B_SHARP)
  //Return -1 if no press
  //Backlight feedback on the key pressed

  //read analog buttons
  char m = not(digitalRead(DB[B_MIN]))*8*sharp;
  for (int i=0; i<7;i++){ 
    if (readVel(i)){//one key was pressed
      SR_one(i);//backlight that key
      delay(100);//wait past rebound
      do {} while (readVel(i));//wait for key release
      SR_blank();//turn off backlight
      return i+m;
    }
  }
  //read DB_SHARP
  if (not(digitalRead(DB[B_SHARP]))){
    delay(100);
    do {} while (not(digitalRead(DB[B_SHARP])));
    return 7+m;
  }
  return -1;
}

void AB::calibrate(){
  //record the max and min values for each analog sensor, for calibration purposes
  unsigned int a;

  //set extreme values
  for (char i=0; i<NB_AB; i++){
      a=analogRead( AB_cal[i][0]);
      AB_cal[i][1]=a; //min values are determined once, initially
      AB_cal[i][2]=a+10;
  }

  //read max values
  do{
    for (char i=0; i<NB_AB; i++){
      a=analogRead( AB_cal[i][0]);
      AB_cal[i][2]=max(a, AB_cal[i][2]);
      digitalWrite(LED_BUILTIN, (millis()/100)&1);
    }    
  } while (digitalRead(DB[B_VOL]));//Exit condition

  //save to EEROM
  for (char i=0; i<NB_AB; i++){
    EEPROM.put(E_AB_CALIBRATION+i*4, AB_cal[i][1]);
    EEPROM.put(E_AB_CALIBRATION+i*4+2, AB_cal[i][2]);
  }
}


///////////////////////////////////////////////
//Support functions

int countN;//DEBUG: nb of notes playing at any given time

void sendMidi(byte a, byte b, byte c){ //is used by the looper to send events
#ifdef OUT_SERIAL
  MIDI_SERIAL.write(a);
  MIDI_SERIAL.write(b);
  MIDI_SERIAL.write(c);
#endif
}

void noteOn(char pitch, char vel, char channel) {
#ifdef OUT_USB
  midiEventPacket_t noteOnUSB = {0x09, 0x90 | channel, pitch, vel};
  MidiUSB.sendMIDI(noteOnUSB);
#endif
#ifdef OUT_SERIAL
  MIDI_SERIAL.write(0x90 | channel);
  MIDI_SERIAL.write(pitch);
  MIDI_SERIAL.write(vel);
#endif
  //Serial.print("On: ");Serial.println((int)pitch);
  //countN++; Serial.println(countN);
}

void noteOff(char pitch, char channel) {
#ifdef OUT_USB
  midiEventPacket_t noteOffUSB = {0x08, 0x80 | channel, pitch, 0};
  MidiUSB.sendMIDI(noteOffUSB);
#endif
#ifdef OUT_SERIAL
  MIDI_SERIAL.write(0x80 | channel);
  MIDI_SERIAL.write(pitch);
  MIDI_SERIAL.write((byte)0);
#endif
  //Serial.print("Off: ");Serial.println((int)pitch);
  //countN--; Serial.println(countN);
} 

void setMidiControl(char m, char v, char channel){
#ifdef OUT_USB
  midiEventPacket_t event = {0x03, 0xB0 | channel, m, v};
  MidiUSB.sendMIDI(event);
#endif
#ifdef OUT_SERIAL
  MIDI_SERIAL.write(0xB0 | channel);
  MIDI_SERIAL.write(m);
  MIDI_SERIAL.write(v);
#endif
}

void setMidiControl(char m, char v1, char v2, char channel){
#ifdef OUT_USB
  midiEventPacket_t event = {0x03, 0xB0 | channel, m, v};
  MidiUSB.sendMIDI(event);
#endif
#ifdef OUT_SERIAL
  MIDI_SERIAL.write(0xB0 | channel);
  MIDI_SERIAL.write(m);
  MIDI_SERIAL.write(v1);
  MIDI_SERIAL.write(v2);
#endif
}

void setMidiInstr(char i, char channel){
#ifdef OUT_USB
  midiEventPacket_t event = {0x02, 0xC0 | channel, 0, i};
  MidiUSB.sendMIDI(event);
  MidiUSB.flush();
#endif
#ifdef OUT_SERIAL
  MIDI_SERIAL.write(0xC0 | channel);
  MIDI_SERIAL.write((byte)0);
  MIDI_SERIAL.write(i);
#endif
}

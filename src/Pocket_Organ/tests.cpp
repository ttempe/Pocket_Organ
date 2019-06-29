#include "arduino.h"
#include "Support.h"
#include "piano.h"
#include "Pocket_Organ.h"
#include "support.h"

///////////////////////////////////////////////
//Test loops

void loop10(){ //blink the data and clock of the shift registers to make them visible on a voltmeter
  static char a=0;
  digitalWrite(SR_CLK, a&1);
  digitalWrite(LED_BUILTIN, a&1);
  digitalWrite(SR_DATA, a&2);
  delay(1000);
  a++;
}

void loop9(){ //shift registers test: blink the buttons backlight
  pinMode( SR_DATA, OUTPUT);
  pinMode( SR_CLK, OUTPUT);

  digitalWrite(SR_DATA, 1);
  for (char i=0; i<16; i++){
    digitalWrite(SR_CLK, 1);
    digitalWrite(SR_CLK, 0);
  }
  delay(2000);
  digitalWrite(SR_DATA, 0);
  for (char i=0; i<16; i++){
    digitalWrite(SR_CLK, 1);
    digitalWrite(SR_CLK, 0);
  }
  delay(2000);
}

void loop8(){ //manually control the backlight shift registers by pressing buttons DB1 (send Clk pulse) and DB4 (switch state of Data) 
  #define B_DATA 8
  #define B_CLK 12
  pinMode( B_DATA, INPUT_PULLUP);
  pinMode( B_CLK, INPUT_PULLUP);

  static char c, d, dSwitch, dd;
  if (not(digitalRead(B_DATA))){
    dSwitch = !dSwitch;
    digitalWrite(SR_DATA, dSwitch);
    digitalWrite(13, dSwitch);
    Serial.print("Data: ");
    Serial.println((int)dSwitch);
    do{delay(100);} while (not(digitalRead(B_DATA)));
  }
  if (not(digitalRead(B_CLK))){
    digitalWrite(SR_CLK, 1);
    Serial.println("Clock pulse");
    delay(100);
    digitalWrite(SR_CLK, 0);
    do{delay(100);} while (not(digitalRead(B_CLK)));
  }
}

void loop7(){ //chenillard (shift registers): run through all buttons, alternating between green and red.
  char a;
  do {   
    digitalWrite(SR_DATA, 1);
    digitalWrite(SR_CLK, 1);
    digitalWrite(SR_CLK, 0);
    digitalWrite(SR_DATA, 0);
    if (a){
      digitalWrite(SR_CLK, 1);
      digitalWrite(SR_CLK, 0);
    }
    a= !a;
    for (char i=0; i<8; i++){
      delay(300);       
      digitalWrite(SR_CLK, 1);
      digitalWrite(SR_CLK, 0);
      digitalWrite(SR_CLK, 1);
      digitalWrite(SR_CLK, 0);
      digitalWrite(LED_BUILTIN, i&1);
    }

  }while(1);
}

void loop6(){ //Play chords
  digitalWrite(13, HIGH);
  for (byte i=0; i<8; i++){
    chordPlayGuitar(i);
    for (int j=0; j<1000; j++){
      chordUpdate(120);
      delay(1);
    }
    chordStop();
  }
}

void loop5(){//play MIDI notes
  for (byte i=40; i<70; i++){
    noteOn(i, 127,0);
    delay(1000);
    noteOff(i,0);
  }
}


void loop4(){ //Display the pressure level of each key, after application of the response curve
  char i, vel;
  int r;
  for (i=0; i<NB_AB; i++){ //iterate over keys 
    vel = AB::readVel(i);
    Serial.print((int)vel);
    Serial.print(",");
  }
  Serial.print("0,126\n");
}
/*
void loop3(){ 
  digitalWrite(13, HIGH);
  //record the max and min values for each analog sensor, for calibration purposes
unsigned int kk[7][2] =
              {{0, 0}, //Analog keys configuration
               {0, 0}, //Extreme values,
               {0, 0},
               {0, 0},
               {0, 0},
               {0, 0},
               {0, 0}};
  unsigned int a;
  //Read max values
  for (int i=0; i<NB_AB; i++){
      kk[i][0]=analogRead( AB_cal[i][0]);
  }
  
  do{
    Serial.print("\n{");
    for (int i=0; i<NB_AB; i++){
      a=analogRead( AB_cal[i][0]);
      kk[i][1]=max(a, kk[i][1]); 
      Serial.print(AB_cal[i][0]);
      Serial.print(",");
      Serial.print(kk[i][0]);
      Serial.print(",");
      Serial.print(kk[i][1]);
      Serial.print("},\n{");
    }    
  } while (1);
}
*/

void loop2() { //Test the analog buttons. Display on Serial Plotter
  for (int i=0; i<NB_AB; i++){
    Serial.print(AB::readVal(i));
    Serial.print(",");
  }
  Serial.print("0,1023\n");
}


void loop1() { //Test the digital buttons
  static char prevTotal=0;
  char total=0;
  for (char i=0; i<NB_DB; i++){
    if (not digitalRead(DB[i])){ 
      total++;
    }
  }
  if (prevTotal != total){
    //Serial.println((int)total);
    for (char i=0; i<NB_DB; i++){
      Serial.print(digitalRead(DB[i])?"1,":"0,");
    }
    Serial.println();
  }
  prevTotal = total;
}

void loop0(){
  AB::readVel(0);
  delay(2000);
}

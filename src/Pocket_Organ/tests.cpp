#include "arduino.h"
#include "Support.h"
#include "piano.h"
#include "Pocket_Organ.h"
#include "support.h"
#include <Wire.h>
#include <EEPROM.h>

///////////////////////////////////////////////
//Test loops

void reset_EEPROM(){
  delay(5000);
  CONSOLE.print("Resetting memory...");
  for (int i=0; i<128; i++){
    EEPROM.write(i, 0);
  }
  CONSOLE.println("Done");
  do{}while(1); 
}

void loop14(){//test reading and writing the same info to ST storage memory
  unsigned long int nextTime = 12345;
  byte data1=13, data2=27, data3=37;
  delay(1000);
    CONSOLE.print("Writing:  ");
    CONSOLE.print("time: ");CONSOLE.print(nextTime, HEX);
    CONSOLE.print("; data: ");CONSOLE.print(data1, HEX);
    CONSOLE.print(" ");CONSOLE.print(data2, HEX);
    CONSOLE.print(" ");CONSOLE.print(data3, HEX);
    CONSOLE.println("");
  ST_write5(0, nextTime, data1, data2, data3);
  ST_read5(0, &nextTime, &data1, &data2, &data3);
    CONSOLE.print("Reading:  ");
    CONSOLE.print("; time: ");CONSOLE.print(nextTime, HEX);
    CONSOLE.print("; data: ");CONSOLE.print(data1, HEX);
    CONSOLE.print(" ");CONSOLE.print(data2, HEX);
    CONSOLE.print(" ");CONSOLE.print(data3, HEX);
    CONSOLE.println("\n");
  delay(20000);
}

void loop13(){ //display the contents of ST storage memory 
  unsigned long int nextTime;
  byte data1, data2, data3;
  delay(1000);
  for (byte l=0; l<16 /*DEBGUG: NB_LOOPS*/; l++){
    ST_read5(l*5, &nextTime, &data1, &data2, &data3);
    CONSOLE.print("Read from ST pos ");CONSOLE.print(l);
    CONSOLE.print("; next time: ");CONSOLE.print((float)nextTime/1000);
    CONSOLE.print("s; data: ");CONSOLE.print(data1, HEX);
    CONSOLE.print(" ");CONSOLE.print(data2, HEX);
    CONSOLE.print(" ");CONSOLE.print(data3, HEX);
    CONSOLE.println("");
  }
  CONSOLE.println("");
  delay(20000);
}

void loop12(){//display the contents of ST storage memory
  delay(1000);
  unsigned long int address;
  unsigned long int nextTime;
  byte data1, data2, data3;
  address=0;    
  for (byte i; i<10; i++){
    ST_read5(address*5, &nextTime, &data1, &data2, &data3);
    CONSOLE.print(address);
    CONSOLE.print(": ");
  /*    Wire.beginTransmission(0x50);
      Wire.write(address*5 >> 8);
      Wire.write(address*5 & 0xFF);
      Wire.endTransmission();
      Wire.beginTransmission(0x50);
      Wire.requestFrom(0x50, 5);
      for (byte j=0;j<5; j++){
        CONSOLE.print(Wire.read(), HEX);
        CONSOLE.print(" "); 
      }  
      Wire.endTransmission();*/

    CONSOLE.print(((float)nextTime)/1000);
    CONSOLE.print("s, ");
    CONSOLE.print(data1,HEX);
    CONSOLE.print(" ");
    CONSOLE.print(data2);
    CONSOLE.print(" ");
    CONSOLE.print(data3,HEX);
    CONSOLE.print("\n");
    address++;
  }
  delay(20000);
}

void loop11(){//test the SR_map feature for displaying any combination of color on the analog buttons backlight
  SR_map(0, 0);
  delay(2000);
  SR_map(2,0);//green
  delay(2000);
}

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
    CONSOLE.print("Data: ");
    CONSOLE.println((int)dSwitch);
    do{delay(100);} while (not(digitalRead(B_DATA)));
  }
  if (not(digitalRead(B_CLK))){
    digitalWrite(SR_CLK, 1);
    CONSOLE.println("Clock pulse");
    delay(100);
    digitalWrite(SR_CLK, 0);
    do{delay(100);} while (not(digitalRead(B_CLK)));
  }
}

void loop7(){ //chenillard (shift registers): run through all buttons, alternating between green and red.
  char a;
  do {   
    digitalWrite(SR_OE, 0);
    digitalWrite(SR_DATA, 1);
    digitalWrite(SR_CLK, 1);
    digitalWrite(SR_CLK, 0);
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

void loop5(){//play MIDI notes
  for (byte i=40; i<70; i++){
    noteOn(i, 127,0);
    CONSOLE.print(".");
    delay(500);
    noteOff(i,0);
  }
}

void loop4(){ //Display the pressure level of each key, after application of the response curve
  char i, vel;
  int r;
  for (i=0; i<NB_AB; i++){ //iterate over keys 
    vel = AB::readVel(i);
    CONSOLE.print((int)vel);
    CONSOLE.print(",");
  }
  CONSOLE.print("0,126\n");
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
    CONSOLE.print("\n{");
    for (int i=0; i<NB_AB; i++){
      a=analogRead( AB_cal[i][0]);
      kk[i][1]=max(a, kk[i][1]); 
      CONSOLE.print(AB_cal[i][0]);
      CONSOLE.print(",");
      CONSOLE.print(kk[i][0]);
      CONSOLE.print(",");
      CONSOLE.print(kk[i][1]);
      CONSOLE.print("},\n{");
    }    
  } while (1);
}
*/

void loop2() { //Test the analog buttons. Display on Serial Plotter
  for (int i=0; i<NB_AB; i++){
    CONSOLE.print(AB::readVal(i));
    CONSOLE.print(",");
  }
  CONSOLE.print("0,1024\n");
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
    //CONSOLE.println((int)total);
    for (char i=0; i<NB_DB; i++){
      CONSOLE.print(digitalRead(DB[i])?"1,":"0,");
    }
    CONSOLE.println();
  }
  prevTotal = total;
}

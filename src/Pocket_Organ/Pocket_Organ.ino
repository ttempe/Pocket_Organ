/////////////////
//This version goes on:
// * v11/v12 (March 2020, STM32 MCU and capacitive touch keys)

/*TODO V11 board support:
 * Heart transplant:
  * redo all I/O
  * review all variable sizes
  * Configure all unused I/Os to output push-pull low (or tie to ground)
 * Drive the VBUS_ON and RST pins, to turn on the peripherals
 * Drive the SR-OE pin to remove the blinking of the AB backlight pins
 * Add self-power off
 * EEprom: switch to SPI. Remember to set the FLASH-CS pin to high-impedence during power-on and power-off, so that it follows VBUS
 * EEPROM.get()/put(): review all calls
 * Wire.write(): review all calls
 * Measure the MOSFET voltage drop, decide whether to keep it
 * 
 */

/*TODO:
 * Review AB::readVel(byte)
 * Display something
 * Looping
 * The display is not stable (HW issue). Understand why and fix it.
 * Can't play melody (except with Melody Lock) while recording a loop
 * Fix calibration key sequence
 * The 7th is higher if added after the end of the chord
 * When pressing a 2nd AB, check if I was briefly lifting the 1st one, and if so, consider it as a new note->make
 * Implement key selection
 * Change the 7th based on the selected key
 * Change the degree of the fundamental based on the selected key (eg: minor keys...)
 * Tune
 * enable USB Midi output, cleanup the code following the addition of the looper
 * more expression channels
 * use one of the expression channels to add more notes from that chord (lower/higher octaves)
 * bend only the top key in that loop?
 * Use different channels for melody and chords?
 * Make each note of a chord play at different pressure levels?
 * Add expression to melody mode
 * Add display
 * Rythm box
 * Calculate (and display on startup) the time spent playing since you got the instrument
 * Vol+/- faster while holding the Minor key
 * Monitor battery voltage
 * Add a beautiful splash screen
 * Add a way to use the percussions bank
 * When displaying the chord name, also list the notes being played
 */




//////////////////////////////////////////////////////////////////////////////////////////////
#include <EEPROM.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#ifdef OUT_USB
#include "MIDIUSB.h"
#endif
#include "Pocket_Organ.h"
#include "Support.h"
#include "piano.h"
#include "tests.h"
#include "Looper.h"


const char keybExpression[7][2] = //Expression1, Expression2
{{1, 2}, //Do
 {0, 2},  //Re
 {0, 1},  //Mi
 {4, 5},  //Fa
 {3, 5},  //Sol
 {3, 4},  //La
 {4, 5}   //Si
 };

char volume = 60;
char transpose = 60;
Looper myLooper;
Polyphony P(&myLooper);
Piano myPiano(&P);
Adafruit_SSD1306 display(128, 64, &Wire, -1);
byte current_instrument = 22; //1=Piano; 22=accordion; 25=nylon guitar

///////////////////////////////////////////////
//Setup
void setup() {
  //CONSOLE.begin(115200);

  //Wire.setClock(3400000); //I2C high speed mode. Tested with the memory chip and display
  //for (char i=0; i<NB_DB; i++){
  //  pinMode( DB[i], INPUT_PULLUP); //Mode switch
  //}
  pinMode( SR_DATA, OUTPUT);
  pinMode( SR_CLK, OUTPUT);
  pinMode( SR_OE, OUTPUT);
  //SR_blank();
  //analogReference(EXTERNAL); //voltage divider //DEFAULT V8; INTERNAL or EXTERNAL for V10
  //analogReference(DEFAULT);//5V 
  //analogReference(INTERNAL); //1V1 or 2V56
  
#ifdef OUT_SERIAL
  delay(500);
  //MIDI_SERIAL.begin(31250);
#endif
  //char v = EEPROM.read(E_VOLUME);
  if (v){
    volume = v;
  }
  //setMidiControl(MIDI_VOLUME, volume, 0);

  
  // //setMidiControl(MIDI_RELEASE, 127);
  // //setMidiControl(MIDI_EXPRESSION, 127);//Max keyboard xpression, for debugging
  //setMidiInstr(current_instrument, 0); 

  //OLED display
  /*
  CONSOLE.println("initializing display");
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3D)) { // Address 0x3D for 128x64
    CONSOLE.println(F("SSD1306 failed"));
    //  for(;;); // Don't proceed, loop forever
  } else {
    display.clearDisplay();
    display.setTextSize(3);
    display.setRotation(2);
    display.setTextColor(WHITE);
    display.setCursor(0, 0); 
    display.cp437(true);
  
    display.print("Hello\n hello");
    display.display();
    */
  }
  delay(100);//let the analog pins settle
}

///////////////////////////////////////////////
//User actions finite-state automaton


void vol_display(){
  display.clearDisplay();
  display.setTextSize(3);
  display.setCursor(0, 0); 
  display.print("Volume");
  display.drawRect(2,40, 124, 16, WHITE);
  display.fillRect(2,40, volume, 15, WHITE);
  display.display();
}

void loopB_Volume(){
  vol_display();
  do {
    if (not digitalRead(DB[B_PLUS]) and volume<125){
      volume+=5;
      vol_display();
      delay(100);
      do {} while (not(digitalRead(DB[B_PLUS])));
    }
    if (not digitalRead(DB[B_MINUS]) and volume>0){
      volume-=5;
      vol_display();
      delay(100);
      do {} while (not(digitalRead(DB[B_MINUS])));
    }
    if (not digitalRead(DB[B_ZERO])){
      volume = 60;
      vol_display();
      delay(100);
      do {} while (not(digitalRead(DB[B_ZERO])));
    }
    if (not digitalRead(DB[B_INSTR]) and not digitalRead(DB[B_LOOP])){
      digitalWrite(LED_BUILTIN, HIGH);
      do {delay(100);} while ((not digitalRead(DB[B_INSTR])) or (not digitalRead(DB[B_LOOP]))or (not digitalRead(DB[B_VOL])));//wait till all 3 keys are released
      AB::calibrate();
      digitalWrite(LED_BUILTIN, LOW);
    }
  } while (not digitalRead(DB[B_RYTHM]));
  EEPROM.update(E_VOLUME, volume);
  setMidiControl(MIDI_VOLUME, volume, 0);
  display.clearDisplay();
}

void loopB_Instr_Transpose(){
  int p1, p2;

  //Instrument change
  do {
    p1 = AB::get_keypad_press(true);
    if (p1>-1){
      do {
        if (digitalRead(DB[B_TRANSP])){
          current_instrument = p1*8;
          setMidiInstr(current_instrument, 0);
          return;
        }
        p2 = AB::get_keypad_press(false);
      } while (p2 == -1);
      current_instrument = p1*8+p2;
      setMidiInstr(current_instrument, 0);
    }
    
    //Transposition
    if (not digitalRead(DB[B_PLUS]) and transpose<96){
      transpose++;
      delay(100);
      do {} while (not(digitalRead(DB[B_PLUS])));
    }
    if (not digitalRead(DB[B_MINUS]) and transpose>24){
      transpose--;
      delay(100);
      do {} while (not(digitalRead(DB[B_MINUS])));
    }
    if (not digitalRead(DB[B_ZERO])){
      transpose=60;
      delay(100);
      do {} while (not(digitalRead(DB[B_ZERO])));
    }    
  } while (not digitalRead(DB[B_TRANSP]));
}

void loopB_Loop(){ //Loop & tune
  P.chordStop(); //Stop the chord before stopping recording
  myLooper.stopRecording();//1st thing: stop recording
  myLooper.displayStatus();//update the key backlight
  delay(100); //debounce
  do {
    for (byte i=0; i<NB_AB; i++){
      if (AB::readVel(i)){ //one key was pressed
        unsigned long t=millis(); 
        delay(100);//debounce
        do {
          delay(10); //wait
        } while (AB::readVel(i) and not digitalRead(DB[B_LOOP]) and millis()-t <1000);//until one of the keys is depressed or time has run out
        if (digitalRead(DB[B_LOOP])){//Loop key released
          SR_blank();
          return;
        } else if (millis()-t < 1000){//short press
          myLooper.togglePlay(i);
          myLooper.displayStatus();
        } else { //long press
          if (myLooper.isRecorded(i)){
            myLooper.deleteRecord(i);
          } else {
            myLooper.startRecording(i);
          }
        myLooper.displayStatus();
        do {} while (AB::readVel(i)); //Wait for AB key release
        }
      }
    }
  } while (not digitalRead(DB[B_LOOP]));
  SR_blank();
}

void loopB_Rythm(){
}

void loopB_Melody(){
  char m[NB_AB], playing=-1, playingNote, b_melody, b_melody_lock, locked, was_locked;
  
  //First read initial state of all analog buttons. Ignore them until they are released.
  for (int i=0; i<NB_AB; i++){
    m[i] = AB::readVel(i);
  }
  digitalWrite(LED_BUILTIN, HIGH);
  do { //Loop: play newly pressed buttons

    //handle analog buttons
    for (int i=0; i<NB_AB; i++){
      char v= AB::readVel(i);
      if (m[i] and not v){ //Initially pressed button was released. Stop ignoring it.
        m[i]=0;
      } else if ((not m[i]) and v and playing==-1){//Start playing one note
        playing = i;
        playingNote = transpose+(not digitalRead(DB[B_SHARP]))+AB::degree(playing)+(not digitalRead(DB[B_PLUS]))*12-(not digitalRead(DB[B_MINUS]))*12;
        noteOn(playingNote, 96,0);
        myLooper.recordNoteOn(playingNote, 96);
        SR_one(i);
      } else if (not v and playing == i) { //stop playing that note
        noteOff(playingNote, 0); 
        myLooper.recordNoteOff(playingNote);
        playing = -1;
        SR_blank();   
      }
    m[i] = v;
    }
    #ifdef OUT_USB
    MidiUSB.flush();
    #endif

    //handle the lock/unlock buttons
    b_melody_lock = digitalRead(DB[B_MELODY_LOCK]);
    b_melody = digitalRead(DB[B_MELODY]);
    if (locked and not b_melody and not was_locked){ //release lock
      delay(100); //wait past rebound
      do {} while (not digitalRead(DB[B_MELODY])); //wait for button release
      locked = 0;
    } else if (not locked and not b_melody_lock and not b_melody){ //lock
      delay(100); //wait past rebound
      do {} while (not digitalRead(DB[B_MELODY_LOCK]));//wait for lock button release
      locked = 1;
      was_locked = 1;
    } else if (locked and b_melody) { //"Melody" button was released, allow to unlock on next press
      was_locked = 0;
    }

    myLooper.playbackLoop();

  } while (not b_melody or locked);
  digitalWrite(LED_BUILTIN, LOW);
  if (playing != -1){
    noteOff(playingNote, 0);
    myLooper.recordNoteOff(playingNote);

  }
}

void loopB_Chord(int b, int velocity){
  static int effect1, effect1_old, effect2, effect2_old, velocity_old;

  //collect initial values, and start playing immediately
  myPiano.chordPlay(b, transpose);
  SR_one(b);

  //Update the play
  do {
    //Expression
    effect1 = AB::readVel(keybExpression[b][0]);
    effect2 = AB::readVel(keybExpression[b][1]);
    if (abs(effect1-effect1_old)>5){
      CONSOLE.print("Effect1: ");CONSOLE.println(effect1);
      setMidiControl(MIDI_EXPRESSION, 127-effect1*3/5, 0);
      effect1_old = effect1;
    }
    if (abs(effect2-effect2_old)>5){
      CONSOLE.print("Effect2: ");CONSOLE.println(effect2);
      setMidiControl(MIDI_PITCH_BEND, 0, (64-(effect2)/2), 0);
      effect2_old = effect2;
    } 
    velocity=AB::readVel(b);
    P.chordUpdate(velocity);
    
    if (abs(velocity-velocity_old)>20){
      velocity_old = velocity;
    }
    if (not digitalRead(DB[B_MELODY])){
      loopB_Melody();
    }
    
    myPiano.chordRefresh();    //Chord shape change
    myLooper.playbackLoop();

  } while(velocity>0 or effect1 >0 or effect2 > 0);
  P.chordStop();
  SR_blank();
}

void loopB(){ //Play music based on button presses
  //Waiting mode. No key pressed
  
  for (int i=0; i<NB_AB; i++){
    int v = AB::readVel(i);
    if (v){
      CONSOLE.print("Chord ");CONSOLE.println(i);
      loopB_Chord(i, v);
      CONSOLE.println("Chord finished");
      
      break;
    }  
  }  
  if (not digitalRead(DB[B_RYTHM])) {
    //loopB_Rythm();
  } else if (not digitalRead(DB[B_LOOP])){
    loopB_Loop();
  } else if (not digitalRead(DB[B_VOL])){
    loopB_Volume();
  } else if (not digitalRead(DB[B_MELODY])){
    loopB_Melody();
  } else if (not digitalRead(DB[B_TRANSP])){
    loopB_Instr_Transpose();
  }
#ifdef OUT_USB
    MidiUSB.flush();
#endif
  myLooper.playbackLoop();
  delay(10);
}

///////////////////////////////////////////////
//Loop

void loop() {
  static int i;
  CONSOLE.println("Loop!");
  delay(1000);
  //loop1(); //Test the digital buttons
  //loop2(); //Test the analog buttons. Display on Serial Plotter
  //loop4(); //Display the pressure level of each key, after application of the response curve
  //loop5(); //play MIDI notes
  loop7(); //chenillard (shift registers): run through all buttons, alternating between green and red.
  //loop13();//display the contents of ST storage memory 
  //loop14();//test reading and writing the same info to ST storage memory
  //reset_EEPROM();
  //loopB(); //Normal loop, play music
}

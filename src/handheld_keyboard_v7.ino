/////////////////
//This version goes on:
// * v7 & V8 & V9 boards (2019-05)

/*TODO:
 * chords: play all chords from the same octave (keep the Si from sounding higher than the Do)
 * Change the 7th based on the selected key
 * Change the degree of the fundamental based on the selected key (eg: minor keys...)
 * Tune
 * enable Midi output
 * more expression channels
 * use one of the expression channels to add more notes from that chord (lower/higher octaves)
 * bend only the top key in that loop?
 * Use different channels for melody and chords?
 * Make each note of a chord play at different pressure levels?
 * Add expression to melody mode
 * Add display
 * Rythm box
 * Calculate (and display on startup) the time spent playing since you got the instrument
 */




//////////////////////////////////////////////////////////////////////////////////////////////
#include <EEPROM.h>
#ifdef OUT_USB
#include "MIDIUSB.h"
#endif
#include "handheld_keyboard.h"
#include "Support.h"
#include "piano.h"
#include "tests.h"



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
Polyphony P;
Piano myPiano(&P);



void chordPlayGuitar(char degree){
  //Determine which chord shape the user wants to play, based on the digital buttons in use
  char scale, n; //M, m, 7, m7, 9, sus4, sus2
  char transp;
  scale = (not digitalRead(DB[B_MIN])) + 2*(not digitalRead(DB[B_7]));
  //Memo: static char guitarChords[7][7][6] = //scale, degree*7, string*6
  transp = not digitalRead(DB[B_SHARP]);
  for (char s=0; s<6; s++){
    n = guitarChords[scale][degree][5-s];
    if (n>-1 and n<64){
      P.playNote(n+transpose+transp+guitarStrings[s]-60);
    }
  }
}

///////////////////////////////////////////////
//Setup
void setup() {
  Serial.begin(115200);
  for (char i=0; i<NB_DB; i++){
    pinMode( DB[i], INPUT_PULLUP); //Mode switch
  }
  pinMode( SR_DATA, OUTPUT);
  pinMode( SR_CLK, OUTPUT);
  SR_blank();
  //analogReference(EXTERNAL);
#ifdef OUT_SERIAL
  delay(500);
  MIDI_SERIAL.begin(31250);
#endif
  char v = EEPROM.read(E_VOLUME);
  if (v){
    volume = v;
  }
  setMidiControl(MIDI_VOLUME, volume, 0);

  
  //setMidiControl(MIDI_RELEASE, 127);
  //setMidiControl(MIDI_EXPRESSION, 127);//Max keyboard xpression, for debugging
  setMidiInstr(22, 0); //1=Piano; 22=accordion; 25=nylon guitar
}

///////////////////////////////////////////////
//Loop

void loopB_Instr_Transpose(){
  int p1, p2;

  //Instrument change
  do {
    p1 = AB::get_keypad_press(true);
    if (p1>-1){
      do {
        if (digitalRead(DB[B_TRANSP])){
          setMidiInstr(p1*8, 0);
          return;
        }
        p2 = AB::get_keypad_press(false);
      } while (p2 == -1);
      setMidiInstr(p1*8+p2, 0);
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

void loopB_Volume(){
  do {
    if (not digitalRead(DB[B_PLUS]) and volume<110){
      volume+=5;
      delay(100);
      do {} while (not(digitalRead(DB[B_PLUS])));
    }
    if (not digitalRead(DB[B_MINUS]) and volume>10){
      volume-=5;
      delay(100);
      do {} while (not(digitalRead(DB[B_MINUS])));
    }
    if (not digitalRead(DB[B_ZERO])){
      volume = 60;
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
        SR_one(i);
      } else if (not v and playing == i) { //stop playing that note
        noteOff(playingNote, 0); 
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

  } while (not b_melody or locked);
  digitalWrite(LED_BUILTIN, LOW);
  if (playing != -1){
    noteOff(playingNote, 0);
  }
}

void loopB_Chord(int b, int velocity){
  static int effect1, effect1_old, effect2, effect2_old, velocity_old;

  //collect initial values, and start playing immediately
  //chordPlayGuitar(b);
  myPiano.chordPlay(b, transpose);
  SR_one(b);

  //Update the play
  do {
    //Expression
    effect1 = AB::readVel(keybExpression[b][0]);
    effect2 = AB::readVel(keybExpression[b][1]);
    if (abs(effect1-effect1_old)>5){
      Serial.print("Effect1: ");Serial.println(effect1);
      setMidiControl(MIDI_EXPRESSION, 127-effect1*3/5, 0);
      effect1_old = effect1;
    }
    if (abs(effect2-effect2_old)>5){
      Serial.print("Effect2: ");Serial.println(effect2);
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
    
    //Chord shape change
    myPiano.chordRefresh();
 
    delay(10);
  } while(velocity>0 or effect1 >0 or effect2 > 0);
  P.chordStop();
  SR_blank();
}

void loopB(){ //Play music based on button presses
  //Waiting mode. No key pressed
  
  for (int i=0; i<NB_AB; i++){
    int v = AB::readVel(i);
    if (v){
      Serial.print("Chord ");Serial.println(i);
      loopB_Chord(i, v);
      Serial.println("Chord finished");
      break;
    }  
  }  
  if (not digitalRead(DB[B_RYTHM])) {
    //loopB_Rythm();
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
  delay(10);
}

///////////////////////////////////////////////
///////////////////////////////////////////////
void loop() {loopB();}

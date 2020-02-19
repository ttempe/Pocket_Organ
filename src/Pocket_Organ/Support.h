//Support functions

#ifndef HEADER_SUPPORT
  #define HEADER_SUPPORT

/////////////////
//Analog buttons
#define NB_AB 7

/////////////////
//Shift register configuration (for backlight)
#define SR_DATA 14
#define SR_CLK 15

/////////////////
//Prototypes

void SR_blank();
void SR_one(char n);
void SR_map(unsigned char green, unsigned char red);

void ST_write1(unsigned long int addr, byte data);
void ST_write2(unsigned long int addr, int data);
void ST_write5(unsigned long int addr, unsigned long int data1, byte data2, byte data3, byte data4);
byte ST_read1(unsigned long int addr);
int  ST_read2(unsigned long int addr);
void ST_read5(unsigned long int addr, unsigned long int* data1, byte* data2, byte* data3, byte* data4);

void sendMidi(byte a, byte b, byte c);
void noteOn(char pitch, char vel, char channel);
void noteOff(char pitch, char channel);
void setMidiControl(char m, char v, char channel);
void setMidiControl(char m, char v1, char v2, char channel);
void setMidiInstr(char i, char channel);



class AB {
  public:
    static const char NB = 7;
    static void init();
    static char degree(byte d);
    static char get_keypad_press(bool sharp);
    static void calibrate();
    static unsigned char readVel(byte i);
    static int readVal(byte i);
};

#endif// HEADER_SUPPORT

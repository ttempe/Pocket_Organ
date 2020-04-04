//Support functions

#ifndef HEADER_TESTS
  #define HEADER_TESTS
void reset_EEPROM();
void loop14();//test reading and writing the same info to ST storage memory
void loop13();//display the contents of ST storage memory using the Support.cpp routines
void loop12();//display the contents of ST storage memory
void loop11();
void loop10();
void loop9();
void loop8();
void loop7();//chenillard (shift registers): run through all buttons, alternating between green and red.
void loop5();//play MIDI notes
void loop4();//Display the pressure level of each key, after application of the response curve
void loop3();
void loop2();//Test the analog buttons. Display on Serial Plotter
void loop1();//Test the digital buttons


#endif// HEADER_TESTS

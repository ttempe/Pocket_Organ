///////////////////////////////////////////////
//Management of multiple notes in parallel, on the main channel

#ifndef HEADER_POLYPHONY
  #define HEADER_POLYPHONY

#define QUEUE 7 //=(Max number of notes to queue)+ 1

class Polyphony {
  private:
    unsigned long timeToPlay;
    char notesQueue[QUEUE], queuePlayedI, queueToPlayI, queuePlaying, playingFast;

  public:
    void playNote(char pitch);
    void chordStop();
    void chordUpdate(char vel);
    void noteStop(char pitch);
};


#endif //HEADER_POLYPHONY

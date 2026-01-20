Silversat gnuradio scripts

2, 6, and 7 below are tested and working on TEST DATA as of 1/9/2026.
I improved the signal processing chain to deal with the DC line.  The signal is converted
to a 200kHz offset and then downconverted back to 0.  Capture uses a 45 kHz bandwidth to
accomodate up to +/- 15kHz of doppler offset.  I also added a gaussian filter on output
of the demodulator.  The GMSK gnuradio block may do the entire thing, but I couldn't 
find much documentation (that I wanted to read ;) on setting the parameters.  It's in the 
processing chain (but disabled) if you want to try it.

1. cw_rx.grc is a basic viewer.  It plays back the magnitude of the received signal
2. passdata_playback.grc will take a .wav file and look for and recover packets using
   Silversat's radio packet format.  Our format is very close to AX.25/IL2P, but includes
   some minor deviations for our specific use case (like a fixed AX.25 header).
3. playback.grc simply plays back the .wav file.
4. raw_waterfall.grc does more or less the same thing.
5. rltsdr_capture_realtime.grc captures the received signal with realtime doppler
   correction.  Output is stored to a .wav file.
6. rtlsdr_iq_capture.grc captures the received signal as-is (no doppler correction)
   to a .wav file.  This is what the processing system uses.
7. silversat_realtime.grc captures the received signal with realtime dopper correction,
   and demodulates and recovers the received packets and stores them to the output file.
   I haven't tried this at all, but conceptually it's close.

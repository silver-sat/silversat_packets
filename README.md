SILVERSAT PACKET PROCESSOR

This is a complete system for managing the data required to process raw
silversat radio packets using an RTL-SDR.  The systems was designed to 
manage all the metadata needed to capture and process the RF downlink
signal. The system is managed through an SQLite3 database.  The system was
developed on a RaspberryPi5.  I also added an M3 drive (500GB) to store the
massive capture files (don't be surprised with a 1GB file).

My implementation also includes a UPS to make the system portable.

In order to install the system you should (after cloning the repo)
1. Create a virtual environment in the /silversat_packets directory
2. Install using pip:
  pip install pytz matplotlib flask requests ephem reedsolo
3. Install using apt:
   sudo apt update && upgrade
   sudo apt install python3-skyfield sqlite3 gnuradio
4. clone gr-satnogs and follow install instructions.
5. clone ssdv from https://github.com/fsphil/ssdv and follow install instructions

I have not tested from scratch, so there may be more.

5. In the silversat_packets create the following folders:
  /silversat_packets/captures
  /silversat_packets/received_packets
  /silversat_packets/static
6. create a new database:
  sqlite3 observations.db < schema.sql
  -OR-
   use the existing database:
   which right now has a bunch of captures that are not included
7. Get Space-Track login (it's free) and store your username and password as
   environment variables.
   The easiest to make them permanent is to modify .profile and add to the end:
   export SPACETRACK_USER = "Your username"
   export SPACETRACK_PASS = "Your password"

start the system
  flask run

navigate your browser to http://127.0.0.1:5000

TO USE THE SYSTEM (assuming you start with existing observations.db)
1. Click on "New Capture".
2. Click on "Fetch TLE from Space-Track".
3. Add operator's notes (optional).
4. The filename is auto-generated.
5. Click "Preview Orbit" if you want to verify when to start and where to point your antenna
6. Click "Create Capture Session".  At that point, gnuradio should start.
   The system will store a date/timestamped file to the captures directory.
   When you're done, simply close the gnuradio window.
7. Click on "Captures" and verify that it worked.
8. Click on "New Processing Run"
9. Select the ID of the Capture run you wish to process.  By default it should be the latest one.
10. Set the frequency offset.  This is the offset in the reference clocks between the satellite and your SDR.
    It may take some trial and error to figure that out, but once you have it, it shouldn't change much.
11. Set the access threshold.  This is the number of bit errors you can have in the access code (Preamble and Sync bytes)
    to continue processing.  By default it's 3.
12. You shouldn't need to change the output folder, but you have the option.
13. Choose whether you wish to store the recovered packets (useful for testing)
14. Choose whether or not you want to process using doppler corrections (also useful for testing)
15. Tell the system if these are SSDV packett, so it knows to continue processing once it has recovered the packets.
16. Add notes as desired about this processing run.
17. Click "Start Processing Run".  This starts the gnuradio playback of the captured .wav file.  Let it run to completion.
    If packets are detected, take a look at the balance of the signal from the quad_demod block (it should be labeled that way, or something close).
    The signal should be balanced between +/- 1.  If it's off, then the offset needs to be adjusted.
18. If it's an SSDV session, the recovered picture should be in the /static folder.
19. Click on "Processing" to look at the output.  You can view the processed output by clicking on "Inspect" in the View column.
    That will give you the basic stats on the recovered packet.  I may add a viewer for the payload at some point.

Have Fun!!
Tom Conrad

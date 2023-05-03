# LoLAutoHighlight
A program that creates clips of important events of a League of Legends spectator video.

The program takes a .mp4 of a League of Legends game and output multiple clips of events (Kills, Baron kills, Dragon kills)

### How does it work?
1. Using open-cv, the program checks every 4 seconds of the video if an event occured in the killfeed
2. It regroups events that are close from one another and add a buffer before and after
3. It create clips by cropping the original video with MoviePy

### Requirements
- python 3.X (I use 3.11, haven not tested with another version)
- moviePy
- opencv-python
- numpy

This is my "first" public open project. I am still learning everyday.

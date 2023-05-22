###########################################################
# USER MODIFIABLE PARAMETERS
VIDEO_DIR= "input/"
VIDEO_OUTPUT_DIR = "output/"
TIME_BEFORE_EVENT = 10 #capture time before the event (kill, dragon, baron, etc.) in seconds
TIME_AFTER_EVENT = 7 #capture time after the event in seconds
REGROUP_TIME = TIME_BEFORE_EVENT + TIME_AFTER_EVENT + 5 #Time between events to regroup them together in 1 clip
BITRATE = "6000k"

CODEC = "libx264" #h264_nvenc for nvidia gpu, libx264 for cpu 
#(might require to install nvidia drivers)

KILL_FEED_AREA = (715, 800, 1655, 1720) #coordinates of the killfeed in the video (top left y, bottom right y, top left x, bottom right x
#NOTE: the killfeed might change position depending on your UI settings
#I made it very large so it should work with most settings but it is slower.

KILL_FEED_DETECTION_THRESHOLD = 0.8 #threshold for the killfeed detection (0.0 to 1.0)
#the lower it is, the more clip it will find, but it will also find false positives (no event clips)

CAP_INTERVAL = 4.5 #Capture interval in seconds (LoL kill feed lasts 5 second)
###########################################################

ICON_DIR = ("icons/")

import cv2
from moviepy.video.io.VideoFileClip import VideoFileClip
from os import listdir, path
from numpy import uint8
import math
from tqdm import tqdm


global killfeedIcons
killfeedIcons = []
for icon in listdir(ICON_DIR):
    if icon.endswith(".png"):
        killfeedIcons.append(cv2.imread(path.join(ICON_DIR, icon)))

global videosPaths
videosPaths = []
for file in listdir(VIDEO_DIR):
    if file.endswith(".mp4"):
        videosPaths.append(path.join(VIDEO_DIR, file))


def findRelevantFramesFromVideo(video):
    frames = []

    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    for frame_counter in tqdm(list(range(0, total_frames, math.floor(CAP_INTERVAL*int(fps)))), colour="green"):
        video.set(1, frame_counter)
        ret, frame = video.read()
            
        if isFrameRelevant(frame):
            frames.append(frame_counter)

    return frames

#check if the frame contains the wanted icon
def isFrameRelevant(frame):

    #crop the video to the killfeed
    #NOTE: the killfeed might change position depending on your UI settings
    killfeed = frame[KILL_FEED_AREA[0]:KILL_FEED_AREA[1], KILL_FEED_AREA[2]:KILL_FEED_AREA[3]]
    
    #check if the killfeed contains any of the icons
    for icon in killfeedIcons:
        res = cv2.matchTemplate(killfeed, icon, cv2.TM_CCOEFF_NORMED)
    
        loc = cv2.findNonZero((res >= KILL_FEED_DETECTION_THRESHOLD).astype(uint8))
        if loc is not None:
            return True
    return False

def findBeginningOfEvent(video, frameNb):
    frameToRewind = math.floor(1 * fps/2)
    video.set(1, frameNb)
    ret, frame = video.read()
    while isFrameRelevant(frame):
        frameNb -= frameToRewind
        video.set(1, frameNb)
        ret, frame = video.read()
    return frameNb + frameToRewind

def findBeginningOfEventFromEnd(video, frameNb):
    frameToRewind = math.floor(1 * fps/2)
    video.set(1, frameNb)
    ret, frame = video.read()
    while isFrameRelevant(frame):
        frameNb += frameToRewind
        video.set(1, frameNb)
        ret, frame = video.read()
    return frameNb - frameToRewind - (5*fps)

def getExactBeginningAndEnd(video, frames):
    joinedFrames = []
    for frame in tqdm(frames, colour="red"):
        if frame[0] == frame[1]:
            frameNb = findBeginningOfEventFromEnd(video, frame[0])
            joinedFrames.append([frameNb, frameNb])
        else:
            joinedFrames.append([findBeginningOfEvent(video, frame[0]), findBeginningOfEventFromEnd(video, frame[1])])
    return joinedFrames

#Join relevent frames together
def joinCloseFrames(frames):
    joinedFrames = []
    maxFrameDistanceInFrames = REGROUP_TIME * fps
    startTime = frames[0]
    endTime = frames[0]

    for frame in frames:
        if frame - endTime < maxFrameDistanceInFrames:
            endTime = frame
        else:
            joinedFrames.append([startTime, endTime])
            startTime = frame
            endTime = frame

    joinedFrames.append([startTime, endTime]) #last frame

    return joinedFrames

def addRegroupTime(frames):
    for frame in frames:
        frame[0] -= TIME_BEFORE_EVENT * fps
        frame[1] += TIME_AFTER_EVENT * fps
    return frames

def cutVideo(videoPath, timestampsToCut, outputDir):
    videoName = path.splitext(path.basename(videoPath))[0]
    for frame in tqdm(timestampsToCut, colour="blue"):
        start_frame, end_frame = frame
        start_time = math.floor(start_frame / fps)
        end_time = math.floor(end_frame / fps)
        clip = VideoFileClip(videoPath).subclip(start_time, end_time)
        timeInSeconds = (start_time,end_time)
        clip.write_videofile(f"{outputDir}{videoName}_cut_video{timeInSeconds}.mp4", codec = CODEC , bitrate= BITRATE)

################################
#MAIN
################################

for videoPath in videosPaths:
    video = cv2.VideoCapture(videoPath)
    videoName = path.basename(videoPath)
    fps = video.get(cv2.CAP_PROP_FPS)

    print(f"processing video:  + {videoName}")
    relevantFrames = findRelevantFramesFromVideo(video)
    closeFrames = joinCloseFrames(relevantFrames)
    exactEventFrames = getExactBeginningAndEnd(video, closeFrames)
    timestampsToCut = addRegroupTime(exactEventFrames)
    cutVideo(videoPath, timestampsToCut, outputDir=VIDEO_OUTPUT_DIR)

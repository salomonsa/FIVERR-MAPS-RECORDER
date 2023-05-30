from moviepy.editor import VideoFileClip
from moviepy.config import change_settings
from playwright.sync_api import sync_playwright, ViewportSize
from moviepy.editor import *
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from playwright.sync_api import Playwright, sync_playwright, expect, TimeoutError as PlaywrightTimeoutError
import keyboard
import time
import csv
from moviepy.video.compositing.concatenate import concatenate_videoclips
import moviepy.video.fx.all as vfx
import moviepy.editor as me
import datetime
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw

change_settings({"IMAGEMAGICK_BINARY":r"c:\Program Files\ImageMagick"})
SCREENSHOTS_DURATION=4

with sync_playwright() as playwright:

    x=input("\nType coordinates: ")
    print("\nOnce you are in the Street View window use the hotkeys to control the recording")
    print("\nHotkeys:\tR: Start recording\tEsc: Finish reocording\t   Space_bar: Pause/Resume\tP: Screenshot")
    browser = playwright.chromium.launch(headless=False, channel="chrome")
    if os.path.exists("./data/state.json"):
        context = browser.new_context(
            storage_state="./data/state.json"
        )
        page = context.new_page()
        page.goto("https://www.google.com/maps/@?api=1&map_action=pano&viewpoint="+x+"&pitch=0?hl=en")
    else:
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.google.com/maps/@?api=1&map_action=pano&viewpoint="+x+"&pitch=0?hl=en")
        page.get_by_role("button", name="Accept all").click()
        context.storage_state(path="./data/state.json")
        context.close()
        browser.close()
        browser = playwright.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(
            storage_state="./data/state.json"
        )
        page = context.new_page()
        page.goto("https://www.google.com/maps/@?api=1&map_action=pano&viewpoint="+x+"&pitch=0?hl=en")
    time_pause=[]
    time_pause.append(0.0)
    st=0.0
    recording=False
    recorded=False
    tscreenshots=[]
    tscreenshots.append(0.0)
    screenshots=[]
    timeside=[]
    timeside.append(0.0)
    finished=False
    side=False
    coords=[]
    #'Google Maps - Google Chrome'
    # define the codec
    fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
    # frames per second
    fps = 15
    # search for the window, getting the first matched window with the title
    w = gw.getWindowsWithTitle('Google Maps - Google Chrome')[0]
    out = cv2.VideoWriter("output.mp4", fourcc, fps, tuple(w.size))
    seconds=0.0
    while True:
        while not recording:
            if keyboard.is_pressed("r") or keyboard.is_pressed("R"):
                print("\nStarted recording")
                recording=True
                recorded=True
            if keyboard.is_pressed('space'):
                print("Recording resumed")
                recording=True
                time.sleep(0.2)
            if keyboard.is_pressed('Esc'):
                    print("\nEnded recording")
                    finished=True
                    break
        while recording:
            seconds=seconds+1/15
            img = pyautogui.screenshot(region=(w.left, w.top, w.width, w.height))
            # convert these pixels to a proper numpy array to work with OpenCV
            frame = np.array(img)
            # convert colors from BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # write the frame
            out.write(frame)
            try:
                if keyboard.is_pressed('Esc'):
                    print("\nEnded recording")
                    finished=True
                    break

                if keyboard.is_pressed('space'):
                    recording=False
                    print("Recording paused")
                    time.sleep(0.2)
                if (keyboard.is_pressed("P") or keyboard.is_pressed("p")):
                    tscreenshots.append(seconds)
                    print("\nScreenshot")
                    i=0
                
                    for j,char in enumerate(page.url):
                        if i==2:
                            break
                        if page.url[j]==",":
                            i=i+1
                        last=j
                    first=last
                    while page.url[first]!="@":
                        first=first-1
                    first=first+1
                    coordinates=""
                    for i in range(first,last):
                        coordinates=coordinates+page.url[i]
                    print(coordinates)    
                    coords.append(coordinates)
                    time.sleep(0.2)
                elif page.get_by_role("button", name="Collapse side panel").is_visible() and not side:
                    side=True
                    timeside.append(seconds)
                elif side and not page.get_by_role("button", name="Collapse side panel").is_visible():
                    side=False
                    timeside.append(seconds)
                with page.expect_navigation(timeout=0.0000001):
                    pass
            except PlaywrightTimeoutError:
                pass
        if finished:
            break
    out.release()
    context.close()
    browser.close()
    



in_loc = "output.mp4"
out_loc = 'output/du_out.mp4'

# Import video clip
clip = VideoFileClip(in_loc)
clip=clip.fx(vfx.crop, y1=102,y2=1000,x1=8,x2=1602).set_fps(15)
clip=clip.resize(width=1280,height=720)
duration=clip.duration
subclips=[]
i=0
for i,pause in enumerate(timeside):
    if(i==len(timeside)-1):
        if i==0:
            subclips.append(clip.subclip(timeside[i],duration))
        elif(i%2!=0):
            subclips.append(clip.subclip(timeside[i],duration).fx(vfx.crop, x1=480).set_fps(15))
        elif(i%2==0):
            subclips.append(clip.subclip(timeside[i],duration))
    elif i==0:
        subclips.append(clip.subclip(timeside[i],timeside[i+1]))
    elif i%2==0:
        subclips.append(clip.subclip(timeside[i],timeside[i+1]))
    elif i%2!=0:
        subclips.append(clip.subclip(timeside[i],timeside[i+1]).fx(vfx.crop, x1=480).set_fps(15))
beta=concatenate_videoclips(subclips, method='compose')
duration=beta.duration
prealfas=[]
if len(tscreenshots)>1:
    for i,t in enumerate(tscreenshots):
        if(i<len(tscreenshots)-1):
            prealfas.append(beta.subclip(tscreenshots[i],tscreenshots[i+1]))
            beta.save_frame("./frames/frame"+str(i+1)+".png", t = tscreenshots[i+1])
            image=me.ImageClip("./frames/frame"+str(i+1)+".png").set_duration(SCREENSHOTS_DURATION)
            prealfas.append(image)
        elif (i==len(tscreenshots)-1):
            prealfas.append(beta.subclip(tscreenshots[i],duration))
    with open('./spreadsheets/timestamps.csv', 'w+') as f:
        for i,t in enumerate(tscreenshots):
            if i==0:
                pass
            else:
                time=str(datetime.timedelta(seconds=t+(i-1)*SCREENSHOTS_DURATION))
                f.write(time+","+str(SCREENSHOTS_DURATION))
                f.write("\n")
    with open('./coordinates.txt', 'w+') as f:
        for coord in coords:
            f.write(str(coord))
            f.write("\n")
    final=concatenate_videoclips(prealfas)
    final.write_videofile(out_loc)
else:
    if recorded:
        beta.write_videofile(out_loc)
    else:
        print("You didn't start recording")

    
clip.close()
os.remove(in_loc)

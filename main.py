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
change_settings({"IMAGEMAGICK_BINARY":r"c:\Program Files\ImageMagick"})
SCREENSHOTS_DURATION=4

with sync_playwright() as playwright:

    x=input("\nType coordinates: ")
    print("\nOnce you are in the Street View window use the hotkeys to control the recording")
    print("\nHotkeys:\tR: Start recording\tEsc: Finish reocording\t   Space_bar: Pause/Resume\tP: Screenshot")
    browser = playwright.chromium.launch(headless=False, channel="chrome")
    if os.path.exists("./data/state.json"):
        context = browser.new_context(
            record_video_dir="videos/",
            record_video_size={"width": 1280, "height": 720},
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
            record_video_dir="videos/",
            record_video_size={"width": 1280, "height": 720},
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
    while True:
        try:
            if (keyboard.is_pressed("r") or keyboard.is_pressed("R")) and recording==False:
                st=time.perf_counter()-1.2
                print("\nStarted recording")
                recording=True
                recorded=True
                time.sleep(0.7)

            elif keyboard.is_pressed('Esc'):
                print("\nEnded recording")
                finished=True
                break

            elif keyboard.is_pressed('space') and recording==True:
                time_pause.append(time.perf_counter()-st)
                if(len(time_pause)%2==0):
                    print("Recording paussed at "+ str(time.perf_counter()-st))
                elif(len(time_pause)%2!=0):
                    print("Recording resumed")
                time.sleep(0.7)
            elif (keyboard.is_pressed('P') or keyboard.is_pressed('p')):
                tscreenshots.append(time.perf_counter()-st)
                print("\nScreenshot at "+str(int(time.perf_counter())-int(st)))
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
                time.sleep(0.7)
            elif page.get_by_role("button", name="Collapse side panel").is_visible() and not side and recording:
                side=True
                timeside.append(time.perf_counter()-st-1.2)
            elif side and not page.get_by_role("button", name="Collapse side panel").is_visible() and recording:
                side=False
                timeside.append(time.perf_counter()-st-1.2)
            with page.expect_navigation(timeout=1):
                pass
        except PlaywrightTimeoutError:
            pass
        
    
    tt=time.perf_counter()
    print("tt:"+str(tt)+"st:"+str(st)+"ft:"+str((tt-st)))
    timestamp=tt-st
    context.close()
    browser.close()

archivos = os.listdir('videos/')
in_loc = "videos/"+archivos[0]
out_loc = 'output/du_out.mp4'

# Import video clip
clip = VideoFileClip(in_loc)
duration=clip.duration
clip=clip.subclip(duration-timestamp,duration)
duration=clip.duration
subclips=[]
i=0
for i,pause in enumerate(timeside):
    if(i==len(timeside)-1):
        if i==0:
            subclips.append(clip.subclip(timeside[i],duration))
        elif(i%2!=0):
            subclips.append(clip.subclip(timeside[i],duration).fx(vfx.crop, x1=480))
        elif(i%2==0):
            subclips.append(clip.subclip(timeside[i],duration))
    elif i==0:
        subclips.append(clip.subclip(timeside[i],timeside[i+1]))
    elif i%2==0:
        subclips.append(clip.subclip(timeside[i],timeside[i+1]))
    elif i%2!=0:
        subclips.append(clip.subclip(timeside[i],timeside[i+1]).fx(vfx.crop, x1=480))
clip=concatenate_videoclips(subclips)
subclips=[]
sumframe=0
k=0
for i,pause in enumerate(time_pause):
    if(i==len(time_pause)-1):
        if(i%2==0):
            subclips.append(clip.subclip(time_pause[i],duration))
    elif(i%2==0):
        subclips.append(clip.subclip(time_pause[i],time_pause[i+1]))
    elif(i%2!=0):
        sumframe=sumframe+time_pause[i+1]-time_pause[i]
        while tscreenshots[k]<time_pause[i+1] and k<len(tscreenshots)-1:
            k=k+1
            tscreenshots[k]=tscreenshots[k]-sumframe



beta=concatenate_videoclips(subclips, method= "compose")
duration=beta.duration
prealfas=[]
if len(tscreenshots)>1:
    for i,t in enumerate(tscreenshots):
        if(i<len(tscreenshots)-1):
            prealfas.append(beta.subclip(tscreenshots[i],tscreenshots[i+1]))
            beta.save_frame("./frames/frame"+str(i+1)+".png", t = tscreenshots[i+1])
            image=me.ImageClip("./frames/frame"+str(i+1)+".png").set_duration(SCREENSHOTS_DURATION).resize(width=1280,height=720)
            prealfas.append(image)
        elif (i==len(tscreenshots)-1):
            prealfas.append(beta.subclip(tscreenshots[i],duration))
    with open('./spreadsheets/timestamps.csv', 'w+') as f:
        for i,t in enumerate(tscreenshots):
            if i==0:
                pass
            else:
                time=str(datetime.timedelta(seconds=t))
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

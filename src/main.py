import uvicorn
from fastapi import File, UploadFile, FastAPI
from typing import List
from fastapi import Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import cv2
import numpy as np
from PIL import Image
import base64
import io
import pickle
import argparse
import time
import io as StringIO
from io import BytesIO
import json
import os
from imutils.video import VideoStream
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import threading
import imutils
import time
import cv2
import uvicorn
from multiprocessing import Process, Queue
import subprocess
import numpy as np

app = FastAPI()

manager = None
count_keep_alive = 0

width = 1280
height = 720
lock = threading.Lock()
confthres = 0.3
nmsthres = 0.1
yolo_path = './static'
labelsPath="configuration/obj.names"
cfgpath="configuration/yolo-obj.cfg"
wpath="weights/yolo-obj_best.weights"
TRAFFIC_FEED_URL = "https://wzmedia.dot.ca.gov/D5/1atHarkinsSloughRd.stream/playlist.m3u8"


def start_stream(TRAFFIC_FEED_URL, manager):
    global width
    global height

    vs = VideoStream(TRAFFIC_FEED_URL).start()
    while True:
        time.sleep(0.2)

        frame = vs.read()
        frame = imutils.resize(frame, width=680)
        output_frame = frame.copy()

        if output_frame is None:
            continue
        (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
        if not flag:
            continue
        manager.put(encodedImage)

def streamer():
    try:
        while manager:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(manager.get()) + b'\r\n')
    except GeneratorExit:
        print("cancelled")

def manager_keep_alive(p):
    global count_keep_alive
    global manager
    while count_keep_alive:
        time.sleep(1)
        print(count_keep_alive)
        count_keep_alive -= 1
    p.kill()
    time.sleep(.5)
    p.close()
    manager.close()
    manager = None

def get_labels(labels_path):
    lpath=os.path.sep.join([yolo_path, labels_path])
    LABELS = open(lpath).read().strip().split("\n")
    return LABELS

def get_colors(LABELS):
    # initialize a list of colors to represent each possible class label
    np.random.seed(42)
    COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),dtype="uint8")
    return COLORS

def get_weights(weights_path):
    # derive the paths to the YOLO weights and model configuration
    weightsPath = os.path.sep.join([yolo_path, weights_path])
    return weightsPath

def get_config(config_path):
    configPath = os.path.sep.join([yolo_path, config_path])
    return configPath

def load_model(configpath,weightspath):
    # load our YOLO object detector trained on COCO dataset (80 classes)
    print("[INFO] loading YOLO from disk...")
    print("[INFO] model config: ",configpath)
    print("[INFO] model weights: ", weightspath)
    net = cv2.dnn.readNetFromDarknet(configpath, weightspath)
    return net

def image_to_byte_array(image:Image):
  imgByteArr = io.BytesIO()
  image.save(imgByteArr, format='JPEG')
  imgByteArr = imgByteArr.getvalue()
  return imgByteArr

def get_predection(image,net,LABELS,COLORS):
    print("[INFO] get_prediction() started")
    (H, W) = image.shape[:2]

    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    # determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]
   
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    print(layerOutputs)
    end = time.time()

    prediction_time = end - start

    print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    boxes = []
    confidences = []
    classIDs = []
    # loop over each of the layer outputs
    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            # print(scores)
            classID = np.argmax(scores)
            # print(classID)
            confidence = scores[classID]

            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > confthres:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

    # apply non-maxima suppression to suppress weak, overlapping bounding
    # boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, confthres,
                            nmsthres)
    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # extract the bounding box coordinates
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            # draw a bounding box rectangle and label on the image
            color = [int(c) for c in COLORS[classIDs[i]]]
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
            text = "{}: {:.4f}".format(LABELS[classIDs[i]], confidences[i])
            print(boxes)
            print(classIDs)
            cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,0.5, color, 2)
    return prediction_time, image

def generate():
    # grab global references to the output frame and lock variables
    global outputFrame, lock
    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue
            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            # ensure the frame was successfully encoded
            if not flag:
                continue
        # yield the output frame in the byte format
        #yield b''+bytearray(encodedImage)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
               bytearray(encodedImage) + b'\r\n')

labelsPath="model/configuration/obj.names"
cfgpath="model/configuration/yolo-obj.cfg"
wpath="model/weights/yolo-obj_last.weights"
Lables=get_labels(labelsPath)
CFG=get_config(cfgpath)
Weights=get_weights(wpath)
nets=load_model(CFG,Weights)
Colors=get_colors(Lables)
IP_CAMERA_RESOLUTION = (640, 360)
templates = Jinja2Templates(directory="templates")
cap = cv2.VideoCapture(TRAFFIC_FEED_URL)

cap.set(cv2.CAP_PROP_BUFFERSIZE,1)
print(cv2.getBuildInformation())
# Find OpenCV version
major_ver, minor_ver, subminor_ver = (cv2.__version__).split('.')

FEED_FPS =0

if int(major_ver)  < 3 :
    FEED_FPS = cap.get(cv2.cv.CV_CAP_PROP_FPS)
    print("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(FEED_FPS))
else :
    FEED_FPS = cap.get(cv2.CAP_PROP_FPS)
    print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(FEED_FPS))

def generate():
    try:
        while True:
            ret, image_np = cap.read()
            print("***Imageread***")
            
            image_np_expanded = np.expand_dims(image_np, axis=0)
            print("***Image expanded***")
            image=cv2.cvtColor(image_np_expanded,cv2.COLOR_BGR2RGB)
            print("***cvtColot expanded image***")
            # Actual detection.
            res=get_predection(image,nets,Lables,Colors)
            print("***Image after prediction***")
            #image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
            image=cv2.cvtColor(res,cv2.COLOR_BGR2RGB)
            print("***Image after cvtColor***")
            np_img=Image.fromarray(image)
            print("***Image fromarray***")
            img_encoded=image_to_byte_array(np_img)
            print("***Image to byte array**")
            img_bin = io.BytesIO(img_encoded)
            print("***Image BytesIOs***")

            cv2.imshow('object_detection', cv2.resize(img_bin, IP_CAMERA_RESOLUTION))
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                break
    except cv2.error as e:
        print("@@@@@@Exception in cv2:@@@@@@@@", e)
        cap.release()

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



#WORKING Solution with cv2.imshow -> display in python
def just_stream():
    myFrameNumber = 50
    #cap = cv2.VideoCapture("video.mp4")

    # get total number of frames
    totalFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    # check for valid frame number
    if myFrameNumber >= 0 & myFrameNumber <= totalFrames:
        # set frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES,myFrameNumber)

    prev_frame_time =0
    curr_frame_time=0
    font = cv2.FONT_HERSHEY_COMPLEX

    count = 0
    while True:
        if (count > 10):
            ret, frame = cap.read()
            count = 0
            image=frame.copy()
            image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
            prediction_time, res=get_predection(image,nets,Lables,Colors)
            image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
            image=cv2.cvtColor(res,cv2.COLOR_BGR2RGB)
            curr_frame_time = time.time()
            fps= 1/(curr_frame_time - prev_frame_time)
            prev_frame_time = curr_frame_time
            feed = FEED_FPS
            frame_lag = (feed - fps) * 60
            time_lag = frame_lag/fps
            
            cv2.putText(image, "prediction fps:"+ str(round(fps,1)), (7, 100), font, 1, (100, 255, 0), 3, cv2.LINE_AA)
            cv2.putText(image, "time taken for prediction:" + str(round(prediction_time,2)) + " (seconds)", (7, 150), font, 1, (100, 255, 0), 3, cv2.LINE_AA)
            cv2.putText(image, "live feed fps:"+ str(int(FEED_FPS)), (7, 200), font, 1, (100, 255, 0), 3, cv2.LINE_AA)
            cv2.putText(image, "Current Frame Lag:"+ str(int(frame_lag)), (7, 250), font, 1, (100, 255, 0), 3, cv2.LINE_AA)
            cv2.putText(image, "Current Time lag: "+ str(round(time_lag,2))+ " (seconds)", (7, 300), font, 1, (100, 255, 0), 3, cv2.LINE_AA)

            cv2.imshow("Video", image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        count = count+ 1

    cv2.destroyAllWindows()
    cap.release()

@staticmethod
def __draw_label(img, text, pos, bg_color):
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.4
    color = (0, 0, 0)
    thickness = cv2.FILLED
    margin = 2

    txt_size = cv2.getTextSize(text, font_face, scale, thickness)

    end_x = pos[0] + txt_size[0][0] + margin
    end_y = pos[1] - txt_size[0][1] - margin

    cv2.rectangle(img, pos, (end_x, end_y), bg_color, thickness)
    cv2.putText(img, text, pos, font_face, scale, color, 1, cv2.LINE_AA)


@app.get("/")
async def landing_page(request: Request):
  return templates.TemplateResponse("index-stream-video.html", {"request": request})

@app.get("/stream_video")
async def stream_video():
    return StreamingResponse(just_stream(), media_type="multipart/x-mixed-replace;boundary=frame")

@app.get("/keep-alive")
def keep_alive():
    global manager
    global count_keep_alive
    count_keep_alive = 100
    if not manager:
        manager = Queue()
        p = Process(target=start_stream, args=(url_rtsp, manager,))
        p.start()
        threading.Thread(target=manager_keep_alive, args=(p,)).start()

if __name__ == '__main__':
    uvicorn.run("main:app", host='0.0.0.0', port=8080, debug=True)
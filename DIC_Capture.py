#Author: Maxwell Vos
#Date 01/2023
#Capturing software used in custom DIC standalone system
import sys
import time
import serial
import csv
import cv2
import neoapi
import matplotlib.pyplot as plt
import numpy as np
import math
import pyfirmata.util
import tifffile as tf
import pip
from threading import Thread
from pyfirmata import Arduino, util
from time import sleep
import easygui
import os

#Record mode simplifies the displays and saves all data
global record_mode
record_mode = False

global exposure_time_ms
exposure_time_ms = 1.6


#Size of the array that the camera loads the images into RAM. Only first image is displayed. Used to increase fps peformance.
global max_buffer_arr

global test_ID
test_ID = ''

if record_mode == True:
    # fpsValues = [0,0.25,1,32,1,0.2,0] # pin sequence for fps, iterates array index everytime quench 4 state is changed.
    #fpsValues = [0, 1, 0.125, 0.125, 0, 0.125]  # Matthew Inconel RBDT

    #fpsValues = [0, 0, 0.125, 0]  # use this for calibration image capture
    fpsValues = [0, 0.125, 0.125, 0.125, 0, 0.125] #Matthew Inconel Testing

    max_buffer_arr = 3

    save_path  = easygui.diropenbox(
        default='C:/Users/maxwe/OneDrive/Documents/Masters/Test_Data/Mathew DIC',
        title='Select an EMPTY folder as the save location for this test')
    print(save_path)
    test_ID = os.path.basename(os.path.normpath(save_path))
    print(test_ID)
    raw_data_save_dir = os.path.join(save_path, "Raw_Data")
    os.mkdir(raw_data_save_dir,0o666)
    cam_1_save_dir = os.path.join(save_path, "Camera_1")
    os.mkdir(cam_1_save_dir, 0o666)
    cam_2_save_dir = os.path.join(save_path, "Camera_2")
    os.mkdir(cam_2_save_dir, 0o666)
    cam_3_save_dir = os.path.join(save_path, "Camera_3")
    os.mkdir(cam_3_save_dir, 0o666)
    synced_data_save_dir = os.path.join(save_path, "Synced_Data")
    os.mkdir(synced_data_save_dir, 0o666)
    DIC_results_save_dir = os.path.join(save_path, "DIC_Results")
    os.mkdir(DIC_results_save_dir, 0o666)
else:
    max_buffer_arr = 3
    fpsValues = [0,20,0]
    save_path = ''
    test_ID = ''
    raw_data_save_dir = ''
    cam_1_save_dir = ''
    cam_2_save_dir = ''

cam1_src = 'P1-6' #'P1-6' USB 3 port at back of laptop, 'P1-5' is USB C to USB 3.1 adaptor
cam2_src = 'P1-5' #'P1-6' USB 3 port at back of laptop, 'P1-5' is USB C to USB 3.1 adaptor

ser = serial.Serial('COM4', 115200, timeout=2)

def hardware_tigger():
    #NOTE: have to wait for everything to initialize, maybe wait before calling the hardware trigger function?
    sleep(1)
    TCTN1_Values = ''
    TCTN1_temp = ''

    for i in fpsValues:
        if i == 0:
            TCTN1_temp = '0'
        else:
            TCTN1_temp = str(round(65536- 16000000/(1024 * i*2)))  # converts frame rate to arduino clock overflow start value
        TCTN1_Values = TCTN1_Values + TCTN1_temp + ', ' #adds this value to a string which will be sent to the arduino
    TCTN1_Values = TCTN1_Values[: -2] #delets the ', ' from the end of the string befor sending

    while True:
        try: #reads serial output from audrino
            ser.write(TCTN1_Values.encode())
            qValue = ser.readline().strip().decode('ascii')
            print('serial output: ', qValue)
            if qValue == "RECIEVED" and (record_mode == True ):
                with open(raw_data_save_dir + "/Arduino_Serial_Output_" + test_ID + '.txt', 'a') as f:
                    heading_write_ard = 'Frame'+'\t'+'Time'+'\t'+'State'+'\t'+'Count'+'\t'+'Last_QTime'+'\n'
                    f.write(heading_write_ard) #headings for .txt file output
                break
        except:
            sleep(0.01)

    while (record_mode == True):
        try:
            while (ser.inWaiting() == 0):
               pass
            qValue = ser.read(ser.in_waiting)

            with open(raw_data_save_dir + "/Arduino_Serial_Output_" + test_ID + '.txt', 'a') as f:
                f.write(qValue.decode('ascii'))

        except:
            pass

class vStream():
    def __init__(self,src,windowName, timeOut_ms, buffer_arr_max, xPos, yPos, xPosHist, yPosHist, cam_save_dir):
        self.buffer_arr_max = buffer_arr_max
        self.timeOut_ms = timeOut_ms
        self.windowName = windowName
        self.zoomWindowName = windowName+' Zoomed'
        self.xPos = xPos
        self.yPos = yPos
        self.src = src
        self.camera = neoapi.Cam()
        self.camera.Connect(self.src)
        self.xPosHist = xPosHist
        self.yPosHist = yPosHist
        self.cam_save_dir = cam_save_dir

        self.camera.SetImageBufferCount(20)
        self.camera.SetImageBufferCycleCount(10)

        self.camera.f.PixelFormat.SetString('Mono12')
        self.camera.f.ExposureTime.Set(exposure_time_ms* 1000)
        self.camera.f.TriggerMode = neoapi.TriggerMode_On
        #self.camera.f.TriggerSource = neoapi.TriggerSource_Software
        #self.camera.f.TriggerSoftware.Execute()
        self.camera.f.TriggerSource = neoapi.TriggerSource_Line2
        self.camera.f.TriggerActivation = neoapi.TriggerActivation_RisingEdge
       #self.camera.f.TriggerActivation neoapi.AcquisitionStatusSelector_AcquisitionTriggerWait
        #self.cam_event = neoapi.NeoEvent()
        #self.camera.ClearEvents()
        #self.camera.EnableEvent("ExposureStart")

        #self.camera.EnableChunk('Image')  # enable the Image chunk to receive the data of the image
        #self.camera.EnableChunk('ExposureTime')
        #self.camera.EnableEvent("ExposureStart")
        self.triggerUpdateBool = False
        self.printFPS = False
        self.img_arr = []

        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True

        self.arr_A_full = False
        self.arr_B_full = False

        self.thread_array_read = Thread(target=self.get_full_arr, args=())
        self.thread_array_read.daemon = True


        self.thread_save_array = Thread(target=self.save_array, args=())
        self.thread_save_array.daemon = True


        self.img_arr_A = []
        self.img_arr_B = []

        self.count_img = 0

        self.displayWait = False

        self.clicked = 0

        self.scale = 0.41

        self.save_last_array = False

        self.cam_t0 = 0



    def click_event(self, event, x, y, flags, params):
        self.event = event
        self.flags = flags
        self.params = params
        if self.event == cv2.EVENT_LBUTTONDOWN:
            self.x_0 = x
            self.y_0 = y
            self.x_0_scaled = round(self.x_0 / self.scale)
            self.y_0_scaled = round(self.y_0 / self.scale)

        if self.event == cv2.EVENT_LBUTTONUP:
            self.x_1 = x
            self.y_1 = y
            self.x_1_scaled = round(self.x_1 / self.scale)
            self.y_1_scaled = round(self.y_1 / self.scale)
            self.clicked = self.clicked + 1

    def start_vStream(self):
        self.thread.start()
        self.thread_array_read.start()
        self.thread_save_array.start()

    def update(self):
        self.temp = []
        for self.k in range(0, self.buffer_arr_max):
            self.img_arr_A.append(self.temp)
            self.img_arr_B.append(self.temp)
        while True:
            for self.i in range(0,self.buffer_arr_max):
                try:
                    self.img = self.camera.GetImage(self.timeOut_ms)
                    self.img_arr_A[self.i] = self.img
                except:
                    pass
                    print('Image grab problem print problem')
            self.arr_A_full = True
            self.arr_B_full = False
            for self.i in range(0,self.buffer_arr_max):
                try:
                    self.img = self.camera.GetImage(self.timeOut_ms)
                    self.img_arr_B[self.i] = self.img
                except:
                    print('Image grab problem print problem')
                    pass
            self.arr_A_full = False
            self.arr_B_full = True

    def save_buffer_remainder(self):
        self.save_last_array = True

    def get_full_arr(self):
        while True:
            if self.arr_A_full:
                self.arr_A_full = False
                return self.img_arr_A
            else:
                if self.arr_B_full:
                    self.arr_B_full = False
                    return self.img_arr_B
                else:
                    return 0

    def save_array(self):
        if (record_mode == True):
            with open(raw_data_save_dir + '/' + test_ID + '_CAM_' + self.windowName + '.txt', 'a') as f:
                self.heading_cam = 'Frame'+'\t'+'Frame_Name'+'\t'+'Cam_Time'+'\n'
                f.write(self.heading_cam)
        while True:
            try:
                self.img_arr = self.get_full_arr()
                if self.save_last_array:
                    if self.arr_A_full:
                        self.img_arr = self.img_arr_B
                    else:
                        if self.arr_B_full:
                            self.img_arr = self.img_arr_A
                        self.save_last_array = False
                if (self.img_arr != 0):
                    self.frame = self.img_arr[0].GetNPArray()
                    self.displayWait = False

                    if (record_mode == True):
                        for self.k in range(0, self.buffer_arr_max): #saves an image as .tif and adds image details to .csv file

                            self.img_title = str(test_ID) + '_' + str(self.img_arr[self.k].GetImageID()) + '_' + self.windowName + '.tif'
                            self.fileName = self.cam_save_dir + '/' + self.img_title
                            self.save_img = self.img_arr[self.k].GetNPArray()
                            self.img_ID = self.img_arr[self.k].GetImageID()
                            self.img_TimeStamp = self.img_arr[self.k].GetTimestamp()


                            if (self.img_TimeStamp != 0):
                                if (self.img_ID == 0):
                                    self.cam_t0 = self.img_TimeStamp
                                self.img_TimeStamp_zerod = round((self.img_TimeStamp - self.cam_t0) / 1000000)
                                self.data = str(self.img_ID) + '\t' + str(self.img_title) + '\t' + str(self.img_TimeStamp_zerod) + '\n'
                                tf.imwrite(self.fileName, self.save_img, photometric='minisblack')
                                with open(raw_data_save_dir + '/'  + test_ID + '_CAM_'+self.windowName+'.txt', 'a') as f:
                                    f.write(self.data)
                                print('saved', self.data)


            except:
                print('save array error')

    def displayFrame(self):
        if self.displayWait == False:

            self.img_8 = (self.frame / 256).astype('uint8')
            self.img_heat_8 = cv2.applyColorMap(self.img_8, cv2.COLORMAP_TURBO)
            #self.img_rotated = cv2.rotate(self.img_heat_8, cv2.ROTATE_90_COUNTERCLOCKWISE)
            self.img_rotated = self.img_heat_8

            self.width = int(self.img_rotated.shape[1] * self.scale)
            self.height = int(self.img_rotated.shape[0] * self.scale)
            self.dim = (self.width, self.height)

            self.img_resized_8 = cv2.resize(self.img_rotated, self.dim, interpolation=cv2.INTER_AREA)

            cv2.line(self.img_resized_8, (0,round(self.height/2)), (self.width,round(self.height/2)), (0,255,0), 1)
            cv2.line(self.img_resized_8, (round(self.width / 2),0), (round(self.width / 2),self.height), (0, 255, 0), 1)

            if self.displayWait == False:
                if (self.clicked > 0):
                    #self.img_grey_rotated = cv2.rotate(self.img_8, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    self.img_grey_rotated = self.img_8
                    cv2.rectangle(self.img_resized_8, (self.x_0,self.y_0), (self.x_1,self.y_1), (0,0,255), 2)
                    self.zoomed_img = self.img_rotated[self.y_0_scaled : self.y_1_scaled, self.x_0_scaled : self.x_1_scaled]
                    self.zoomed_gray = self.img_grey_rotated[self.y_0_scaled: self.y_1_scaled, self.x_0_scaled: self.x_1_scaled]
                    cv2.imshow(self.zoomWindowName, self.zoomed_img)
                    self.showHistogram()

            cv2.namedWindow(self.windowName)
            cv2.moveWindow(self.windowName, self.xPos, self.yPos)
            cv2.imshow(self.windowName, self.img_resized_8)

            self.displayWait = True

    def showHistogram(self):
        self.histr = cv2.calcHist([self.zoomed_gray], [0], None, [255], [0, 255])
        self.histr[254] = self.histr[254] * 10000
        if self.histr[254] > 0:
            self.histr[254] = int(((max(self.histr) / 10)))
        self.hist_height = 255
        self.hist_width = 260
        self.img_hist = np.zeros((self.hist_height + 1, self.hist_width), dtype=np.uint8)
        for self.k in range(0, 255):
            self.temp_hist = int((self.histr[self.k] / (max(self.histr))) * self.hist_height)
            self.img_hist[0:self.temp_hist, self.k] = self.k  # black
        self.img_hist[0:self.temp_hist, 255:self.hist_width] = self.k
        self.img_hist = cv2.flip(self.img_hist, 0)
        self.img_hist = (self.img_hist).astype('uint8')
        self.img_hist = cv2.applyColorMap(self.img_hist, cv2.COLORMAP_TURBO)
        self.hist_window_name = str(self.windowName + ' Histogram')
        cv2.namedWindow(self.hist_window_name)  # Create a named window
        cv2.moveWindow(self.hist_window_name, self.xPosHist, self.yPosHist)
        cv2.imshow(self.hist_window_name, self.img_hist)

    def getImgID(self):
        return self.imgID

    def getFPS(self):
        return 10

    def getTimestamp(self):
        return self.timestamp_arr[1]

    def getFrame(self):
        return self.img_16

    def returnCaptured(self):
        return self.captured

    def getFrameTimestamp(self):
        return self.img_timestamp

    def triggerUpdate(self):
        self.triggerUpdateBool = True

class VideoShow: #still have to work out if I still nead the video show class
    """
    Class that continuously shows a frame using a dedicated thread.
    """
    def __init__(self, frame=None):
        self.frame = frame
        self.stopped = False
        self.triggerUpdateShowBool = False
        self.thread = Thread(target=self.show, args=())
        self.thread.daemon = True
        self.thread.start()


    def triggerUpdateShow(self):
        self.triggerUpdateShowBool = True


    def show(self):
        #self.windowName = windowName
        while not self.stopped:
            try:
                VideoShow.getScaledFrame_8(self)
                cv2.imshow(self.windowName, self.img_resized_8)
                if cv2.waitKey(1) == ord("q"):
                    self.stopped = True
            except:
                pass
                #print('Video Show Exception')

    def stop(self):
        self.stopped = True

    def convert16to8bit(self):
        self.img_8 = (self.frame / 256).astype('uint8')

    def getScaledFrame_8(self):
        self.img_8 = (self.frame / 256).astype('uint8')
        self.img_heat_8 = cv2.applyColorMap(self.img_8, cv2.COLORMAP_TURBO)
        self.width = int((self.img_heat_8.shape[1] * 40) / 100)
        self.height = int((self.img_heat_8.shape[0] * 40) / 100)
        self.dim = (self.width, self.height)
        self.img_resized_8 = cv2.resize(self.img_heat_8, self.dim, interpolation=cv2.INTER_AREA)


def getScaledFrame_8(img_8,scale_percent):
    img_8 = cv2.applyColorMap(img_8, cv2.COLORMAP_TURBO)
    width = int(img_8.shape[1] * scale_percent / 100)
    height = int(img_8.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized = cv2.resize(img_8, dim, interpolation=cv2.INTER_AREA)
    return resized

def getHistogram(img_8):
    histr = cv2.calcHist([img_8], [0], None, [255], [0, 255])
    histr[254] = histr[254] * 500
    if histr[254] > 0:
        histr[254] = int(((max(histr) / 10)))
    hist_height = 255
    hist_width = 260
    img_hist = np.zeros((hist_height + 1, hist_width), dtype=np.uint8)
    for k in range(0, 255):
        temp_hist = int((histr[k] / (max(histr))) * hist_height)
        img_hist[0:temp_hist, k] = k  # black
    img_hist[0:temp_hist, 255:hist_width] = k
    img_hist = (img_hist).astype('uint8')
    img_hist = cv2.applyColorMap(img_hist, cv2.COLORMAP_TURBO)

    for j in range(0, 255):
        temp_hist = int((histr[j] / (max(histr))) * hist_height)
        img_hist[temp_hist:hist_height, j] = (255, 255, 255)
        img_hist[temp_hist, j] = (0, 0, 0)

    img_hist[temp_hist:hist_height, 255:hist_width] = (255, 255, 255)
    img_hist[temp_hist, 255:hist_width] = (0, 0, 0)
    img_hist = cv2.flip(img_hist, 0)
    return img_hist

threadTrigger = Thread(target=hardware_tigger, args=())
threadTrigger.daemon = True
threadTrigger.start()


#(self,src,windowName, timeOut_ms)
cam1 = vStream(cam1_src, '1', 4000, max_buffer_arr,-16,0,1655,450,cam_1_save_dir)
cam2 = vStream(cam2_src, '2', 4000, max_buffer_arr,823,0,1655,740,cam_2_save_dir)

cam1.start_vStream()
cam2.start_vStream()

sleep(2)

while True:
    try:
        cam1.displayFrame()
        cam2.displayFrame()
        cv2.setMouseCallback(cam1.windowName, cam1.click_event)
        cv2.setMouseCallback(cam2.windowName, cam2.click_event)
    except:
        #print('Loading Camera')
        #sleep(0.2)
        pass
    if cv2.waitKey(10) == "TEMPORTY BLOCK":#ord('q'):
        #cam1.capture.release()
        cam1.save_buffer_remainder()
        cv2.destroyAllWindows()
        exit(1)
        break
    #if cv2.waitKey(10) == ord('q'):
     #   exposure_time_ms = exposure_time_ms + 10


"""
LIST OF EVENT NAMES FOR BAUMER VCXU-50:
Event name: FrameTransferSkipped
Event name: DeviceTemperatureStatusChanged
Event name: ExposureEnd
Event name: Line1RisingEdge
Event name: EventLost
Event name: TriggerOverlapped
Event name: FrameEnd
Event name: Line3RisingEdge
Event name: EventTest
Event name: ExposureStart
Event name: FrameStart
Event name: Line0FallingEdge
Event name: Line0RisingEdge
Event name: Line1FallingEdge
Event name: Line2FallingEdge
Event name: Line2RisingEdge
Event name: Line3FallingEdge
Event name: TransferBufferFull
Event name: TransferBufferReady
Event name: TriggerReady
Event name: TriggerSkipped

CHUNKS:
'Binning', 'BlackLevel', 'Image', 'Height', 'DeviceTemperature', 'ExposureTime', 'FrameID', 'Gain', 'Width', 'ImageControl', 'LineStatusAll', 'OffsetX', 'OffsetY', 'PixelFormat', 'Timestamp'
'Binning' 
'BlackLevel' 
'Image' 
'Height' 
'DeviceTemperature' 
'ExposureTime' 
'FrameID' 
'Gain' 
'Width' 
'ImageControl' 
'LineStatusAll' 
'OffsetX' 
'OffsetY' 
'PixelFormat'
'Timestamp'
"""
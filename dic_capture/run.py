"""This module contains the run function, which contains the main program loop. It is called by the GUI when the user
clicks the "Run" button. The GUI is used to create a config file, which is then passed to the run function."""

# ======================================================================================================================
# Imports

import logging
import os
import threading
import tkinter.messagebox
from threading import Thread
from time import sleep, time
from typing import Dict, Any, List

import cv2
import neoapi
import numpy as np
import serial
import tifffile as tf

# ======================================================================================================================
# Classes

# ======================================================================================================================
# Main Program Loop
logging_level = logging.INFO


def timer_func(func):
    """
    This wrapper shows the execution time of the function/method passed.
    To use:
    Either pass a function or object method, and it's argument into the
    timer, or decorate a function with @timer_func() for it to run on
    all occurrences.
    https://www.geeksforgeeks.org/timing-functions-with-decorators-python/
    """

    def wrap_func(*args, **kwargs):
        # Function imports:
        # from time import time
        t0 = time()
        result = func(*args, **kwargs)
        t1 = time()
        print(f'Function {func.__name__!r} executed in {(t1 - t0):.4f}s')
        return result

    return wrap_func


def run(config: Dict[str, Any]):


    """Run the DIC Capture software with the given config file path and record mode.
    
    Example config file:
    {
        "Record Mode": false,
        "I/O": {
            "Config File": [
                "default_config.json"
            ],
            "Test ID": "Test_ID_20240112_154944",
            "Output Folder":
        },
        "Arduino": {
            "Choose COM Port:": [
                "COM1",
                "COM2"
            ],
            "Baud Rate": 115200,
            "Max Buffer": 3
        },
        "Camera 1": {
            "Camera Source": "P1-6",
            "Exposure Time (ms)": 1.6,
            "FPS Stages (e.g. \"0, 0.1, 0, 0.1\")": "0, 0.1"
        },
        "Camera 2": {
            "Camera Source": "P1-5",
            "Exposure Time (ms)": 1.6,
            "FPS Stages (e.g. \"0, 0.1, 0, 0.1\")": "0, 0.1"
        },
        "Camera 3": {
            "Camera Source": [
                "Camera auto-detect not yet implemented."
            ],
            "Exposure Time (ms)": "",
            "FPS Stages (e.g. \"0, 0.1, 0, 0.1\")": ""
        }
    }
    """
    # Extract the IO settings from config
    working_folder: str = config["I/O"]["Working Folder"]
    config_file: str = config["I/O"]["Config File"]
    test_id: str = config["I/O"]["Test ID"]

    # Extract the Arduino settings from config
    arduino_com_port: int = config["Arduino"]["Choose COM Port:"]
    arduino_baud_rate: int = config["Arduino"]["Baud Rate"]
    arduino_max_buffer: int = config["Arduino"]["Image Buffer"]
    trigger_period_stages_ms: str = config["Arduino"]["Trigger speed per stage (ms)"]
    

    # Extract the Camera 1 settings from config
    cam1_src: str = config["Camera 1"]["Camera Source"][:4]
    cam1_exposure_time_ms = config["Camera 1"]["Exposure Time (ms)"]

    # Extract the Camera 2 settings from config
    cam2_src: str = config["Camera 2"]["Camera Source"][:4]
    cam2_exposure_time_ms = config["Camera 2"]["Exposure Time (ms)"]


    # Extract the Camera 3 settings from config
    cam3_source: str = config["Camera 3"]["Camera Source"][:4]
    cam3_exposure_time_ms: float = config["Camera 3"]["Exposure Time (ms)"]

    # Output directories
    test_id_dir = os.path.join(working_folder, test_id)
    raw_data_save_dir = os.path.join(working_folder, test_id, 'Raw_Data')
    cam_1_save_dir = os.path.join(working_folder, test_id, 'Camera_1')
    cam_2_save_dir = os.path.join(working_folder, test_id, 'Camera_2')
    cam_3_save_dir = os.path.join(working_folder, test_id, 'Camera_3')
    synced_data_save_dir = os.path.join(working_folder, test_id, 'Synced_Data')
    dic_results_save_dir = os.path.join(working_folder, test_id, 'DIC_Results')
    log_save_dir = os.path.join(working_folder, test_id, 'Logs')

    # Create the output folder and sub-folders if record mode is true
    record_mode: bool = config["Record Mode"]
    if record_mode:
        # Try to create a folder for the test ID, stop running if folder already exists
        if os.path.exists(test_id_dir):
            tkinter.messagebox.showerror("Error", f"Folder for test ID {test_id} already exists. Please choose a "
                                                  f"different test ID.")
            return 1
        else:
            os.makedirs(test_id_dir)
        # Create the sub-folders
        output_subfolders = [raw_data_save_dir, cam_1_save_dir, cam_2_save_dir, cam_3_save_dir, synced_data_save_dir,
                             dic_results_save_dir, log_save_dir]
        for folder in output_subfolders:
            os.makedirs(folder)
    else:  # If record mode is false, don't create any folders
        pass

        # Set up logging
    if record_mode:
        logging.basicConfig(filename=os.path.join(log_save_dir, f'{test_id} dic-capture run log.log'), filemode='w',
                            format='%(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
    else:
        logging.basicConfig(level=logging.CRITICAL)

    logging.info('Starting DIC Capture run function.')

    # Create a serial connection to the Arduino
    try:
        ser = serial.Serial(arduino_com_port, arduino_baud_rate, timeout=2)
    except serial.SerialException as e:
        logging.error(f'Error creating serial connection to Arduino: {e}')
        tkinter.messagebox.showerror("Error", "Error creating serial connection to Arduino.")
        # return 1
    finally:
        pass

    # OLD VARIABLE NAMES HERE
    #exposure_time_ms = cam1_exposure_time_ms
    max_buffer_arr = arduino_max_buffer

    def get_period_stages():
        return trigger_period_stages_ms

    def hardware_trigger():
        trigger_period_stages_ms_1 = get_period_stages()
        # NOTE: have to wait for everything to initialize, maybe wait before calling the hardware trigger function?
        print('Waiting for serial connection to initialize.')
        logging.info('Waiting for serial connection to initialize.')
        #sleep(1)

        while True:
            try:  # reads serial output from audrino
                ser.write(trigger_period_stages_ms.encode())
                qValue = ser.readline().strip().decode('ascii')
                print('serial output: ', qValue)

                if qValue == "RECIEVED":
                    print("Should break here")
                    break
            except Exception as e:
                logging.error(f'Error reading serial output from Arduino: {e}')
                print('serial output error')
                break

        while record_mode:
            try:
                while ser.inWaiting() == 0:
                    pass
                qValue = ser.read(ser.in_waiting)

                with open(raw_data_save_dir + "/Arduino_Serial_Output_" + test_id + '.txt', 'a') as f:
                    f.write(qValue.decode('ascii'))

            except Exception as e:
                logging.error(f'Error reading serial output from Arduino in second block: {e}')
                print('serial output error in second block')
                break

        while record_mode == False:
            try:
                while ser.inWaiting() == 0:
                    pass
                qValue = ser.read(ser.in_waiting)
                #print(qValue)

            except Exception as e:
                logging.error(f'Error reading serial output from Arduino in second block: {e}')
                print('serial output error in second block')
                break



    class vStream():
        def __init__(self, src, windowName, timeOut_ms, buffer_arr_max, xPos, yPos, xPosHist, yPosHist, cam_save_dir, exposure_time_ms):
            self.buffer_arr_max = int(buffer_arr_max)
            self.timeOut_ms = timeOut_ms
            self.windowName = windowName
            self.zoomWindowName = windowName + ' Zoomed'
            self.xPos = xPos
            self.yPos = yPos
            self.src = src
            self.camera = neoapi.Cam()
            self.camera.Connect(self.src)
            self.xPosHist = xPosHist
            self.yPosHist = yPosHist
            self.cam_save_dir = cam_save_dir
            self.float_exposure_time = float(exposure_time_ms) * 1000


            self.camera.SetImageBufferCount(20)
            self.camera.SetImageBufferCycleCount(10)

            self.camera.f.PixelFormat.SetString('Mono12')

            self.camera.f.ExposureTime.Set(self.float_exposure_time)
            self.camera.f.Gain.Set(1)

            self.camera.f.TriggerMode = neoapi.TriggerMode_On
            self.camera.f.TriggerSource = neoapi.TriggerSource_Line2
            self.camera.f.TriggerActivation = neoapi.TriggerActivation_FallingEdge

            # self.camera.f.TriggerActivation neoapi.AcquisitionStatusSelector_AcquisitionTriggerWait
            # self.cam_event = neoapi.NeoEvent()
            # self.camera.ClearEvents()
            # self.camera.EnableEvent("ExposureStart")

            # self.camera.EnableChunk('Image')  # enable the Image chunk to receive the data of the image
            # self.camera.EnableChunk('ExposureTime')
            # self.camera.EnableEvent("ExposureStart")
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
            logging.info('Click event detected.')

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

            logging.info('Starting camera thread.')

            self.thread.start()
            self.thread_array_read.start()
            self.thread_save_array.start()


        def update(self):
            self.temp = []
            for self.k in range(0, self.buffer_arr_max):
                self.img_arr_A.append(self.temp)
                self.img_arr_B.append(self.temp)
            while True:

                for self.i in range(0, self.buffer_arr_max):
                    try:
                        self.img = self.camera.GetImage(self.timeOut_ms)
                        self.img_arr_A[self.i] = self.img
                    except:
                        pass
                        print('Image grab problem print problem')
                self.arr_A_full = True
                self.arr_B_full = False

                for self.i in range(0, self.buffer_arr_max):
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
                with open(raw_data_save_dir + '/' + test_id + '_CAM_' + self.windowName + '.txt', 'a') as f:
                    self.heading_cam = 'Frame' + '\t' + 'Frame_Name' + '\t' + 'Cam_Time' + '\n'
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
                            for self.k in range(0, self.buffer_arr_max):  # saves an image as .tif and adds image details to .csv file
                                self.img_title = str(test_id) + '_' + str(self.img_arr[self.k].GetImageID()) + '_' + self.windowName + '.tif'
                                self.fileName = self.cam_save_dir + '/' + self.img_title
                                self.save_img = self.img_arr[self.k].GetNPArray()
                                self.img_ID = self.img_arr[self.k].GetImageID()
                                self.img_TimeStamp = self.img_arr[self.k].GetTimestamp()
                                if self.img_TimeStamp != 0:
                                    if (self.img_ID == 0):
                                        self.cam_t0 = self.img_TimeStamp
                                    self.img_TimeStamp_zerod = round((self.img_TimeStamp - self.cam_t0) / 1000000)
                                    self.data = str(self.img_ID) + '\t' + str(self.img_title) + '\t' + str(
                                        self.img_TimeStamp_zerod) + '\n'
                                    tf.imwrite(self.fileName, self.save_img, photometric='minisblack')
                                    with open(raw_data_save_dir + '/' + test_id + '_CAM_' + self.windowName + '.txt',
                                              'a') as f:
                                        f.write(self.data)
                                    print('saved', self.data)


                except:
                    logging.error('Error saving array.')
                    print('save array error')


        def displayFrame(self):

            try:
                if self.displayWait == False:
                    self.t0 = time()
                    self.img_8 = (self.frame / 256).astype('uint8')
                    self.t1 = time()
                    print('Display frame: ', (self.t1 - self.t0) * 1000)

                    self.img_heat_8 = cv2.applyColorMap(self.img_8, cv2.COLORMAP_TURBO)
                    #self.img_heat_8 = self.img_8#cv2.applyColorMap(self.img_8, cv2.COLORMAP_TURBO)

                    # self.img_rotated = cv2.rotate(self.img_heat_8, cv2.ROTATE_90_COUNTERCLOCKWISE)

                    self.img_rotated = self.img_heat_8



                    self.width = int(self.img_rotated.shape[1] * self.scale)
                    self.height = int(self.img_rotated.shape[0] * self.scale)
                    self.dim = (self.width, self.height)

                    self.img_resized_8 = cv2.resize(self.img_rotated, self.dim, interpolation=cv2.INTER_AREA)



                    cv2.line(self.img_resized_8, (0, round(self.height / 2)), (self.width, round(self.height / 2)), (0, 255, 0), 1)
                    cv2.line(self.img_resized_8, (round(self.width / 2), 0), (round(self.width / 2), self.height), (0, 255, 0), 1)

                    if not self.displayWait:
                        if self.clicked > 0:
                            # self.img_grey_rotated = cv2.rotate(self.img_8, cv2.ROTATE_90_COUNTERCLOCKWISE)
                            self.img_grey_rotated = self.img_8
                            cv2.rectangle(self.img_resized_8, (self.x_0, self.y_0), (self.x_1, self.y_1), (0, 0, 255), 2)
                            self.zoomed_img = self.img_rotated[self.y_0_scaled: self.y_1_scaled, self.x_0_scaled: self.x_1_scaled]
                            self.zoomed_gray = self.img_grey_rotated[self.y_0_scaled: self.y_1_scaled, self.x_0_scaled: self.x_1_scaled]
                            cv2.imshow(self.zoomWindowName, self.zoomed_img)
                            self.showHistogram()

                    cv2.namedWindow(self.windowName)
                    cv2.moveWindow(self.windowName, self.xPos, self.yPos)
                    cv2.imshow(self.windowName, self.img_resized_8)

                    self.displayWait = True

            except:
                pass


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

    class VideoShow:  # still have to work out if I still nead the video show class
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
            # self.windowName = windowName
            while not self.stopped:
                try:
                    VideoShow.getScaledFrame_8(self)
                    cv2.imshow(self.windowName, self.img_resized_8)
                    if cv2.waitKey(1) == ord("q"):
                        self.stopped = True
                except:
                    pass
                    print('Video Show Exception')

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

    def getScaledFrame_8(img_8, scale_percent):
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
    logging.info('Starting hardware trigger thread.')
    threading.Thread(target=hardware_trigger, args=(), daemon=True).start()
    # (self,src,windowName, timeOut_ms)
    try:
        logging.info('Creating camera objects.')
        cam1 = vStream(cam1_src, '1', 4000, max_buffer_arr, -16, 0, 1655, 450, cam_1_save_dir, cam1_exposure_time_ms)
        cam2 = vStream(cam2_src, '2', 4000, max_buffer_arr, 823, 0, 1655, 740, cam_2_save_dir, cam2_exposure_time_ms)
        # cam3 = vStream(cam3_source, '3', 4000, max_buffer_arr, 823, 0, 1655, 740, cam_3_save_dir)
        logging.info('Starting camera threads.')
        cam1.start_vStream()
        cam2.start_vStream()

        print('Waiting for cameras to initialize.')
        logging.info('Waiting for cameras to initialize.')
        #sleep(2)

    except Exception as e:
        logging.error(f'Error creating camera objects: {e}')
        tkinter.messagebox.showerror("Error", f"Error creating camera objects: {e}.")
        # return 1

    error_count = 0
    while True:
        try:
            #logging.info('Displaying frames.')
            cam1.displayFrame()
            cam2.displayFrame()

            cv2.setMouseCallback(cam1.windowName, cam1.click_event)
            cv2.setMouseCallback(cam2.windowName, cam2.click_event)

        except Exception as e:
            pass

        if cv2.waitKey(10) == "TEMPORTY BLOCK":  # ord('q'):
            logging.info('Exiting program.')

            # cam1.capture.release()
            #cam1.save_buffer_remainder()
            cv2.destroyAllWindows()
            exit(1)
            break
        # if cv2.waitKey(10) == ord('q'):
        #   exposure_time_ms = exposure_time_ms + 10
    return 0

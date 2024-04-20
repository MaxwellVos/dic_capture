"""This module contains the run function, which contains the main program loop. It is called by the GUI when the user
clicks the "Run" button. The GUI is used to create a config file, which is then passed to the run function."""

# ======================================================================================================================
# Imports

import logging
import os
import sys
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
    #cam3_source: str = config["Camera 3"]["Camera Source"][:4]
    #cam3_exposure_time_ms: float = config["Camera 3"]["Exposure Time (ms)"]

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
    display_skip = arduino_max_buffer

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
                print(qValue)

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
                #logging.error(f'Error reading serial output from Arduino in second block: {e}')
                print('serial output error in second block')
                break
        qValue_decode_sum = ''
        event = threading.Event()
        while record_mode == False:
            try:
                while ser.inWaiting() == 0:
                    pass
                qValue = ser.read(ser.in_waiting)
                #print(qValue.decode('ascii'))
                qValue = ser.readline().strip().decode('ascii')
                serial_list = qValue.split(',')
                adc_1 = serial_list[5]
                adc_2 = serial_list[6]
                adc_3 = serial_list[7]
                adc_4 = serial_list[8]
                print_string = adc_1+'\t'+'\t'+adc_2+'\t'+'\t'+adc_3+'\t'+'\t'+adc_4
                print(print_string)
                #displays the adc values every 1 second
                event.wait(1)

            except Exception as e:
                #logging.error(f'Error reading serial output from Arduino in second block: {e}')
                #print('serial output error in second block')
                event.wait(0.001)




    class vStream():
        def __init__(self, src, windowName, timeOut_ms, max_image_count, xPos, yPos, xPosHist, yPosHist, cam_save_dir, exposure_time_ms, display_skip, cycle_count):
            # Variable declaration
            self.timeOut_ms = timeOut_ms
            self.windowName = windowName
            self.zoomWindowName = windowName + ' Zoomed'
            self.xPos = xPos
            self.yPos = yPos
            self.src = src
            self.xPosHist = xPosHist
            self.yPosHist = yPosHist
            self.k_super = 0
            self.n = 0
            self.super_img_arr = []
            self.img_arr = []
            self.super_img_arr_len = 300    # Limited by computer RAM (this is about 3GB RAM per camera maximum)
            self.count_images_captured = 0
            self.count_images_saved = 0
            self.cam_save_dir = cam_save_dir
            self.float_exposure_time = float(exposure_time_ms) * 1000
            self.display_skip = display_skip
            self.count_img = 0
            self.displayWait = False
            self.clicked = 0
            self.scale = 0.5
            self.save_last_array = False
            self.cam_t0 = 0
            self.save_array()
            self.show_ready = False
            self.cycle_count = cycle_count

            # Camera setup
            self.camera = neoapi.Cam()
            self.camera.SetImageBufferCount(int(max_image_count))
            self.camera.SetImageBufferCycleCount(cyclecount=self.cycle_count)
            self.camera.Connect(self.src)
            self.t0 = time()
            self.camera.f.PixelFormat.SetString('Mono12')
            self.camera.f.ExposureTime.Set(self.float_exposure_time)
            self.camera.f.Gain.Set(1)
            self.camera.f.TriggerMode = neoapi.TriggerMode_On
            self.camera.f.TriggerSource = neoapi.TriggerSource_Line2
            self.camera.f.TriggerActivation = neoapi.TriggerActivation_FallingEdge
            # use falling edge for thermal camera as well
            self.t1 = time()
            print('Camera',self.windowName,'initialized in', (self.t1 - self.t0), 'seconds.')


            self.thread_update = Thread(target=self.update, args=())
            self.thread_update.daemon = True


        def inc_exposure_ms(self,inc_ms):
            self.inc_ms = inc_ms
            self.float_exposure_time = self.float_exposure_time + inc_ms*1000
            self.camera.f.ExposureTime.Set(self.float_exposure_time)
            print("Cam"+self.windowName+' changed exposure time to: ', str(self.float_exposure_time/1000)+'ms')

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
                print('clicked:',self.clicked)

        def start_vStream(self):
            logging.info('Starting camera thread.')
            self.thread_update.start()

        def update(self):

            for self.j in range(0, self.super_img_arr_len):
                self.super_img_arr.append([])

            #self.k_super = 0
            while True:
                try:
                    self.img = self.camera.GetImage(self.timeOut_ms)
                    #print(self.img)
                    self.super_img_arr[self.k_super] = self.img
                    self.count_images_captured = self.count_images_captured + 1

                    self.k_super = self.k_super + 1
                    if self.k_super == self.super_img_arr_len:
                        self.k_super = 0
                    #print(self.k_super)
                except:
                    pass
                    print('Image grab problem print problem')


        def save_array(self):
            if (record_mode == True):
                with open(raw_data_save_dir + '/' + test_id + '_CAM_' + self.windowName + '.txt', 'a') as f:
                    self.heading_cam = 'Frame' + '\t' + 'Frame_Name' + '\t' + 'Cam_Time' + '\n'
                    f.write(self.heading_cam)


        def continuous_save(self):
            try:
                # print('While true', self.k_super)
                if self.count_images_saved < self.count_images_captured:
                    self.save_arr = self.super_img_arr[self.n]
                    self.img_title = str(test_id) + '_' + str(self.save_arr.GetImageID()) + '_' + self.windowName + '.tif'
                    self.fileName = self.cam_save_dir + '/' + self.img_title
                    self.save_img = self.save_arr.GetNPArray()
                    self.img_ID = self.save_arr.GetImageID()
                    self.img_TimeStamp = self.save_arr.GetTimestamp()
                    if self.img_TimeStamp != 0:

                        if (self.img_ID == 0):
                            self.cam_t0 = self.img_TimeStamp
                        self.img_TimeStamp_zerod = round((self.img_TimeStamp - self.cam_t0) / 1000000)
                        self.data = str(self.img_ID) + '\t' + str(self.img_title) + '\t' + str(
                            self.img_TimeStamp_zerod) + '\n'
                        self.print_data = str(self.img_ID) + '\t' + str(self.img_title) + '\t' + str(
                            self.img_TimeStamp_zerod)

                        if record_mode:
                            # tf.imwrite(self.fileName, self.save_img, photometric='minisblack')
                            self.save_tif(self.fileName, self.save_img)
                            with open(raw_data_save_dir + '/' + test_id + '_CAM_' + self.windowName + '.txt',
                                      'a') as f:
                                f.write(self.data)
                            print('Saved:', self.print_data)
                            self.mod_check = int(self.count_images_saved) % int(self.display_skip)
                            if self.mod_check == 0:
                                self.displayFrame(self.save_img)
                        else:
                            self.displayFrame(self.save_img)

                        self.count_images_saved = self.count_images_saved + 1
                        if record_mode:
                            print(str(self.count_images_captured - self.count_images_saved))
                        self.super_img_arr[self.n] = []
                        self.n = self.n + 1
                        if self.n == self.super_img_arr_len:
                            self.n = 0

            except:
                print("Save Problem")
                pass
        def save_tif(self, file_name, tif_data):
            tf.imwrite(file_name, tif_data, photometric='minisblack')

        def displayFrame(self, display_image):
            try:
                self.frame = display_image
                self.heighTest = self.frame.shape[1]
                self.widthTest = self.frame.shape[0]
                self.img_resized = self.frame[0:self.widthTest:2,0:self.heighTest:2] #uint16
                self.img_resized_8 = (self.img_resized / 256).astype(np.uint8)
                self.img_heat_8 = cv2.applyColorMap(self.img_resized_8, cv2.COLORMAP_TURBO)
                # self.img_heat_8 = cv2.rotate(self.img_heat_8, cv2.ROTATE_90_COUNTERCLOCKWISE #use to rotate image if needed
                self.img_rotated = self.img_heat_8
                self.img_display = self.img_heat_8
                self.width = int(self.img_rotated.shape[1])
                self.height = int(self.img_rotated.shape[0])
                if self.clicked > 0:
                    self.zoomed_16 = self.frame[self.y_0_scaled: self.y_1_scaled, self.x_0_scaled: self.x_1_scaled]
                    self.zoomed_8 = (self.zoomed_16 / 256).astype(np.uint8)
                    self.zoomed_heat = cv2.applyColorMap(self.zoomed_8, cv2.COLORMAP_TURBO)
                self.show_ready = True
            except:
                print('Display problem')

        def showWindow(self):
            if self.show_ready:
                if self.clicked > 0:
                    # histogram display
                    try:
                        self.showHistogram(self.zoomed_8)
                    except Exception as e:
                        print(e)
                    # zoomed window display
                    try:
                        cv2.namedWindow(self.zoomWindowName)
                        cv2.imshow(self.zoomWindowName, self.zoomed_heat)
                    except Exception as e:
                        print(e)
                    # main window with red rectangle
                    cv2.rectangle(self.img_display, (self.x_0, self.y_0), (self.x_1, self.y_1), (0, 0, 255), 2)
                    cv2.namedWindow(self.windowName)
                    cv2.imshow(self.windowName, self.img_display)
                else:
                    cv2.namedWindow(self.windowName)
                    cv2.imshow(self.windowName, self.img_display)
                self.show_ready = False

        def showHistogram(self, zoomed_img):
            self.zoomed_hist = zoomed_img
            self.histr = cv2.calcHist([self.zoomed_hist], [0], None, [255], [0, 255])
            self.histr[254] = self.histr[254] * 10000
            if self.histr[254] > 0:
                self.histr[254] = int(((max(self.histr) / 10)))
            self.hist_height = 255
            self.hist_width = 260
            self.img_hist = np.zeros((self.hist_height + 1, self.hist_width), dtype=np.uint8)
            for self.k in range(0, 255):
                self.temp_hist = int((self.histr[self.k] / (max(self.histr)+0.001)) * self.hist_height)
                self.img_hist[0:self.temp_hist, self.k] = self.k  # black
            self.img_hist[0:self.temp_hist, 255:self.hist_width] = self.k
            self.img_hist = cv2.flip(self.img_hist, 0)
            self.img_hist = (self.img_hist).astype('uint8')
            self.img_hist = cv2.applyColorMap(self.img_hist, cv2.COLORMAP_TURBO)
            self.hist_window_name = str(self.windowName + ' Histogram')
            cv2.namedWindow(self.hist_window_name)
            cv2.imshow(self.hist_window_name, self.img_hist)
        def getTimestamp(self):
            return self.timestamp_arr[1]


    logging.info('Starting hardware trigger thread.')
    threading.Thread(target=hardware_trigger, args=(), daemon=True).start()
    exposure_inc = 1
    camera_timeout = 9999999   # ms (Had problems with cameras timing out while waiting for test to start if this was
    # set to a recommended values of 4000ms)

    if record_mode:
        max_image_count = 1000
        cycle_count = 20
    else:
        max_image_count = 2
        cycle_count = 1
        display_skip = 1

    try:
        logging.info('Creating camera objects.')
        print('Initializing Cameras:')

        cam1 = vStream(src=cam1_src,
                       windowName='1',
                       timeOut_ms=camera_timeout,
                       max_image_count=max_image_count,
                       xPos=-16,
                       yPos=0,
                       xPosHist=1655,
                       yPosHist=450,
                       cam_save_dir=cam_1_save_dir,
                       exposure_time_ms=cam1_exposure_time_ms,
                       display_skip=display_skip,
                       cycle_count=cycle_count)
        cam2 = vStream(src=cam2_src,
                       windowName='2',
                       timeOut_ms=camera_timeout,
                       max_image_count=max_image_count,
                       xPos=823,
                       yPos=0,
                       xPosHist=1655,
                       yPosHist=740,
                       cam_save_dir=cam_2_save_dir,
                       exposure_time_ms=cam2_exposure_time_ms,
                       display_skip=display_skip,
                       cycle_count=cycle_count)
        cam1.start_vStream()
        cam2.start_vStream()

        print('READY TO START TEST.')


    except Exception as e:
        logging.error(f'Error creating camera objects: {e}')
        tkinter.messagebox.showerror("Error", f"Error creating camera objects: {e}.")
        # return 1

    error_count = 0
    while True:
        try:
            #logging.info('Displaying frames.')

            if record_mode:

                cam1.continuous_save()
                cam2.continuous_save()
                cam1.showWindow()
                cam2.showWindow()
                #sleep(0.05)

                key = cv2.waitKeyEx(2)

            else:
                cam1.showWindow()
                cam2.showWindow()
                cam1.continuous_save()
                cam2.continuous_save()
                cv2.setMouseCallback(cam1.windowName, cam1.click_event)
                cv2.setMouseCallback(cam2.windowName, cam2.click_event)
                key = cv2.waitKeyEx(2)

                if key == 2555904: #RIGHT arrow key for cam 1
                    cam1.inc_exposure_ms(exposure_inc)
                elif key == 2424832: #LEFT arrow key for cam 1
                    cam1.inc_exposure_ms(-exposure_inc)
                elif key == 2490368: #UP arrow key for cam 2
                    cam2.inc_exposure_ms(exposure_inc)
                elif key == 2621440: #DOWN arrow key for cam 2
                    cam2.inc_exposure_ms(-exposure_inc)

        except Exception as e:
            pass

        if cv2.waitKey(1) == "TEMPORTY BLOCK":  # ord('q'): #work out a safe command for stopping the program
            logging.info('Exiting program.')
            print()
            cv2.destroyAllWindows()
            exit(1)
            break
        # if cv2.waitKey(10) == ord('q'):
        #   exposure_time_ms = exposure_time_ms + 10
    return 0

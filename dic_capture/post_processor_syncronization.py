#Author: Maxwell Vos
#Date 01/2023
#Syncs the Gleeble data with images from the DIC system
import pandas as pd
import os
import easygui
import numpy as np
import shutil

def find_neighbours(value, df, colname):
    exactmatch = df[df[colname] == value]
    if not exactmatch.empty:
        return exactmatch.index, exactmatch.index
    else:
        try:
            lowerneighbour_ind = df[df[colname] < value][colname].idxmax()
            upperneighbour_ind = df[df[colname] > value][colname].idxmin()
            return [lowerneighbour_ind, upperneighbour_ind]
        except:
            print('Neighbour Problem')

#This code is based on the assumption that there is not a period in the middle of a test where image aquisition stops. Some form of burst imaging may be more apropriate for such a task
cam_1_path = 'EMPTY'
cam_2_path = 'EMPTY'
cam_3_path = 'EMPTY'
gleeble_path = 'EMPTY'

test_folder_dir  = easygui.diropenbox(default='C:/Users/maxwe/OneDrive/Documents/Masters/Test_Data/Sync Data V3/Nkopo_2024_026',
                                      title='The test_data folder for the test. It should be the same as the TEST ID')
raw_data_dir = os.path.join(test_folder_dir, "Raw_Data")
synced_data_dir = os.path.join(test_folder_dir, "Synced_Data")
files_in_dir = os.listdir(raw_data_dir)


test_ID = os.path.basename(os.path.normpath(test_folder_dir))
print('Test ID: ',test_ID)

gleeble_drop_dir = 'C:/Users/maxwe/OneDrive - University of Cape Town/GleebleDropFromControl/'

for k in range(0,len(files_in_dir)):
    if ('.d0' in files_in_dir[k]):  #will have to adjust this if there are more than 10 .dxx files from the gleeble. It should only be one or two as each new gleeble test should have a unique GSL code and save location
        gleeble_path = os.path.join(raw_data_dir, files_in_dir[k])
    if ('CAM_1' in files_in_dir[k]):
        cam_1_path = os.path.join(raw_data_dir, files_in_dir[k])
    if ('CAM_2' in files_in_dir[k]):
        cam_2_path = os.path.join(raw_data_dir, files_in_dir[k])
    if ('CAM_3' in files_in_dir[k]):
        cam_3_path = os.path.join(raw_data_dir, files_in_dir[k])
    if ('Serial' in files_in_dir[k]):
        arduino_path = os.path.join(raw_data_dir, files_in_dir[k])

title = 'Select the gleeble output file. (.d0) for test ID: ' + test_ID
if (gleeble_path == 'EMPTY'):
    gleeble_path = easygui.fileopenbox(default=gleeble_drop_dir,
                                       title=title)
    dest_path = raw_data_dir
    shutil.copy2(gleeble_path, dest_path)
    print(gleeble_path)

gleeble_df = pd.read_csv(gleeble_path, sep='\t', lineterminator='\n')
arduino_df = pd.read_csv(arduino_path, sep=',', lineterminator='\n')


gleeble_units_df = gleeble_df.iloc[0]


#arduino_df['Time'] = arduino_df['Time'].astype(float)
#print(gleeble_units_df)
gleeble_df = gleeble_df.drop([0])
gleeble_reordered_df = pd.DataFrame()
print(gleeble_df.iloc[:0,0].name)
gleeble_reordered_df['Time' + gleeble_units_df[gleeble_df.iloc[:0,0].name]] = gleeble_df[gleeble_df.iloc[:0,0].name].astype(float)
gleeble_reordered_df['Time(msec)'] = gleeble_reordered_df['Time' + gleeble_units_df[gleeble_df.iloc[:0,0].name]].mul(1000)
#['DIC_Trigger'] = gleeble_df['DIC.trigger'].astype(float)


for k in range(1,len(gleeble_df.axes[1])):
    parameter = gleeble_df.iloc[:0, k].name
    unit = gleeble_units_df[gleeble_df.iloc[:0,k].name]
    parameter_unit = str(parameter) + str(unit)
    gleeble_reordered_df[parameter_unit] = gleeble_df.iloc[:,k].astype(float)

col_name = 'DIC.trigger(lbloo)'
DIC_index = gleeble_reordered_df.columns.get_loc(col_name)
#print(gleeble_reordered_df.iloc[:0,17].name)
#print(gleeble_reordered_df.iat[3,DIC_index])
#print(gleeble_reordered_df.inf)
DIC_trig_prev = 0
DIC_trig_times_df = pd.DataFrame(columns = ['GleebleTrigTime'])
for k in range(1,len(gleeble_reordered_df.axes[0])):
    DIC_trig_current = gleeble_reordered_df.iat[k,DIC_index]
    # finds rising edge to the nearest msec
    if (DIC_trig_current>0) and (DIC_trig_prev == 0):
        print(gleeble_reordered_df.iat[k,1])
        DIC_trig_times_df = DIC_trig_times_df._append({'GleebleTrigTime': gleeble_reordered_df.iat[k,1]},
                                                  ignore_index=True)
    DIC_trig_prev = DIC_trig_current

DIC_trig_times_df.drop(index=DIC_trig_times_df.index[-1],axis=0,inplace=True)

print(DIC_trig_times_df)
#DIC_trig_times_df['GleebleTrigTime'] = DIC_trig_times_df['GleebleTrigTime'].sub(DIC_trig_times_df['GleebleTrigTime'].min())
#print(DIC_trig_times_df)

arduino_df.columns = ['trigger_frame_count','adc_frame_count','test_run_time','fps_change_count','fps_change_time','adc.ch1_volts','adc.ch2_volts','adc.ch3_volts','adc.ch4_volts','data_delta']
arduino_quench_times_df = arduino_df.iloc[:,4]
arduino_fps_change_times = arduino_quench_times_df.unique()
print(arduino_fps_change_times)


DIC_trig_times_df.insert(1,'ArduinoTrigTimes',arduino_fps_change_times,True)
DIC_trig_times_df['ArduinoTrigTimes'] = DIC_trig_times_df['ArduinoTrigTimes'].add(DIC_trig_times_df['GleebleTrigTime'].min())

#DIC_trig_times_df['TranslatedArd'] = gleeble_quench_times_df['ArduinoQuenchTimes'].add(gleeble_t0)
DIC_trig_times_df['Difference'] = DIC_trig_times_df['GleebleTrigTime'].sub(DIC_trig_times_df['ArduinoTrigTimes'])
print(DIC_trig_times_df)
////////////////////////////////////////////
gleeble_quench_times_df['DifferenceRatio'] = gleeble_quench_times_df['GleebleTrigTime'].div(gleeble_quench_times_df['ArduinoTrigTimes'])
gleeble_quench_times_df['GleebeArduinoDiff'] = gleeble_quench_times_df['GleebleQuenchTime'].sub(gleeble_quench_times_df['ArduinoQuenchTimes'])

average_difference_ratio = gleeble_quench_times_df["DifferenceRatio"].mean()
start_count = gleeble_quench_times_df.shape[0]

for k in range(0,start_count):
    start_time = gleeble_quench_times_df.iat[k,1]
    if (k == start_count-1):
        end_time = arduino_df.iat[-1,1]
    else:
        end_time = gleeble_quench_times_df.iat[k+1,1]
    single_ard_df = arduino_df[arduino_df['Time'].between(start_time,end_time,inclusive='left')]

    col_loc = gleeble_quench_times_df.columns.get_loc
    temp_add = gleeble_quench_times_df.iat[k,col_loc('GleebeArduinoDiff')]
    arduino_df.loc[arduino_df['Time'].between(start_time, end_time), 'AddedTime'] = arduino_df['Time'].add(temp_add)

    if (k == start_count-1):
        arduino_df.loc[arduino_df['Time'].between(start_time, end_time), 'MultTime'] = arduino_df['AddedTime'].mul(average_difference_ratio)
    else:
        temp_mult = gleeble_quench_times_df.iat[k + 1, col_loc('DifferenceRatio')]
        arduino_df.loc[arduino_df['Time'].between(start_time, end_time), 'MultTime'] = arduino_df['AddedTime'].mul(temp_mult)

frame_time_df = arduino_df[['Frame', 'MultTime']]
output_len = frame_time_df.shape[0]
col_loc = gleeble_copy_df.columns.get_loc
gleeble_copy_df['FrameTriggered'] = 0
number_of_col = gleeble_copy_df.shape[1]
column_names_list = list(gleeble_copy_df)

for k in range(0, output_len):
    frame_time = frame_time_df.iat[k,1]
    try:
        lower_ind, upper_ind = find_neighbours(frame_time,gleeble_copy_df,'Time(ms)')
    except:
        print('Neighbour problem')
    lower_time = gleeble_copy_df.iat[lower_ind,col_loc('Time(ms)')]
    upper_time = gleeble_copy_df.iat[upper_ind, col_loc('Time(ms)')]
    average_ind = (upper_ind+lower_ind)/2
    gleeble_copy_df.loc[average_ind] = np.nan

    interpolate_ratio = (frame_time-lower_time)/(upper_time-lower_time)
    gleeble_copy_df.loc[average_ind,'Time'] = frame_time

    for k in range(1,number_of_col):
        lower_val = gleeble_copy_df.iat[lower_ind,k]
        upper_val = gleeble_copy_df.iat[upper_ind, k]
        interpolated_val = lower_val + (upper_val-lower_val)*interpolate_ratio
        if (k == number_of_col-1):
            gleeble_copy_df.loc[average_ind, column_names_list[k]] = 1
        else:
            gleeble_copy_df.loc[average_ind, column_names_list[k]] = interpolated_val

    gleeble_copy_df = gleeble_copy_df.sort_index().reset_index(drop=True)

gleeble_copy_df = gleeble_copy_df.drop(['Time(ms)', 'quench4_diff'], axis=1)
gleeble_copy_df.columns = ['Time(s)', 'Quench4', 'Force(kN)', 'Jaw(mm)', 'Strain', 'Stress(MPa)', 'Stroke(mm)', 'Wedge(mm)', 'TC1', 'TC2', 'PTemp', 'FrameTriggered']
gleeble_copy_df['Time(s)'] = gleeble_copy_df['Time(s)'].div(1000)

gleeble_copy_df.columns = ['Time [s]', 'Quench4 []', 'Force[kN]', 'Jaw[mm]', 'Strain []', 'Stress [MPa]', 'Stroke [mm]', 'Wedge [mm]', 'TC1 [C]', 'TC2 [C]', 'PTemp [C]', 'FrameTriggered []']

camera_output_df = gleeble_copy_df[gleeble_copy_df['FrameTriggered []'].between(0.5,1.5)]
camera_output_df = camera_output_df.sort_index().reset_index(drop=True)
camera_output_df = camera_output_df.drop(['FrameTriggered []'], axis=1)

if (cam_1_path != 'EMPTY'):
    cam_1_df = pd.read_csv(cam_1_path, sep='\t', lineterminator='\n')
    camera_output_df['Cam1_FrameName'] = cam_1_df['Frame_Name']
if (cam_2_path != 'EMPTY'):
    cam_2_df = pd.read_csv(cam_2_path, sep='\t', lineterminator='\n')
    camera_output_df['Cam2_FrameName'] = cam_2_df['Frame_Name']
if (cam_3_path != 'EMPTY'):
    cam_3_df = pd.read_csv(cam_3_path, sep='\t', lineterminator='\n')
    camera_output_df['Cam3_FrameName'] = cam_3_df['Frame_Name']

acquision_file_df = camera_output_df

acquision_file_df.insert(0,'File',camera_output_df['Cam1_FrameName'],True)

acquision_file_df = acquision_file_df.drop(['Cam1_FrameName'], axis=1)
print(acquision_file_df.info())
acquision_file_df.rename(columns = {'Time [s]':'TimeStamp'}, inplace = True)
print(acquision_file_df.info())

#with pd.option_context('display.max_rows', None, 'display.max_columns', None):
#    print(camera_output_df)

camera_output_file_name = synced_data_dir + '\SyncedCameraData_' + test_ID + '.csv'
gleeble_output_file_name = synced_data_dir + '\SyncedGleebleData_' + test_ID + '.csv'
acquision_file_name = synced_data_dir + '\MatchID_AcquisitionFile_' + test_ID + '.csv'

camera_output_df.to_csv(camera_output_file_name)
gleeble_copy_df.to_csv(gleeble_output_file_name)
acquision_file_df.to_csv(acquision_file_name,index=False, sep=';') #matchID needs a semi-colon deliminated file with the units in [], if there are no units, still include the []. First column: 'File', second column: 'TimeStamp', rest can be anything


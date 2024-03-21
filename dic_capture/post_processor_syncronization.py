# Author: Maxwell Vos
# Date 01/2023
# Syncs the Gleeble data with images from the DIC system
import pandas as pd
import os
import easygui
import numpy as np
import shutil
import matplotlib.pyplot as plt

# first set up adc channels and set names. Polynomial conversions may be added later so this is kept basic for now.
adc1_name = 'adc1'
adc1_mul_constant = 1
adc1_offset_constant = 0

adc2_name = 'adc2'
adc2_mul_constant = 1
adc2_offset_constant = 0

adc3_name = 'adc3'
adc3_mul_constant = 1
adc3_offset_constant = 0

adc4_name = 'Force(kN)'
adc4_mul_constant = 20 # +-10V on a +-200kN loadcell
adc4_offset_constant = 0

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


# This code is based on the assumption that there is not a period in the middle of a test where image aquisition
# stops. Some form of burst imaging may be more apropriate for such a task
cam_1_path = 'EMPTY'
cam_2_path = 'EMPTY'
cam_3_path = 'EMPTY'
gleeble_path = 'EMPTY'

test_folder_dir = easygui.diropenbox(
    default='C:/Users/maxwe/OneDrive/Documents/Masters/Test_Data/Sync Data V3/Nkopo_2024_026',
    title='The test_data folder for the test. It should be the same as the TEST ID')
raw_data_dir = os.path.join(test_folder_dir, "Raw_Data")
synced_data_dir = os.path.join(test_folder_dir, "Synced_Data")
files_in_dir = os.listdir(raw_data_dir)

test_ID = os.path.basename(os.path.normpath(test_folder_dir))
print('Test ID: ', test_ID)

gleeble_drop_dir = 'C:/Users/maxwe/OneDrive - University of Cape Town/GleebleDropFromControl/'

for k in range(0, len(files_in_dir)):
    if '.d0' in files_in_dir[k]:
        # will have to adjust this if there are more than 10 .dxx files from the Gleeble. It should only be one or
        # two as each new Gleeble test should have a unique GSL code and save location
        gleeble_path = os.path.join(raw_data_dir, files_in_dir[k])
    if 'CAM_1' in files_in_dir[k]:
        cam_1_path = os.path.join(raw_data_dir, files_in_dir[k])
    if 'CAM_2' in files_in_dir[k]:
        cam_2_path = os.path.join(raw_data_dir, files_in_dir[k])
    if 'CAM_3' in files_in_dir[k]:
        cam_3_path = os.path.join(raw_data_dir, files_in_dir[k])
    if 'Serial' in files_in_dir[k]:
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

# arduino_df['Time'] = arduino_df['Time'].astype(float)
# print(gleeble_units_df)

#  drop the row of units from the gleeble doc as it messes with the data
gleeble_df = gleeble_df.drop([0])
gleeble_reordered_df = pd.DataFrame()

# concat unit to time variable
time_name = 'Time' + gleeble_units_df[gleeble_df.iloc[:0, 0].name]
gleeble_reordered_df[time_name] = gleeble_df[gleeble_df.iloc[:0, 0].name].astype(float)
# all calculations done in milliseconds in this program
gleeble_reordered_df['Time(msec)'] = gleeble_reordered_df[time_name].mul(1000)

# pull in all variable names and concat the relevant unit.
for k in range(1, len(gleeble_df.axes[1])):
    parameter = gleeble_df.iloc[:0, k].name
    unit = gleeble_units_df[gleeble_df.iloc[:0, k].name]
    parameter_unit = str(parameter) + str(unit)
    gleeble_reordered_df[parameter_unit] = gleeble_df.iloc[:, k].astype(float)

# seems backwards to have to find the DIC.trigger index like this; but I can't find a more elegant syntax.
col_name = 'DIC.trigger(lbloo)'
DIC_index = gleeble_reordered_df.columns.get_loc(col_name)

# making a df with the rising edge times of the Gleeble DIC.trigger variable
DIC_trig_times_df = pd.DataFrame(columns=['GleebleTrigTime(msec)'])
DIC_trig_prev = 0

for k in range(0, len(gleeble_reordered_df.axes[0])):
    DIC_trig_current = gleeble_reordered_df.iat[k, DIC_index]
    # finds rising edge to the nearest msec as Gleeble is always sampling at 1000Hz during a DIC.trigger event. There
    # is some form of software averaging to the DIC.trigger signal which averages the step signal over 100ms. It was
    # determined that finding the zero intersect of a line of best fit contributed insignificantly to timing accuracy
    # so the first non-zero value was used instead. This should be more robust if Gleeble removes this averaging
    # function in the future.
    if (DIC_trig_current > 0) and (DIC_trig_prev == 0):
        print(gleeble_reordered_df.iat[k, 1])
        DIC_trig_times_df = DIC_trig_times_df._append({'GleebleTrigTime(msec)': gleeble_reordered_df.iat[k, 1]},
                                                      ignore_index=True)
    DIC_trig_prev = DIC_trig_current

DIC_trig_times_df.drop(index=DIC_trig_times_df.index[-1],
                       axis=0,
                       inplace=True)

print(DIC_trig_times_df)

arduino_df.columns = ['trigger_frame_count',
                      'adc_frame_count',
                      'test_run_time',
                      'fps_change_count',
                      'fps_change_time',
                      'adc.ch1_volts',
                      'adc.ch2_volts',
                      'adc.ch3_volts',
                      'adc.ch4_volts',
                      'data_delta']

arduino_quench_times_df = arduino_df.iloc[:, 4]
# The exact time of the last trigger signal is recorded in each row. This isn't very efficient; but, we had the
# head-room, and it was the simplest solution as it kept row formats consistent which greatly simplified the serial
# communication process.
arduino_fps_change_times = arduino_quench_times_df.unique()
print(arduino_fps_change_times)

DIC_trig_times_df.insert(1,
                         'ArduinoTrigTimes(msec)',
                         arduino_fps_change_times,
                         True)

zero_offset = DIC_trig_times_df['GleebleTrigTime(msec)'].min()

DIC_trig_times_df['ArduinoTrigTimes(msec)'] = (DIC_trig_times_df['ArduinoTrigTimes(msec)']
                                               .add(zero_offset))

arduino_df['GleebleTime(msec)'] = arduino_df['test_run_time'].add(zero_offset)


DIC_trig_times_df['Difference(msec)'] = (DIC_trig_times_df['GleebleTrigTime(msec)']
                                         .sub(DIC_trig_times_df['ArduinoTrigTimes(msec)'])
                                         .round(2))

print(DIC_trig_times_df)

# Note that the timing error is far greater than the 2ppm for the esp32, so it is likely that the timing error is
# Gleeble related there does not appear to be any consistency in this error, so I believe the best option is to not
# correct the data as it is possible that the DIC.trigger signal is not perfectly synced with other signals such as
# force or jaw, thus any corrections would just throw things out further. If high accuracy temporal syncing is
# required, using the ADC values is still the best method.

# saving the timing different file as a troubleshooting tool in the future
Trigger_file_name = synced_data_dir + '\Trigger_Timing_Differences_' + test_ID + '.csv'
DIC_trig_times_df.to_csv(Trigger_file_name)

max_timing_diff = DIC_trig_times_df['Difference(msec)'].abs().max()
if max_timing_diff > 100:
    print('Largest timing difference is', max_timing_diff,
          'msec which is greater than the threshold of 100msec and the data should therefore be checked.')

arduino_df[adc1_name] = (arduino_df['adc.ch1_volts']
                         .mul(adc1_mul_constant)
                         .add(adc1_offset_constant))

arduino_df[adc2_name] = (arduino_df['adc.ch2_volts']
                         .mul(adc2_mul_constant)
                         .add(adc2_offset_constant))

arduino_df[adc3_name] = (arduino_df['adc.ch3_volts']
                         .mul(adc3_mul_constant)
                         .add(adc3_offset_constant))

arduino_df[adc4_name] = (arduino_df['adc.ch4_volts']
                         .mul(adc4_mul_constant)
                         .add(adc4_offset_constant))
print(arduino_df)

x1 = arduino_df['GleebleTime(msec)']
y1 = arduino_df[adc4_name]
plt.scatter(x1,y1)
plt.plot(x1,y1)
plt.show()

///////////////////////////////

for k in range(0, output_len):
    frame_time = frame_time_df.iat[k, 1]
    try:
        lower_ind, upper_ind = find_neighbours(frame_time, gleeble_copy_df, 'Time(ms)')
    except:
        print('Neighbour problem')
    lower_time = gleeble_copy_df.iat[lower_ind, col_loc('Time(ms)')]
    upper_time = gleeble_copy_df.iat[upper_ind, col_loc('Time(ms)')]
    average_ind = (upper_ind + lower_ind) / 2
    gleeble_copy_df.loc[average_ind] = np.nan

    interpolate_ratio = (frame_time - lower_time) / (upper_time - lower_time)
    gleeble_copy_df.loc[average_ind, 'Time'] = frame_time

    for k in range(1, number_of_col):
        lower_val = gleeble_copy_df.iat[lower_ind, k]
        upper_val = gleeble_copy_df.iat[upper_ind, k]
        interpolated_val = lower_val + (upper_val - lower_val) * interpolate_ratio
        if (k == number_of_col - 1):
            gleeble_copy_df.loc[average_ind, column_names_list[k]] = 1
        else:
            gleeble_copy_df.loc[average_ind, column_names_list[k]] = interpolated_val

    gleeble_copy_df = gleeble_copy_df.sort_index().reset_index(drop=True)

gleeble_copy_df = gleeble_copy_df.drop(['Time(ms)', 'quench4_diff'], axis=1)
gleeble_copy_df.columns = ['Time(s)', 'Quench4', 'Force(kN)', 'Jaw(mm)', 'Strain', 'Stress(MPa)', 'Stroke(mm)',
                           'Wedge(mm)', 'TC1', 'TC2', 'PTemp', 'FrameTriggered']
gleeble_copy_df['Time(s)'] = gleeble_copy_df['Time(s)'].div(1000)

gleeble_copy_df.columns = ['Time [s]', 'Quench4 []', 'Force[kN]', 'Jaw[mm]', 'Strain []', 'Stress [MPa]', 'Stroke [mm]',
                           'Wedge [mm]', 'TC1 [C]', 'TC2 [C]', 'PTemp [C]', 'FrameTriggered []']

camera_output_df = gleeble_copy_df[gleeble_copy_df['FrameTriggered []'].between(0.5, 1.5)]
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

acquision_file_df.insert(0, 'File', camera_output_df['Cam1_FrameName'], True)

acquision_file_df = acquision_file_df.drop(['Cam1_FrameName'], axis=1)
print(acquision_file_df.info())
acquision_file_df.rename(columns={'Time [s]': 'TimeStamp'}, inplace=True)
print(acquision_file_df.info())

# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
#    print(camera_output_df)

camera_output_file_name = synced_data_dir + '\SyncedCameraData_' + test_ID + '.csv'
gleeble_output_file_name = synced_data_dir + '\SyncedGleebleData_' + test_ID + '.csv'
acquision_file_name = synced_data_dir + '\MatchID_AcquisitionFile_' + test_ID + '.csv'

camera_output_df.to_csv(camera_output_file_name)
gleeble_copy_df.to_csv(gleeble_output_file_name)
acquision_file_df.to_csv(acquision_file_name, index=False,
                         sep=';')  # matchID needs a semi-colon deliminated file with the units in [], if there are no units, still include the []. First column: 'File', second column: 'TimeStamp', rest can be anything

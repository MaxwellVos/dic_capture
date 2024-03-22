# Author: Maxwell Vos
# Date 01/2023
# Syncs the Gleeble data with images from the DIC system
import pandas as pd
import os
import easygui
import numpy as np
import shutil
import matplotlib.pyplot as plt

# offset_constant is derived emperically, there seems to be a delay from starting the gleeble zeroing the sysTime and
# sampleStart. For now, it is easiest to adjust the offset constant so that the graphs line up perfectly (this offset
# constant should be between 0 and 200ms normally)
offset_constant = 113 #ms

# first set up adc channels and set names. Polynomial conversions may be added later so this is kept basic for now.
adc1_name = 'adc1 [V]'
adc1_mul_constant = 1
adc1_offset_constant = 0

adc2_name = 'adc2 [V]'
adc2_mul_constant = 1
adc2_offset_constant = 0

adc3_name = 'adc3 [V]'
adc3_mul_constant = 1
adc3_offset_constant = 0

adc4_name = 'ADC_Force [kN]'
adc4_mul_constant = 20 # +-10V on a +-200kN loadcell
adc4_offset_constant = 0

show_force_plot = True

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
time_name = 'Time [sec]' #+ gleeble_units_df[gleeble_df.iloc[:0, 0].name]
gleeble_reordered_df[time_name] = gleeble_df[gleeble_df.iloc[:0, 0].name].astype(float)
# all calculations done in milliseconds in this program
gleeble_reordered_df['Time [msec]'] = gleeble_reordered_df[time_name].mul(1000)

# pull in all variable names and concat the relevant unit with [] instead of () to be compatible with MatchID.
for k in range(1, len(gleeble_df.axes[1])):
    parameter = gleeble_df.iloc[:0, k].name
    unit = str(gleeble_units_df[gleeble_df.iloc[:0, k].name])
    if unit == 'nan':
        unit = ''
    unit = unit.replace("(", "")
    unit = unit.replace(")", "")
    unit = '['+unit+']'

    parameter_unit = str(parameter) + ' ' + str(unit)
    gleeble_reordered_df[parameter_unit] = gleeble_df.iloc[:, k].astype(float)

# seems backwards to have to find the DIC.trigger index like this; but I can't find a more elegant syntax.
col_name = 'DIC.trigger [lbloo]'
DIC_index = gleeble_reordered_df.columns.get_loc(col_name)
print(gleeble_reordered_df.info())

# making a df with the rising edge times of the Gleeble DIC.trigger variable
DIC_trig_times_df = pd.DataFrame(columns=['GleebleTrigTime [msec]'])
DIC_trig_prev = 0

for k in range(0, len(gleeble_reordered_df.axes[0])):
    DIC_trig_current = gleeble_reordered_df.iat[k, DIC_index]
    # finds rising edge to the nearest msec as Gleeble is always sampling at 1000Hz during a DIC.trigger event. There
    # is some form of software averaging to the DIC.trigger signal which averages the step signal over 100ms. It was
    # determined that finding the zero intersect of a line of best fit contributed insignificantly to timing accuracy
    # so the first non-zero value was used instead. This should be more robust if Gleeble removes this averaging
    # function in the future. There may be a workaround for people who have the DIC module by connecting the DIC.trigger
    # out to the DIC.in and recording that instead of the DIC.trigger. It should give a more responsive reading, however
    # this requires the purchase of the DIC module. For most cases the current setup should be fine and can be connected
    # to quench 3 or 4 which all gleeble customers have.
    if (DIC_trig_current > 0) and (DIC_trig_prev == 0):
        print(gleeble_reordered_df.iat[k, 1])
        DIC_trig_times_df = DIC_trig_times_df._append({'GleebleTrigTime [msec]': gleeble_reordered_df.iat[k, 1]},
                                                      ignore_index=True)
    DIC_trig_prev = DIC_trig_current

DIC_trig_times_df.drop(index=DIC_trig_times_df.index[-1],
                       axis=0,
                       inplace=True)

print(DIC_trig_times_df)

arduino_df.columns = ['trigger_frame_count []',
                      'adc_frame_count []',
                      'test_run_time [msec]',
                      'fps_change_count []',
                      'fps_change_time [msec]',
                      'adc.ch1_volts [V]',
                      'adc.ch2_volts [V]',
                      'adc.ch3_volts [V]',
                      'adc.ch4_volts [V]',
                      'data_delta []']

arduino_quench_times_df = arduino_df.iloc[:, 4]
# The exact time of the last trigger signal is recorded in each row. This isn't very efficient; but, we had the
# head-room, and it was the simplest solution as it kept row formats consistent which greatly simplified the serial
# communication process.
arduino_fps_change_times = arduino_quench_times_df.unique()
print(arduino_fps_change_times)

DIC_trig_times_df.insert(1,
                         'ArduinoTrigTimes [msec]',
                         arduino_fps_change_times,
                         True)

zero_offset = DIC_trig_times_df['GleebleTrigTime [msec]'].min() + offset_constant

DIC_trig_times_df['ArduinoTrigTimes [msec]'] = (DIC_trig_times_df['ArduinoTrigTimes [msec]']
                                               .add(zero_offset))

arduino_df['GleebleTime [msec]'] = arduino_df['test_run_time [msec]'].add(zero_offset)


DIC_trig_times_df['Difference [msec]'] = (DIC_trig_times_df['GleebleTrigTime [msec]']
                                         .sub(DIC_trig_times_df['ArduinoTrigTimes [msec]'])
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

max_timing_diff = DIC_trig_times_df['Difference [msec]'].abs().max()
if (max_timing_diff-offset_constant) > 100:
    print('Largest timing difference is', max_timing_diff,
          'msec which is greater than the threshold of 100msec and the data should therefore be checked.')

arduino_df[adc1_name] = (arduino_df['adc.ch1_volts [V]']
                         .mul(adc1_mul_constant)
                         .add(adc1_offset_constant))

arduino_df[adc2_name] = (arduino_df['adc.ch2_volts [V]']
                         .mul(adc2_mul_constant)
                         .add(adc2_offset_constant))

arduino_df[adc3_name] = (arduino_df['adc.ch3_volts [V]']
                         .mul(adc3_mul_constant)
                         .add(adc3_offset_constant))

arduino_df[adc4_name] = (arduino_df['adc.ch4_volts [V]']
                         .mul(adc4_mul_constant)
                         .add(adc4_offset_constant))
#print(arduino_df)
#print(arduino_df.info())

arduino_frame_count_past = -1
arduino_frame_df = pd.DataFrame()
# build a df which only holds the data assosiated with an image
for k in range(0, len(arduino_df.axes[0])):
    arduino_frame_count_current = arduino_df.iat[k, 0]

    if arduino_frame_count_current != arduino_frame_count_past:
        arduino_frame_df = arduino_frame_df._append(arduino_df.loc[k, :],
                                                      ignore_index=True)
    arduino_frame_count_past = arduino_frame_count_current

if show_force_plot:
    x1 = arduino_df['GleebleTime [msec]']
    print('----------------',x1)
    print('mmmmmmmmmmmmmmmmmmmm')
    print(arduino_df['GleebleTime [msec]'].info())
    x2 = arduino_frame_df['GleebleTime [msec]']
    x3 = gleeble_reordered_df['Time [msec]']
    y1 = arduino_df[adc4_name]
    y2 = arduino_frame_df[adc4_name]
    y3 = gleeble_reordered_df['Force [kN]']

    plt.plot(arduino_df['GleebleTime [msec]'],
             y1,
             linewidth=1)

    plt.scatter(x=x1,
                y=y1,
                color='blue',
                s=20,
                label="ADC subsampling")

    plt.scatter(x=x2,
                y=y2,
                color='red',
                s=20,
                label="DIC Frame")

    plt.scatter(x=x3,
                y=y3,
                color='black',
                s=20,
                label="Gleeble Data")

    title = "Comparison of DIC and Gleeble data for testID: " + test_ID
    plt.title(title)
    plt.xlabel('Time [msec]')
    plt.ylabel('Force [kN]')
    plt.legend(loc='lower right')
    plt.show()

# create a common column of Time(msec) so that the df concat doesnt merge rows
arduino_frame_df['Time [msec]'] = arduino_frame_df['GleebleTime [msec]']
combined_df = pd.concat([gleeble_reordered_df, arduino_frame_df], ignore_index=True, sort=False)
combined_df = combined_df.sort_values(by=['Time [msec]'], ignore_index=True, ascending=True)
number_of_col = len(gleeble_reordered_df.axes[1])
col_name = 'trigger_frame_count []'
combined_index = combined_df.columns.get_loc(col_name)
combined_number_of_rows = len(combined_df.axes[0])
matchID_df = pd.DataFrame()

# interpolate frame data into gleeble data
for k in range(0, combined_number_of_rows):
    # definitly not the fastst code but it gets the job done
    if combined_df.isnull().iloc[k, 0]:
        # find the closest previous data row
        k_previous = k - 1
        while combined_df.isnull().iloc[k_previous, 0]:
            k_previous = k_previous - 1
        # find the closest next data row
        k_next = k + 1
        while combined_df.isnull().iloc[k_next, 0]:
            k_next = k_next + 1
        # interpolate between these two rows for every column that came from the gleeble_reordered_df (we dont want
        # to interpolate the data that came from the arduino_frame_df as it'll just make the data harder to read)

        previous_time = combined_df.iloc[k_previous, 1]
        next_time = combined_df.iloc[k_next, 1]
        current_time = combined_df.iloc[k, 1]
        interpolate_ratio = (current_time - previous_time) / (next_time - previous_time)
        # time(sec) is done seperately as its linked to time(ms) and rounnding errors in the interpolate function
        # could mess with the value
        interpolated_val_time = (previous_time + (next_time - previous_time) * interpolate_ratio)/1000
        combined_df.iloc[k, 0] = interpolated_val_time

        # cycles through the columns of the gleeble_reordered_df headings and interpolates the values so that each
        # DIC frame has the assosiated Gleeble data with it.
        for j in range(2, number_of_col):
            prev_value = combined_df.iloc[k_previous, j]
            next_value = combined_df.iloc[k_next, j]
            interpolated_val = prev_value + (next_value - prev_value) * interpolate_ratio
            combined_df.iloc[k, j] = interpolated_val

        print('Frame Number:', round(combined_df.iloc[k, combined_index]))
        # builds the df used to output the MatchID .csv file
        matchID_df = matchID_df._append(combined_df.loc[k, :], ignore_index=True)

# gets the names of the images from the CAMx .txt file created in the run.py module when recording.
frame_name_from_cam_df = pd.DataFrame()
if (cam_1_path != 'EMPTY'):
    frame_name_from_cam_df = pd.read_csv(cam_1_path, sep='\t', lineterminator='\n')
    matchID_df.insert(0, 'File', frame_name_from_cam_df['Frame_Name'], True)

#
matchID_df = matchID_df.drop(['Time [msec]'], axis=1)
matchID_df = matchID_df.drop(['GleebleTime [msec]'], axis=1)
matchID_df = matchID_df.drop(['data_delta []'], axis=1)
matchID_df = matchID_df.drop(['fps_change_time [msec]'], axis=1)
matchID_df = matchID_df.drop(['adc_frame_count []'], axis=1)
combined_df = combined_df.drop(['Time [msec]'], axis=1)
combined_df = combined_df.drop(['GleebleTime [msec]'], axis=1)

matchID_df['Force [kN]'] = matchID_df['Force [kN]'].round(-3)



gleeble_output_file_name = synced_data_dir + '\SyncedGleebleData_' + test_ID + '.csv'
matchID_file_name = synced_data_dir + '\MatchID_AcquisitionFile_' + test_ID + '.csv'

combined_df.to_csv(gleeble_output_file_name)
matchID_df.to_csv(matchID_file_name, index=False, sep=';')
#still need to conver the (unit) to [unit]
# matchID needs a semi-colon deliminated file with the units in [], if there are no units, still include the [].
# First column: 'File', second column: 'TimeStamp', rest can be anything











#
#
#
#
#
#
#
#
# combined_file_name = synced_data_dir + '\combinedDF_' + test_ID + '.csv'
# combined_df.to_csv(combined_file_name)
#
# for k in range(0, len(arduino_frame_df.axes[0])):
#     frame_time = arduino_frame_df.iat[k, 10]
#     try:
#         lower_ind, upper_ind = find_neighbours(frame_time, gleeble_reordered_df, 'Time(msec)')
#     except:
#         print('Neighbour problem')
#     #print(lower_ind, 'lowIND')
#     lower_time = gleeble_reordered_df.iat[lower_ind, gleeble_index]
#     upper_time = gleeble_reordered_df.iat[upper_ind, gleeble_index]
#     average_ind = (upper_ind + lower_ind) / 2
#     gleeble_reordered_df.loc[average_ind] = np.nan
#     if (upper_time - lower_time) == 0:
#         interpolate_ratio = 1
#     else:
#         interpolate_ratio = (frame_time - lower_time) / (upper_time - lower_time)
#     gleeble_reordered_df.loc[average_ind, 'Time(msec)'] = frame_time
#
#     for j in range(0, number_of_col):
#         lower_val = gleeble_reordered_df.iat[lower_ind[0], j]
#         upper_val = gleeble_reordered_df.iat[upper_ind[0], j]
#         interpolated_val = lower_val + (upper_val - lower_val) * interpolate_ratio
#         #print(interpolated_val,'intVAL')
#         if (j == number_of_col - 1):
#             gleeble_reordered_df.loc[average_ind, 'FrameTriggered'] = 1
#         else:
#             gleeble_reordered_df.loc[average_ind, gleeble_reordered_df.iloc[:0, j].name] = interpolated_val
#             #print(gleeble_reordered_df.loc[average_ind, gleeble_reordered_df.iloc[:0, j].name])
#
#     gleeble_reordered_df = gleeble_reordered_df.sort_index().reset_index(drop=True)
#     #print(gleeble_reordered_df.info())
#     #print(gleeble_reordered_df)
#
#
# gleeble_copy_df = gleeble_copy_df.drop(['Time(ms)', 'quench4_diff'], axis=1)
# gleeble_copy_df.columns = ['Time(s)', 'Quench4', 'Force(kN)', 'Jaw(mm)', 'Strain', 'Stress(MPa)', 'Stroke(mm)',
#                            'Wedge(mm)', 'TC1', 'TC2', 'PTemp', 'FrameTriggered']
# gleeble_copy_df['Time(s)'] = gleeble_copy_df['Time(s)'].div(1000)
#
# gleeble_copy_df.columns = ['Time [s]', 'Quench4 []', 'Force[kN]', 'Jaw[mm]', 'Strain []', 'Stress [MPa]', 'Stroke [mm]',
#                            'Wedge [mm]', 'TC1 [C]', 'TC2 [C]', 'PTemp [C]', 'FrameTriggered []']
#
# camera_output_df = gleeble_copy_df[gleeble_copy_df['FrameTriggered []'].between(0.5, 1.5)]
# camera_output_df = camera_output_df.sort_index().reset_index(drop=True)
# camera_output_df = camera_output_df.drop(['FrameTriggered []'], axis=1)
#
# if (cam_1_path != 'EMPTY'):
#     cam_1_df = pd.read_csv(cam_1_path, sep='\t', lineterminator='\n')
#     camera_output_df['Cam1_FrameName'] = cam_1_df['Frame_Name']
# if (cam_2_path != 'EMPTY'):
#     cam_2_df = pd.read_csv(cam_2_path, sep='\t', lineterminator='\n')
#     camera_output_df['Cam2_FrameName'] = cam_2_df['Frame_Name']
# if (cam_3_path != 'EMPTY'):
#     cam_3_df = pd.read_csv(cam_3_path, sep='\t', lineterminator='\n')
#     camera_output_df['Cam3_FrameName'] = cam_3_df['Frame_Name']
#
# acquision_file_df = camera_output_df
#
# acquision_file_df.insert(0, 'File', camera_output_df['Cam1_FrameName'], True)
#
# acquision_file_df = acquision_file_df.drop(['Cam1_FrameName'], axis=1)
# print(acquision_file_df.info())
# acquision_file_df.rename(columns={'Time [s]': 'TimeStamp'}, inplace=True)
# print(acquision_file_df.info())
#
# # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
# #    print(camera_output_df)
#
# camera_output_file_name = synced_data_dir + '\SyncedCameraData_' + test_ID + '.csv'
# gleeble_output_file_name = synced_data_dir + '\SyncedGleebleData_' + test_ID + '.csv'
# acquision_file_name = synced_data_dir + '\MatchID_AcquisitionFile_' + test_ID + '.csv'
#
# camera_output_df.to_csv(camera_output_file_name)
# gleeble_copy_df.to_csv(gleeble_output_file_name)
# acquision_file_df.to_csv(acquision_file_name, index=False,
#                          sep=';')  # matchID needs a semi-colon deliminated file with the units in [], if there are no units, still include the []. First column: 'File', second column: 'TimeStamp', rest can be anything

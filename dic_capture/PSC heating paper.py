

import matplotlib.pyplot as plt
import numpy as np
import cv2
import pandas as pd
import os
import easygui
import numpy as np
import shutil
import tifffile as tf
import threading

def plt_show_sec(duration: float = 3):
    def _stop():
        time.sleep(duration)
        plt.close()
    if duration:
        threading.Thread(target=_stop).start()
    plt.show(block=False)
    plt.pause(duration)


material = 'EN8'
full_range_temperature = 100
offset = -30 #temperature offset to make image more readable

figure, axis = plt.subplots(2, 5)

#custom_xlim = (0, 100)
custom_ylim = (-20, 20)
plt.setp(axis, ylim=custom_ylim)


n_lines = 12
color_count = 0
cmap = plt.colormaps['viridis']
# Take colors at regular intervals spanning the colormap.
colors = cmap(np.linspace(0, 1, n_lines))
temperature_list = ['200C','350C','500C','700C','950C']


# Thermal images are resized to be the same as the DIC images to avoid scaling issues.

test_folder_dir = easygui.diropenbox(
    default='C:/Users/maxwe/OneDrive/Documents/Masters/Test_Data/PSC Heating',
    title='The test_data folder for the test. It should be the same as the TEST ID')

output_match_ID_file = os.path.join(test_folder_dir, "Camera_3_Thermal_MatchID")
front_path = os.path.join(test_folder_dir, "View_Front")
bottom_path = os.path.join(test_folder_dir, "View_Bottom")
input_file = os.path.join(test_folder_dir, "Camera_3")
data_path_default = os.path.join(test_folder_dir, "Synced_Data/")
Q4_front_path = os.path.join(test_folder_dir, "View_Q4_Front")
emisivity_correct = os.path.join(test_folder_dir, "Emissivity_Correction")
test_ID = os.path.basename(os.path.normpath(test_folder_dir))
print('Test ID: ', test_ID)
E_file_name = emisivity_correct + '\Emisivity_Correction' + test_ID + '.csv'
perspective_path = os.path.join(test_folder_dir, "Perspective_Points")

data_path = easygui.fileopenbox(
    default=data_path_default,
    title='Select the MatchID .csv file')

synced_master_df = pd.read_csv(data_path, sep=';', lineterminator='\n')

#(synced_master_df)
#print(synced_master_df.info())

try:
    os.makedirs(output_match_ID_file)
except:
    print('File already created')

try:
    os.makedirs(front_path)
except:
    print('File already created')

try:
    os.makedirs(bottom_path)
except:
    print('File already created')

try:
    os.makedirs(Q4_front_path)
except:
    print('File already created')

try:
    os.makedirs(perspective_path)
except:
    print('File already created')
    perspective_file_name = perspective_path + '\perspective_points_' + test_ID + '.csv'
    print(perspective_file_name)
    pp_df = pd.read_csv(perspective_file_name, sep=',', lineterminator='\n')
    pp_x = pp_df['x'].to_numpy()
    print(pp_x)
    pp_y = pp_df['y'].to_numpy()
    print(pp_y)
try:
    os.makedirs(emisivity_correct)
    emisivity_exists = False
    E_df = pd.DataFrame(columns=['img_ID', 'pTemp', 'TC1', 'TC2', 'camTemperature', 'Correction Factor'])
except:
    emisivity_exists = True
    E_complete_df = pd.read_csv(E_file_name, sep=',', lineterminator='\n')
    half_point = int(len(E_complete_df)/2)-1
    first_half_df = E_complete_df.loc[:half_point]
    second_half_df = E_complete_df.loc[(half_point+1):]
    x = first_half_df['TC1'].to_numpy()
    y = first_half_df['Correction Factor\r'].to_numpy()
    p1 = np.polyfit(x, y, 2)
    half_ID = np.max(first_half_df['img_ID'].to_numpy())
    print('half ID', half_ID)

    x = second_half_df['TC1'].to_numpy()
    y = second_half_df['Correction Factor\r'].to_numpy()
    p2 = np.polyfit(x, y, 2)

prev_check_ID = 0
files_in_dir = os.listdir(input_file)
img_save_count = 0
q3_count = -1
q3_current = 0
q3_past = 0
y_axis_count = 0
q3_inc = 1
step = 0
timeStamp_past = 0
timeStamp_current = 0

for filename in os.listdir(input_file):
    temp_img_df = synced_master_df.iloc[img_save_count]
    q3_current = temp_img_df['Quench3 [lbloo]']
    timeStamp_current = temp_img_df['TimeStamp']
    jaw = temp_img_df['Jaw [mm]']
    if (q3_current > 0) and (q3_past == 0):
        step = step + 1
        color_change_flag = True
        q3_count = q3_count + q3_inc
        if q3_count == 4:
            q3_inc = -1
        if step == 6:
            y_axis_count = 1
            q3_count = q3_count + 1

    q3_past = q3_current


    input_path = os.path.join(input_file, filename)
    split = os.path.splitext(filename)
    new_img_ID = test_ID + '_' + str(img_save_count) + str('_3') + split[1]
    new_img_txt_ID = test_ID + '_' + str(img_save_count) + str('_3') + '.thermal.tiff'
    output_match_ID_path = os.path.join(output_match_ID_file, new_img_txt_ID)
    output_front_image_path = os.path.join(front_path, new_img_ID)
    output_bottom_image_path = os.path.join(bottom_path, new_img_ID)
    import_image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if emisivity_exists:
        if temp_img_df['trigger_frame_count []'] > (half_ID+1):
            p = p2
            pts_bottom = np.float32([[pp_x[8], pp_y[8]], [pp_x[9], pp_y[9]],
                                     [pp_x[10], pp_y[10]], [pp_x[11], pp_y[11]]])
            print('bottom: ',pts_bottom)
            print('p2')
        else:
            p = p1
            pts_bottom = np.float32([[pp_x[4], pp_y[4]], [pp_x[5], pp_y[5]],
                                     [pp_x[6], pp_y[6]], [pp_x[7], pp_y[7]]])
            print('bottom: ',pts_bottom)
            print('p1')
        import_image = import_image

        correction_matrix = p[0]*import_image*import_image + p[1]*import_image + p[2]
        print('p0:',p[0])
        print('p1:', p[1])
        #print("average correction: ", np.average(correction_matrix))
        import_image = ((import_image + 273.15) * correction_matrix) - 273.15
        print("Max Import: ", np.max(import_image))
    else:
        pts_bottom = np.float32([[234, 216], [326, 213],
                                 [244, 392], [329, 392]])
    pts_front =  np.float32([[pp_x[0], pp_y[0]], [pp_x[1], pp_y[1]],
                            [pp_x[2], pp_y[2]], [pp_x[3], pp_y[3]]])
    print('front: ', pts_front)
    pts2 = np.float32([[0, 0], [200, 0],
                       [0, 400], [200, 400]])
    size = (200, 400)
    M = cv2.getPerspectiveTransform(pts_front, pts2)
    corrected_img = cv2.warpPerspective(import_image, M, size, flags = cv2.INTER_LINEAR)
    #print(corrected_img)
    avg_val = np.mean(corrected_img)
    max_val = np.max(corrected_img)
    min_val = np.min(corrected_img)
    print(avg_val, max_val, min_val)
    TC1_cam = corrected_img[230, 100]+ offset
    print('TC1', TC1_cam)
    upper_limit = TC1_cam + 0.5*full_range_temperature
    lower_limit = TC1_cam - 0.5*full_range_temperature
    set_range_img = (corrected_img - TC1_cam) * (256 / full_range_temperature) + 128


    set_range_img[set_range_img > 255] = 0
    set_range_img[set_range_img < 0] = 255
    corrected_img = set_range_img.astype(np.uint8)
    heat_front_img = cv2.applyColorMap(corrected_img, cv2.COLORMAP_INFERNO)

    #heat_front_img = corrected_img
    # 008 Bottom

    pts2 = np.float32([[0, 0], [200, 0],
                       [0, 600], [200, 600]])
    size = (200, 600)
    M = cv2.getPerspectiveTransform(pts_bottom, pts2)
    corrected_img = cv2.warpPerspective(import_image, M, size)
    raw_bottom_img = corrected_img
    avg_val = np.mean(corrected_img)
    max_val = np.max(corrected_img)
    min_val = np.min(corrected_img)

    #print(img_save_count,avg_val, max_val, min_val)
    TC1_cam = corrected_img[300, 100]
    graph_img_bottom = corrected_img

    set_range_img = (corrected_img - TC1_cam) * (256 / full_range_temperature) + 128
    set_range_img[set_range_img > 255] = 0
    set_range_img[set_range_img < 0] = 255
    corrected_img = set_range_img.astype(np.uint8)
    heat_bottom_img = cv2.applyColorMap(corrected_img, cv2.COLORMAP_INFERNO)

    cv2.imwrite(output_front_image_path, heat_front_img)
    cv2.imwrite(output_bottom_image_path, heat_bottom_img)

    if temp_img_df['Quench3 [lbloo]'] == 1 and (timeStamp_current-timeStamp_past) > 9.95:
        timeStamp_past = timeStamp_current
        bottom_y_3 = graph_img_bottom[:, [97, 98, 99, 100, 101]]
        bottom_y = np.average(bottom_y_3, axis=1)
        bottom_y = bottom_y - np.average(bottom_y)
        bottom_x = np.arange(0, 30, 0.05)
        #print(bottom_y)
        p_graph_bottom = np.poly1d(np.polyfit(bottom_x, bottom_y, 10))
        if color_change_flag:
            color_count = 0
            color_change_flag = False
            color = colors[n_lines-color_count-1]
            time_legend = 0
        else:
            color_count = color_count + 1
            color = colors[n_lines-color_count-1]
            time_legend = time_legend+10



        axis[y_axis_count, int(q3_count)].plot(bottom_x, p_graph_bottom(bottom_x),
                                               color=color,
                                               label = str(time_legend) + 's')
        axis[y_axis_count, int(q3_count)].set_title('TC1.setpoint = ' + temperature_list[q3_count],
                                                    fontdict={'fontsize': 9, 'fontweight': 'medium'})

        axis[y_axis_count, int(q3_count)].tick_params(axis='both', which='major', labelsize=8)
        axis[y_axis_count, int(q3_count)].tick_params(axis='y', which='major', labelrotation=90)
        axis[0, 4].legend(loc='upper right', bbox_to_anchor=(1.55, 0.3))
        #axis[0, int(q3_count)].xaxis.set_tick_params(labelbottom=True, fontdict={'fontsize': 8, 'fontweight': 'medium'})
        #axis[y_axis_count, int(q3_count)].set_xlabel('x')
        #figure.text(0.5, 0.04, 'Deviation from line average (Celcius)', ha='center')
        figure.supylabel('Deviation from line average temperature (Celcius)')
        figure.supxlabel('y-distance along center line of bottom face (mm)')
        figure.suptitle('Temperature deviation in y-direction along bottom face. Material: ' + material)
        #figure.text(0.04, 0.5, 'Y distance along center line of bottom face (mm)', va='center', rotation='vertical')
        plt.ylim(-20, 20)
        #plt.xlabel('Y distance along center line of bottom face (mm)')
        #plt.ylabel('Deviation from line average (Celcius)')
        #plt.plot(bottom_x, bottom_y, color=[r, g, b])
        plt_show_sec(0.01)#show for 3 sec

    #print(temp_img_df['Quench4 [lbloo]'])
    if (temp_img_df['Quench4 [lbloo]'] == 1) and ((img_save_count-prev_check_ID)>1):
        thermal_img_name = str(test_ID) + str('_') + str(img_save_count) + str('_')+ str(round(temp_img_df['TC1.setpoint [C]'])) + '.TIF'
        print(output_front_image_path)
        output_Q4_front_image_path = os.path.join(Q4_front_path, thermal_img_name)
        #print(output_Q4_front_image_path)
        if emisivity_exists == False:
            text = "Enter Temperature on thermal image number" + str(img_save_count+1)
            title = "Emissivity correction"
            d_text = ""
            cam_temperature = easygui.enterbox(text, title, d_text)
            pTemp = round(temp_img_df['TC1.setpoint [C]'])
            TC1 = temp_img_df['TC1 [C]']
            TC2 = temp_img_df['TC2 [C]']
            correction_factor = (TC1 + 273.15)/(float(cam_temperature)+273.15)

            temp_list = [img_save_count, pTemp, TC1, TC2, cam_temperature, correction_factor]
            E_df.loc[len(E_df)] = temp_list

        try:
            cv2.imwrite(output_Q4_front_image_path, heat_front_img)
        except:
            pass
        prev_check_ID = img_save_count


    #tf.imwrite(output_image_path, corrected_img, photometric='minisblack')
    print('Saved:', output_front_image_path)
    #print('Saved:', output_bottom_image_path)
    img_save_count = img_save_count + 1
plt.show()


E_df.to_csv(E_file_name, index=False, sep=',')


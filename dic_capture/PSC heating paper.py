

import matplotlib.pyplot as plt
import numpy as np
import cv2
import pandas as pd
import os
import easygui
import numpy as np
import shutil
import tifffile as tf

# Thermal images are resized to be the same as the DIC images to avoid scaling issues.

test_folder_dir = easygui.diropenbox(
    default='C:/Users/maxwe/OneDrive/Documents/Masters/Test_Data/PSC Heating',
    title='The test_data folder for the test. It should be the same as the TEST ID')

output_match_ID_file = os.path.join(test_folder_dir, "Camera_3_Thermal_MatchID")
front_path = os.path.join(test_folder_dir, "View_Front")
bottom_path = os.path.join(test_folder_dir, "View_Bottom")
input_file = os.path.join(test_folder_dir, "Camera_3")
data_path_default = os.path.join(test_folder_dir, "Synced_Data")
Q4_front_path = os.path.join(test_folder_dir, "View_Q4_Front")
emisivity_correct = os.path.join(test_folder_dir, "Emissivity_Correction")
test_ID = os.path.basename(os.path.normpath(test_folder_dir))
print('Test ID: ', test_ID)
E_file_name = emisivity_correct + '\Emisivity_Correction' + test_ID + '.csv'

data_path = easygui.fileopenbox(
    default=data_path_default,
    title='Select the MatchID .csv file')

synced_master_df = pd.read_csv(data_path, sep=';', lineterminator='\n')

print(synced_master_df)
print(synced_master_df.info())

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
    os.makedirs(emisivity_correct)
    emisivity_exists = False
    E_df = pd.DataFrame(columns=['img_ID', 'pTemp', 'TC1', 'TC2', 'camTemperature', 'Correction Factor'])
except:
    emisivity_exists = True
    E_complete_df = pd.read_csv(E_file_name, sep=',', lineterminator='\n')


prev_check_ID = 0



files_in_dir = os.listdir(input_file)
img_save_count = 0

for filename in os.listdir(input_file):

    input_path = os.path.join(input_file, filename)
    split = os.path.splitext(filename)
    new_img_ID = test_ID + '_' + str(img_save_count) + str('_3') + split[1]
    new_img_txt_ID = test_ID + '_' + str(img_save_count) + str('_3') + '.thermal.tiff'
    output_match_ID_path = os.path.join(output_match_ID_file, new_img_txt_ID)
    output_front_image_path = os.path.join(front_path, new_img_ID)
    output_bottom_image_path = os.path.join(bottom_path, new_img_ID)

    import_image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    #009 FRONT
    pts1 = np.float32([[234, 81], [326, 81],
                       [234, 216], [326, 213]])
    pts2 = np.float32([[0, 0], [200, 0],
                       [0, 400], [200, 400]])
    size = (200, 400)
    M = cv2.getPerspectiveTransform(pts1, pts2)
    corrected_img = cv2.warpPerspective(import_image, M, size)
    raw_front_img = corrected_img
    avg_val = np.mean(corrected_img)
    max_val = np.max(corrected_img)
    min_val = np.min(corrected_img)
    #print(avg_val, max_val, min_val)
    set_range_img = ((corrected_img - avg_val)*3.5 + 128)
    corrected_img = set_range_img.astype(np.uint8)
    heat_front_img = cv2.applyColorMap(corrected_img, cv2.COLORMAP_TURBO)
    # 008 Bottom
    pts1 = np.float32([[234, 216], [326, 213],
                       [244, 392], [329, 392]])
    pts2 = np.float32([[0, 0], [200, 0],
                       [0, 600], [200, 600]])
    size = (200, 600)
    M = cv2.getPerspectiveTransform(pts1, pts2)
    corrected_img = cv2.warpPerspective(import_image, M, size)
    raw_bottom_img = corrected_img
    avg_val = np.mean(corrected_img)
    max_val = np.max(corrected_img)
    min_val = np.min(corrected_img)
    print(img_save_count,avg_val, max_val, min_val)
    set_range_img = ((corrected_img - avg_val) * 3.5 + 128)
    corrected_img = set_range_img.astype(np.uint8)
    heat_bottom_img = cv2.applyColorMap(corrected_img, cv2.COLORMAP_TURBO)

    cv2.imwrite(output_front_image_path, heat_front_img)
    cv2.imwrite(output_bottom_image_path, heat_bottom_img)

    temp_img_df = synced_master_df.iloc[img_save_count]
    print(temp_img_df['Quench4 [lbloo]'])
    if (temp_img_df['Quench4 [lbloo]'] == 1) and ((img_save_count-prev_check_ID)>1):
        thermal_img_name = str(test_ID) + str('_') + str(img_save_count) + str('_')+ str(round(temp_img_df['TC1.setpoint [C]'])) + '.TIF'
        print(output_front_image_path)
        output_Q4_front_image_path = os.path.join(Q4_front_path, thermal_img_name)
        print(output_Q4_front_image_path)
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
    #print('Saved:', output_front_image_path)
    #print('Saved:', output_bottom_image_path)
    img_save_count = img_save_count + 1


E_df.to_csv(E_file_name, index=False, sep=',')


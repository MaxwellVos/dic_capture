# Required filename:
# filename_3.thermal.tiff
# Required file data:
# • MatchID identifier
# • Image width
# • Image height
# • Unit
# • Data format
# • Semicolon delineated data

# Required file formatting: (Note the spelling of Heigth)
# ***MatchID Thermal
# <Width>=<2448>
# <Heigth>=<2048>
# <Unit>=<1>
# <Matrix>
# 0;0;0;0;0;0;0;0
# 0;0;0;0;0;0;0;0
# Note: last entry of each row does not have a “;” afterwards. File ends with the entry itself.

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
image_width = 2448
image_height = 2048

# MatchID requires the following heating to the text file image. Will not work without this exact text
heading_string = ('***MatchID Thermal\n<Width>=<' + str(image_width) + '>\n<Heigth>=<' + str(image_height) +
                  '>\n<Unit>=<1>\n<Matrix>')

DIC_image_shape = np.array([image_height, image_width])  # HEIGHT, WIDTH



test_folder_dir = easygui.diropenbox(
    default='C:/Users/maxwe/OneDrive/Documents/Masters/Test_Data/Sync Data V3/Nkopo_2024_Calibration_005',
    title='The test_data folder for the test. It should be the same as the TEST ID')

output_match_ID_file = os.path.join(test_folder_dir, "Camera_3_Thermal_MatchID")
output_image_file = os.path.join(test_folder_dir, "Camera_3_Thermal_Resized")
input_file = os.path.join(test_folder_dir, "Camera_3")

try:
    os.makedirs(output_match_ID_file)
except:
    print('File already created')

try:
    os.makedirs(output_image_file)
except:
    print('File already created')

test_ID = os.path.basename(os.path.normpath(test_folder_dir))
print('Test ID: ', test_ID)

files_in_dir = os.listdir(input_file)
img_save_count = 0

for filename in os.listdir(input_file):
    input_path = os.path.join(input_file, filename)
    split = os.path.splitext(filename)
    new_img_ID = test_ID + '_' + str(img_save_count) + str('_3') + split[1]
    new_img_txt_ID = test_ID + '_' + str(img_save_count) + str('_3') + '.thermal.tiff'
    output_match_ID_path = os.path.join(output_match_ID_file, new_img_txt_ID)
    output_image_path = os.path.join(output_image_file, new_img_ID)

    img_save_count = img_save_count + 1

    import_image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    divide_arr = DIC_image_shape / np.shape(import_image)

    output_size = np.round(np.array(np.shape(import_image)) * np.min(divide_arr))
    resize_height = int(output_size[0])
    resize_width = int(output_size[1])
    max_val = np.max(import_image)
    min_val = np.min(import_image)
    normalized_img = ((import_image - min_val) / (max_val - min_val))*255



    resized_img = cv2.resize(import_image, (resize_width, resize_height), interpolation=cv2.INTER_LINEAR)
    resized_normalized_img = cv2.resize(normalized_img, (resize_width, resize_height), interpolation=cv2.INTER_LINEAR)
    resized_normalized_img = resized_normalized_img.astype(np.uint8)

    if resize_height < DIC_image_shape[0]:
        boarder_size = int(DIC_image_shape[0] - resize_height)
        boarder_img = cv2.copyMakeBorder(resized_img, 0, boarder_size, 0, 0, cv2.BORDER_CONSTANT, value=0)
        resized_normalized_img = cv2.copyMakeBorder(resized_normalized_img, 0, boarder_size, 0, 0, cv2.BORDER_CONSTANT, value=0)
    if resize_width < DIC_image_shape[1]:
        boarder_size = int(DIC_image_shape[1] - resize_width)
        boarder_img = cv2.copyMakeBorder(resized_img, 0, 0, 0, boarder_size, cv2.BORDER_CONSTANT, value=0)
        resized_normalized_img = cv2.copyMakeBorder(resized_normalized_img, 0, 0, 0, boarder_size, cv2.BORDER_CONSTANT,
                                                    value=0)

    resized_img = np.round(boarder_img)
    print(np.max(boarder_img))
    np.savetxt(output_match_ID_path,
               boarder_img,
               fmt='%1.0f',
               delimiter=';',
               newline='\n',
               header=heading_string,
               comments='',
               encoding=None)

    #resized_normalized_img = np.round(resized_normalized_img)
    #print(np.shape(resized_normalized_img))
    #resized_normalized_img = cv2.cvtColor(resized_normalized_img, cv2.COLOR_GRAY2RGB)
    #print(np.shape(resized_normalized_img))
    #cv2.imwrite(output_image_path, resized_normalized_img)
    tf.imwrite(output_image_path, resized_normalized_img, photometric='miniswhite')
    print('Saved:', output_image_path)

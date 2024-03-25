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

# Thermal images are resized to be the same as the DIC images to avoid scaling issues.
image_width = 2448
image_height = 2048

# MatchID requires the following heating to the text file image. Will not work without this exact text
heading_string = ('***MatchID Thermal\n<Width>=<' + str(image_width) + '>\n<Heigth>=<' + str(image_height) +
                  '>\n<Unit>=<1>\n<Matrix>')


DIC_image_shape = np.array([image_height, image_width]) # HEIGHT, WIDTH

import_image = cv2.imread('C:/Users/maxwe/PycharmProjects/dic_capture/dic_capture/TestThermalImage.tif',
                          cv2.IMREAD_UNCHANGED)
divide_arr = DIC_image_shape/np.shape(import_image)

output_size = np.round(np.array(np.shape(import_image))*np.min(divide_arr))
resize_height = int(output_size[0])
resize_width = int(output_size[1])
resized_img = cv2.resize(import_image, (resize_width, resize_height), interpolation = cv2.INTER_LINEAR)

if resize_height < DIC_image_shape[0]:
    boarder_size = int(DIC_image_shape[0] - resize_height)
    print('Increased Height')
    boarder_img = cv2.copyMakeBorder(resized_img, 0, boarder_size, 0,0, cv2.BORDER_CONSTANT, value=0)
if resize_width < DIC_image_shape[1]:
    print('Increased Width')
    boarder_size = int(DIC_image_shape[1] - resize_width)
    boarder_img = cv2.copyMakeBorder(resized_img, 0,0,0,boarder_size, cv2.BORDER_CONSTANT, value=0)

resized_img = np.round(boarder_img,2)
print(resized_img)
np.savetxt('testSave.txt', boarder_img,fmt='%1.2f', delimiter=';', newline='\n', header=heading_string, comments='', encoding=None)
cv2.imwrite('testSave.tif', boarder_img)

-------------------------------

cam_1_path = 'EMPTY'
cam_2_path = 'EMPTY'
cam_3_path = 'EMPTY'
gleeble_path = 'EMPTY'
arduino_path = 'EMPTY'

test_folder_dir = easygui.diropenbox(
    default='C:/Users/maxwe/OneDrive/Documents/Masters/Test_Data/Sync Data V3/Nkopo_2024_026',
    title='The test_data folder for the test. It should be the same as the TEST ID')
raw_thermal_data_dir = os.path.join(test_folder_dir, "Raw_Data")
synced_data_dir = os.path.join(test_folder_dir, "Synced_Data")
files_in_dir = os.listdir(raw_data_dir)

test_ID = os.path.basename(os.path.normpath(test_folder_dir))
print('Test ID: ', test_ID)

gleeble_drop_dir = 'C:/Users/maxwe/OneDrive - University of Cape Town/GleebleDropFromControl/'

for k in range(0, len(files_in_dir)):
    if 'CAM_3' in files_in_dir[k]:
        cam_3_path = os.path.join(raw_data_dir, files_in_dir[k])





heatmap = cv2.applyColorMap(image, cv2.COLORMAP_TURBO)
heatmap = cv2.resize(heatmap, (200, 200),
               interpolation = cv2.INTER_LINEAR)


#cv2.imshow('image', image)
cv2.imshow('heatmap', heatmap)

filename = 'logo.png'

# Using cv2.imwrite() method
# Saving the image
cv2.imwrite(filename, heatmap)

cv2.waitKey()
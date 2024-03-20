import matplotlib.pyplot as plt
import numpy as np
import cv2

image = cv2.imread('Resized.png', 0)
#colormap = plt.get_cmap('hot')
#heatmap = (colormap(image) * 2**16).astype(np.uint16)[:,:,:3]
#heatmap = cv2.cvtColor(heatmap, cv2.COLOR_RGB2BGR)
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
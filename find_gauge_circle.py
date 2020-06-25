import numpy as np
import scipy.ndimage as ndimage

# takes a bw image (img2) and various analysis parameters and returns location (xloc,yloc) and radius (rad) of the gauge.
# surrounding area for the gauge must be lighter than the gauge's border
def find_gauge_circle(img2,hist_frac=0.1,k_size=10,iterations=1,prev_loc = None):

    # generate histogram, find index that represents the [hist_frac] percentile 
    # (if chosen correctly will include only black border of gauge)
    hist, bin_edges = np.histogram(img2.flatten(),np.arange(0,255))
    summation,idx = 0,0

    while summation<(np.size(img2)*hist_frac):
        summation+=hist[idx]
        idx+=1

    # for 1 iteration, functions with k_size [1,25]
    opening = ndimage.binary_erosion(img2<idx,structure=np.ones((k_size,k_size)),iterations=iterations)

    # if no previous location given, choose the center of the image.
    # edges of gauge must straddle this point in both dimensions
    if prev_loc is None:
        prev_loc = np.flipud(np.shape(opening))/2
      
    # sum across vertical axis and find peaks in dark pixel count
    ax1 = np.mean(opening,axis=0)
    side1 = np.argmax(ax1[:int(prev_loc[0])])
    side2 = np.argmax(ax1[int(prev_loc[0]):])+int(prev_loc[0])

    # radius is half distance between peaks, xloc is average
    rad = abs(side1-side2)/2
    xloc = (side1+side2)/2

    # sum across horizontal axis, however assume radius found previously is right.
    # and trust only the overall maximum (light can be weird from the overhead light on this axis)
    ax2 = np.mean(opening,axis=1)
    max_pt = np.argmax(ax2)
    
    # if max is higher than center pt, subtract radius. Otherwise add it.
    if max_pt > prev_loc[1]:
        yloc = max_pt-rad
    else:
        yloc = max_pt+rad
    
    
    return (xloc,yloc), rad
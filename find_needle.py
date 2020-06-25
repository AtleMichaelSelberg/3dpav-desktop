import numpy as np
import math


# Old methods:
"""
# img is a numpy array, center is [x,y] *in coordinates of the image.*
def find_needle(img,center,radius_range,theta_range = None,return_vec = False):
    
    # simplifies calculations, errors abound if fractions are allowed.
    radius_range = [int(r) for r in radius_range]
    
    # define relevant parts of the image
    xmin,xmax = int(center[0]-radius_range[1]),int(center[0]+radius_range[1]+1)
    ymin,ymax = int(center[1]-radius_range[1]),int(center[1]+radius_range[1]+1)
    
    # define relevant part of image and sum if RGB
    img = np.array(img,dtype='float')
    if len(np.shape(img))== 3:
        img = np.sum(img[ymin:ymax,xmin:xmax,:],2)
    else: # two dimensions
        img = img[ymin:ymax,xmin:xmax]
     
    x, y = np.meshgrid(np.arange(-radius_range[1], radius_range[1]+1),np.arange(-radius_range[1], radius_range[1]+1))
    r = np.sqrt(x**2 + y**2)
    theta_box = np.arctan2(x,-y)+math.pi # (-x,y) works nicely for our purpose so that theta=0,2pi is straight down
    
    # sort theta and image values by theta values
    dummy = sorted(zip(theta_box[(r>radius_range[0])*(r<radius_range[1])],img[(r>radius_range[0])*(r<radius_range[1])]))
    
    # filter size to smooth data, depends on the area of the anulus between radii. forced to be odd.
    N = int(2*(radius_range[1]**2-radius_range[0]**2)*math.pi/360)*2+1
    
    # if theta range specified, find indicees of relevant data
    if theta_range is None or theta_range[0] <= 0:
        theta_range = [N,len(dummy)-N]
    else:
        theta_range = list(int(tr*len(dummy)/(2.0*math.pi)) for tr in theta_range)
        if theta_range[0]<N:
            theta_range[0] = N
        if theta_range[1] >= len(dummy)-N:
            theta_range[1] = len(dummy)-N
        
 
    # create relevant lists
    out = [i for _,i in dummy[theta_range[0]-N:theta_range[1]+N]] 
    theta = [i for i,_ in dummy[theta_range[0]-N:theta_range[1]+N]]    
      
        
   # print(theta[theta_range[0]],theta[theta_range[1]])
    # smooth [out] to reduce noise
   # print(theta_range)
    out = np.convolve(out, np.ones((N,))/N, mode='valid')
    
    # find minimum, which is where the needle is
    out_theta = theta[np.argmin(out)+int((N-1)/2)] # N is odd

    
    
    # plots the theta values within  0.02 radians of the found value
    #theta_box = abs(np.arctan2(-x,y)-out_theta)<0.02
    
    if return_vec:
        theta = theta[int((N-1)/2):-int((N-1)/2)]
        return out_theta,out,theta
    else:
        return out_theta
    
    
    


# img is a numpy array, center is [x,y] *in coordinates of the image.*
# find_needle2 allows looking at the whole circle (no cutting the near theta=0 values)
def find_needle2(img,center,rad,return_vec = False):
    
    # integer values needed to simplify calculations
   # radius_range = [int(0.1*rad),int(0.4*rad),int(0.9*rad)] # defining the inner, outer donuts to look at
    
    radius_range = [int(0.2*rad),int(0.4*rad)]
   
    # define relevant parts of the image
    xmin,xmax = int(center[0]-radius_range[-1]),int(center[0]+radius_range[-1]+1)
    ymin,ymax = int(center[1]-radius_range[-1]),int(center[1]+radius_range[-1]+1)
    
    # define relevant part of image and sum if RGB
    img = np.array(img,dtype='float')
    if len(np.shape(img))== 3:
        img = np.sum(img[ymin:ymax,xmin:xmax,:],2)
    else: # two dimensions
        img = img[ymin:ymax,xmin:xmax]
     
    x, y = np.meshgrid(np.arange(-radius_range[-1], radius_range[-1]+1),np.arange(-radius_range[-1], radius_range[-1]+1))
    r = np.sqrt(x**2 + y**2)
    theta_box = np.arctan2(x,-y)+math.pi # (-x,y) works nicely for our purpose so that theta=0,2pi is straight down
    
    # sort theta and image values by theta values
    dummy = sorted(zip(theta_box[(r>radius_range[0])*(r<radius_range[1])],img[(r>radius_range[0])*(r<radius_range[1])]))
    
    # filter size to smooth data, depends on the area of the anulus between radii. forced to be odd.
    N = int(4*(radius_range[1]**2-radius_range[0]**2)*math.pi/360)*2+1
    
    # if theta range specified, find indicees of relevant data
    theta_range = [N,len(dummy)-N]
   
        
 
    # create relevant lists, add extra N on both sides of out for smoothing (to be cropped later)
    out = [i for _,i in dummy+dummy[:(2*N)]]
    theta = [i for i,_ in dummy[N:]+dummy[:N]]
      
    pre_conv_out = out    
    # smooth [out] to reduce noise, crop edges
    out = np.convolve(out, np.ones((N,))/N, mode='same')[N:-N]
    
    print(len(out),len(theta),N)
    # find minimum, which is where the needle is
    out_theta = theta[np.argmin(out)] # N is odd
    out_theta = (out_theta + math.pi)%(2*math.pi)
    
    
    # plots the theta values within  0.02 radians of the found value
    #theta_box = abs(np.arctan2(-x,y)-out_theta)<0.02
    
    if return_vec:
        return out_theta,out,pre_conv_out[N:-N],theta
    else:
        return out_theta
    
    
    



# img is a numpy array, center is [x,y] *in coordinates of the image.*
# find_needle3 looks both at an inner (back of the needle) and outer (front of the needle) ring
def find_needle3(img,center,radius_range,return_vec = False):
    
    # integer values needed to simplify calculations
   # radius_range = [int(0.1*rad),int(0.4*rad),int(0.9*rad)] # defining the inner, outer donuts to look at
   # radius_range = [int(0.4*rad),int(0.55*rad)] # inner circle and outer ring have ~ same area
   
    # define relevant parts of the image
    xmin,xmax = int(center[0]-radius_range[-1]),int(center[0]+radius_range[-1]+1)
    ymin,ymax = int(center[1]-radius_range[-1]),int(center[1]+radius_range[-1]+1)
    
    # define relevant part of image and sum if RGB
    img = np.array(img,dtype='float')
    if len(np.shape(img))== 3:
        img = np.sum(img[ymin:ymax,xmin:xmax,:],2)
    else: # two dimensions
        img = img[ymin:ymax,xmin:xmax]
     
    x, y = np.meshgrid(np.arange(-radius_range[-1], radius_range[-1]+1),np.arange(-radius_range[-1], radius_range[-1]+1))
    r = np.sqrt(x**2 + y**2)
    theta_box = np.arctan2(x,-y)+math.pi # (-x,y) works nicely for our purpose so that theta=0,2pi is straight down
    
    # rotate inner box by 180 degrees (inner box will have best spot at BACK of needle)
    theta_box[r<radius_range[0]] = (theta_box[r<radius_range[0]]+math.pi)%(math.pi*2)
    
   # ordr = numpy.argsort(theta_box[(r<radius_range[1])])
    
    # sort theta and image values by theta values
    dummy = sorted(zip(theta_box[(r<radius_range[1])],img[(r<radius_range[1])]))
    
    # filter size to smooth data, depends on the area of the anulus between radii. forced to be odd.
    N = int(4*(radius_range[1]**2-radius_range[0]**2)*math.pi/360)*2+1
        
 
    # create relevant lists, add extra N on both sides of out for smoothing (to be cropped later)
    out = [i for _,i in dummy+dummy[:(2*N)]]
    theta = [i for i,_ in dummy[N:]+dummy[:N]]
  
    pre_conv_out = out    
    # smooth [out] to reduce noise, crop edges
    out = np.convolve(out, np.ones((N,))/N, mode='same')[N:-N]
    
    # find minimum, which is where the needle is
    out_theta = theta[np.argmin(out)] # N is odd
    
    
    # plots the theta values within  0.02 radians of the found value
    #theta_box = abs(np.arctan2(-x,y)-out_theta)<0.02
    
    if return_vec:
        return out_theta,out,pre_conv_out[N:-N],theta
    else:
        return out_theta
    
    
    """
 
# Current methods:

# Helper function to memoize results of radial sort
def memoize(f):
    results = {}
    def helper(n1,n2):
        if (n1,n2) not in results:
            results[(n1,n2)] = f(n1,n2)
        return results[(n1,n2)]
    return helper
    


# Helper function that generates order (to sort) theta and image values. Memoize to speed computation.    
@memoize    
def radial_sort(r1,r2):
    x, y = np.meshgrid(np.arange(-r2, r2+1),np.arange(-r2, r2+1))
    r = np.sqrt(x**2 + y**2)
    theta_box = np.arctan2(x,-y)+math.pi # (-x,y) works nicely for our purpose so that theta=0,2pi is straight down

    # rotate inner box by 180 degrees (inner box will have best spot at BACK of needle)
    theta_box[r<r1] = (theta_box[r<r1]+math.pi)%(math.pi*2)

    # make outer values very high
    theta_box[r>r2] = 10
    keep_idx = np.sum(theta_box!=10) # end index of relevant pixels

    # find sort order (large r are all put last and then cut)
    ordr1 = np.argsort(theta_box.flatten())[:keep_idx]
    theta1 = list(theta_box.flatten()[ordr1])

    return ordr1,theta1
    
    

# img is a numpy array, center is [x,y] *in coordinates of the image.*
# find_needle4 looks both at an inner (back of the needle) and outer (front of the needle) ring
def find_needle4(img,center,radius_range,in_ordr=None, return_vec = False):
    
    # integer values needed to simplify calculations
   # radius_range = [int(0.1*rad),int(0.4*rad),int(0.9*rad)] # defining the inner, outer donuts to look at
   # radius_range = [int(0.4*rad),int(0.55*rad)] # inner circle and outer ring have ~ same area
   
    # define relevant parts of the image
    xmin,xmax = int(center[0]-radius_range[-1]),int(center[0]+radius_range[-1]+1)
    ymin,ymax = int(center[1]-radius_range[-1]),int(center[1]+radius_range[-1]+1)
    
    if xmin<0 or xmax<0 or ymin<0 or ymax<0:
        print((xmin,xmax,ymin,ymax))
    
    # define relevant part of image (input img is 2D)
    img = np.array(img,dtype='float')[ymin:ymax,xmin:xmax]
  
    # find order to radially sort by theta (or look up from memoize)
    ordr1,theta = radial_sort(radius_range[0],radius_range[-1])
    
    # filter size to smooth data, depends on the area of given circle. forced to be odd.
    N = int(2*(radius_range[1]**2)*math.pi/360)*2+1
        
    # create relevant lists, add extra N on both sides of out for smoothing (to be cropped later)
    theta = theta[N:]+theta[:N]
    try:
        out = list(img.flatten()[ordr1])
    except:
        print(img)
        print(ordr1)
        raise NameError('hi')
        
    out = out + out[:(2*N)] 
 
    # smooth [out] to reduce noise, crop edges
    out = np.convolve(out, np.ones((N,))/N, mode='same')[N:-N]
    
    # find minimum, which is where the needle is
    out_theta = theta[np.argmin(out)] # N is odd
    
  
    return out_theta
    
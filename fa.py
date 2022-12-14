# -*- coding: utf-8 -*-
"""FA.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ZQMh4GnlehXyP5UZ0UaixVFQPXUoqvYz

# Introduction
This colab worksheet provides a starting point for the computer vision assignment.

# Data Loading
"""

################################################################################
# SPRING 2022 UNIVERSITY OF SUSSEX COMPUTER VISION                             #
# UFKUN OZALP                                                                  #
# 22106687                                                                     #
################################################################################

# Download the data stored in a zipped numpy array from one of these two locations
# The uncommented one is likely to be faster. If you're running all your experiments
# on a machine at home rather than using colab, then make sure you save it 
# rather than repeatedly downloading it.

#!wget "http://users.sussex.ac.uk/~is321/training_images.npz" -O training_images.npz
!wget "https://sussex.box.com/shared/static/jqrklxpl2c5hnrkpa2m7f9da2o3np8g9.npz" -O training_images.npz

# The test images (without points)
#!wget "http://users.sussex.ac.uk/~is321/test_images.npz" -O test_images.npz
!wget "https://sussex.box.com/shared/static/xxlgvjpa86s6xgjzy5im06saoj57s7gt.npz" -O test_images.npz

# The example images are here
#!wget "http://users.sussex.ac.uk/~is321/examples.npz" -O examples.npz
!wget "https://sussex.box.com/shared/static/kbodelmaqw5dd59i5x2kis55lor7ydhf.npz" -O examples.npz

"""# Check the data downloaded correctly
If any of these assertions fail, redownload the data
"""

def confirm_checksum(filename, true_checksum):
  import subprocess
  checksum = subprocess.check_output(['shasum',filename]).decode('utf-8')
  assert checksum.split(' ')[0] == true_checksum, 'Checksum does not match for ' + filename + ' redownload the data.'

confirm_checksum('training_images.npz', 'f313a54fc57a1235e6307d176fc5fc83fd7ec530')
confirm_checksum('test_images.npz', '4b9efd8eb3b87c07d9c5400ef2494d476bc318a3')
confirm_checksum('examples.npz', 'bf51ebbf42f17e3cbe06bb299746565c53d16c40')

"""# Load the data"""

import numpy as np


# Load the data using np.load
data = np.load('training_images.npz', allow_pickle=True)

# Extract the images
images = data['images']
# and the data points
pts = data['points']

print(images.shape, pts.shape)

test_data = np.load('test_images.npz', allow_pickle=True)
test_images = test_data['images']
print(test_images.shape)

"""# Data Visualisation
Here's an example of how to display the images and their points
"""

def visualise_pts(img, pts):
  import matplotlib.pyplot as plt
  plt.imshow(img)
  for i in pts:
    plt.plot(i[0],i[1], '+r')
  plt.show()

for i in range(3):
  idx = np.random.randint(0, images.shape[0])
  visualise_pts(images[idx, ...], pts[idx, ...])

"""# Calculating Prediction Error and exporting results"""

def euclid_dist(pred_pts, gt_pts):
  """
  Calculate the euclidean distance between pairs of points
  :param pred_pts: The predicted points
  :param gt_pts: The ground truth points
  :return: An array of shape (no_points,) containing the distance of each predicted point from the ground truth
  """
  import numpy as np
  pred_pts = np.reshape(pred_pts, (-1, 2))
  gt_pts = np.reshape(gt_pts, (-1, 2))
  return np.sqrt(np.sum(np.square(pred_pts - gt_pts), axis=-1))

def save_as_csv(points, location = '.'):
    """
    Save the points out as a .csv file
    :param points: numpy array of shape (no_test_images, no_points, 2) to be saved
    :param location: Directory to save results.csv in. Default to current working directory
    """
    assert points.shape[0]==554, 'wrong number of image points, should be 554 test images'
    assert np.prod(points.shape[1:])==2*42, 'wrong number of points provided. There should be 42 points with 2 values (x,y) per point'
    np.savetxt(location + '/results.csv', np.reshape(points, (points.shape[0], -1)), delimiter=',')

"""# PIP Installs and Imports"""

!pip uninstall opencv-python -y
!pip install opencv-python==3.4.2.17
!pip install opencv-contrib-python==3.4.2.17 --force-reinstall
# Newer versions of OpenCV does not support SIFT functions
import numpy as np
import cv2
from google.colab.patches import cv2_imshow
from sklearn.decomposition import PCA
from sklearn import linear_model
from PIL import Image
from matplotlib.pyplot import imshow
import matplotlib.pyplot as plt

"""# Load Sets"""

# Loading data sets (with np.load)
testData = np.load('test_images.npz', allow_pickle=True)
exampleData = np.load('examples.npz', allow_pickle = True)
trainingData = np.load('training_images.npz', allow_pickle=True)

# Getting images from data
testImages = testData['images']
exampleImages = exampleData['images']
trainingImages = trainingData['images']

# Getting points from data (last 500 points)
trainingPoints = trainingData['points']
trainingSet = trainingImages[:-500]     
trainingSetPoints = trainingPoints[:-500]
validationSet = trainingImages[-500:]   
validationSetPoints = trainingPoints[-500:]

"""# Pre-processing"""

# Convert all images to gray
grayImagesList = []
for i in trainingSet:
  grayImagesList.append(np.uint8(np.mean(i, axis=-1)))     # Reduce all images to single axis by averaging pixel intensities

# Get average image to get the mean face
averageImage = np.average(grayImagesList, axis = 0)   

averagePoints = []
LEN_SET = (np.shape(trainingSetPoints)[1])
# for each marker, append average x and y coordinates to the list
for i in range(LEN_SET):                          
  px = np.average(trainingSetPoints[:,i,0]) 
  py = np.average(trainingSetPoints[:,i,1]) 
  averagePoints.append([px, py]) 

def addGaussianBlur(image):
  blurImage = cv2.GaussianBlur(image,(5,5),0)
  return (cv2.resize(blurImage, (122,122), interpolation = cv2.INTER_AREA))   # Reducing size by half (from 244 to 122)

def scalePoints(points, flagString):
  resizedPoints = []
  for point in points:
    rx = point[0]
    ry = point[1]
    if flagString == "upscale":
      rx = rx * 2
      ry = ry * 2
    if flagString == "downscale":
      rx = rx / 2
      ry = ry / 2
    resizedPoints.append([rx, ry])
  return resizedPoints

visualise_pts(averageImage, averagePoints) # Displays average face

"""# Train Model"""

def getKeypoints(facePoints, keypointSize=1):
  keypoints = []
  for i in range(LEN_SET): 
    px = facePoints[i][0]
    py = facePoints[i][1]
    keypoints.append(cv2.KeyPoint(px, py,keypointSize))
  return keypoints

def predictRegressor(image, regressor, previousPoints, SIFT, dampingFactor=0.15):
  points = previousPoints
  a = SIFT.compute(image,getKeypoints(points))[1]  # Get descriptors
  prediction = regressor.predict(a.reshape(-1,5376)) * dampingFactor   # Array is flattened, therefore its size now 128 (depth of SIFT features) * 42 (features) = 5376 
  return (points + (prediction.reshape(-1,2)))                         


def trainCascade(numRegressor, dampingFactor):
  SIFT = cv2.xfeatures2d_SIFT.create()
  points = []
  processedImagesList = []
  downscaledGroundPoints = []  

  for i in trainingSetPoints:                        
    avgPtsCpy = np.copy(averagePoints)                         
    points.append(scalePoints(avgPtsCpy, "downscale"))                 
    downscaledGroundPoints.append(scalePoints(i, "downscale"))       # Resizing the starting points and ground points

  for i in trainingSet:
    processedImagesList.append(addGaussianBlur(i))   

  # Convert them to np arrays
  points = np.array(points)
  downscaledGroundPoints = np.array(downscaledGroundPoints)       

  regressors = []       
  for i in range(numRegressor):  # Loop for each regressor
    A  = []
    target = []
    for j in range(len(processedImagesList)): # Loop for each image
      if i != 0: # Since there is no previous regressor in the first iteration 
        points[j] = predictRegressor(processedImagesList[j],regressors[i-1], points[j], SIFT, dampingFactor) 
                                                                                                            
      A.append(SIFT.compute(processedImagesList[j], getKeypoints(points[j]))[1])  # Append descriptors
      target.append(downscaledGroundPoints[j] - points[j])

    A = np.array([a.flatten() for a in A]) # Make "a" flattened
    target = np.array([t.flatten() for t in target])                  
    model = linear_model.LinearRegression()                           
    regressors.append(model.fit(A,target))

  return regressors

regressors = trainCascade(25, 0.15) # According to many runs and trial-error method, 25 regressors and 0.15 damping factor gives the most accurate results

def runReg(image, regressors, dampingFactor):
  sift = cv2.xfeatures2d.SIFT_create()
  points = scalePoints(averagePoints, "downscale")
  image = addGaussianBlur(image)
  for i in range(len(regressors)):  # Loop for each regressor                                             
    a = sift.compute(image, getKeypoints(points))[1]  # SIFT features calculation
    prediction = regressors[i].predict(a.reshape(-1,5376)) * dampingFactor # Make prediction
    points = points + (prediction.reshape(-1,2))
  return scalePoints(points, "upscale")

"""# Get Output and Results"""

output = []
for image in testImages:
  points = runReg(image, regressors, dampingFactor=0.15)
  visualise_pts(image, points)
  output.append(points)
save_as_csv(np.array(output), location = '.')
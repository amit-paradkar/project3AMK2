# Vehicular Classification -- Data Preparation
This repository contains the scripts and instructions to prepare data for a vehicular classification project using the BDD100K dataset, formatted for use with the YOLO object detection algorithm (AlexeyAB's Darknet).

## Overview
This step focuses on preparing the BDD100K dataset for training a YOLO model to classify different types of vehicles (e.g., cars, buses, trucks, motorcycles). The BDD100K dataset contains diverse driving scenes across different times of day and weather conditions, making it well-suited for robust vehicular detection and classification.

## Requirements

- Python 3.7+
- opencv-python
- numpy
- tqdm
- pandas
- BDD100K Dataset. Download from [BDD100K Dataset](http://bair.berkeley.edu/blog/2018/05/30/bdd/)

### Install Dependencies
```
pip install opencv-python numpy tqdm pandas
```

## Steps
1. Download BDD100K Dataset
   
   Download the following:

   - images/100k/train/
   - images/100k/val/
   - labels/bdd100k_labels_images_train.json
   - labels/bdd100k_labels_images_val.json

2. Data Preparation
    
    a. The images and labels for BDD dataset are not consistent. User Data set cleaning script [clean_images_labels.py](https://github.com/amit-paradkar/project3AMK2/blob/master/pre_processing/clean_images_labels.py) to create images and labels data
    
    b. Convert the JSON labels from BDD to text labels required by darknet. Use [convert_json_labels_to_txt.py](https://github.com/amit-paradkar/project3AMK2/blob/master/pre_processing/clean_images_labels.py)

    c. Use [process.py](https://github.com/amit-paradkar/project3AMK2/blob/master/pre_processing/process.py) for creating train.txt and test.txt file. This script ramdomnly divides the data set into 90% (train) & 10% (test)

3. Colab instance preparation and Model Generation
    
    i. Use the [driver.ipynb](https://github.com/amit-paradkar/project3AMK2/blob/master/driver.ipynb) for setting up colab instance
    
    ii. Build darknet. Follow instructions in [Alexy AB darknet](https://github.com/AlexeyAB/darknet) to build darknet binary
    
    iii.  Create [yolo-obj.cfg](https://github.com/amit-paradkar/project3AMK2/blob/master/static/model/configuration/yolo-obj.cfg) and copy it to darknet/cfg folder
    
    iv. Create [obj.names](https://github.com/amit-paradkar/project3AMK2/blob/master/static/model/configuration/obj.names) and obj.data and copy them to darknet/data folder.
    
    v.    Create a obj.zip containing images and their labels on local
    vi.   Uplooad it to colab google drive
    vii.  Copy the obj.zip to /home directory in colab instance. This will    
          create /home/obj folder which will contain all images and label files
    viii. Execute command "python process.py" to create train.txt and test.txt files.
    ix.   Run the command"!./darknet detector train data/obj.data cfg/
          yolo-obj.cfg yolov4.conv.137 -dont_show -map 2>&1 | tee darknet.log"
    x.    In case the colab session doesn't complete run the command until 
          iterations (max_batch_size) is complete
          
          ```
        !./darknet detector train data/obj.data cfg/yolo-obj.cfg /mydrive/yolov4/training/yolo-obj_last.weights -dont_show -map 2>&1 | tee darknet.log
        ```
    
    xi. Check the yolo-chart.png created to verify the loss
    
    xii.Once training is complete change the following line in yolo-obj.cfg
        batch=1
        subdivisions=1
        comment all other lines containing batch and subdivision
    
    xiii. Execute the following command 
    ```
    "!./darknet detector test data/obj.data cfg/yolo-obj.cfg /mydrive/yolov4/training/yolo-obj_best.weights /mydrive/yolov4/Validate/0a0a0b1a-7c39d841.jpg -thresh 0.005 -ext_output "
    ```
    
    xiv. Validate your model based on the "predictions.jpg" file created by

    xv. In case predictions are not good, then change the learning_rate in yolo-obj.cfg and run steps #ix to #xiv

# Live Traffic camera : Build and Deploy Application



## Deployment
1) Copy the files obj.names, yolo-obj.cfg, and yolo-obj_last_weights files to static/model/configuration and static/weights folder

2) Install docker on your local machine
3) In main.py update the variable TRAFFIC_FEED_URL to the feed address
4) Run command "docker build -t project3amk2 .   " to build docker image
5) Run command "docker run 8080:8080 project3amk2" to run the container on your local machine
6) Wait for the FastAPI server starts completely
7) Point your browser to "http://127.0.0.1:5000"

Predictions
![alt text](https://github.com/amit-paradkar/project3AMK2/blob/master/prediction.png)

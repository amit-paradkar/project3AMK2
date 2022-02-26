from contextlib import nullcontext
import json, string
from stat import FILE_ATTRIBUTE_NOT_CONTENT_INDEXED
import argparse
from pathlib import Path
import os, shutil
from turtle import xcor 

IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720 

def create_list_of_labels(label_json_file):

    with open(label_json_file, 'r') as labels_file:
        labels_data=labels_file.read()

    # parse file
    label_arry = json.loads(labels_data)

    # show values
    print("number of labels: " + str(len(label_arry)))
    
    return label_arry
'''
car
bus
person
bike
truck
motor
train
rider
traffic sign
traffic light
'''
def  get_category_number(category):
    return {
        'car': 0,
        'bus': 1,
        'person': 2,
        'bike': 3,
        'truck': 4,
        'motor': 5,
        'train': 6,
        'rider': 7,
        'traffic sign': 8,
        'traffic light': 9
    }.get(category, 100)


def create_text_files_from_json(image_dir,labels):
    clean_image_list =list()
    clean_label_list = list()
    bounding_boxes_list = list()

    for label in labels:
        image_file = label["name"].replace("jpg","txt")
        label_txt_file = Path.joinpath(image_dir, image_file)
        print("image file:", label["name"])
        with open(label_txt_file, 'w') as label_file:
            for category in label['labels']:
                #print(category.get('category'))
                bbox = category.get('box2d')
                if(bbox != None):
                    #print("X1:",bbox['x1'])
                    #Division by image width and heigh gives usabsolute value
                    fl_x1 = float(bbox['x1'])/IMAGE_WIDTH
                    fl_x2 = float(bbox['x2'])/IMAGE_WIDTH
                    fl_y1 = float(bbox['y1'])/IMAGE_HEIGHT
                    fl_y2 = float(bbox['y2'])/IMAGE_HEIGHT
                    fl_xc = ((fl_x2 + fl_x1)/2)
                    fl_yc = ((fl_y2 + fl_y1)/2)
                    fl_width = abs((fl_x2 - fl_x1))
                    fl_height = abs((fl_y2 - fl_y1))
                    print("fl_xc:",fl_xc)
                    print("fl_yc:",fl_yc)
                    print("fl_width:",fl_width)
                    print("fl_height:",fl_height)

                    label_file.write("{} {} {} {} {}\n".format(get_category_number(category.get('category')), fl_xc, fl_yc,fl_width, fl_height))

    return

def convert_json_labels_to_text(label_json_file,images_dir,output_dir):
    
    labels_list = create_list_of_labels(label_json_file)
    
    create_text_files_from_json(images_dir, labels_list)
    
    return

def main():

    ap = argparse.ArgumentParser()
    ap.add_argument("-l", "--labels_json_file", help="path to the bdd labels json file")
    ap.add_argument("-i", "--images_dir", help="path to images directory")
    ap.add_argument('-o', '--output_dir', help='path to output directory')
    args = ap.parse_args()

    label_json_file = Path(args.labels_json_file).absolute()
    images_dir = Path(args.images_dir).absolute()
    output_dir = Path(args.output_dir).absolute()
    assert label_json_file.is_file(), "Given argument is not a label.json file"
    assert images_dir.is_dir(), "Given argument is not an images directory"
    assert output_dir.is_dir(), "Given argument is not an output directory"
    print("Processing labels file: " + str(label_json_file) + " and images directory: " + str(images_dir))
    print("Output files and directories willbe created in: " + str(output_dir))

    convert_json_labels_to_text(label_json_file,images_dir,output_dir)
    
if __name__ == "__main__":
    main()
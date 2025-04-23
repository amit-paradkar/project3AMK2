import json, string
import argparse
from pathlib import Path
import os, shutil 
 

def generate_output(clean_image_list,clean_labels_list,output_dir, image_dir):

    clean_image_dir = Path.joinpath(output_dir, "images")
    clean_json_file = Path.joinpath(output_dir, "cleaned.json")
    clean_images_file = Path.joinpath(output_dir, "cleaned_images_path.txt")
    with open(clean_json_file, 'w') as f:
        json.dump(clean_labels_list, f)
    
    print("Created Clean JSON file: ", clean_json_file)

    with open(clean_images_file, 'w') as f:
        for item in clean_image_list:
            f.write("%s\n" % item)

    print("After creating clean images file")
    
    os.mkdir(clean_image_dir)
    
    print("Created clean image dir: ", str(clean_image_dir))

    for f in clean_image_list:
        shutil.copy(f, clean_image_dir)

    #with os.scandir(clean_image_dir) as it:
    #    for clean_image_file in it:
    #        print(clean_image_file.name, clean_image_file.path)

    print("Completed generating output files")
    return

def create_list_of_labels(label_json_file):

    with open(label_json_file, 'r') as labels_file:
        labels_data=labels_file.read()

    # parse file
    label_arry = json.loads(labels_data)

    # show values
    print("number of labels: " + str(len(label_arry)))
    
    return label_arry

def create_cleaned_images_labels_list(images_dir,labels):
    clean_image_list =list()
    clean_label_list = list()

    match_count =0
    with os.scandir(images_dir) as it:
        for image_file in it:
            if image_file.name.endswith(".jpg") and image_file.is_file():
                #print(image_file.name, image_file.path)
                for label in labels:
                    if label["name"] == image_file.name:
                        #print("Matched Label: " +label["name"] + " Image file: :" + str(image_file.name))
                        clean_image_list.append(image_file.path)
                        clean_label_list.append(label)
                        match_count += 1

    print("Matched Labels and Images: " + str(match_count))

    return clean_image_list, clean_label_list


def create_cleaned_images_and_labels(label_json_file,images_dir,output_dir):
    
    labels_list = create_list_of_labels(label_json_file)
    clean_image_list,clean_labels_list = create_cleaned_images_labels_list(images_dir, labels_list)
    print("Image list count: " + str(len(clean_image_list)))
    print("Label list count: " + str(len(clean_labels_list)))
    generate_output(clean_image_list,clean_labels_list,output_dir,images_dir)
    
    return

def main():

    ap = argparse.ArgumentParser()
    ap.add_argument("-l", "--labels_json_file", help="path to the labels json file")
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

    create_cleaned_images_and_labels(label_json_file,images_dir,output_dir)
    
if __name__ == "__main__":
    main()
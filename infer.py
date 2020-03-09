# -*- coding: utf-8 -*-

# This driver performs 2-functions for the validation images specified in configuration file:
#     1) evaluate fscore of validation images.
#     2) stores the prediction results of the validation images.

import argparse
import json
import cv2
import numpy as np
#import yolo
#from yolo.frontend import create_yolo
#from yolo.backend.utils.box import draw_scaled_boxes
#from yolo.backend.utils.annotation import parse_annotation
#from yolo.backend.utils.eval.fscore import count_true_positives, calc_score

from networks.segnet.frontend_segnet import create_segnet
from networks.segnet.predict import predict_multiple

import os


import tensorflow as tf
gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
config = tf.ConfigProto(gpu_options=gpu_options)
config.gpu_options.allow_growth = True
session = tf.Session(config=config)

DEFAULT_THRESHOLD = 0.3

argparser = argparse.ArgumentParser(
    description='Predict digits driver')

argparser.add_argument(
    '-c',
    '--conf',
    help='path to configuration file')

argparser.add_argument(
    '-t',
    '--threshold',
    default=DEFAULT_THRESHOLD,
    help='detection threshold')

argparser.add_argument(
    '-w',
    '--weights',
    help='trained weight files')

argparser.add_argument(
    '-p',
    '--path',
    help='path to images')

if __name__ == '__main__':
    # 1. extract arguments
    args = argparser.parse_args()
    with open(args.conf) as config_buffer:
        config = json.loads(config_buffer.read())

    if config['model']['type']=='SegNet':
        print('Segmentation')           
        # 1. Construct the model 
        segnet = create_segnet(config['model']['architecture'],
                                   config['model']['input_size'],
                                   config['model']['n_classes'],
                                   int(config['train']['first_trainable_layer']))   
        # 2. Load the pretrained weights (if any) 
        segnet.load_weights(args.weights)
        predict_multiple(segnet._network, inp_dir=config['train']['valid_image_folder'], out_dir='detected',overlay_img=True)


    if config['model']['type']=='Detector':
        if config['train']['is_only_detect']:
            labels = ['']
        else:
            if config['model']['labels']:
                labels = config['model']['labels']
            else:
                labels = get_object_labels(config['train']['train_annot_folder'])
        print(labels)
        # 2. create yolo instance & predict
        yolo = create_yolo(config['model']['architecture'],
                           labels,
                           config['model']['input_size'],
                           config['model']['anchors'])
        yolo.load_weights(args.weights)

        # 3. read image
        write_dname = "detected"
        if not os.path.exists(write_dname): os.makedirs(write_dname)
        annotations = parse_annotation(config['train']['valid_annot_folder'],
                                       config['train']['valid_image_folder'],
                                       config['model']['labels'],
                                       is_only_detect=config['train']['is_only_detect'])

        #n_true_positives = 0
        #n_truth = 0
        #n_pred = 0
        #for i in range(len(annotations)):
        for filename in os.listdir(args.path):
            #img_path = annotations.fname(i)
            img_path = os.path.join(args.path,filename)
            #img_fname = os.path.basename(img_path)
            img_fname = filename
            image = cv2.imread(img_path)
            #true_boxes = annotations.boxes(i)
            #true_labels = annotations.code_labels(i)
            
            boxes, probs = yolo.predict(image, float(args.threshold))

            # 4. save detection result
            image = draw_scaled_boxes(image, boxes, probs, labels)
            output_path = os.path.join(write_dname, os.path.split(img_fname)[-1])
            label_list = config['model']['labels']
            right_label = np.argmax(probs, axis=1) if len(probs) > 0 else [] 
            #cv2.imwrite(output_path, image)
            print("{}-boxes are detected. {} saved.".format(len(boxes), output_path))
            if len(probs) > 0:
                #create_ann(filename,image,boxes,right_label,label_list)
                cv2.imwrite(output_path, image)

            #n_true_positives += count_true_positives(boxes, true_boxes, labels, true_labels)
            #n_truth += len(true_boxes)
            #n_pred += len(boxes)
        #print(calc_score(n_true_positives, n_truth, n_pred))
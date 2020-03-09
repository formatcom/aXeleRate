# -*- coding: utf-8 -*-
# This module is responsible for communicating with the outside of the yolo package.
# Outside the package, someone can use yolo detector accessing with this module.

import os
import numpy as np

from .data_utils.data_loader import create_batch_generator, verify_segmentation_dataset
from ..common_utils.feature import create_feature_extractor
from ..common_utils.fit import train
from .models.segnet import mobilenet_segnet

def masked_categorical_crossentropy(gt , pr ):
    from keras.losses import categorical_crossentropy
    mask = 1-  gt[: , : , 0 ] 
    return categorical_crossentropy( gt , pr )*mask

def create_segnet(architecture, input_size, n_classes ,first_trainable_layer):
    
    model = mobilenet_segnet(n_classes ,input_height=input_size,input_width=input_size)
    output_size = model.output_height
    network = Segnet(model,input_size, n_classes, output_size)

    return network

class Segnet(object):
    def __init__(self,
                 network,
                 input_size,
                 n_classes,
                 output_size):
        self._network = network       
        self._n_classes = n_classes
        self._input_size = input_size
        self._output_size = output_size

    def load_weights(self, weight_path, by_name=False):
        if os.path.exists(weight_path):
            print("Loading pre-trained weights in", weight_path)
            self._network.load_weights(weight_path, by_name=by_name)
        else:
            print("Fail to load pre-trained weights. Make sure weight file path.")

    def predict(self, image):
        preprocessed_image = prepare_image(image,show=False)
        pred = model.predict(preprocessed_image)
        predicted_class_indices=np.argmax(pred,axis=1)
        predictions = [labels[k] for k in predicted_class_indices]
        return predictions

    def train(self,
              img_folder,
              ann_folder,
              nb_epoch,
              saved_weights_name,
              batch_size=8,
              jitter=True,
              learning_rate=1e-4, 
              train_times=1,
              valid_times=1,
              valid_img_folder="",
              valid_ann_folder="",
              first_trainable_layer=None,
              ignore_zero_class=False):
        
        if ignore_zero_class:
            loss_k = masked_categorical_crossentropy
        else:
            loss_k = 'categorical_crossentropy'
        
        train_generator = create_batch_generator(img_folder, ann_folder, self._input_size, self._output_size, self._n_classes,
                                                     batch_size,train_times)
        if valid_img_folder:
            validation_generator = create_batch_generator(valid_img_folder, valid_ann_folder, self._input_size,self._output_size, self._n_classes,
                                                     batch_size,valid_times)
        
        self._network.summary()
        train(self._network,loss_k,train_generator,validation_generator,learning_rate, nb_epoch,saved_weights_name)
        print("Saving model")
        self._network.save(saved_weights_name)
    
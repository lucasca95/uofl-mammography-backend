# -*- coding: utf-8 -*-
"""
Created on Fri Feb 18 09:52:10 2022

@author: Baccouche, Asma.
"""
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
import os
import numpy as np
from keras.models import load_model
from keras.layers import Input
from PIL import Image
from yolo3_model import yolo_eval, yolo_body
from yolo3_utils import letterbox_image

np.random.seed(10101)

def get_anchors(anchors_path):
    anchors_path = os.path.expanduser(anchors_path)
    with open(anchors_path) as f:
        anchors = f.readline()
    anchors = [float(x) for x in anchors.split(',')]
    return np.array(anchors).reshape(-1, 2)

def detect(image_path, anchors_path, class_names, model_path, t_score = 0.35, t_iou = 0.45, model_image_size = (448, 448)):
    anchors = get_anchors(anchors_path)   
    model_path = os.path.expanduser(model_path)
    
    num_anchors = len(anchors)
    num_classes = len(class_names)
    
    try:
        yolo_model = load_model(model_path, compile=False)
    except:
        yolo_model = yolo_body(Input(shape=(None,None,3)), num_anchors//3, num_classes)
        yolo_model.load_weights(model_path) 
    else:
        assert yolo_model.layers[-1].output_shape[-1] == num_anchors/len(yolo_model.output) * (num_classes + 5), 'Mismatch between model and given anchor and class sizes'

    image = Image.open(image_path)
    image = image.convert('RGB')
    
    if model_image_size != (None, None):
        assert model_image_size[0]%32 == 0, 'Multiples of 32 required'
        assert model_image_size[1]%32 == 0, 'Multiples of 32 required'
        boxed_image = letterbox_image(image, tuple(reversed(model_image_size)))
    else:
        new_image_size = (image.width - (image.width % 32),
                          image.height - (image.height % 32))
        boxed_image = letterbox_image(image, new_image_size)
    image_data = np.array(boxed_image, dtype='float32')
    
    image_data /= 255.
    image_data = np.expand_dims(image_data, 0) 

    out_boxes, out_scores, out_classes = yolo_eval(yolo_model(image_data),
              anchors=anchors,
              num_classes=len(class_names),
              image_shape = [image.size[1],image.size[0]],score_threshold=t_score,
              iou_threshold=t_iou)

    if len(out_classes) == 0:
        roi = None
        detection_label = None
    else:
        i = 0
        predicted_class = class_names[out_classes[i]]
        box = out_boxes[i]
        score = out_scores[i]
        detection_label = '{} {:.2f}'.format(predicted_class, score)
        top, left, bottom, right = box
        top = max(0, np.floor(top + 0.5).astype('int32'))
        left = max(0, np.floor(left + 0.5).astype('int32'))
        bottom = min(image.size[1], np.floor(bottom + 0.5).astype('int32'))
        right = min(image.size[0], np.floor(right + 0.5).astype('int32'))
        
        if (bottom < 100 or right < 100) or (bottom < 100 and right < 100):  
            if left-50<=0 and top-50 >0:
                (left, top, right, bottom) = (left, top-50, right+100, bottom+50)
            if top-50<=0 and left-50 >0:
                (left, top, right, bottom) = (left-50, top, right+50, bottom+100)
            if top-50<=0 and left-50<=0:
                (left, top, right, bottom) = (left, top, right+100, bottom+100)
            if top-50>0 and left-50>0:
                (left, top, right, bottom) = (left-50, top-50, right+50, bottom+50)

        roi = (left, top, right, bottom)
    return roi, detection_label


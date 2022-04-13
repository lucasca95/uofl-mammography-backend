# -*- coding: utf-8 -*-
"""
Created on Sun Feb 20 18:11:59 2022

@author: Asma Baccouche
"""
import warnings
import pdb

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
import numpy as np
import tensorflow as tf

np.random.seed(10101)

def classify(task, nb, img, path):
    
    if task == 'birads':
        labels = ['Biradsirads2', 'Birads-3', 'Birads-4', 'Birads-5', 'Birads-6']
       
    elif task == 'shape':
        labels = ['IRREGULAR', 'LOBULATED', 'OVAL', 'ROUND']
        
    else:
        labels = ['Malignant', 'Benign']
        
    p = path + "/"+ task

    interpreter1 = tf.lite.Interpreter(p+'_ResNet50V2_model_quant.tflite')
    interpreter1.allocate_tensors()
    interpreter2 = tf.lite.Interpreter(p+'_ResNet101V2_model_quant.tflite')
    interpreter2.allocate_tensors()
    interpreter3 = tf.lite.Interpreter(p+'_ResNet152V2_model_quant.tflite')
    interpreter3.allocate_tensors()
    
    input_index = interpreter1.get_input_details()[0]["index"]
    output_index = interpreter1.get_output_details()[0]["index"]
     
    interpreter1.set_tensor(input_index, tf.expand_dims(img, axis=0))
    interpreter1.invoke()
    y1 = (interpreter1.get_tensor(output_index)).flatten()
    
    input_index = interpreter2.get_input_details()[0]["index"]
    output_index = interpreter2.get_output_details()[0]["index"]
    interpreter2.set_tensor(input_index, tf.expand_dims(img, axis=0))
    interpreter2.invoke()
    y2 = (interpreter2.get_tensor(output_index)).flatten()
        
    input_index = interpreter3.get_input_details()[0]["index"]
    output_index = interpreter3.get_output_details()[0]["index"]
    interpreter3.set_tensor(input_index, tf.expand_dims(img, axis=0))
    interpreter3.invoke()
    y3 = (interpreter3.get_tensor(output_index)).flatten()
    
    interpreter = tf.lite.Interpreter(p+'_stacked_ResNet_models_quant.tflite')
    interpreter.allocate_tensors()

    input1_index = interpreter.get_input_details()[0]["index"]
    input2_index = interpreter.get_input_details()[1]["index"]
    input3_index = interpreter.get_input_details()[2]["index"]
    output_index = interpreter.get_output_details()[0]["index"]
    
    interpreter.set_tensor(input1_index, tf.expand_dims(y1, axis=0))
    interpreter.set_tensor(input2_index, tf.expand_dims(y2, axis=0))
    interpreter.set_tensor(input3_index, tf.expand_dims(y3, axis=0))
    
    interpreter.invoke()
    predictions = (interpreter.get_tensor(output_index)).flatten()   

    diagnosis = task + ' prediction: ' + labels[predictions.argmax(axis=0)]
    
    return diagnosis


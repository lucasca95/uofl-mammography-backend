# -*- coding: utf-8 -*-
"""
Created on Sun Feb 20 18:11:59 2022

@author: Asma Baccouche
"""
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
import numpy as np
import tensorflow as tf
import keras
from keras.models import Model
from keras.layers import Dense, Dropout
from keras.layers.merge import concatenate
from keras.losses import BinaryCrossentropy, CategoricalCrossentropy
# from keras.optimizers import Adam
from keras.optimizers import adam_v2


np.random.seed(10101)

def define_stacked_model(nb, c, loss_fn, members):
  
    ensemble_outputs = []
    for i in range(len(members)):
        ipt = keras.layers.Input((c))
        #ipt._name = 'ensemble_' + str(i+1) + '_' + ipt.name
        ensemble_outputs.append(ipt)
    
    merge = concatenate(ensemble_outputs)
    hidden = Dense(1000, activation='sigmoid')(merge)   
    hidden2 = Dense(100, activation='relu')(hidden)
    hidden3 = Dense(10, activation='sigmoid')(hidden2)    
    output = Dense(nb, activation='softmax')(hidden3)
    
    model = Model(inputs=ensemble_outputs, outputs=output)
    model.compile(loss=loss_fn,
                  metrics=['accuracy'],
                  optimizer=tf.keras.optimizers.Adam(learning_rate=0.000001))
    return model

def classify(task, nb, img, path):
    
    if task == 'birads':
        labels = ['Biradsirads2', 'Birads-3', 'Birads-4', 'Birads-5', 'Birads-6']
        loss_fn = CategoricalCrossentropy(label_smoothing=0.25)
        c = 1024
    elif task == 'shape':
        labels = ['IRREGULAR', 'LOBULATED', 'OVAL', 'ROUND']
        loss_fn = CategoricalCrossentropy(label_smoothing=0.25)
        c = 100
    else:
        labels = ['Malignant', 'Benign']
        loss_fn = BinaryCrossentropy(label_smoothing=0.25)
        c = 1024
    
    model1 = keras.applications.resnet_v2.ResNet50V2()
    model2 = keras.applications.resnet_v2.ResNet101V2()
    model3 = keras.applications.resnet_v2.ResNet152V2()
    
    models = [model1, model2, model3]
    
    for i in range(len(models)):
        x = models[i].output
        x = Dense(c, activation='relu')(x)
        x = Dropout(0.3)(x)
        predictions = Dense(nb, activation='softmax')(x)
        models[i] = Model(inputs=models[i].input, outputs=predictions)  
        
    p = path + "/"+ task
    
    model1 = models[0]        
    model1.load_weights(p+'_ResNet50V2_model.h5')
    model2 = models[1]       
    model2.load_weights(p+'_ResNet101V2_model.h5')
    model3 = models[2]       
    model3.load_weights(p+'_ResNet152V2_model.h5')
    
    model1 = Model(inputs=model1.input, outputs=model1.layers[-2].output)
    model2 = Model(inputs=model2.input, outputs=model2.layers[-2].output)
    model3 = Model(inputs=model3.input, outputs=model3.layers[-2].output)
    
    y1 = model1.predict(img)
    y2 = model2.predict(img)
    y3 = model3.predict(img)
    
    models = [model1, model2, model3]
        
    filepath = p+"_stacked_ResNet_models.h5"
    stacked_model = define_stacked_model(nb, c, loss_fn, models)
    stacked_model.load_weights(filepath)
    predictions = stacked_model.predict([y1, y2, y3], verbose=0)
    #diagnosis = task + ' prediction: ' + labels[predictions.argmax(axis=1)[0]] + ' with prob ' + str(round(predictions.max()*100, 2)) + " %"
    diagnosis = task + ' prediction: ' + labels[predictions.argmax(axis=1)[0]]
    return diagnosis


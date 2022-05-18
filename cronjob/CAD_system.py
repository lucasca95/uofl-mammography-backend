# -*- coding: utf-8 -*-
"""
Created on Thu Feb 17 10:55:26 2022

@author: User
"""


import warnings, pdb, os, sys
from dotenv import load_dotenv
load_dotenv('../server/.env')


with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)

import cv2, glob
import pydicom as dicom
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
from skimage.io import imsave
from keras.preprocessing.image import load_img, img_to_array
from keras.applications.resnet_v2 import preprocess_input
from detection import detect
from segmentation import segment
from classification import classify


if (len(sys.argv) > 1):

    image_name = sys.argv[1]
    name = image_name[:-4]

    # Revisar la idea de tener carpetas con resultados por paciente adentro de la carpeta Prediction
    foldername = "Prediction"
    try:
        os.mkdir(foldername)
    except:
        print(foldername, "Folder already exists!") 

    # =============================================================================
    #   Convertion from DICOM to png
    # =============================================================================
        
    try:
        file = f"{os.getenv('CRON_IMG_URL')}{image_name}"
        ds = dicom.read_file(file)
        pixel_array_numpy = ds.pixel_array
        image = file.replace('.dcm', '.png')
        cv2.imwrite(image, pixel_array_numpy)

    except:
        print("Dicom file is either corrupted or does not exist")

    # =============================================================================
    #   Preprocessing
    # =============================================================================

    img = cv2.imread(f"{file}")
    try:
        img.shape
    except:
        print(image_name, "image either does not exist or image type is not supported !")
        
    subfoldername = foldername+"/variations"
    try:
        os.mkdir(subfoldername)
    except:
        print("Folder already exists!")     
        

    if len(os.listdir(subfoldername)) == 0:
        for angle in [0,90,180,270]:
            rotated = ndimage.rotate(img, angle)
            rotated = cv2.resize(rotated, (448,448), cv2.INTER_CUBIC)
            cv2.imwrite(subfoldername+"/"+str(angle)+"_"+image_name, rotated)

    try:
        images = glob.glob(subfoldername+"/*.png")
        if len(images) == 0:
            images = glob.glob(subfoldername+"/*.jpg")
    except:       
        print("image either does not exist or image type is not supported!")

    # =============================================================================
    #   Detection (Fusion)
    # ============================================================================= 

    # Specify the path is different than default path
    single_anchors_path = f"{os.getenv('MODELS_FOLDER_URL')}mass_datasets_anchor.txt"
    multiple_anchors_path = f"{os.getenv('MODELS_FOLDER_URL')}all_datasets_anchor.txt"
    single_class_model_path = f"{os.getenv('MODELS_FOLDER_URL')}yolo_mass_trained_weights_final.h5"
    multiple_class_model_path = f"{os.getenv('MODELS_FOLDER_URL')}yolo_all_trained_weights_final.h5"
    single_classes = ['mass']
    multiple_classes = ['mass', 'calcification']

    detection_results = {}
    for image_path in images:
        roi1, detection_label1 = detect(image_path, single_anchors_path, single_classes, single_class_model_path)
        roi2, detection_label2 = detect(image_path, multiple_anchors_path, multiple_classes, multiple_class_model_path)
        
        if roi1 is None and roi2 is None:
            #detection_results[image_path] = (None, None)
            continue
        elif roi1 is not None and roi2 is None:
            detection_results[image_path] = (roi1, detection_label1)
        elif roi2 is not None and roi1 is None:
            detection_results[image_path] = (roi2, detection_label2)
        else:
            score1 = detection_label1.split(' ')[1]
            score2 = detection_label2.split(' ')[1]
            if score1 > score2:
                detection_results[image_path] = (roi1, detection_label1)
            else:
                detection_results[image_path] = (roi2, detection_label2)

    if len(detection_results) > 0:
        angles = {0: 0, 1: 180, 2: 270, 3: 90}

        all_images = list(detection_results)
        all_rois = [elt[0] for elt in list(detection_results.values())]
        all_labels = [elt[1].split(' ')[0] for elt in list(detection_results.values())]
        all_scores = [elt[1].split(' ')[1] for elt in list(detection_results.values())]

        predicted_score = max(all_scores)
        index_max_value = all_scores.index(predicted_score)
        selected_image = Image.open(all_images[index_max_value])
        predicted_roi = selected_image.crop(all_rois[index_max_value])

        shape = all_rois[index_max_value]
        img1 = ImageDraw.Draw(selected_image)  
        img1.rectangle(shape, outline ="red")

        selected_image = selected_image.rotate(angles[index_max_value])
        predicted_roi = predicted_roi.rotate(angles[index_max_value])

        predicted_label = all_labels[index_max_value]
        predicted_roi = predicted_roi.resize((256, 256), Image.ANTIALIAS)
        
        name = image_name[:-4]
        selected_image.save(foldername+"/"+name+"_with_bounding_box.png")
        predicted_roi.save(foldername+"/"+name+"_detected.png")

        print("Detection prediction: ", predicted_label, " with score = ", predicted_score)

        f = open(foldername+"/"+name+"_detection_result.txt", "w+")
        f.write("Detection prediction: " + predicted_label + " with score = " + predicted_score)
        f.close()

        # =============================================================================
        #   Segmentation (Connected ResUnets)
        # ============================================================================= 
        img = cv2.imread(foldername+"/"+name+"_detected.png")
        #enhancement
        gray_img=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        gray_img_eqhist=cv2.equalizeHist(gray_img)
        img = cv2.cvtColor(gray_img_eqhist, cv2.COLOR_GRAY2BGR)
        #end enhancement
        img = img.astype('float32')
        mean = np.mean(img)
        std = np.std(img)
        img -= mean
        img /= std
        img = np.array([img])

        model_path = f"{os.getenv('MODELS_FOLDER_URL')}rwnet_weights.h5"

        img_mask = segment(model_path, img)
        imsave(foldername+"/"+name+"_mask.png", img_mask)
        
        # =============================================================================
        #   Postprocessing 
        # ============================================================================= 
        img_mask = cv2.imread(foldername+"/"+name+"_mask.png", 0)
        _, img_mask = cv2.threshold(img_mask, 127, 255, cv2.THRESH_BINARY)
        pred_contour, _ = cv2.findContours(img_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]
        if len(pred_contour) != 1:
            areas = [cv2.contourArea(c) for c in pred_contour]
            max_index = np.argmax(areas)
            pred_contour=[pred_contour[max_index]]
            
        new_img_mask = np.zeros([256, 256], np.uint8)
        cv2.drawContours(new_img_mask, pred_contour, 0, (255, 255, 255), -1)  

        imsave(foldername+"/"+name+"_mask_postprocessed.png", new_img_mask)

        # =============================================================================
        #   Draw Countour
        # ============================================================================= 

        new_img_mask = cv2.imread(foldername+"/"+name+"_mask_postprocessed.png", 0)
        _, seg_img = cv2.threshold(new_img_mask, 127, 255, cv2.THRESH_BINARY)
        pred_contour, _ = cv2.findContours(seg_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]

        if len(pred_contour) != 1:
            areas = [cv2.contourArea(c) for c in pred_contour]
            max_index = np.argmax(areas)
            pred_contour=[pred_contour[max_index]]

        roi = cv2.imread(foldername+"/"+name+"_detected.png")
        cv2.drawContours(roi, pred_contour, 0, (0, 0, 255), 1)

        cv2.imwrite(foldername+'/'+name+'_countour.png', roi)
        
        # =============================================================================
        #   Masked Roi
        # ============================================================================= 

        roi = cv2.imread(foldername+"/"+name+"_detected.png")
        mask = cv2.imread(foldername+"/"+name+"_mask_postprocessed.png", 0)

        for k in range(256):
            for j in range(256):
                if mask[k, j] == 0:
                    roi[k, j, :] = 0
                    
        cv2.imwrite(foldername+'/'+name+'_segmented.png', roi)

        # =============================================================================
        #   Classification and Diagnosis
        # ============================================================================= 
        img = load_img(foldername+'/'+name+'_segmented.png', target_size=(224, 224))
        img = img_to_array(img)
        img = img.reshape((1, img.shape[0], img.shape[1], img.shape[2]))
        img = preprocess_input(img)

        pathology_diagnosis = classify(task='pathology', nb = 2, img=img, path=os.getenv('MODELS_FOLDER_URL'))
        birads_diagnosis = classify(task='birads', nb = 5, img=img, path=os.getenv('MODELS_FOLDER_URL'))
        shape_diagnosis = classify(task='shape', nb = 4, img=img, path=os.getenv('MODELS_FOLDER_URL'))

        print(pathology_diagnosis)
        print(birads_diagnosis)
        print(shape_diagnosis)

        f = open(foldername+"/"+name+"_classification_result.txt", "a+")
        f.write("Pathology prediction: " + pathology_diagnosis+"\n")
        f.write("BIRADS score prediction: " + birads_diagnosis+"\n")
        f.write("Shape prediction: " + shape_diagnosis+"\n")
        f.close()
        
    else:
        print("Prediction for Mass lesions is not possible, the system could not proceed")
   
else:
    print(f"\nError: some arguments are missing\n")

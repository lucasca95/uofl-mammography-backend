# Backend: Computer-aided Diagnosis (CAD) system for Breast Cancer Analysis
The presented work proposed three main steps to process a mammogram using deep learning architecture model. First, the system should detect the location of abnormalities and distinguish their types to either Mass, Calcification. Next, the system focused on Mass lesions in mammograms and generated a precise contour of the Mass tumors to help determining their malignancy and grading score. Consequently, the ROI of masses were segmented to mask the tissue background and highlight the tumor. Finally, the integrated system predicted the pathology of the detected tumors and classified their BI-RADS score and shape.

1) Detection and Identification of breast abnormalities
We developed a YOLO-based fusion model to detect location and type of abnormal lesions in mammograms. Details are explained in the paper below.

Reference: Baccouche, A., Garcia-Zapirain, B., Olea, C. C., & Elmaghraby, A. S. (2021). Breast lesions detection and classification via yolo-based fusion models. Comput. Mater. Contin., 69, 1407-1425.
https://www.techscience.com/cmc/v69n1/42797

2) Mass Segmentation and Image-to-image translation
We proposed a novel architecture, called Connected-UNets, for mass segmentation and the results were enhanced by adding sysnthtic images generated using CycleGAN. Details are explained in the paper below.

Reference: Baccouche, A., Garcia-Zapirain, B., Castillo Olea, C., & Elmaghraby, A. S. (2021). Connected-UNets: a deep learning architecture for breast mass segmentation. NPJ Breast Cancer, 7(1), 1-12.
https://www.nature.com/articles/s41523-021-00358-x

3) Mass Pathology Classification and Diagnosis
The methodology for the final diagnosis was conducted using a stacked ensemble of ResNets. Details are explained in the paper below.

Reference: Baccouche, A., Garcia-Zapirain, B., & Elmaghraby, A. (2022). An integrated Framework for Breast Mass Classification and Diagnosis using Stacked Ensemble of Residual Neural Networks.
https://assets.researchsquare.com/files/rs-1389924/v1/b7279c30-6023-4d49-86ff-66cf524c5660.pdf?c=1646171041


## Frontend project repository
[Check the frontend](https://github.com/lucasca95/uofl-mammography-frontend)

## Quick start

-- Get models from [here](https://terabox.com/s/1FxeNSQwMbvFlf5rIuCxzcQ) and make sure the extracted data is on /crontab/models

--- Activate virtual environment
```bash
source venv/bin/activate
```

--- Install requirements from file
```bash
pip install -r requirements.txt
```
--- Define system variables
```bash
export FLASK_APP=/system/path/to/app.py
export BASE_URL=/system/path/to/code/base/folder
```

--- Run Flask App
```bash
flask run --host=0.0.0.0 --port=5000
```

--- Deactivate virtual environment (must have been activated first!)
```bash
deactivate
```



## To check
https://keras.io/guides/functional_api/
https://keras.io/api/optimizers/adam/

-- changes: 
    parameter name tf.keras.optimizers.Adam(learning_rate=1e-4)
    use of .env to read paths
    use of tf.keras.layers.BatchNormalization()

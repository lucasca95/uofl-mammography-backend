# Backend: Mammography analysis
Pending...

## Frontend project repository
[Check the frontend](https://github.com/lucasca95/uofl-mammography-frontend)

## Quick start

-- Get models from [here](https://terabox.com/s/1hmhLpCTp_QsxXlLHregapg) and make sure the extracted data is on /crontab/models

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

#!/bin/bash
source "/home/lucascamino/Documentos/Proyectos/mamografias/backend/venv/bin/activate";
cd "/home/lucascamino/Documentos/Proyectos/mamografias/backend/cronjob";

source ../server/.env

tmp_img_path="${SRC_IMG_FOLDER_URL}";
proc_img_path="${CRON_PROC_IMG_URL}";

echo -e "Looking for images in \n\n   ${tmp_img_path}\n"


file_length=$(ls ${tmp_img_path} | wc -l)

if (( $file_length > 0 )); then
    echo "$(ls ${tmp_img_path})";
    echo "There are files to process...";
    
    # echo -n "Proceed? [y/n]: "; read ans;
    files_to_process=$(ls ${tmp_img_path} | cut -d ' ' -f1)
    echo "$files_to_process" | while read line; do
        file_name="${line}"
        echo "${file_name}";
        echo "${tmp_img_path}${file_name}";
        echo "${CRON_IMG_URL}${file_name}";
        echo "${CRON_URL}CAD_system.py";

        mv "${tmp_img_path}${file_name}" "${CRON_IMG_URL}${file_name}"
        python3 "${CRON_URL}CAD_system.py" "${file_name}";
        echo "   Done!"
    done
else
    echo "No images were detected..."
fi

    # echo -n "Proceed? [y/n]: "; read ans;
    # if [[ "${ans}" != "y" ]]; then
    #     return 1;
    # fi

    # echo "Processing.";sleep 0.25s;echo "Processing..";sleep 0.25s;echo "Processing...";sleep 0.25s;
    # echo "Done!"
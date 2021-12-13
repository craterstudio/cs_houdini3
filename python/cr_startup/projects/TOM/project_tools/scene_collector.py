'''
This is a scene collect script for ttv (TOM) project. It is extremly rough and 
it makes very specific assumptions which could easily fail on diferent scenes 
and certainly not work in any other scenario.

USE WITH EXTREME CAUTION!
'''


import os
import sys
import shutil
from datetime import datetime

import hou


COLLECT_TO = "U:/collected"


def get_scene_filelist():
    refs = hou.fileReferences()

    files = set()

    for i in refs:
        files.add(i[1])

    files = list(files)

    return files

def main():

    now = datetime.now()
    now_formated = now.strftime("%Y%m%d")

    collect_root = os.path.join(COLLECT_TO, now_formated)

    if not os.path.isdir(collect_root):
        os.makedirs(collect_root)

    hou_file_path = hou.hipFile.path()
    hou_file = hou.hipFile.basename()

    print("Collecting {}".format(hou_file))

    files = get_scene_filelist()

    # copy dependencies
    for each in files:

        if "$HIPNAME" in each:
            continue

        each = os.path.abspath(each.replace("$HIP", os.environ["HIP"]))

        if each.startswith("Q:"):
            continue

        folder = os.path.dirname(each)
        each_file = os.path.basename(each)

        save_to_folder = os.path.join(collect_root, folder[3:])
        save_to_file = os.path.join(save_to_folder, each_file)

        if not os.path.isdir(save_to_folder):
            os.makedirs(save_to_folder)

        if not os.path.isfile(save_to_file):
            shutil.copy2(each, save_to_folder)

    # copy scene file
    hip_folder = os.path.dirname(hou_file_path)
    hip_save_to_folder = os.path.join(collect_root, hip_folder[3:])
    hip_save_to_file = os.path.join(hip_save_to_folder, hou_file)

    if not os.path.isdir(hip_save_to_folder):
        os.makedirs(hip_save_to_folder)

    if not os.path.isfile(hip_save_to_file):
        shutil.copy2(hou_file_path, hip_save_to_folder)

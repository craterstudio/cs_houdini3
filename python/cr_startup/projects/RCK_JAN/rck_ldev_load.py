import hou
import os
import rck_utils
from nodesearch import parser


def main():

    reload(rck_utils)
    proj_path = os.environ["CRX_PROJECTPATH"]
    seq = os.environ["CRX_SCENE_PROJECT_PATH"].lstrip(proj_path).split("/")[1]
    shot = os.environ["CRX_ENTITY"]
    shot_dir = proj_path+"/sequences/"+seq+"/"+shot
    found_files = os.listdir(shot_dir+"/LYT/publish/houdini/")
    v = 0
    ver_index = 0
    i = 0
    for file in found_files:
        ver_string = ((file.rstrip(".hip")).split("_"))[-1]
        if ver_string.startswith("v"):
            try:
                ver_int = int(ver_string.lstrip("v"))
                if ver_int > v:
                    v = ver_int
                    ver_index = i
            except:
                print "invalid publised file: " + file
        i += 1

    latest_publish = found_files[ver_index]
    publish_ver = ((latest_publish.rstrip(".hip")).split("_"))[-1]
    metadata = rck_utils.get_metadata(shot_dir+"/LYT/publish/houdini/"+latest_publish)

    # print latest_publish

    camera_path = metadata["camera_alembic_path"]
    anim_cache_path = metadata["anim_cache_path"]
    ocean_spectrum_ver = metadata["ldev_ver"]

    root = hou.node("/obj")

    #import camera
    cam_name = shot+"_cam_"+publish_ver
    existing_cam = None
    try:
        matcher = parser.parse_query(shot+"_cam_*")
        existing_cam = matcher.nodes(root, recursive=False)[0]
    except:
        print "no existing camera_found, creating camera..."

    if existing_cam:
        cam = existing_cam
    else:
        cam = root.createNode("alembicarchive", cam_name)
        cam.setName(cam_name)

    cam.parm("fileName").set(camera_path)
    cam.parm("buildHierarchy").pressButton()
    next_pos = (cam.position()[0], cam.position()[1]-1)

    print "camera import sucess"

    #import ocean
    hou.hda.installFile("S:/PRODUCTIONS/RCK_JAN/assets/HDA/CR_ocean_ldev.hda")
    existing_ocean = None
    try:
        matcher = parser.parse_query("cr_ocean_ldev")
        existing_ocean = matcher.nodes(root, recursive=False)[0]
    except:
        print "no existing ocean found, creating ocean..."

    if existing_ocean:
        ocean_node = existing_ocean
    else:
        ocean_node = root.createNode("cr_ocean_ldev", "cr_ocean_ldev")
        ocean_node.setPosition(next_pos)

    index = ocean_node.parm("ver").menuItems().index(
        ocean_spectrum_ver) if ocean_spectrum_ver in ocean_node.parm("ver").menuItems() else None
    if index is not None:
        ocean_node.parm("ver").set(index)

    next_pos = (ocean_node.position()[0], ocean_node.position()[1]-1)

    print "ocean load sucess"

    #import ship

    hou.hda.installFile("S:/PRODUCTIONS/RCK_JAN/assets/Prop/boat/LDV/work/houdini/hda/RCK_ship_ldev.hda")
    existing_ship = None
    try:
        matcher = parser.parse_query("RCK_ship_ldev")
        existing_ship = matcher.nodes(root, recursive=False)[0]
    except:
        print "no exising ship found, creating ship..."

    if existing_ship:
        ship_node = existing_ship
    else:
        ship_node = root.createNode("RCK_ship_ldev", "RCK_ship_ldev")
        ship_node.setPosition(next_pos)

    index = ship_node.parm("ver").menuItems().index(
        publish_ver) if publish_ver in ship_node.parm("ver").menuItems() else None
    if index is not None:
        ship_node.parm("ver").set(index)

    print "ship load sucess"

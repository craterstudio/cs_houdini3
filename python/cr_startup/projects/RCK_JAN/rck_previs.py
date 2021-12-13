import hou
import os
import _alembic_hom_extensions as abc


def main():

    hip = os.environ["HIP"]
    shot = os.environ["CRX_ENTITY"]

    previs_path = "z:/PRODUCTIONS/RCK_JAN/sequences/sc01/"+shot+"/PRV/publish/alembic/"
    previs_env_path = previs_path+"previs_env.abc"
    previs_ship_path = previs_path+"previs_ship.abc"
    previs_cam_path = previs_path+"previs_cam.abc"

    root = hou.node("/obj")
    previs_cam = root.createNode("alembicarchive", "previs_cam")
    previs_cam.parm("fileName").set(previs_cam_path)
    previs_cam.parm("buildHierarchy").pressButton()
    previs_cam_pos = previs_cam.position()

    null = root.createNode("null")
    null.parm("scale").set(0.01)
    previs_cam.setFirstInput(null)
    null.setPosition((previs_cam_pos[0], previs_cam_pos[1]+1))

    previs_env = root.createNode("geo", "previs_env")
    previs_env.setPosition((previs_cam_pos[0]+2, previs_cam_pos[1]))
    env_alembic_geo = previs_env.createNode("alembic", "env_alembic")
    env_alembic_geo.parm("fileName").set(previs_env_path)
    transform = previs_env.createNode("xform")
    transform.parm("scale").set(0.01)
    transform.setFirstInput(env_alembic_geo)
    previs_env.layoutChildren()
    transform.setDisplayFlag(1)

    previs_ship = root.createNode("geo", "previs_ship")
    previs_ship.setPosition((previs_cam_pos[0]+4, previs_cam_pos[1]))
    ship_alembic_geo = previs_ship.createNode("alembic", "ship_alembic")
    ship_alembic_geo.parm("fileName").set(previs_ship_path)
    transform = previs_ship.createNode("xform")
    transform.parm("scale").set(0.01)
    transform.setFirstInput(ship_alembic_geo)
    previs_ship.layoutChildren()
    transform.setDisplayFlag(1)

    previs_global_tr = root.createNode("null", "previs_tr")
    previs_global_tr.setPosition((previs_cam_pos[0]+2, previs_cam_pos[1]+4))
    previs_env.setFirstInput(previs_global_tr)
    previs_ship.setFirstInput(previs_global_tr)
    null.setFirstInput(previs_global_tr)

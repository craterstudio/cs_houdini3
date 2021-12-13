import os
import hou
import sgtk
import json


logger = sgtk.platform.get_logger(__name__)


def publish_layout_scene():
    engine = sgtk.platform.current_engine()
    tk = engine.sgtk
    context = engine.context
    publish_app = engine.apps.get("tk-multi-publish2")
    if not publish_app:
        raise Exception("The publisher is not configured for this context.")

    print("")
    print("-" * 40)
    print("publish_layout_scene()")
    print("-" * 40)

    print("Exporting camera...")
    shot = os.environ["CRX_ENTITY"]
    fstart = hou.playbar.frameRange()[0]
    hou.setFrame(fstart)

    root = hou.node("/obj")
    cam = hou.node("/obj/cam_main")
    # Get Camera parent nodes
    listCameraNodes = '{}'.format(cam.name())
    for i in cam.inputAncestors():
        listCameraNodes += ' {}'.format(i.name())

    out = hou.node("/out")
    camera_rop = out.createNode("sgtk_alembic")
    camera_rop.setName("pub_camera")

    camera_rop.parm("trange").set(1)
    camera_rop.parm("objects").set(listCameraNodes)
    camera_rop.parm("execute").pressButton()

    alembicnode_app = engine.apps["tk-houdini-alembicnode"]
    camera_output = alembicnode_app.get_output_path(camera_rop)
    scenefile_path = hou.hipFile.path()

    camera_rop.destroy()

    # --------------------------------------------------------------------------
    # metadata
    print("Exporting ship animation...")

    ldev_ver = next(iter([i.parm("ver").evalAsString() for i in hou.node(
        "/obj").children() if i.type().name() == "cr_ocean_ldev"]), None)

    ship_rig_node = next(iter([i for i in hou.node(
        "/obj").children() if i.type().name() == "RCK_ship_rig"]), None)
    anim_cache_path = next(iter([i.parm("sopoutput").evalAsString() for i in hou.node(
        "/obj").children() if i.type().name() == "RCK_ship_rig"]), None)

    if not ldev_ver:
        raise Exception("ldev_ver parameter unknown.")

    if not ship_rig_node:
        raise Exception("ship_rig_node not found in scene.")

    anim_cache_path = ship_rig_node.parm("sopoutput").evalAsString()
    if not anim_cache_path:
        raise Exception("anim_cache_path parameter unknown.")

    ship_rig_node.parm("execute").pressButton()
    if not os.path.isfile(anim_cache_path):
        raise Exception("Animation alembic file not found on disc.")

    print("Compiling metadata...")
    metadata = {
        "ldev_ver": ldev_ver,
        "anim_cache_path": anim_cache_path,
        "camera_alembic_path": camera_output,
    }

    # --------------------------------------------------------------------------
    # publish

    print("Preparing publish...")
    manager = publish_app.create_publish_manager()
    collect = manager.collect_session()
    print("Collected: {}".format(collect))

    publish_path = None
    # set only session items active (only publish houdini session)
    for session in manager.tree.root_item.children:
        if session.type == "houdini.session":
            print("    > Publish item: {}".format(session))

            session.active = True
            publish_task = None
            for task in session.tasks:
                if task.name == "Publish to Shotgun":
                    publish_task = task
                    task.active = True

            if not publish_task:
                raise Exception("publish_task not found.")

            publish_template_name = publish_task.plugin.settings["Publish Template"].value
            print("    > Publish template: {}".format(publish_template_name))

            publish_template = tk.templates.get(publish_template_name)
            print("    > Publish template: {}".format(publish_template))

            fields = context.as_template_fields(publish_template)
            version = publish_app.util.get_version_number(scenefile_path)
            print("    > Publish fields: {}".format(fields))

            fields.update({"version": version})
            publish_path = publish_template.apply_fields(fields)
            print("    > Publish path: {}".format(publish_path))

            sg_metadata = json.dumps(metadata)
            session.properties.publish_fields = {"sg_metadata": sg_metadata}
            print("    > Publish metadata: {}".format(sg_metadata))

        else:
            session.active = False
            for task in session.tasks:
                task.active = False

    if not publish_path:
        raise Exception("Publish path has not been compiled.")

    print("Validating...")
    # validate the items to publish
    tasks_failed_validation = manager.validate()

    # oops, some tasks are invalid. see if they can be fixed
    if tasks_failed_validation:
        raise Exception, "Failed to validate tasks: {}".format(tasks_failed_validation)

    print("Publishing...")
    # all good. let's publish and finalize
    try:
        manager.publish()
        manager.finalize()
    except Exception as error:
        logger.error("There was trouble trying to publish!")
        logger.error("Error: %s", error)

    print("Done.")

# ------------------------------------------------------------------------------


def main():
    # get current step
    context = sgtk.platform.current_engine().context
    step = context.step or None

    if step:
        step_name = step.get("name")

        if step_name == "Layout":
            publish_layout_scene()

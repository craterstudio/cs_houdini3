'''
Automaticaly sets up the scene for TOM project.

'''
import os
import re
import hou
import glob
import traceback
import hdefereval


def update_aov_list_func():
    try:
        from project_tools import import_rop_nodes
        reload(import_rop_nodes)
        print("Updating AOVs...")
        import_rop_nodes.update_aov_list()
        print("Done.")
    except Exception as err:
        print("Could not update AOVs...")
        print(err.args)
        traceback.print_exc()


def check_if_latest_character_alembic():
    light_rig_node = hou.node("/obj/light_rig")

    if light_rig_node:
        loaded_alembic = light_rig_node.parm("charmain_LOAD").eval()
        loaded_alembic = os.path.abspath(loaded_alembic)

        alembic_dir = os.path.dirname(loaded_alembic)
        loaded_alembic_basename = os.path.basename(loaded_alembic)

        loaded_alembic_name, _ = os.path.splitext(loaded_alembic_basename)
        pattern = r"^(.+__CHARMAIN)(_CR)?([0-9]+)?$"
        match = re.match(pattern, loaded_alembic_name)

        if match:
            name = match.group(1)
            msg = ""

            latest = None
            cr = None
            num = None

            for file in glob.glob(alembic_dir + "\\" + name + "*.abc"):
                alembic_file = os.path.basename(file)
                alembic_name, _ = os.path.splitext(alembic_file)

                match = re.match(pattern, alembic_name)
                if match:
                    cr = match.group(2) or None
                    num = match.group(3) or None
                    latest = file

            if cr:
                exporter = "Crater Studio"
            else:
                exporter = "Poster Studio"

            if latest:
                if loaded_alembic.replace("\\", "/") != latest.replace("\\", "/"):
                    msg += "There is a newer version of character alembic file.\n"
                    msg += "Vendor: {}\n".format(exporter)
                    msg += "Number: {}\n".format(str(num))
                    msg += "\n"
                    msg += "Do you wish to update?"

                    if hou.ui.displayConfirmation(msg, title="TOM Notification"):
                        relative_path = os.path.relpath(
                            latest, os.environ["HIP"])
                        relative_path = "$HIP" + "/" + \
                            relative_path.replace("\\", "/")

                        try:
                            light_rig_node.parm(
                                "charmain_LOAD").set(relative_path)
                            hou.ui.displayMessage(
                                "Alembic successfully replaced.")
                        except:
                            hou.ui.displayMessage(
                                "Sorry, could not replace alembic.")


def check_if_latest_propenv_alembic():
    obj = hou.node("/obj")

    asset_nodes = list()
    children = obj.allSubChildren()
    for child in children:
        if child.name().startswith("ttv_envint") or child.name().startswith("ttv_prop"):
            asset_nodes.append(child)

    replace_data = dict()
    for each in asset_nodes:
        fileName = each.parm("fileName")
        if fileName:
            abc_path = os.path.abspath(fileName.evalAsString())
            abc_name = os.path.basename(abc_path)
            abc_dir = os.path.abspath(
                os.path.dirname(os.path.dirname(abc_path)))
            directories = os.listdir(abc_dir)
            pattern = r"^v[0-9]{0,3}$"
            versions = [i for i in directories if re.match(pattern, i)]

            if versions:
                current = os.path.basename(os.path.dirname(abc_path))
                latest = max(versions, key=lambda s: int(s[1:]))

                if current != latest:
                    latest_file = os.path.join(abc_dir, latest, abc_name)

                    if os.path.isfile(latest_file):
                        replace_data[each] = {
                            "current_version": current,
                            "latest_version": latest,
                            "current_file": abc_path,
                            "latest_file": latest_file
                        }

    if replace_data:
        found = len(replace_data)

        details = ""
        for k, v in replace_data.items():
            details += "Node:\n\t{node}\n\tCurrent: {current}\n\tLatest: {latest}\n\n".format(
                node=k.name(), current=v["current_version"], latest=v["latest_version"])

        text = "Found {} asset nodes with newer versions of animation data.\nDo you wish to replace them?".format(
            found)

        if hou.ui.displayConfirmation(text, details=details, title="Replace Debug Nodes"):
            try:
                for node, data in replace_data.items():
                    hip_folder = os.path.dirname(hou.hipFile.path())
                    rel_path = "$HIP/" + \
                        os.path.relpath(data["latest_file"],
                                        hip_folder).replace("\\", "/")
                    node.parm("fileName").set(rel_path)
                hou.ui.displayMessage("Alembics successfully replaced.")
            except:
                hou.ui.displayMessage("Sorry, could not replace alembics.")


def main():

    # update AOV's on rop nodes
    hdefereval.executeDeferred(update_aov_list_func)

    # check if loaded character alembic is the latest one
    hdefereval.executeDeferred(check_if_latest_character_alembic)

    # check if loaded props/environment asset alembic is the latest one
    hdefereval.executeDeferred(check_if_latest_propenv_alembic)

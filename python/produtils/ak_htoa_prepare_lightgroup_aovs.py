import os
import re
import hou
import htoa


LIGHT_AOVS = [
    "RGBA",
    "diffuse_direct",
    "diffuse_indirect",
    "specular_direct",
    "specular_indirect",
    "coat_direct",
    "coat_indirect",
    "sss_direct",
    "sss_indirect",
    "transmission_direct",
    "transmission_indirect",
    "sheen_direct",
    "sheen_indirect",
    "volume_direct",
    "volume_indirect"
]


def run():
    selected_nodes = hou.selectedNodes()

    if not len(selected_nodes) == 1:
        msg = "Select one arnold ROP!"
        print(msg)
        hou.ui.displayMessage(msg)
        return

    selected_node = selected_nodes[0]

    if not selected_node.type().name() in ["arnold", "sgtk_arnold"]:
        msg = "Please select one Arnold ROP node."
        print(msg)
        hou.ui.displayMessage(msg)
        return

    print("Setting up light group AOVs for: '{}'".format(selected_node))

    # get light groups in scene
    light_groups = htoa.properties.lightGroups()
    if not light_groups:
        msg = "No light groups are defined."
        print(msg)
        hou.ui.displayMessage(msg)
        return

    ar_aovs = selected_node.parm("ar_aovs")
    aov_parm_instances = ar_aovs.multiParmInstances()

    current_aovs = list()
    pattern = r"^ar_aov_label[0-9]{1,4}$"
    for each in aov_parm_instances:
        name = each.name()
        if re.match(pattern, name):
            current_aovs.append(each.rawValue())

    missing = list()
    for aov in LIGHT_AOVS:
        if aov in current_aovs:
            for grp in light_groups:
                light_aov_name = aov + "_" + grp
                if not light_aov_name in current_aovs:
                    missing.append(light_aov_name)

    if missing:
        num_of_aovs = ar_aovs.evalAsInt()
        for aov in missing:
            print("Adding AOV: {}".format(aov))
            index = num_of_aovs

            # create aov
            ar_aovs.insertMultiParmInstance(index)

            # set label
            label = selected_node.parm("ar_aov_label{}".format(index + 1))
            label.set(aov)

            num_of_aovs += 1

        hou.ui.displayMessage("Following AOVs have been created:\n\n  - {}".format("\n  - ".join(missing)))

    else:
        hou.ui.displayMessage("No need to do anything.")


def main():
    run()

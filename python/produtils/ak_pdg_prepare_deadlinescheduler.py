import os
import re
import traceback

import hou


PARAMETER_MAP = {
    "deadline_repository": "",
    "deadline_connection_type": "Direct",
    "overrideremoterootpath": False,
    "pdg_workingdir": "$HIP",
    "deadline_hfs": "$HFS",
    "deadline_python": "$HFS/python27/python\$PDG_EXE",
    "deadline_jobname": "PDG $OS $HIPNAME",
    "deadline_jobpool": "3d",
    "deadline_submitjobusemqspecs": 1,
    "deadline_verboselog": 1,
    "deadline_pdgmquseip": True,
    "deadline_jobbatchname": "PDG $HIPNAME \$DL_TIME",
    "deadline_mqjobbatchname": "PDG $HIPNAME \$DL_TIME",
    "mqaddr": "192.168.70.128",
    "taskcallbackport": "53444",
    "mqrelayport": "53444",
    "mqusage": 2,
    "deadline_mqjobpool": "3d",
    "deadline_envmulti": [
        {
            "deadline_envname": "NETWORK_COLOR",
            "deadline_envvalue": "$NETWORK_COLOR"
        },
        {
            "deadline_envname": "NETWORK_PIPELINE_ROOT",
            "deadline_envvalue": "$NETWORK_PIPELINE_ROOT"
        },
        {
            "deadline_envname": "NETWORK_REPO_CONFIG_ROOT",
            "deadline_envvalue": "$NETWORK_REPO_CONFIG_ROOT"
        },
        {
            "deadline_envname": "NETWORK_RESOURCES",
            "deadline_envvalue": "$NETWORK_RESOURCES"
        },
        {
            "deadline_envname": "OCIO",
            "deadline_envvalue": "$OCIO"
        }
    ],
    "deadline_pluginfilekvpair": [
        {
            "deadline_pluginfilekey": "Version",
            "deadline_pluginfilevalue": "$CRX_APP_VERSION"
        },
        {
            "deadline_pluginfilekey": "HostIP",
            "deadline_pluginfilevalue": "$CRX_HOST_IP"
        }
    ]
}


def run():
    selected_nodes = hou.selectedNodes()

    if not len(selected_nodes) == 1:
        msg = "Please select a single node."
        print(msg)
        hou.ui.displayMessage(msg)
        return

    selected_node = selected_nodes[0]

    if not selected_node.type().name() == "deadlinescheduler":
        msg = "Please select one deadlinescheduler node."
        print(msg)
        hou.ui.displayMessage(msg)
        return

    print("Setting up deadlinescheduler node: '{}'".format(selected_node))

    for k, v in PARAMETER_MAP.items():
        if isinstance(v, list):
            print("INFO: Setting parameter '{}' of type '{}'.".format(k, type(v)))
            multiparm_instances = selected_node.parm(k).multiParmInstances()

            for item in v:
                item_set = False

                found_p = [i for i in multiparm_instances if i.unexpandedString() in item.values()]

                for p in found_p:
                    pattern = r"^(.*?)(\d+)$"
                    inst_name_full = p.name()
                    inst_name, inst_index = re.match(pattern, inst_name_full).groups()

                    for key, value in item.items():
                        try:
                            selected_node.parm(key + str(inst_index)).set(value)
                        except Exception as err:
                            print("ERROR: Could not set parameter '{}' to '{}'.".format(key, value))
                            print(err.message)
                            print(traceback.format_exc())

                        item_set = True

                if not item_set:
                    last_index = selected_node.parm(k).evalAsInt()
                    selected_node.parm(k).insertMultiParmInstance(last_index)

                    for key, value in item.items():
                        try:
                            selected_node.parm(key + str(last_index + 1)).set(value)
                        except Exception as err:
                            print("ERROR: Could not set parameter '{}' to '{}'.".format(key, value))
                            print(err.message)
                            print(traceback.format_exc())

        elif isinstance(v, bool):
            print("INFO: Setting parameter '{}' of type '{}'.".format(k, type(v)))
            try:
                selected_node.parm(k).set(v)
            except Exception as err:
                print("ERROR: Could not set parameter '{}' to '{}'.".format(k, v))
                print(err.message)
                print(traceback.format_exc())

        elif isinstance(v, (str, int)):
            print("INFO: Setting parameter '{}' of type '{}'.".format(k, type(v)))
            try:
                selected_node.parm(k).set(v)
            except Exception as err:
                print("ERROR: Could not set parameter '{}' to '{}'.".format(k, v))
                print(err.message)
                print(traceback.format_exc())

        else:
            print("WARNING: Type for parameter '{}' not supported.".format(k))

def main():
    run()

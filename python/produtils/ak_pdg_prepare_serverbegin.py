import os
import re
import hou


NODE_SETUP_MAP = {
    "houdiniserver": {
        "parms": [
            ("timeout", 180),
            # ("serverbinary", "$NETWORK_PROCESS_BAT"),
            ("serverbinary", "$HFS/bin/hython.exe"),
        ],
        "env_node_name": "hython_environment",
        "env": [
            ("PILOTPDG_ENABLED", "0"),
            ("USE_PROCESS_APP_NAME", "Hython"),
            ("USE_PROCESS_APP_VERSION", "$PROCESS_APP_VERSION"),
            ("USE_PROCESS_APP_VARIANT", "regular"),
            ("USE_PROCESS_BATCH_MODE", "1"),
            ("USE_PROCESS_START_MODE", "special"),
        ],
    }
}


def run(node):
    setup_map = NODE_SETUP_MAP[node.type().name()]

    # set parameters
    for parm in setup_map["parms"]:
        if parm[0] in [i.name() for i in node.parms()]:
            node.parm(parm[0]).set(parm[1])

    # insert environmentedit node before server begin
    env_edit = node.parent().createNode("environmentedit")
    env_edit.setName(setup_map["env_node_name"], unique_name=True)

    input_con = None
    if node.inputConnections():
        input_con = node.inputConnections()[0].inputItem()

    node.setInput(0, env_edit)
    if input_con:
        env_edit.setInput(0, input_con)

    # set environment variables
    for env in setup_map["env"]:
        index = env_edit.parm("environment").eval()

        value_type = "String"
        value_parm = "strvarvalue"
        if isinstance(env[1], int):
            value_type = "Integer"
            value_parm = "intvarvalue"
        if isinstance(env[1], float):
            value_type = "Float"
            value_parm = "floatvarvalue"

        env_edit.parm("environment").insertMultiParmInstance(index)
        env_edit.parm("varname{}".format(index + 1)).set(env[0])
        env_edit.parm("vartype{}".format(index + 1)).set(
            env_edit.parm("vartype{}".format(index + 1)).menuLabels().index(value_type)
        )
        env_edit.parm("{}{}".format(value_parm, index + 1)).set(env[1])

        # move env node above server begin node
        env_edit.setPosition((node.position()[0], node.position()[1] + 1))

def main():

    # get selected nodes
    selected = hou.selectedNodes()

    if len(selected) != 1:
        hou.ui.displayMessage("Please select Server Begin node.",
                              severity=hou.severityType.Warning)
        return

    selected = selected[0]

    if selected.type().name() not in NODE_SETUP_MAP.keys():
        hou.ui.displayMessage("Node type '{}' is not supported.".format(selected.type().name()),
                              severity=hou.severityType.Warning)
        return

    run(selected)

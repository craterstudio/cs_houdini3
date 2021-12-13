import os
import re
import hou

from collections import OrderedDict


DEFAULT_ARNOLD_AOVS = [
    {
        "name": "beauty",
        "parms": [
            ("ar_enable_aov", True),
            ("ar_aov_label", "beauty"),
            ("ar_aov_lpe_enable", True),
            ("ar_aov_lpe", "C.*"),
            ("ar_aov_separate", True),
            ("ar_aov_type", "RGBA"),
            ("sgtk_aov_name", "beauty"),
        ],
    },

    {"name": "direct", "parms": [("ar_enable_aov", True), ("ar_aov_label", "direct"), ("ar_aov_separate", True)]},
    {"name": "indirect", "parms": [("ar_enable_aov", True), ("ar_aov_label", "indirect"), ("ar_aov_separate", True)]},
    {"name": "emission", "parms": [("ar_enable_aov", True), ("ar_aov_label", "emission"), ("ar_aov_separate", True)]},
    {"name": "background", "parms": [("ar_enable_aov", True), ("ar_aov_label", "background"), ("ar_aov_separate", True)]},
    {"name": "sss", "parms": [("ar_enable_aov", True), ("ar_aov_label", "sss"), ("ar_aov_separate", True)]},
    {"name": "volume", "parms": [("ar_enable_aov", True), ("ar_aov_label", "volume"), ("ar_aov_separate", True)]},
    {"name": "albedo", "parms": [("ar_enable_aov", True), ("ar_aov_label", "albedo"), ("ar_aov_separate", True)]},

    {"name": "diffuse_direct", "parms": [("ar_enable_aov", True), ("ar_aov_label", "diffuse_direct"), ("ar_aov_separate", True)]},
    {"name": "diffuse_indirect", "parms": [("ar_enable_aov", True), ("ar_aov_label", "diffuse_indirect"), ("ar_aov_separate", True)]},
    {"name": "diffuse_albedo", "parms": [("ar_enable_aov", True), ("ar_aov_label", "diffuse_albedo"), ("ar_aov_separate", True)]},

    {"name": "specular_direct", "parms": [("ar_enable_aov", True), ("ar_aov_label", "specular_direct"), ("ar_aov_separate", True)]},
    {"name": "specular_indirect", "parms": [("ar_enable_aov", True), ("ar_aov_label", "specular_indirect"), ("ar_aov_separate", True)]},
    {"name": "specular_albedo", "parms": [("ar_enable_aov", True), ("ar_aov_label", "specular_albedo"), ("ar_aov_separate", True)]},

    {"name": "coat_direct", "parms": [("ar_enable_aov", True), ("ar_aov_label", "coat_direct"), ("ar_aov_separate", True)]},
    {"name": "coat_indirect", "parms": [("ar_enable_aov", True), ("ar_aov_label", "coat_indirect"), ("ar_aov_separate", True)]},
    {"name": "coat_albedo", "parms": [("ar_enable_aov", True), ("ar_aov_label", "coat_albedo"), ("ar_aov_separate", True)]},

    {"name": "sheen_direct", "parms": [("ar_enable_aov", True), ("ar_aov_label", "sheen_direct"), ("ar_aov_separate", True)]},
    {"name": "sheen_indirect", "parms": [("ar_enable_aov", True), ("ar_aov_label", "sheen_indirect"), ("ar_aov_separate", True)]},
    {"name": "sheen_albedo", "parms": [("ar_enable_aov", True), ("ar_aov_label", "sheen_albedo"), ("ar_aov_separate", True)]},

    {"name": "transmission_direct", "parms": [("ar_enable_aov", True), ("ar_aov_label", "transmission_direct"), ("ar_aov_separate", True)]},
    {"name": "transmission_indirect", "parms": [("ar_enable_aov", True), ("ar_aov_label", "transmission_indirect"), ("ar_aov_separate", True)]},
    {"name": "transmission_albedo", "parms": [("ar_enable_aov", True), ("ar_aov_label", "transmission_albedo"), ("ar_aov_separate", True)]},

    {"name": "sss_direct", "parms": [("ar_enable_aov", True), ("ar_aov_label", "sss_direct"), ("ar_aov_separate", True)]},
    {"name": "sss_indirect", "parms": [("ar_enable_aov", True), ("ar_aov_label", "sss_indirect"), ("ar_aov_separate", True)]},
    {"name": "sss_albedo", "parms": [("ar_enable_aov", True), ("ar_aov_label", "sss_albedo"), ("ar_aov_separate", True)]},

    {"name": "volume_direct", "parms": [("ar_enable_aov", True), ("ar_aov_label", "volume_direct"), ("ar_aov_separate", True)]},
    {"name": "volume_indirect", "parms": [("ar_enable_aov", True), ("ar_aov_label", "volume_indirect"), ("ar_aov_separate", True)]},
    {"name": "volume_albedo", "parms": [("ar_enable_aov", True), ("ar_aov_label", "volume_albedo"), ("ar_aov_separate", True)]},

    {"name": "Z", "parms": [("ar_enable_aov", True), ("ar_aov_label", "Z"), ("ar_aov_separate", True)]},
    {"name": "P", "parms": [("ar_enable_aov", True), ("ar_aov_label", "P"), ("ar_aov_separate", True)]},
    {"name": "Pref", "parms": [("ar_enable_aov", True), ("ar_aov_label", "Pref"), ("ar_aov_separate", True)]},
    {"name": "N", "parms": [("ar_enable_aov", True), ("ar_aov_label", "N"), ("ar_aov_separate", True)]},
    {"name": "opacity", "parms": [("ar_enable_aov", True), ("ar_aov_label", "opacity"), ("ar_aov_separate", True)]},
    {"name": "shadow_matte", "parms": [("ar_enable_aov", True), ("ar_aov_label", "shadow_matte"), ("ar_aov_separate", True)]},

    {
        "name": "crypto_asset",
        "parms": [
            ("ar_enable_aov", True),
            ("ar_aov_label", "crypto_asset"),
            ("ar_aov_separate", True),
        ],
        "shader": [
            {
                "name": "aiCryptomatte",
                "type": "arnold::cryptomatte",
                "output": "rgba",
                "input": {"node": "OUT_aov", "input_name": "aov_shader#"},
                "parms": [],
            },
        ],
    },
    {
        "name": "crypto_object",
        "parms": [
            ("ar_enable_aov", True),
            ("ar_aov_label", "crypto_object"),
            ("ar_aov_separate", True),
        ],
        "shader": [
            {
                "name": "aiCryptomatte",
                "type": "arnold::cryptomatte",
                "output": "rgba",
                "input": {"node": "OUT_aov", "input_name": "aov_shader#"},
                "parms": [],
            },
        ],
    },
    {
        "name": "crypto_material",
        "parms": [
            ("ar_enable_aov", True),
            ("ar_aov_label", "crypto_material"),
            ("ar_aov_separate", True),
        ],
        "shader": [
            {
                "name": "aiCryptomatte",
                "type": "arnold::cryptomatte",
                "output": "rgba",
                "input": {"node": "OUT_aov", "input_name": "aov_shader#"},
                "parms": [],
            },
        ],
    },

]

ADDITIONAL_ARNOLD_AOVS = [
    {
        "name": "AO",
        "parms": [
            ("ar_enable_aov", True),
            ("ar_aov_label", "AO"),
            ("ar_aov_separate", True),
        ],
        "shader": [
            {
                "name": "aiAO_write_rgb",
                "type": "arnold::aov_write_rgb",
                "output": "shader",
                "input": {"node": "OUT_aov", "input_name": "aov_shader#"},
                "parms": [
                    ("aov_name", "AO"),
                ],
            },
            {
                "name": "aiAO",
                "type": "arnold::ambient_occlusion",
                "output": "rgb",
                "input": {"node": "aiAO_write_rgb", "input_name": "aov_input"},
                "parms": [],
            },
        ],
    },
    {
        "name": "UV",
        "parms": [
            ("ar_enable_aov", True),
            ("ar_aov_label", "UV"),
            ("ar_aov_separate", True),
        ],
        "shader": [
            {
                "name": "aiUV_write_rgb",
                "type": "arnold::aov_write_rgb",
                "output": "shader",
                "input": {"node": "OUT_aov", "input_name": "aov_shader#"},
                "parms": [
                    ("aov_name", "UV"),
                ],
            },
            {
                "name": "aiUV",
                "type": "arnold::utility",
                "output": "rgb",
                "input": {"node": "aiUV_write_rgb", "input_name": "aov_input"},
                "parms": [
                    ("color_mode", "uv"),
                    ("shade_mode", "flat"),
                ],
            },
        ],
    },
    {
        "name": "Fresnel",
        "parms": [
            ("ar_enable_aov", True),
            ("ar_aov_label", "fresnel"),
            ("ar_aov_separate", True),
        ],
        "shader": [
            {
                "name": "aiFresnel_write_rgb",
                "type": "arnold::aov_write_rgb",
                "output": "shader",
                "input": {"node": "OUT_aov", "input_name": "aov_shader#"},
                "parms": [
                    ("aov_name", "fresnel"),
                ],
            },
            {
                "name": "aiFresnel",
                "type": "arnold::utility",
                "output": "rgb",
                "input": {"node": "aiFresnel_write_rgb", "input_name": "aov_input"},
                "parms": [
                    ("color_mode", "color"),
                    ("shade_mode", "ndoteye"),
                ],
            },
        ],
    },
    {
        "name": "Curvature",
        "parms": [
            ("ar_enable_aov", True),
            ("ar_aov_label", "curvature"),
            ("ar_aov_separate", True),
        ],
        "shader": [
            {
                "name": "aiCurvature_write_rgb",
                "type": "arnold::aov_write_rgb",
                "output": "shader",
                "input": {"node": "OUT_aov", "input_name": "aov_shader#"},
                "parms": [
                    ("aov_name", "curvature"),
                ],
            },
            {
                "name": "aiCurvature",
                "type": "arnold::curvature",
                "output": "rgb",
                "input": {"node": "aiCurvature_write_rgb", "input_name": "aov_input"},
                "parms": [
                    ("output", "both"),
                    ("radius", 1),
                ],
            },
        ],
    },
]


# ------------------------------------------------------------------------------
# Arnold

def create_arnold_aovs(node, additional=False):

    node_type = node.type().name()

    ar_picture = node.parm("ar_picture").eval()
    if ar_picture in ["", "ip"]:
        print("Please fill in Output Picture parameter.")
        return

    ar_aovs = node.parm("ar_aovs")

    index = ar_aovs.evalAsInt()

    if additional:
        aovs = ADDITIONAL_ARNOLD_AOVS
    else:
        aovs = DEFAULT_ARNOLD_AOVS

    for each in aovs:
        # create aov
        ar_aovs.insertMultiParmInstance(index)
        number = index + 1

        parameters = [i.name() for i in node.parms()]

        print("Setting up AOV: '{}'".format(each.get("name")))


        parms = each.get("parms")
        if not parms:
            print("No parameters defined for AOV '{}', skipping..".format(each.get("name")))
            continue

        for p in parms:
            parm_name = "{}{}".format(p[0], number)
            if parm_name in parameters:
                try:
                    node.parm(parm_name).set(p[1])
                except Exception as err:
                    print("[{}][{}] Error: {}".format(node.name(), parm_name, err.message))


        # if regular arnold node, make sure custom aov shaders are set up
        # NOTE: for sgtk_arnold nodes, shaders are contained inside digital asset and dont
        # need any extra steps
        shader = each.get("shader")
        if shader:
            aov_shaders_node = node.parm("ar_aov_shaders").evalAsNode()

            if node_type == "arnold":
                # if there is no aov shaders arnold_vopnet, create it
                if not aov_shaders_node:
                    aov_shaders_shopnet = node.parent().createNode(
                        "shopnet", node_name=node.name() + "-auto_oavsetup")
                    aov_shaders_shopnet.setPosition((node.position()[0], node.position()[1] + 1))

                    # create vopnet
                    aov_shaders_node = aov_shaders_shopnet.createNode(
                        "arnold_vopnet", node_name="passes")

                    # delete default "OUT_material"
                    aov_shaders_node.node("OUT_material").destroy()

                    # create "OUT_aov"
                    aov_shaders_node.createNode("arnold_aov")

                    # set
                    rel_path = node.relativePathTo(aov_shaders_node)
                    node.parm("ar_aov_shaders").set(rel_path)

                for sn in shader:
                    sn_name = sn.get("name")
                    sn_type = sn.get("type")
                    sn_output = sn.get("output")
                    sn_input = sn.get("input")
                    sn_parms = sn.get("parms")

                    sn_node = aov_shaders_node.node(sn_name)
                    if not sn_node:
                        sn_node = aov_shaders_node.createNode(sn_type, sn_name)
                        for sn_p in sn_parms:
                            try:
                                sn_node.parm(sn_p[0]).set(sn_p[1])
                            except Exception as err:
                                print("[{}][{}] Error: {}".format(sn_node.name(), sn_p[0], err.message))

                    # connect
                    output_index = sn_node.outputNames().index(sn_output)
                    input_node = aov_shaders_node.node(sn_input["node"])

                    if input_node not in sn_node.outputs():
                        if sn_input["input_name"] in input_node.inputNames():
                            input_index = input_node.inputNames().index(sn_input["input_name"])
                            input_node.setInput(input_index, sn_node, output_index)
                        elif "#" in sn_input["input_name"]:
                            input_index = 0
                            input_names = input_node.inputNames()
                            for input_name in input_names:
                                if input_name.startswith(sn_input["input_name"].replace("#", "")):
                                    input_index = input_node.inputNames().index(input_name)
                            input_node.setInput(input_index, sn_node, output_index)

                aov_shaders_node.layoutChildren()

        # increment index
        index += 1

    # if sgtk node, refresh parameter path
    if node_type == "sgtk_arnold":
        node.hdaModule().app().handler.reset_render_path(node=node)

    # if regular arnold node, call script to fill in separate AOV paths
    if node_type == "arnold":
        from produtils import ak_htoa_prepare_separate_aovs
        reload(ak_htoa_prepare_separate_aovs)
        ak_htoa_prepare_separate_aovs.main(nodes=[node])


# ------------------------------------------------------------------------------
# Redshift

def create_redshift_aovs(node, additional=False):
    print("[{}] Redshift not implemented yet, skipping..".format(node))
    pass


# ------------------------------------------------------------------------------

def main(nodes=None, additional=False):

    if nodes:
        rop_nodes = nodes
    else:
        rop_nodes = hou.selectedNodes()

    for rop in rop_nodes:
        node_type = rop.type().name()
        if not node_type in ["arnold", "sgtk_arnold", "Redshift_ROP"]:
            print("[{}] Only Arnold and Reshift ROP nodes are supported, skipping..".format(node_type))
            return

        if node_type in ["arnold", "sgtk_arnold"]:
            create_arnold_aovs(rop, additional=additional)

        if node_type in ["Redshift_ROP"]:
            create_redshift_aovs(rop, additional=additional)

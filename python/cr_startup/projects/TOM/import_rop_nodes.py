import hou
import os
import nodesearch
import sys


def import_rop_nodes():
    hou.hipFile.merge("u:/HoudiniDigitalAssets/render_nodes/ROP_nodes_v002.hip", ignore_load_warnings=True)

    fullname = hou.hipFile.name()
    file = os.path.basename(fullname)

    for part in fullname.split("/"):
        if part.startswith("sq"):
            seq = part.lstrip("sq")
        if part.startswith("sh"):
            shot = part.lstrip("sh")
        if part.startswith("e") and len(part) == 4:
            episode = part.lstrip("e")

    matcher = nodesearch.Name("e405_"+seq+"_"+shot)

    network = hou.node("/obj/")
    for node in matcher.nodes(network, recursive=True):
        if node.name().endswith("CAM"):
            cam = node

    render_nodes = ["main", "charmain", "whiskers",
                    "env_prepass", "env_pc", "env_bf"]
    for render_node in render_nodes:
        hou.node("/out/"+render_node).parm("RS_renderCamera").set(cam.path())


def create_bundles():
    animProp_names = ["ufoBalloon", "microphone"]

    if hou.nodeBundle("charmain"):
        char_bundle = hou.nodeBundle("charmain")
    else:
        char_bundle = hou.addNodeBundle("charmain")
    if hou.nodeBundle("eyes"):
        eyes_bundle = hou.nodeBundle("eyes")
    else:
        eyes_bundle = hou.addNodeBundle("eyes")

    if hou.nodeBundle("animProps"):
        animProps_bundle = hou.nodeBundle("animProps")
    else:
        animProps_bundle = hou.addNodeBundle("animProps")

    if hou.nodeBundle("charsec"):
        charsec_bundle = hou.nodeBundle("charsec")
    else:
        charsec_bundle = hou.addNodeBundle("charsec")

    char_bundle.clear()
    eyes_bundle.clear()
    animProps_bundle.clear()
    charsec_bundle.clear()

    if hou.node("/obj/light_rig/GeoMat_e408/"):
        for node in hou.node("/obj/light_rig/GeoMat_e408/").allSubChildren():
            if node.type().name() == 'geo':
                char_bundle.addNode(node)
                if node.name().endswith('eyes') or node.name().endswith('eye') or node.name().endswith('corneas'):
                    eyes_bundle.addNode(node)

    for animProp_name in animProp_names:
        matcher = nodesearch.Name(animProp_name)

        network = hou.node("/obj")

        for node in matcher.nodes(network, recursive=True):
            if node.type().name() == 'geo':
                animProps_bundle.addNode(node)

import os
import re
import sys
import json
import subprocess
from pprint import pprint

import hou
import nodesearch


ROP_NODES_TEMPLATE = "U:/projects/ttv/episodes/e000/work/sq000/sh000/Houdini/ROP_nodes_v001.hip"


def import_rop_nodes():
    hou.hipFile.merge(ROP_NODES_TEMPLATE, ignore_load_warnings=True)

    fullname = hou.hipFile.name()

    for part in fullname.split("/"):
        if part.startswith("sq"):
            seq = part.lstrip("sq")
        if part.startswith("sh"):
            shot = part.lstrip("sh")
        if part.startswith("e") and len(part) == 4:
            episode = part.lstrip("e")

    matcher = nodesearch.Name("e405_"+seq+"_"+shot)

    network = hou.node("/obj/")
    cam = None
    for node in matcher.nodes(network, recursive=True):
        if node.name().endswith("CAM"):
            cam = node

    render_nodes = ["main", "charmain", "whiskers",
                    "env_prepass", "env_pc", "env_bf"]

    if cam:
        for render_node in render_nodes:
            hou.node("/out/"+render_node).parm("RS_renderCamera").set(cam.path())


def export_aov_list():

    json_file_path = os.path.join(
        os.path.dirname(ROP_NODES_TEMPLATE),
        os.path.splitext(os.path.basename(ROP_NODES_TEMPLATE))[0] + ".json"
    )

    # empty
    template_rops_dict = dict()

    # regex pattern for aov multi-parameter name parsing
    pattern = re.compile(r"^RS_(.+)_([0-9]+)([x|y|z])?$")
    
    # get aovs for each redshift rop node as dict 
    for x in hou.node("/out").children():
        if x.type().name() == "Redshift_ROP":
            rop_dict = dict()

            aov_multi = x.parm("RS_aov").multiParmInstances()

            for i in aov_multi:
                match = re.match(pattern, i.name())
                if not match:
                    continue
                else:
                    name = match.group(1)
                    index = match.group(2)

                    if len(match.groups()) == 3:
                        suffix = match.group(3)
                    else:
                        suffix = None

                    if index in rop_dict:
                        temp_list = rop_dict[index]
                    else:
                        temp_list = list()

                    temp_list.append(
                        {
                            "name": name,
                            "suffix": suffix,
                            "value": i.rawValue(),
                        }
                    )

                    rop_dict[index] = temp_list

            template_rops_dict[x.name()] = rop_dict

    with open(json_file_path, "w") as outfile:  
        json.dump(template_rops_dict, outfile)


def update_aov_list():

    json_file_path = os.path.join(
        os.path.dirname(ROP_NODES_TEMPLATE),
        os.path.splitext(os.path.basename(ROP_NODES_TEMPLATE))[0] + ".json"
    )

    if not os.path.isfile(json_file_path):
        print("File not found: {}".format(json_file_path))
        return

    with open(json_file_path) as json_file:  
        template_rops_dict = json.load(json_file)

    # regex pattern for aov multi-parameter name parsing
    pattern = re.compile(r"^RS_(.+)_([0-9]+)([x|y|z])?$")

    # compare and update
    for k, v in template_rops_dict.items():
        template_dict = v
        rop_node = hou.node("/out/" + k)
        if rop_node:
            aov_parm = rop_node.parm("RS_aov")
            aov_parm_multi = aov_parm.multiParmInstances()

            aov_exists = list()

            for i in aov_parm_multi:
                if i.name().startswith("RS_aovID"):

                    aov_type = i.rawValue()

                    match = re.match(pattern, i.name())
                    index = match.group(2)

                    aov_name = rop_node.parm("RS_aovSuffix_{}".format(index)).rawValue()

                    for key, value in template_dict.items():
                        aov_sfx = [x["value"] for x in value if x["name"] == "aovSuffix"][0]
                        aov_id = [x["value"] for x in value if x["name"] == "aovID"][0]

                        if (aov_sfx == aov_name) and (aov_id == aov_type):
                            aov_exists.append(key)

            for key, value in template_dict.items():
                if key not in aov_exists:
                    aov_suffix_value = [x["value"] for x in value if x["name"] == "aovSuffix"][0]
                    print("Creating AOV '{aov_suffix}' on node '{node_name}'".format(aov_suffix=aov_suffix_value, node_name=rop_node.name()))

                    aov_parm.insertMultiParmInstance(0)

                    for i in value:
                        parm_name = "RS_" + i["name"] + "_1" + (i["suffix"] or "")
                        parm_value = i["value"]

                        if parm_value == "on":
                            parm_value = 1

                        if parm_value == "off":
                            parm_value = 0

                        try:

                            rop_node.parm(parm_name).set(parm_value)
                        except:
                            print("Could not set value {} on parm {}".format(parm_value, parm_name))
                            pass

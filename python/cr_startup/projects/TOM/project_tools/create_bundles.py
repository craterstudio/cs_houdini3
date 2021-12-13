import hou


def create_bundles(additional_characters=list(), anim_props=list()):
    light_rig_node = hou.node("/obj/light_rig")

    characters = {
        "tom2": 1-int(light_rig_node.parm("tdisplay3").eval()),
        "ben": 1-int(light_rig_node.parm("tdisplay2").eval()),
        "Ben2": 1-int(light_rig_node.parm("tdisplay6").eval()),
        "ginger": 1-int(light_rig_node.parm("tdisplay4").eval()),
        "hank": 1-int(light_rig_node.parm("tdisplay5").eval()),
        "angela2": 1-int(light_rig_node.parm("tdisplay7").eval())
    }

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

    char_bundle.clear()
    eyes_bundle.clear()
    animProps_bundle.clear()

    for char in characters:
        if characters[char] == 1:
            if not hou.nodeBundle(char):
                hou.addNodeBundle(char)
            current_char_bundle = hou.nodeBundle(char)
            current_char_bundle.clear()

        static_path = "/obj/light_rig/GeoMat_e408/"
        children = hou.node(static_path+char+"_geoGrp").children()
        for child in children:
            char_bundle.addNode(child)
            if child.name().endswith('eyes') or child.name().endswith('eye') or child.name().endswith('corneas'):
                eyes_bundle.addNode(child)
            if characters[char] == 1:
                current_char_bundle.addNode(child)

    for c in additional_characters:
        node = hou.node(c)
        if node:
            for i in node.allSubChildren():
                if i.type().name() == "geo":
                    char_bundle.addNode(i)

    for p in anim_props:
        node = hou.node(p)
        if node:
            for i in node.allSubChildren():
                if i.type().name() == "geo":
                    animProps_bundle.addNode(i)

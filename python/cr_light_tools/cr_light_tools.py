import hou


def get_average_pos(objects):
    pos_sum = [0, 0, 0]
    s = float(len(objects))
    for object in objects:
        pos = object.origin()
        pos_sum = [pos_sum[0]+pos[0], pos_sum[1]+pos[1], pos_sum[2]+pos[2]]
    pos_avg = [pos_sum[0]/s, pos_sum[1]/s, pos_sum[2]/s]
    return pos_avg


def get_average_node_pos(nodes):
    pos_sum = [0, 0]
    s = float(len(nodes))
    for node in nodes:
        pos = node.position()
        pos_sum = [pos_sum[0]+pos[0], pos_sum[1]+pos[1]]
    pos_avg = [pos_sum[0]/s, pos_sum[1]/s]
    return pos_avg


def create_aims(z):
    sel = hou.selectedNodes()
    root = hou.node("/obj")
    aims = []
    if sel:
        for current_node in sel:
            current_node.parm("lookatpath").set("")
            pos = current_node.position()
            null = root.createNode("null", node_name=current_node.name()+"_aim")
            xform = current_node.worldTransform()
            pos = [pos[0], pos[1]-5]
            null.setPosition(pos)
            null.setWorldTransform(xform)
            matrix = null.localTransform()
            null.moveParmTransformIntoPreTransform()
            tz = null.parm("tz").eval()-z
            null.parm("tz").set(tz)
            null.parm("keeppos").set(1)
            aims.append(null)
            current_node.parm("lookatpath").set(null.path())

        meta_pos = get_average_pos(aims)
        meta_ctr = root.createNode("null", node_name="stage_lights_meta_aim")
        meta_ctr.parm("tx").set(meta_pos[0])
        meta_ctr.parm("ty").set(meta_pos[1])
        meta_ctr.parm("tz").set(meta_pos[2])

        meta_ctr.setPosition([get_average_node_pos(aims)[0], get_average_node_pos(aims)[1]+2])
        meta_ctr.parm("geoscale").set(4)
        meta_ctr.parm("controltype").set("box")
        meta_ctr.parm("dcolorr").set(1)
        meta_ctr.parm("dcolorg").set(0)
        meta_ctr.parm("dcolorb").set(0)

        for aim in aims:
            aim.setFirstInput(meta_ctr)

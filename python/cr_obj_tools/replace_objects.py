import hou


def replace_objects:
    sel = hou.selectedNodes()
    if len(sel > 1):
        for node in sel[1:]:

            xform = node.worldTransform()
            inputs = node.inputs()
            name = node.name()
            position = node.position()
            node.destroy()
            new_node = hou.copyNodesTo([sel[0]], hou.node("/obj"))[0]
            new_node.setPosition(position)
            new_node.setFirstInput(inputs[0])
            new_node.setWorldTransform(xform)

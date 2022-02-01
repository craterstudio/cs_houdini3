import os
import re
import hou


EXPRESSION = """
import hou 
import re
import os

pattern = r"^.+file([0-9]+)$"
current = hou.evaluatingParm().name()
match = re.match(pattern, current)
index = match.group(1)
aov_name = ch("ar_aov_label" + index)
ar_picture = ch("ar_picture")
directory = os.path.dirname(ar_picture)
filename = os.path.basename(ar_picture)
return os.path.join(directory, aov_name, aov_name + "_" + filename).replace("\\\\", "/")
"""


def main(nodes=None):

    if not isinstance(nodes, (type(None), list)):
        raise TypeError("'nodes' keyword argument must by of type None or List")

    if nodes:
        rop_nodes = nodes
    else:
        rop_nodes = hou.selectedNodes()

    for rop in rop_nodes:

        if not rop.type().name() == "arnold":
            print("[{}] Only Arnold ROP nodes supported, skipping..".format(rop))
            return

        ar_picture = rop.parm("ar_picture").eval()
        if ar_picture in ["", "ip"]:
            print("[{}] Please fill in Output Picture parameter, skipping..".format(rop))
            return

        ar_aovs = rop.parm("ar_aovs")
        aov_parm_instances = ar_aovs.multiParmInstances()

        pattern = r"^.+file([0-9]+)$"
        for i in aov_parm_instances:
            if i.name().startswith("ar_aov_separate_file"):
                parm_name = i.name()
                match = re.match(pattern, parm_name)
                index = match.group(1)

                checkbox = rop.parm("ar_aov_separate" + index)
                checkbox.set(True)

                editbox = rop.parm(parm_name)
                editbox.setExpression(EXPRESSION, language=hou.exprLanguage.Python)

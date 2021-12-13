from __future__ import print_function
import os
import sys
import traceback

import hou

from CallDeadlineCommand import CallDeadlineCommand

def main():
    path = os.path.join(os.environ["HOUDINI_CONFIG_ROOT"], "deadline", "submitter")
    if os.path.isdir(path):
        path = path.replace( "\\", "/" )

        # Add the path to the system path
        if path not in sys.path :
            print("Deadline submitter script will not be sourced from deadline repository...")
            print("Loading customized submitter script instead: " + os.path.join(path, "SubmitNukeToDeadline.py").replace("\\", "/"))

            print("Appending \"" + path + "\" to system path to import SubmitHoudiniToDeadline module")
            sys.path.append( path )
        else:
            print("\"%s\" is already in the system path" % path)

        if hou.hipFile.basename() == "untitled.hip":
            msg = "Submitter cannot run on unsaved file."
            print(msg)
            hou.ui.displayMessage(msg)
            return

        # Import the script and call the main() function
        try:
            import SubmitHoudiniToDeadline
            reload(SubmitHoudiniToDeadline)
            SubmitHoudiniToDeadline.SubmitToDeadline()
        except:
            print(traceback.format_exc())
            print("The SubmitHoudiniToDeadline.py script could not be found. Please make sure " \
                "that the Deadline Client has been installed on this machine, that the Deadline " \
                "Client bin folder is set in the DEADLINE_PATH environment variable, and that " \
                "the Deadline Client has been configured to point to a valid Repository.")
    else:
        print( "The SubmitHoudiniToDeadline.py script could not be found. Please make sure that " \
            "the Deadline Client has been installed on this machine, that the Deadline Client " \
            "bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline " \
            "Client has been configured to point to a valid Repository.")

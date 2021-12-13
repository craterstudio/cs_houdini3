import os
import re
import hou
import glob

new_suffix_format = '_v001'
regex = re.compile(r'(.*?)_v(\d+)(\.\w+)')


def incremental_save():
    filename = hou.hipFile.path()
    basename = os.path.basename(filename)
    if basename != "untitled.hip":
        match = regex.match(filename)
        if match:
            filename, number, ext = match.groups()
            filename += "_v" + str(int(number) + 1).rjust(len(number), '0') + ext
        else:
            filename, ext = os.path.splitext(filename)
            filename += new_suffix_format + ext

        if os.path.isfile(filename):
            next_available = hou.ui.displayConfirmation(
                "Next version already exists on file system. Do you wish to save as next available?",
                severity=hou.severityType.ImportantMessage
            )
            if next_available:
                filename, number, ext = match.groups()
                version = 0
                for workfile in glob.glob(filename + "_v*"):
                    w_match = regex.match(workfile)
                    _, w_number, _ = w_match.groups()
                    if int(w_number) > version:
                        version = int(w_number)

                filename += "_v" + str(int(version) + 1).rjust(len(number), '0') + ext
            else:
                return

        hou.hipFile.save(filename)

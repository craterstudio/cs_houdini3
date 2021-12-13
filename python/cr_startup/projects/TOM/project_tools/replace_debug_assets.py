import os
import hou
import traceback


def main():

    details = ""

    found = 0
    replaced = 0
    failed = 0

    # get all installed assets
    asset_files = list()
    loaded_hda_files = hou.hda.loadedFiles()
    for i in loaded_hda_files:
        if "assets/publish" in i:
            asset_files.append(i)
            details += "Found File: {}\n".format(i)

    if asset_files:
        print("Replacing debug assets...")
        details += "\n"

    # for each asset check if there is main asset and replace if true
    for hda_path in asset_files:
        hda_file_name = os.path.basename(hda_path)
        parent_dir = os.path.dirname(hda_path)
        parent_name = os.path.basename(parent_dir)
        if parent_name.startswith("hda_TEMP"):

            found += 1

            main_hda_dir = os.path.join(os.path.abspath(os.path.join(hda_path, "..", "..")), "hda")
            if not os.path.isdir(main_hda_dir):
                failed += 1
            else:
                main_hda_file = os.path.join(main_hda_dir, hda_file_name)

                if not os.path.isfile(main_hda_file):
                    failed += 1
                else:

                    print("Replacing {} with {}".format(hda_path, main_hda_file))

                    try:
                        hou.hda.installFile(main_hda_file, oplibraries_file="Current HIP File")
                        hou.hda.uninstallFile(hda_path)
                        print("INFO: Success")
                        replaced += 1
                        details += "Success: {}\n".format(main_hda_file)
                    except:
                        print("ERROR: Something went wrong")
                        traceback.print_exc()
                        failed += 1
                        details += "Fail: {}\n".format(main_hda_file)

    output = "Debug HDA Replacement\n\nOutput:\n\n"
    output += "    Files found:\t\t{}\n".format(found)
    output += "    Replaced:\t\t{}\n".format(replaced)
    output += "    Failed:\t\t{}\n".format(failed)

    hou.ui.displayMessage(output, buttons=("OK",), details=details, severity=hou.severityType.Message, title="Replace Debug Nodes")

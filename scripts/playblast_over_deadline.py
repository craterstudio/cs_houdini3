import os
import sys
import re
import toolutils
import hdefereval

import hou


def viewname(viewer):
    viewname = {
        'desktop' : viewer.pane().desktop().name(),
        'pane' : viewer.name(),
        'type' :'world',
        'viewport': viewer.curViewport().name()
    }
    return '{desktop}.{pane}.{type}.{viewport}'.format(**viewname)

def viewwrite(options='', outpath='ip'):
    current_view = viewname(toolutils.sceneViewer())
    hou.hscript('viewwrite {} {} {}'.format(options, current_view, outpath))

def functionToExecuteOnStartup():
    # get Houdini file name
    full_hou_file_path = hou.hipFile.name()
    rekey_version="v[0-9][0-9][0-9]"
    rxp=re.compile(rekey_version)

    start = int(sys.argv[1]) #int(hou.playbar.playbackRange()[0])
    end = int(sys.argv[2]) #int(hou.playbar.playbackRange()[1]) 

    res_x = int(sys.argv[3])
    res_y = int(sys.argv[4])
    camera=str(sys.argv[5])

    hou_file_dir = os.path.split( full_hou_file_path )[0]
    hou_file_name = os.path.split( full_hou_file_path )[1].split('.')[0]
    partv=rxp.findall(hou_file_name)[0]
    partcamera=camera.replace("/","_")
    partcamera=partcamera[1:]
    playblast_dir = (hou_file_dir + '/review/playblast/{TODOversion}/{TODOcamera}/' + hou_file_name + "_{TODOcamera}").format(TODOversion=partv,TODOcamera=partcamera)

    # create playblast dir if it does not exist
    if not os.path.exists(playblast_dir):
        os.makedirs(playblast_dir, 0775)
        
    path_parts = [ playblast_dir, os.path.split(full_hou_file_path)[1].split('.')[0]+"."+"'$F4'"+".png"]   
    houdini_playblast_file = '/'.join( path_parts )

    current_view=toolutils.sceneViewer().curViewport()
    current_view.setCamera(camera)

    # houdini playblast command
    viewwrite('-q 4 -c -r ' + str(res_x) + ' ' + str(res_y) + ' -f ' + str(start) + ' ' + str(end), houdini_playblast_file)
    
    #exit houdini
    hou.exit(exit_code=0, suppress_save_prompt=True)

# waits until view port is loaded
hdefereval.executeDeferred(functionToExecuteOnStartup)

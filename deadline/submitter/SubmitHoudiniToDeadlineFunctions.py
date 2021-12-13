from __future__ import print_function

import os
import re
import ast
import sys
import json
import time
import subprocess

import hou

shotgun_active = bool(ast.literal_eval(os.environ.get("SHOTGUN_PIPELINE_ACTIVE") or "0"))

# TODO: This function is a duplicate from CallDeadlineCommand.py. Once we're a full major version
# from Deadline 10 we can remove this since the client script will have the be updated.
def GetDeadlineCommand():
    deadlineBin = ""
    try:
        deadlineBin = os.environ['DEADLINE_PATH']
    except KeyError:
        #if the error is a key error it means that DEADLINE_PATH is not set. however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
        pass

    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if deadlineBin == "" and  os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f:
            deadlineBin = f.read().strip()

    deadlineCommand = os.path.join(deadlineBin, "deadlinecommand")

    return deadlineCommand

# TODO: This function is a duplicate from CallDeadlineCommand.py. Once we're a full major version
# from Deadline 10 we can remove this since the client script will have the be updated.
def CallDeadlineCommand( arguments, hideWindow=True, readStdout=True ):
    deadlineCommand = GetDeadlineCommand()
    startupinfo = None
    creationflags = 0
    if os.name == 'nt':
        if hideWindow:
            # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
            if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            # still show top-level windows, but don't show a console window
            CREATE_NO_WINDOW = 0x08000000   #MSDN process creation flag
            creationflags = CREATE_NO_WINDOW

    environment = {}
    for key in os.environ.keys():
        environment[key] = str(os.environ[key])

    # Need to set the PATH, cuz windows seems to load DLLs from the PATH earlier that cwd....
    if os.name == 'nt':
        deadlineCommandDir = os.path.dirname( deadlineCommand )
        if not deadlineCommandDir == "" :
            environment['PATH'] = deadlineCommandDir + os.pathsep + os.environ['PATH']

    arguments.insert( 0, deadlineCommand )

    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, env=environment, creationflags=creationflags)

    output = ""
    if readStdout:
        output, errors = proc.communicate()

    return output.strip()

def GetOutputPath( node ):
    outputFile = ""
    nodeType = node.type().description()
    category = node.type().category().name()

    #Figure out which type of node is being rendered
    if nodeType == "Geometry" or nodeType == "Filmbox FBX" or ( nodeType == "ROP Output Driver" and category == "Sop" ):
        outputFile = node.parm( "sopoutput" )
    elif nodeType == "Composite":
        outputFile = node.parm( "copoutput" )
    elif nodeType == "Channel":
        outputFile = node.parm( "chopoutput" )
    elif nodeType == "Dynamics" or ( nodeType == "ROP Output Driver" and category == "Dop" ):
        outputFile = node.parm( "dopoutput" )
    elif nodeType == "Alfred":
        outputFile = node.parm( "alf_diskfile")
    elif nodeType == "RenderMan" or nodeType == "RenderMan RIS":
        outputFile = node.parm( "ri_display" )
    elif nodeType == "Redshift":
        outputFile = node.parm( "RS_outputFileNamePrefix" )
    elif nodeType == "Mantra":
        outputFile = node.parm( "vm_picture" )
    elif nodeType == "Wedge":
        driverNode = node.node( node.parm( "driver" ).eval() )
        if driverNode:
            outputFile = GetOutputPath(driverNode)
    elif nodeType == "Arnold":
        outputFile = node.parm("ar_picture")
    elif nodeType == "HQueue Simulation":
        innerNode = node.node( node.parm( "hq_driver" ).eval() )
        if innerNode:
            outputFile = GetOutputPath( innerNode )
    elif nodeType == "ROP Alembic Output":
        outputFile = node.parm( "filename" )
    elif nodeType == "Redshift":
        outputFile = node.parm( "RS_outputFileNamePrefix" )
    elif nodeType == "Alembic":
        outputFile = node.parm( "filename" )
    elif nodeType == "Shotgun Mantra":
        outputFile = node.parm( "sgtk_vm_picture" )
    elif nodeType == "Shotgun Alembic":
        outputFile = node.parm( "filename" )
    elif nodeType == "Bake Texture":
        outputFile = node.parm("vm_uvoutputpicture1")
    elif nodeType == "OpenGL":
        outputFile = node.parm("picture")
    elif nodeType == "Octane":
        outputFile = node.parm("HO_img_fileName")
    elif nodeType == "Fetch":
        innerNode = node.node( node.parm( "source" ).eval() )
        if innerNode:
            outputFile = GetOutputPath( innerNode )


    #Check if outputFile could "potentially" be valid. ie. Doesn't allow Houdini's "ip"
    # or "md" values to be overridden, but silliness like " /*(xc*^zx$*asdf " would be "valid")
    if outputFile and not os.path.isabs( outputFile.eval() ):
        outputFile = "COMMAND"

    return outputFile

def GetExportPath( node ):
    ifdFile = None
    nodeType = node.type().description()

    # Ensures the proper Take is selected for each ROP to retrieve the correct ifd
    try:
        ropTake = hou.takes.findTake( node.parm( "take" ).eval() )
        if ropTake is not None:
            hou.takes.setCurrentTake( ropTake )
    except AttributeError:
        # hou object doesn't always have the 'takes' attribute
        pass

    if nodeType == "Mantra" and node.parm( "soho_outputmode" ).eval():
        ifdFile = node.parm( "soho_diskfile" )
    elif nodeType == "Alfred":
        ifdFile = node.parm( "alf_diskfile")
    elif ( nodeType == "RenderMan" or nodeType == "RenderMan RIS" ) and node.parm( "rib_outputmode" ) and node.parm( "rib_outputmode" ).eval():
        ifdFile = node.parm( "soho_diskfile" )
    elif nodeType == "Redshift" and node.parm( "RS_archive_enable" ).eval():
        ifdFile = node.parm( "RS_archive_file" )
    elif nodeType == "Wedge" and node.parm( "driver" ).eval():
        ifdFile = GetExportPath( node.node(node.parm( "driver" ).eval()) )
    elif nodeType == "Arnold":
        ifdFile = node.parm( "ar_ass_file" )
    elif nodeType == "Alembic" and node.parm( "use_sop_path" ).eval():
        ifdFile = node.parm( "sop_path" )
    elif nodeType == "Shotgun Mantra" and node.parm( "soho_outputmode" ).eval():
        ifdFile = node.parm( "sgtk_soho_diskfile" )
    elif nodeType == "Shotgun Alembic" and node.parm( "use_sop_path" ).eval():
        ifdFile = node.parm( "sop_path" )

    return ifdFile

def NodeSupportsTiles( node ):
    supportedTypes = [ "geometry", "ifd", "arnold", "comp", "channel", "dop", "rib" ]
    nodeType = node.type().name()

    return ( nodeType in supportedTypes )

def WedgeTasks( wedgeNode ):
    numTasks = 1

    if wedgeNode.type().description() == "Wedge":
        numParams = wedgeNode.parm("wedgeparams").eval()
        random = wedgeNode.parm("random").eval()

        if random:
            # We're using the random settings
            numRandom = wedgeNode.parm("numrandom").eval()
            numTasks = numRandom * numParams
        else:
            # Using the number wedge params to determine task count
            for i in range(1, numParams+1):
                numTasks = numTasks * wedgeNode.parm("steps"+str(i)).eval()

    return numTasks

def isExportJob( node, jobProperties ):
    if node.type().description() == "Mantra":
        return jobProperties.get( "mantrajob", False )
    elif node.type().description() == "Arnold":
        return jobProperties.get( "arnoldjob", False )
    elif node.type().description() == "RenderMan" or node.type().description() == "RenderMan RIS":
        return jobProperties.get( "rendermanjob", False )
    elif node.type().description() == "Redshift":
        return jobProperties.get( "redshiftjob", False )

    return False

def isExportLocal( node, jobProperties ):
    if isExportJob( node, jobProperties ):
        if node.type().description() == "Mantra":
            return jobProperties.get( "mantralocalexport", False )
        elif node.type().description() == "Arnold":
            return jobProperties.get( "arnoldlocalexport", False )
        elif node.type().description() == "RenderMan" or node.type().description() == "RenderMan RIS":
            return jobProperties.get( "rendermanlocalexport", False )
        elif node.type().description() == "Redshift":
            return jobProperties.get( "redshiftlocalexport", False )

    return False

def IsPathLocal( path ):
    lowerPath = path.lower()
    return lowerPath.startswith( "c:" ) or lowerPath.startswith( "d:" ) or lowerPath.startswith( "e:" )

def hqueueSliceCount( node ):
    sliceCount = 1
    sliceType = node.parm("slice_type").evalAsString()
    if sliceType == "volume":
        slicesInX = node.parm("slicediv1").eval()
        slicesInY = node.parm("slicediv2").eval()
        slicesInZ = node.parm("slicediv3").eval()
        sliceCount = slicesInX * slicesInY * slicesInZ
    elif sliceType == "particle":
        sliceCount = node.parm("num_slices").eval()
    elif sliceType == "cluster":
        clusterNodeName = node.parm("hq_cluster_node").eval()
        if not clusterNodeName == "":
            clusterNode = node.node(clusterNodeName)
            sliceCount = clusterNode.parm("num_clusters").eval()
    elif sliceType == "None":
        pass

    return sliceCount

def GetFrameInfo( renderNode ):
    startFrame = 0
    endFrame = 0
    frameStep = 1
    frameString = ""

    if renderNode.type().description() == "Wedge":
        if renderNode.parm("driver").eval():
            return GetFrameInfo(renderNode.node(renderNode.parm("driver").eval()))

    startFrameParm = renderNode.parm( "f1" )
    if startFrameParm != None:
        startFrame = int(startFrameParm.eval())

    endFrameParm = renderNode.parm( "f2" )
    if endFrameParm != None:
        endFrame = int(endFrameParm.eval())

    frameStepParm = renderNode.parm( "f3" )
    if frameStepParm != None:
        frameStep = int(frameStepParm.eval())

    frameString = str(startFrame) + "-" + str(endFrame)
    if frameStep > 1:
        frameString = frameString + "x" + str(frameStep)

    return frameString

def RightReplace( fullString, oldString, newString, occurences ):
    return newString.join( fullString.rsplit( oldString, occurences ) )

def WriteIntegrationSettings( fileHandle, doShotgun, doDraft, groupBatch, integrationKVPs ):
    if 'integrationSettingsPath' in integrationKVPs:
        with open( integrationKVPs['integrationSettingsPath'] ) as file:
            for line in file.readlines():
                fileHandle.write( line )

        if 'batchMode' in integrationKVPs:
            if integrationKVPs['batchMode'] == "True":
                groupBatch = True

    return groupBatch

def SubmitRenderJob( node, jobProperties, dependencies ):
    paddedNumberRegex = re.compile( "([0-9]+)", re.IGNORECASE )
    jobCount = 1

    tilesEnabled = jobProperties.get( "tilesenabled", False )
    tilesInX = jobProperties.get( "tilesinx", 1 )
    tilesInY = jobProperties.get( "tilesiny", 1 )
    regionCount = tilesInX * tilesInY
    singleFrameTiles = jobProperties.get( "tilessingleframeenabled", False )
    singleFrame = jobProperties.get( "tilessingleframe", 1)

    jigsawEnabled = jobProperties.get( "jigsawenabled", False )
    jigsawRegionCount =  jobProperties.get( "jigsawregioncount", 1 )
    jigsawRegions = jobProperties.get( "jigsawregions", [] )

    if jigsawEnabled:
        regionCount = jigsawRegionCount

    if tilesEnabled:
        tilesEnabled = NodeSupportsTiles( node )

    regionJobCount = 1
    if tilesEnabled and not singleFrameTiles:
        regionJobCount = regionCount

    ignoreInputs = jobProperties.get( "ignoreinputs", True )

    separateWedgeJobs = jobProperties.get( "separateWedgeJobs", False )
    isWedge = node.type().description() == "Wedge"

    isHQueueSim = node.type().description() == "HQueue Simulation"
    isArnold = node.type().description() == "Arnold"

    wedgeJobCount = 1
    if isWedge and separateWedgeJobs:
        wedgeJobCount = WedgeTasks( node )

    groupBatch = jobProperties.get( "batch", False )

    integrationKVPs = jobProperties.get( "integrationKVPs", {} )

    exportJob = isExportJob( node, jobProperties )
    localExport = isExportLocal( node, jobProperties )

    isRedshift = ( node.type().description() == "Redshift" )

    outputFile = ""
    paddedOutputFile = ""
    ifdFile = ""
    paddedIfdFile = ""

    subInfo = json.loads( hou.getenv("Deadline_Submission_Info") )
    homeDir = subInfo["UserHomeDir"]

    renderJobIds = []
    exportJobIds = []
    assemblyJobIds = []

    if exportJob:
        ifdFileParameter = GetExportPath( node )
        if ifdFileParameter != None:
            ifdFile = ifdFileParameter.eval()
            matches = paddedNumberRegex.findall( os.path.basename( ifdFile ) )
            if matches != None and len( matches ) > 0:
                paddingString = matches[ len( matches ) - 1 ]
                paddingSize = len( paddingString )
                padding = "0"
                while len(padding) < paddingSize:
                    padding = padding + "0"
                paddedIfdFile = RightReplace( ifdFile, paddingString, padding, 1 )
            else:
                paddedIfdFile = ifdFile
        if ifdFile == "":
            exportJob = False

    # Check the output file
    output = GetOutputPath( node )
    if output and output != "COMMAND":
        outputFile = output.eval()
        matches = paddedNumberRegex.findall( os.path.basename( outputFile ) )
        if matches != None and len( matches ) > 0:
            paddingString = matches[ len( matches ) - 1 ]
            paddingSize = len( paddingString )
            padding = "#"
            while len(padding) < paddingSize:
                padding = padding + "#"
            paddedOutputFile = RightReplace( outputFile, paddingString, padding, 1 )
    elif output is None and node.type().description() == "RenderMan":
        print( 'Warning: RenderMan 21 has deprecated the "RenderMan" node, please use the newer "RenderMan RIS" node.' )
    elif output != "COMMAND":
        print("Output path for ROP: \"%s\" is not specified" % node.path())
    else:
        print("Unable to resolve output path for ROP: \"%s\"" % node.path())
    
    if node.type().description() == "Octane":
        if node.parm("HO_img_fileFormat").eval() < 2 or node.parm("HO_img_fileFormat").eval() > 3:
            paddedOutputFile += ".exr"
        else:
            paddedOutputFile += ".png"
    
     # Get the IFD info, if applicable
    for wedgeNum in range(0, wedgeJobCount):
        if localExport:
            if singleFrameTiles and tilesEnabled:
                node.render( (singleFrame,singleFrame,1), (), ignore_inputs=ignoreInputs )
            else:
                frameStep = 1

                if jobProperties.get( "overrideframes", False ):
                    frameList = CallDeadlineCommand( [ "-ParseFrameList", jobProperties.get( "framelist", "0" ) , "False" ] ).strip()
                    renderFrames = frameList.split( "," )
                    for frame in renderFrames:
                        frame = int( frame )
                        node.render( ( frame, frame, frameStep ), (), ignore_inputs=ignoreInputs )
                else:
                    startFrame = 1
                    startFrameParm = node.parm( "f1" )
                    if startFrameParm != None:
                        startFrame = int(startFrameParm.eval())

                    endFrame = 1
                    endFrameParm = node.parm( "f2" )
                    if endFrameParm != None:
                        endFrame = int(endFrameParm.eval())

                    frameStepParm = node.parm( "f3" )
                    if frameStepParm != None:
                        frameStep = int(frameStepParm.eval())

                    if output and output != "COMMAND":
                        paddedOutputFile = output.eval()

                    node.render( (startFrame,endFrame,frameStep), (), ignore_inputs=ignoreInputs )
        else:
            for regionjobNum in range( 0, regionJobCount ):
                not ( exportJob or tilesEnabled )
                doShotgun = not ( exportJob or tilesEnabled )
                doDraft = not ( exportJob or tilesEnabled )

                jobName = jobProperties.get( "jobname", "Untitled" )
                jobName = "%s - %s"%(jobName, node.path())

                if isWedge and separateWedgeJobs:
                    jobName = jobName + "{WEDGE #"+str(wedgeNum)+"}"

                if tilesEnabled and singleFrameTiles and not exportJob:
                    jobName = jobName + " - Region "+str( regionjobNum )

                # Create submission info file
                jobInfoFile = os.path.join(homeDir, "temp", "houdini_submit_info%d.job") % ( wedgeNum * regionJobCount + regionjobNum )
                with open( jobInfoFile, "w" ) as fileHandle:
                    fileHandle.write( "Plugin=Houdini\n" )
                    fileHandle.write( "Name=%s\n" % jobName )
                    fileHandle.write( "Comment=%s\n" % jobProperties.get( "comment", "" ) )
                    fileHandle.write( "Department=%s\n" % jobProperties.get( "department", "" ) )
                    fileHandle.write( "Pool=%s\n" % jobProperties.get( "pool", "None" ) )
                    fileHandle.write( "SecondaryPool=%s\n" % jobProperties.get( "secondarypool", "" ) )
                    fileHandle.write( "Group=%s\n" % jobProperties.get( "group", "None" ) )
                    fileHandle.write( "Priority=%s\n" % jobProperties.get( "priority", 50 ) )
                    fileHandle.write( "TaskTimeoutMinutes=%s\n" % jobProperties.get( "tasktimeout", 0 ) )
                    fileHandle.write( "EnableAutoTimeout=%s\n" % jobProperties.get( "autotimeout", False ) )
                    fileHandle.write( "ConcurrentTasks=%s\n" % jobProperties.get( "concurrent", 1 ) )
                    fileHandle.write( "MachineLimit=%s\n" % jobProperties.get( "machinelimit", 0 ) )
                    fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % jobProperties.get( "slavelimit", False ) )
                    fileHandle.write( "LimitGroups=%s\n" % jobProperties.get( "limits", 0 ) )
                    fileHandle.write( "JobDependencies=%s\n" % dependencies )
                    fileHandle.write( "OnJobComplete=%s\n" % jobProperties.get( "onjobcomplete", "Nothing" ) )

                    print("[*] Setting deadline job environment...")
                    network_color = os.environ.get("NETWORK_COLOR", False)
                    network_pipeline_root = os.environ.get("NETWORK_PIPELINE_ROOT", False)
                    network_repo_config_root = os.environ.get("NETWORK_REPO_CONFIG_ROOT", False)

                    if network_color and network_pipeline_root and network_repo_config_root:
                        fileHandle.write( "EnvironmentKeyValue0=NETWORK_COLOR={}\n".format(network_color) )
                        fileHandle.write( "EnvironmentKeyValue1=NETWORK_PIPELINE_ROOT={}\n".format(network_pipeline_root) )
                        fileHandle.write( "EnvironmentKeyValue2=NETWORK_REPO_CONFIG_ROOT={}\n".format(network_repo_config_root) )

                    if "OCIO" in os.environ:
                        fileHandle.write( "EnvironmentKeyValue3=OCIO=%s\n" % os.environ["OCIO"] )

                    if isRedshift:
                        redshift_version = os.environ.get("REDSHIFT_VERSION", "None")
                        fileHandle.write( "EnvironmentKeyValue4=USE_REDSHIFT_VERSION=%s\n" % redshift_version )

                    if jobProperties.get("shotguneviewitem", True):
                        print("Creating Shotgun review item...")
                        
                        if node.type().name() not in ["sgtk_arnold", "arnold", "sgtk_mantra", "ifd", "sgtk_alembic", "alembic"]:
                            print("[x] Node type '{}' is not supported.".format(node.type().name()))
                        else:
                            if not shotgun_active:
                                print("[x] Shotgun environment disabled, skipping this step...")
                            else:
                                print("[*] Collecting info...")

                                try:
                                    import sgtk
                                except ImportError:
                                    msg = "[x] Could not import sgtk module..."
                                    print(msg)
                                    hou.ui.displayMessage(msg)
                                    sys.exit()

                                camera = node.parm( "camera" ).eval()
                                cameraNode = node.node(camera)

                                width = cameraNode.parm("resx").eval()
                                height = cameraNode.parm("resy").eval()

                                current_engine = sgtk.platform.current_engine()
                                app = current_engine.apps.get("tk-cs-multi-review")
                                create = app.lib.create_review("render", app, {"width": width, "height": height, "node": node.name()})

                                if not create:
                                    msg = "[x] Could not create Shotgun Review Item. This is probably caused by en existing item. Please, save new scene version and try again..."
                                    print(msg)
                                    hou.ui.displayMessage(msg)
                                    sys.exit()
                                else:
                                    print("[*] Adding Extra Info Key-Value Pairs...")
                                    SGReviewItemID = create[0]
                                    SGUserID = create[1]
                                    SGReviewResources = create[2]
                                    fileHandle.write( "ExtraInfoKeyValue0=SGReviewItemID={}\n".format(SGReviewItemID) )
                                    fileHandle.write( "ExtraInfoKeyValue1=SGUserID={}\n".format(SGUserID) )
                                    fileHandle.write( "ExtraInfoKeyValue2=SGReviewResources={}\n".format(SGReviewResources) )

                                    print("[*] Adding post-job script...")
                                    postTaskShotgunScript = os.path.join(SGReviewResources, "scripts", "deadline_prepare.py")
                                    fileHandle.write( "PreJobScript={}\n".format(postTaskShotgunScript.replace("\\", "/")) )

                                    print("[*] Done...")

                    if jobProperties.get( "jobsuspended", False ):
                        fileHandle.write( "InitialStatus=Suspended\n" )

                    if jobProperties.get( "isblacklist", False ):
                        fileHandle.write( "Blacklist=%s\n" % jobProperties.get( "machinelist", "" ) )
                    else:
                        fileHandle.write( "Whitelist=%s\n" % jobProperties.get( "machinelist", "" ) )

                    if isHQueueSim:
                        sliceCount = hqueueSliceCount( node )
                        fileHandle.write( "Frames=0-%s\n" % ( sliceCount - 1 ) )
                    elif singleFrameTiles and tilesEnabled:
                        if not exportJob:
                            fileHandle.write( "TileJob=True\n" )
                            if jigsawEnabled:
                                fileHandle.write( "TileJobTilesInX=%s\n" % jigsawRegionCount )
                                fileHandle.write( "TileJobTilesInY=%s\n" % 1 )
                            else:
                                fileHandle.write( "TileJobTilesInX=%s\n" % tilesInX )
                                fileHandle.write( "TileJobTilesInY=%s\n" % tilesInY )
                            fileHandle.write( "TileJobFrame=%s\n" % singleFrame  );
                        else:
                            fileHandle.write( "Frames=%s\n" % singleFrame )
                    elif jobProperties.get( "overrideframes", False ):
                        fileHandle.write( "Frames=%s\n" % jobProperties.get( "framelist","0" ) )
                    else:
                        fileHandle.write( "Frames=%s\n" % GetFrameInfo( node ) )

                    if isHQueueSim:
                        fileHandle.write( "ChunkSize=1\n" )
                    elif node.type().name() == "rop_alembic":
                        if not node.parm("render_full_range").eval():
                            fileHandle.write("ChunkSize=10000\n" )
                        else:
                            fileHandle.write( "ChunkSize=%s\n" %  jobProperties.get( "framespertask", 1 ) )
                    elif singleFrameTiles and tilesEnabled:
                        if exportJob:
                            fileHandle.write( "ChunkSize=1\n" )
                        else:
                            fileHandle.write( "ChunkSize=%s\n" %  jobProperties.get( "framespertask", 1 ) )
                    else:
                        fileHandle.write( "ChunkSize=%s\n" %  jobProperties.get( "framespertask", 1 ) )

                    if tilesEnabled and singleFrameTiles and not exportJob:
                        imageFileName = outputFile
                        tileName = ""
                        paddingRegex = re.compile( "(#+)", re.IGNORECASE )
                        matches = paddedNumberRegex.findall( imageFileName )
                        if matches != None and len( matches ) > 0:
                            paddingString = matches[ len( matches ) - 1 ]
                            paddingSize = len( paddingString )
                            padding = str( singleFrame )
                            padding = "_tile?_" + padding
                            tileName = RightReplace( imageFileName, paddingString, padding, 1 )
                        else:
                            splitFilename = os.path.splitext(imageFileName)
                            tileName = splitFilename[0]+"_tile?_"+splitFilename[1]

                        tileRange = range(0, tilesInX*tilesInY)
                        if jigsawEnabled:
                            tileRange = range(0, jigsawRegionCount)

                        for currTile in tileRange:
                            regionOutputFileName = tileName.replace( "?", str(currTile) )
                            fileHandle.write( "OutputFilename0Tile%s=%s\n"%(currTile,regionOutputFileName) )

                    if not exportJob:
                        if paddedOutputFile != "":
                            tempPaddedOutputFile = paddedOutputFile
                            if isRedshift:
                                tempPaddedOutputFile += node.parm( "RS_outputFileFormat" ).evalAsString()

                            fileHandle.write( "OutputFilename0=%s\n" % tempPaddedOutputFile )

                            doDraft = True
                            doShotgun = True
                    elif ifdFile != "":
                        fileHandle.write( "OutputDirectory0=%s\n" % os.path.dirname( ifdFile ) )

                    if ( singleFrameTiles and tilesEnabled ) or exportJob or separateWedgeJobs:
                        groupBatch = True

                    if not ( tilesEnabled or exportJob ):
                        groupBatch = WriteIntegrationSettings( fileHandle, doShotgun, doDraft, groupBatch, integrationKVPs )

                    if groupBatch:
                        fileHandle.write( "BatchName=%s\n" % jobProperties.get( "jobname", "Untitled" ) )

                pluginInfoFile = os.path.join( homeDir, "temp", "houdini_plugin_info%d.job" % (wedgeNum * regionJobCount + regionjobNum) )
                with open( pluginInfoFile, "w" ) as fileHandle:
                    if not jobProperties.get( "submitscene",False ):
                        fileHandle.write( "SceneFile=%s\n" % hou.hipFile.path() )

                    #alf sets it's own output driver
                    if node.type().description() == "Alfred" and node.parm( "alf_driver" ) != None:
                        fileHandle.write( "OutputDriver=%s\n" % node.parm( "alf_driver" ).eval() )
                    else:
                        fileHandle.write( "OutputDriver=%s\n" % node.path() )

                    fileHandle.write( "IgnoreInputs=%s\n" % jobProperties.get( "ignoreinputs", False ) )
                    ver = hou.applicationVersion()
                    fileHandle.write( "Version=%s.%s\n" % ( ver[0], ver[1] ) )
                    fileHandle.write( "Build=%s\n" % jobProperties.get( "bits", "None" ) )

                    if isHQueueSim:
                        fileHandle.write( "SimJob=True\n" )
                        sliceType = node.parm( "slice_type" ).evalAsString()
                        requiresTracking = ( sliceType == "volume" or sliceType == "particle" )
                        fileHandle.write( "SimRequiresTracking=%s\n" % requiresTracking )

                    if separateWedgeJobs and isWedge:
                        fileHandle.write("WedgeNum=%s\n" % wedgeJobCount )

                    fileHandle.write( "OpenCLUseGPU=%s\n" % jobProperties.get( "gpuopenclenable", False ) )
                    fileHandle.write( "GPUsPerTask=%s\n" % jobProperties.get( "gpuspertask", 0 ) )
                    fileHandle.write( "SelectGPUDevices=%s\n" % jobProperties.get( "gpudevices", "" ) )

                    if not exportJob and tilesEnabled:
                        fileHandle.write( "RegionRendering=True\n" )
                        if singleFrameTiles:
                            curRegion = 0
                            if jigsawEnabled:
                                for region in range( 0, jigsawRegionCount ):
                                    xstart = jigsawRegions[region*4]
                                    xend = jigsawRegions[region*4 + 1]
                                    ystart = jigsawRegions[region*4 + 2]
                                    yend = jigsawRegions[region*4 + 3]

                                    fileHandle.write( "RegionLeft%s=%s\n" % (curRegion, xstart) )
                                    fileHandle.write( "RegionRight%s=%s\n" % (curRegion, xend) )
                                    fileHandle.write( "RegionBottom%s=%s\n" % (curRegion, ystart) )
                                    fileHandle.write( "RegionTop%s=%s\n" % (curRegion,yend) )
                                    curRegion += 1
                            else:
                                for y in range(0, tilesInY):
                                    for x in range(0, tilesInX):

                                        xstart = x * 1.0 / tilesInX
                                        xend = ( x + 1.0 ) / tilesInX
                                        ystart = y * 1.0 / tilesInY
                                        yend = ( y + 1.0 ) / tilesInY

                                        fileHandle.write( "RegionLeft%s=%s\n" % (curRegion, xstart) )
                                        fileHandle.write( "RegionRight%s=%s\n" % (curRegion, xend) )
                                        fileHandle.write( "RegionBottom%s=%s\n" % (curRegion, ystart) )
                                        fileHandle.write( "RegionTop%s=%s\n" % (curRegion,yend) )
                                        curRegion += 1
                        else:
                            fileHandle.write( "CurrentTile=%s\n" % regionjobNum )

                            if jigsawEnabled:
                                xstart = jigsawRegions[ regionjobNum * 4 ]
                                xend = jigsawRegions[ regionjobNum * 4 + 1 ]
                                ystart = jigsawRegions[ regionjobNum * 4 + 2 ]
                                yend = jigsawRegions[ regionjobNum * 4 + 3 ]

                                fileHandle.write( "RegionLeft=%s\n" % xstart )
                                fileHandle.write( "RegionRight=%s\n" % xend )
                                fileHandle.write( "RegionBottom=%s\n" % ystart )
                                fileHandle.write( "RegionTop=%s\n" % yend )
                            else:
                                curY, curX = divmod(regionjobNum, tilesInX)

                                xstart = curX * 1.0 / tilesInX
                                xend = ( curX + 1.0 ) / tilesInX
                                ystart = curY * 1.0 / tilesInY
                                yend = ( curY + 1.0 ) / tilesInY

                                fileHandle.write( "RegionLeft=%s\n" % xstart )
                                fileHandle.write( "RegionRight=%s\n" % xend )
                                fileHandle.write( "RegionBottom=%s\n" % ystart )
                                fileHandle.write( "RegionTop=%s\n" % yend )

                arguments = []
                arguments.append( jobInfoFile )
                arguments.append( pluginInfoFile )
                if jobProperties.get( "submitscene", False ):
                    arguments.append( hou.hipFile.path() )

                jobResult = CallDeadlineCommand( arguments )
                jobId = ""
                resultArray = jobResult.split("\n")
                for line in resultArray:
                    if line.startswith("JobID="):
                        jobId = line.replace("JobID=","")
                        jobId = jobId.strip()
                        break

                renderJobIds.append( jobId )

                print("---------------------------------------------------")
                print(jobResult)
                print("---------------------------------------------------")

        if exportJob:
            exportTilesEnabled = tilesEnabled
            exportJobCount = 1

            exportType = node.type().description()

            # rename the export type to RenderMan so the RenderMan Deadline plugin is used
            if exportType == "RenderMan RIS":
                exportType = "RenderMan"

            lowerExportType = exportType.lower()
            if exportTilesEnabled:
                if ( exportType == "Mantra" and node.parm("vm_tile_render") is not None ) or exportType == "Arnold":
                    if not singleFrameTiles:
                        if jigsawEnabled:
                            exportJobCount = jigsawRegionCount
                        else:
                            exportJobCount = tilesInX * tilesInY
                else:
                    exportTilesEnabled = False
            exportJobDependencies = ",".join( renderJobIds )

            for exportJobNum in range( 0, exportJobCount ):
                exportJobInfoFile = os.path.join( homeDir, "temp", "export_job_info%d.job" % exportJobNum )
                exportPluginInfoFile = os.path.join( homeDir, "temp", "export_plugin_info%d.job" % exportJobNum )
                exportJobName = ( jobProperties.get( "jobname", "Untitled" ) + "- " + exportType + "- " +node.path() )
                if exportTilesEnabled and not singleFrameTiles:
                    exportJobName += " - Region " + str( exportJobNum )

                with open( exportJobInfoFile, 'w' ) as fileHandle:
                    fileHandle.write( "Plugin=%s\n" % exportType )
                    fileHandle.write( "Name=%s\n" % exportJobName )
                    if exportTilesEnabled or not isExportLocal( node, jobProperties  ):
                        fileHandle.write( "BatchName=%s\n" % jobProperties.get( "jobname", "Untitled" ) )

                    fileHandle.write( "Comment=%s\n" % jobProperties.get( "comment", "" ) )
                    fileHandle.write( "Department=%s\n" % jobProperties.get( "department", "" ) )
                    fileHandle.write( "Pool=%s\n" % jobProperties.get( ( "%spool" % lowerExportType ), "None" ) )
                    fileHandle.write( "SecondaryPool=%s\n" % jobProperties.get( ( "%ssecondarypool" % lowerExportType ), "" ) )
                    fileHandle.write( "Group=%s\n" % jobProperties.get( ( "%sgroup" % lowerExportType ), "None" ) )
                    fileHandle.write( "Priority=%s\n" % jobProperties.get( ( "%spriority" % lowerExportType ), 50 ) )
                    fileHandle.write( "TaskTimeoutMinutes=%s\n" % jobProperties.get( ( "%stasktimeout" % lowerExportType ), 0 ) )
                    fileHandle.write( "EnableAutoTimeout=%s\n" % jobProperties.get( ( "%sautotimeout" % lowerExportType ), False ) )
                    fileHandle.write( "ConcurrentTasks=%s\n" % jobProperties.get( ( "%sconcurrent" % lowerExportType ), 1 ) )
                    fileHandle.write( "MachineLimit=%s\n" % jobProperties.get( ( "%smachinelimit" % lowerExportType ), 0 ) )
                    fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % jobProperties.get( ( "%sslavelimit" % lowerExportType ), False ) )
                    fileHandle.write( "LimitGroups=%s\n" % jobProperties.get( ( "%slimits" % lowerExportType ), 0 ) )
                    fileHandle.write( "JobDependencies=%s\n" % exportJobDependencies )
                    fileHandle.write( "IsFrameDependent=true\n" )
                    fileHandle.write( "OnJobComplete=%s\n" % jobProperties.get( "%sonjobcomplete" % lowerExportType, jobProperties.get( "onjobcomplete", "Nothing" ) ) )

                    if jobProperties.get( "jobsuspended", False ):
                        fileHandle.write( "InitialStatus=Suspended\n" )

                    if jobProperties.get( ( "%sisblacklist" % lowerExportType ), False ):
                        fileHandle.write( "Blacklist=%s\n" % jobProperties.get( ( "%smachinelist" % lowerExportType ), "" ) )
                    else:
                        fileHandle.write( "Whitelist=%s\n" % jobProperties.get( ( "%smachinelist" % lowerExportType ), "" ) )

                    if exportTilesEnabled and singleFrameTiles:
                        fileHandle.write( "TileJob=True\n" )
                        if jigsawEnabled:
                            fileHandle.write( "TileJobTilesInX=%s\n" % jigsawRegionCount )
                            fileHandle.write( "TileJobTilesInY=%s\n" % 1 )
                        else:
                            fileHandle.write( "TileJobTilesInX=%s\n" % tilesInX )
                            fileHandle.write( "TileJobTilesInY=%s\n" % tilesInY )

                        fileHandle.write( "TileJobFrame=%s\n" % singleFrame )
                    elif jobProperties.get( "overrideframes", False ):
                        fileHandle.write( "Frames=%s\n" % jobProperties.get( "framelist","0" ) )
                        fileHandle.write( "ChunkSize=1\n" )
                    else:
                        fileHandle.write( "Frames=%s\n" % GetFrameInfo( node ) )
                        fileHandle.write( "ChunkSize=1\n" )

                    if paddedOutputFile != "":
                        if exportTilesEnabled and singleFrameTiles:
                            tileName = paddedOutputFile
                            paddingRegex = re.compile( "(#+)", re.IGNORECASE )
                            matches = paddingRegex.findall( os.path.basename( tileName ) )
                            if matches != None and len( matches ) > 0:
                                paddingString = matches[ len( matches ) - 1 ]
                                paddingSize = len( paddingString )
                                padding = str(singleFrame)
                                while len(padding) < paddingSize:
                                    padding = "0" + padding

                                padding = "_tile?_" + padding
                                tileName = RightReplace( tileName, paddingString, padding, 1 )
                            else:
                                splitFilename = os.path.splitext(tileName)
                                tileName = splitFilename[0]+"_tile?_"+splitFilename[1]

                            for currTile in range(0, tilesInX*tilesInY):
                                regionOutputFileName = tileName.replace( "?", str(currTile) )
                                fileHandle.write( "OutputFilename0Tile%s=%s\n"%(currTile,regionOutputFileName) )

                        else:
                            fileHandle.write( "OutputFilename0=%s\n" % paddedOutputFile)

                    if not tilesEnabled:
                        WriteIntegrationSettings( fileHandle, True, True, True, integrationKVPs )

                with open( exportPluginInfoFile, 'w' ) as fileHandle:
                    if exportType == "Mantra":
                        fileHandle.write( "SceneFile=%s\n" % paddedIfdFile )

                        majorVersion, minorVersion = hou.applicationVersion()[:2]
                        fileHandle.write( "Version=%s.%s\n" % ( majorVersion, minorVersion ) )
                        fileHandle.write( "Threads=%s\n" % jobProperties.get( "mantrathreads", 0 ) )
                        fileHandle.write( "CommandLineOptions=\n" )

                        if exportTilesEnabled:
                            fileHandle.write( "RegionRendering=True\n" )
                            if singleFrameTiles:
                                curRegion = 0
                                if jigsawEnabled:
                                    for region in range(0,jigsawRegionCount):
                                        xstart = jigsawRegions[ region * 4 ]
                                        xend = jigsawRegions[ region * 4 + 1 ]
                                        ystart = jigsawRegions[ region * 4 + 2 ]
                                        yend = jigsawRegions[ region * 4 + 3 ]

                                        fileHandle.write( "RegionLeft%s=%s\n" % (curRegion, xstart) )
                                        fileHandle.write( "RegionRight%s=%s\n" % (curRegion, xend) )
                                        fileHandle.write( "RegionBottom%s=%s\n" % (curRegion, ystart) )
                                        fileHandle.write( "RegionTop%s=%s\n" % (curRegion,yend) )
                                        curRegion += 1
                                else:
                                    for y in range(0, tilesInY):
                                        for x in range(0, tilesInX):

                                            xstart = x * 1.0 / tilesInX
                                            xend = ( x + 1.0 ) / tilesInX
                                            ystart = y * 1.0 / tilesInY
                                            yend = ( y + 1.0 ) / tilesInY

                                            fileHandle.write( "RegionLeft%s=%s\n" % (curRegion, xstart) )
                                            fileHandle.write( "RegionRight%s=%s\n" % (curRegion, xend) )
                                            fileHandle.write( "RegionBottom%s=%s\n" % (curRegion, ystart) )
                                            fileHandle.write( "RegionTop%s=%s\n" % (curRegion,yend) )
                                            curRegion += 1
                            else:
                                fileHandle.write( "CurrentTile=%s\n" % exportJobNum )

                                if jigsawEnabled:
                                    xstart = jigsawRegions[j*4]
                                    xend = jigsawRegions[j*4+1]
                                    ystart = jigsawRegions[j*4+2]
                                    yend = jigsawRegions[j*4+3]

                                    fileHandle.write( "RegionLeft=%s\n" % xstart )
                                    fileHandle.write( "RegionRight=%s\n" % xend )
                                    fileHandle.write( "RegionBottom=%s\n" % ystart )
                                    fileHandle.write( "RegionTop=%s\n" % yend )
                                else:
                                    curY, curX = divmod(exportJobNum, tilesInX)

                                    xstart = curX * 1.0 / tilesInX
                                    xend = ( curX + 1.0 ) / tilesInX
                                    ystart = curY * 1.0 / tilesInY
                                    yend = ( curY + 1.0 ) / tilesInY

                                    fileHandle.write( "RegionLeft=%s\n" % xstart )
                                    fileHandle.write( "RegionRight=%s\n" % xend )
                                    fileHandle.write( "RegionBottom=%s\n" % ystart )
                                    fileHandle.write( "RegionTop=%s\n" % yend )

                    elif exportType == "Arnold":
                        fileHandle.write( "InputFile=" + ifdFile + "\n" );
                        fileHandle.write( "Threads=%s\n" % jobProperties.get( "arnoldthreads", 0 ) )
                        fileHandle.write( "CommandLineOptions=\n" );
                        fileHandle.write( "Verbose=4\n" );

                        if exportTilesEnabled:
                            fileHandle.write( "RegionJob=True\n" )

                            camera = node.parm( "camera" ).eval()
                            cameraNode = node.node(camera)

                            width = cameraNode.parm("resx").eval()
                            height = cameraNode.parm("resy").eval()

                            if singleFrameTiles:
                                fileHandle.write( "SingleAss=True\n" )
                                fileHandle.write( "SingleRegionFrame=%s\n"% singleFrame )
                                curRegion = 0


                                output = GetOutputPath( node )
                                imageFileName = outputFile
                                if imageFileName == "":
                                    continue

                                tileName = ""
                                outputName = ""
                                paddingRegex = re.compile( "(#+)", re.IGNORECASE )
                                matches = paddedNumberRegex.findall( imageFileName )
                                if matches != None and len( matches ) > 0:
                                    paddingString = matches[ len( matches ) - 1 ]
                                    paddingSize = len( paddingString )
                                    padding = str(singleFrame)
                                    while len(padding) < paddingSize:
                                        padding = "0" + padding

                                    outputName = RightReplace( imageFileName, paddingString, padding, 1 )
                                    padding = "_tile#_" + padding
                                    tileName = RightReplace( imageFileName, paddingString, padding, 1 )
                                else:
                                    outputName = imageFileName
                                    splitFilename = os.path.splitext(imageFileName)
                                    tileName = splitFilename[0]+"_tile#_"+splitFilename[1]

                                if jigsawEnabled:
                                    for region in range(0,jigsawRegionCount):
                                        xstart = int(jigsawRegions[region*4] * width +0.5 )
                                        xend = int(jigsawRegions[region*4+1] * width +0.5 )
                                        ystart = int(jigsawRegions[region*4+2] * height +0.5 )
                                        yend = int(jigsawRegions[region*4+3] * height +0.5 )

                                        if xend >= width:
                                            xend  = width-1
                                        if yend >= height:
                                            yend  = height-1

                                        regionOutputFileName = tileName
                                        matches = paddingRegex.findall( os.path.basename( tileName ) )
                                        if matches != None and len( matches ) > 0:
                                            paddingString = matches[ len( matches ) - 1 ]
                                            paddingSize = len( paddingString )
                                            padding = str(curRegion)
                                            while len(padding) < paddingSize:
                                                padding = "0" + padding
                                            regionOutputFileName = RightReplace( tileName, paddingString, padding, 1 )

                                        fileHandle.write( "RegionFilename%s=%s\n" % (curRegion, regionOutputFileName) )
                                        fileHandle.write( "RegionLeft%s=%s\n" % (curRegion, xstart) )
                                        fileHandle.write( "RegionRight%s=%s\n" % (curRegion, xend) )
                                        fileHandle.write( "RegionBottom%s=%s\n" % (curRegion,yend) )
                                        fileHandle.write( "RegionTop%s=%s\n" % (curRegion,ystart) )
                                        curRegion += 1
                                else:
                                    for y in range(0, tilesInY):
                                        for x in range(0, tilesInX):

                                            xstart = x * 1.0 / tilesInX
                                            xend = ( x + 1.0 ) / tilesInX
                                            ystart = y * 1.0 / tilesInY
                                            yend = ( y + 1.0 ) / tilesInY

                                            xstart = int(xstart * width +0.5 )
                                            xend = int(xend * width +0.5 )
                                            ystart = int(ystart * height +0.5 )
                                            yend = int(yend * height +0.5 )

                                            if xend >= width:
                                                xend  = width-1
                                            if yend >= height:
                                                yend  = height-1

                                            regionOutputFileName = tileName
                                            matches = paddingRegex.findall( os.path.basename( tileName ) )
                                            if matches != None and len( matches ) > 0:
                                                paddingString = matches[ len( matches ) - 1 ]
                                                paddingSize = len( paddingString )
                                                padding = str(curRegion)
                                                while len(padding) < paddingSize:
                                                    padding = "0" + padding
                                                regionOutputFileName = RightReplace( tileName, paddingString, padding, 1 )

                                            fileHandle.write( "RegionFilename%s=%s\n" % (curRegion, regionOutputFileName) )
                                            fileHandle.write( "RegionLeft%s=%s\n" % (curRegion, xstart) )
                                            fileHandle.write( "RegionRight%s=%s\n" % (curRegion, xend) )
                                            fileHandle.write( "RegionBottom%s=%s\n" % (curRegion, yend) )
                                            fileHandle.write( "RegionTop%s=%s\n" % (curRegion,ystart) )
                                            curRegion += 1
                            else:
                                fileHandle.write( "CurrentTile=%s\n" % exportJobNum )
                                fileHandle.write( "SingleAss=False\n" )
                                if jigsawEnabled:
                                    xstart = jigsawRegions[j*4]
                                    xend = jigsawRegions[j*4+1]
                                    ystart = jigsawRegions[j*4+2]
                                    yend = jigsawRegions[j*4+3]

                                    fileHandle.write( "RegionLeft=%s\n" % xstart )
                                    fileHandle.write( "RegionRight=%s\n" % xend )
                                    fileHandle.write( "RegionBottom=%s\n" % ystart )
                                    fileHandle.write( "RegionTop=%s\n" % yend )
                                else:
                                    curY = 0
                                    curX = 0
                                    jobNumberFound = False
                                    tempJobNum = 0
                                    for y in range(0, tilesInY):
                                        for x in range(0, tilesInX):
                                            if tempJobNum == exportJobNum:
                                                curY = y
                                                curX = x
                                                jobNumberFound = True
                                                break
                                            tempJobNum = tempJobNum + 1
                                        if jobNumberFound:
                                            break

                                    xstart = curX * 1.0 / tilesInX
                                    xend = ( curX + 1.0 ) / tilesInX
                                    ystart = curY * 1.0 / tilesInY
                                    yend = ( curY + 1.0 ) / tilesInY

                                    fileHandle.write( "RegionLeft=%s\n" % xstart )
                                    fileHandle.write( "RegionRight=%s\n" % xend )
                                    fileHandle.write( "RegionBottom=%s\n" % ystart )
                                    fileHandle.write( "RegionTop=%s\n" % yend )

                    elif exportType == "RenderMan":
                        fileHandle.write( "RibFile=" + ifdFile + "\n" )
                        fileHandle.write( "Threads=%s\n" % jobProperties.get( "rendermanthreads", 0 ) )
                        fileHandle.write( "CommandLineOptions=%s\n" % jobProperties.get( "rendermanarguments", "" ) )
                        fileHandle.write( "WorkingDirectory=\n" )

                    elif exportType == "Redshift":
                        fileHandle.write( "SceneFile=%s\n" % ifdFile )
                        fileHandle.write( "WorkingDirectory=\n" )
                        fileHandle.write( "CommandLineOptions=%s\n" % jobProperties.get( "redshiftarguments", "" ) )
                        fileHandle.write( "GPUsPerTask=%s\n" % jobProperties.get( "gpuspertask", 0 ) )
                        fileHandle.write( "SelectGPUDevices=%s\n" % jobProperties.get( "gpudevices", "" ) )

                arguments = []
                arguments.append( exportJobInfoFile )
                arguments.append( exportPluginInfoFile )

                jobResult = CallDeadlineCommand( arguments )
                jobId = ""
                resultArray = jobResult.split()
                for line in resultArray:
                    if line.startswith( "JobID=" ):
                        jobId = line.replace( "JobID=","" )
                        break

                exportJobIds.append( jobId )

                print("---------------------------------------------------")
                print(jobResult)
                print("---------------------------------------------------")

        if tilesEnabled and jobProperties.get( "submitdependentassembly" ) and len(renderJobIds)>0:
            assemblyJobIds = []

            renderFrames = None
            if singleFrameTiles:
                renderFrames = [ singleFrame ]
            else:
                if jobProperties.get( "overrideframes", False ):
                    frameList = CallDeadlineCommand( [ "-ParseFrameList", jobProperties.get( "framelist","0" ) ,"False" ] ).strip()
                    renderFrames = frameList.split( "," )
                else:
                    frameList = CallDeadlineCommand( [ "-ParseFrameList", GetFrameInfo( node ) ,"False" ] ).strip()
                    renderFrames = frameList.split( "," )

            jobName = jobProperties.get( "jobname", "Untitled" )
            jobName = "%s - %s - Assembly"%(jobName, node.path())

            # Create submission info file
            jobInfoFile = os.path.join(homeDir, "temp", "jigsaw_submit_info%d.job") % wedgeNum
            fileHandle = open( jobInfoFile, "w" )
            fileHandle.write( "Plugin=DraftTileAssembler\n" )
            fileHandle.write( "Name=%s\n" % jobName )
            fileHandle.write( "Comment=%s\n" % jobProperties.get( "comment", "" ) )
            fileHandle.write( "Department=%s\n" % jobProperties.get( "department", "" ) )
            fileHandle.write( "Pool=%s\n" % jobProperties.get( "pool", "None" ) )
            fileHandle.write( "SecondaryPool=%s\n" % jobProperties.get( "secondarypool", "" ) )
            fileHandle.write( "Group=%s\n" % jobProperties.get( "group", "None" ) )
            fileHandle.write( "Priority=%s\n" % jobProperties.get( "priority", 50 ) )
            fileHandle.write( "TaskTimeoutMinutes=%s\n" % jobProperties.get( "tasktimeout", 0 ) )
            fileHandle.write( "EnableAutoTimeout=%s\n" % jobProperties.get( "autotimeout", False ) )
            fileHandle.write( "ConcurrentTasks=%s\n" % jobProperties.get( "concurrent", 1 ) )
            fileHandle.write( "MachineLimit=%s\n" % jobProperties.get( "machinelimit", 0 ) )
            fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % jobProperties.get( "slavelimit", False ) )
            fileHandle.write( "LimitGroups=%s\n" % jobProperties.get( "limits", 0 ) )
            if exportJob:
                fileHandle.write( "JobDependencies=%s\n" % ",".join( exportJobIds ) )
            else:
                fileHandle.write( "JobDependencies=%s\n" % ",".join( renderJobIds ) )
            fileHandle.write( "OnJobComplete=%s\n" % jobProperties.get( "onjobcomplete", "Nothing" ) )

            if jobProperties.get( "jobsuspended", False ):
                fileHandle.write( "InitialStatus=Suspended\n" )

            if jobProperties.get( "isblacklist", False ):
                fileHandle.write( "Blacklist=%s\n" % jobProperties.get( "machinelist", "" ) )
            else:
                fileHandle.write( "Whitelist=%s\n" % jobProperties.get( "machinelist", "" ) )


            if singleFrameTiles:
                fileHandle.write( "Frames=%s\n" % singleFrame )
            else:
                fileHandle.write( "IsFrameDependent=true\n" )
                if jobProperties.get( "overrideframes", False ):
                    fileHandle.write( "Frames=%s\n" % jobProperties.get( "framelist","0" ) )
                else:
                    fileHandle.write( "Frames=%s\n" % GetFrameInfo( node ) )

            fileHandle.write( "ChunkSize=1\n" )

            if paddedOutputFile != "":
                fileHandle.write( "OutputFilename0=%s\n" % paddedOutputFile )
            else:
                fileHandle.write( "OutputDirectory0=%s\n" % os.path.dirname( ifdFile ) )

            WriteIntegrationSettings( fileHandle, True, True, True, integrationKVPs )

            fileHandle.write( "BatchName=%s\n" % jobProperties.get( "jobname", "Untitled" ) )

            fileHandle.close()

            # Create plugin info file
            pluginInfoFile = os.path.join( homeDir, "temp", "jigsaw_plugin_info%d.job" % wedgeNum )
            fileHandle = open( pluginInfoFile, "w" )

            fileHandle.write( "ErrorOnMissing=%s\n" % jobProperties.get( "erroronmissingtiles", True ) )
            fileHandle.write( "ErrorOnMissingBackground=%s\n" % jobProperties.get( "erroronmissingbackground", True ) )

            fileHandle.write( "CleanupTiles=%s\n" % jobProperties.get( "cleanuptiles", True ) )
            fileHandle.write( "MultipleConfigFiles=%s\n" % True )

            fileHandle.close()

            configFiles = []

            for frame in renderFrames:

                output = GetOutputPath( node )
                imageFileName = outputFile

                tileName = ""
                outputName = ""
                paddingRegex = re.compile( "(#+)", re.IGNORECASE )
                matches = paddedNumberRegex.findall( imageFileName )
                if matches != None and len( matches ) > 0:
                    paddingString = matches[ len( matches ) - 1 ]
                    paddingSize = len( paddingString )
                    padding = str(frame)
                    while len(padding) < paddingSize:
                        padding = "0" + padding

                    outputName = RightReplace( imageFileName, paddingString, padding, 1 )
                    padding = "_tile#_" + padding
                    tileName = RightReplace( imageFileName, paddingString, padding, 1 )
                else:
                    outputName = imageFileName
                    splitFilename = os.path.splitext(imageFileName)
                    tileName = splitFilename[0]+"_tile#_"+splitFilename[1]

                # Create the directory for the config file if it doesn't exist.
                directory = os.path.dirname(imageFileName)
                if not os.path.exists(directory):
                    os.makedirs(directory)

                fileName, fileExtension = os.path.splitext(imageFileName)

                date = time.strftime("%Y_%m_%d_%H_%M_%S")
                configFilename = fileName+"_"+str(frame)+"_config_"+date+".txt"
                fileHandle = open( configFilename, "w" )
                fileHandle.write( "\n" )

                fileHandle.write( "ImageFileName=" +outputName +"\n" )
                backgroundType = jobProperties.get( "backgroundoption", "None" )

                if backgroundType == "Previous Output":
                    fileHandle.write( "BackgroundSource=" +outputName +"\n" )
                elif backgroundType == "Selected Image":
                    fileHandle.write( "BackgroundSource=" + jobProperties.get( "backgroundimage", "" ) +"\n" )

                if isArnold:
                    renderWidth = cameraNode.parm("resx").eval()
                    renderHeight = cameraNode.parm("resy").eval()
                    fileHandle.write("ImageHeight=%s\n" % renderHeight)
                    fileHandle.write("ImageWidth=%s\n" % renderWidth)
                fileHandle.write( "TilesCropped=False\n" )

                if jigsawEnabled:
                    fileHandle.write( "TileCount=" +str( jigsawRegionCount ) + "\n" )
                else:
                    fileHandle.write( "TileCount=" +str( tilesInX * tilesInY ) + "\n" )
                fileHandle.write( "DistanceAsPixels=False\n" )

                currTile = 0
                if jigsawEnabled:
                    for region in range(0,jigsawRegionCount):
                        width = jigsawRegions[region*4+1]-jigsawRegions[region*4]
                        height = jigsawRegions[region*4+3]-jigsawRegions[region*4+2]
                        xRegion = jigsawRegions[region*4]
                        yRegion = jigsawRegions[region*4+2]

                        regionOutputFileName = tileName
                        matches = paddingRegex.findall( os.path.basename( tileName ) )
                        if matches != None and len( matches ) > 0:
                            paddingString = matches[ len( matches ) - 1 ]
                            paddingSize = len( paddingString )
                            padding = str(currTile)
                            while len(padding) < paddingSize:
                                padding = "0" + padding
                            regionOutputFileName = RightReplace( tileName, paddingString, padding, 1 )

                        fileHandle.write( "Tile%iFileName=%s\n"%(currTile,regionOutputFileName) )
                        fileHandle.write( "Tile%iX=%s\n"%(currTile,xRegion) )
                        if isArnold:
                            fileHandle.write( "Tile%iY=%s\n"%(currTile,1.0-yRegion-height) )
                        else:
                            fileHandle.write( "Tile%iY=%s\n"%(currTile,yRegion) )
                        fileHandle.write( "Tile%iWidth=%s\n"%(currTile,width) )
                        fileHandle.write( "Tile%iHeight=%s\n"%(currTile,height) )
                        currTile += 1
                    fileHandle.close()
                    configFiles.append(configFilename)
                else:
                    for y in range(0, tilesInY):
                        for x in range(0, tilesInX):
                            width = 1.0/tilesInX
                            height = 1.0/tilesInY
                            xRegion = x*width
                            yRegion = y*height

                            regionOutputFileName = tileName
                            matches = paddingRegex.findall( os.path.basename( tileName ) )
                            if matches != None and len( matches ) > 0:
                                paddingString = matches[ len( matches ) - 1 ]
                                paddingSize = len( paddingString )
                                padding = str(currTile)
                                while len(padding) < paddingSize:
                                    padding = "0" + padding
                                regionOutputFileName = RightReplace( tileName, paddingString, padding, 1 )

                            fileHandle.write( "Tile%iFileName=%s\n"%(currTile,regionOutputFileName) )
                            fileHandle.write( "Tile%iX=%s\n"%(currTile,xRegion) )
                            if isArnold:
                                fileHandle.write( "Tile%iY=%s\n"%(currTile,1.0-yRegion-height) )
                            else:
                                fileHandle.write( "Tile%iY=%s\n"%(currTile,yRegion) )
                            fileHandle.write( "Tile%iWidth=%s\n"%(currTile,width) )
                            fileHandle.write( "Tile%iHeight=%s\n"%(currTile,height) )
                            currTile += 1
                    fileHandle.close()
                    configFiles.append(configFilename)

            arguments = []
            arguments.append( jobInfoFile )
            arguments.append( pluginInfoFile )
            arguments.extend( configFiles )

            jobResult = CallDeadlineCommand( arguments )

            jobId = ""
            resultArray = jobResult.split()
            for line in resultArray:
                if line.startswith("JobID="):
                    jobId = line.replace("JobID=","")
                    break

            assemblyJobIds.append( jobId )

            print("---------------------------------------------------")
            print(jobResult)
            print("---------------------------------------------------")


    if not exportJob and not tilesEnabled:
        return renderJobIds
    elif exportJob and not tilesEnabled:
        return exportJobIds
    else:
        return assemblyJobIds

from __future__ import print_function
import os
import sys
import ast
import uuid
import json
import socket
import tempfile
import threading
import traceback
import subprocess

import hou

try:
    import sgtk
    SGTK_INITIALIZED = True
except ImportError:
    SGTK_INITIALIZED = False

from CallDeadlineCommand import CallDeadlineCommand
import SubmitHoudiniToDeadlineFunctions as SHTDFunctions

try:
    import configparser
except:
    try:
        import ConfigParser
    except:
        print("Could not load ConfigParser module, sticky settings will not be loaded/saved")

dialog = None
closing = False

containsWedge = False

stickyProps = [
    # [ propertyName, isThePropertyAnInteger ]
    [ 'department', False ],
    [ 'pool', False ],
    [ 'secondarypool', False ],
    [ 'group', False ],
    [ 'priority', True ],
    [ 'tasktimeout', True ],
    [ 'autotimeout', True ],
    [ 'machinelimit', True ],
    [ 'isblacklist', True ],
    [ 'machinelist', False ],
    [ 'limits', False ],
    [ 'jobsuspended', True ],
    [ 'upversion', True ],
    # [ 'shotguneviewitem', shotgun_active ],
    [ 'onjobcomplete', False ],
    [ 'overrideframes', True ],
    [ 'framelist', False ],
    [ 'framespertask', True ],
    [ 'concurrent', True ],
    [ 'slavelimit', True ],
    [ 'ignoreinputs', True ],
    [ 'submitscene', True ],
    [ 'bits', False ],

    [ 'mantrajob', True ],
    [ 'mantrathreads', True ],
    [ 'mantrapool', False ],
    [ 'mantrasecondarypool', False ],
    [ 'mantragroup', False ],
    [ 'mantrapriority', True ],
    [ 'mantratasktimeout', True ],
    [ 'mantraautotimeout', True ],
    [ 'mantramachinelimit', True ],
    [ 'mantraisblacklist', True ],
    [ 'mantramachinelist', False ],
    [ 'mantralimits', False ],
    [ 'mantraconcurrent', True ],
    [ 'mantraslavelimit', True ],
    [ 'mantralocalexport', True ],
    [ 'mantraonjobcomplete', False ],

    [ 'arnoldjob', True ],
    [ 'arnoldthreads', True ],
    [ 'arnoldpool', False ],
    [ 'arnoldsecondarypool', False ],
    [ 'arnoldgroup', False ],
    [ 'arnoldpriority', True ],
    [ 'arnoldtasktimeout', True ],
    [ 'arnoldautotimeout', True ],
    [ 'arnoldmachinelimit', True ],
    [ 'arnoldisblacklist', True ],
    [ 'arnoldmachinelist', False ],
    [ 'arnoldlimits', False ],
    [ 'arnoldconcurrent', True ],
    [ 'arnoldslavelimit', True ],
    [ 'arnoldlocalexport', True ],
    [ 'arnoldonjobcomplete', False ],

    [ 'rendermanjob', True ],
    [ 'rendermanlocalexport', True ],
    [ 'rendermanthreads', True ],
    [ 'rendermanpool', False ],
    [ 'rendermansecondarypool', False ],
    [ 'rendermangroup', False ],
    [ 'rendermanpriority', True ],
    [ 'rendermantasktimeout', True ],
    [ 'rendermanconcurrent', True ],
    [ 'rendermanmachinelimit', True ],
    [ 'rendermanisblacklist', True ],
    [ 'rendermanmachinelist', False ],
    [ 'rendermanlimits', False ],
    [ 'rendermanonjobcomplete', False ],
    [ 'rendermanarguments', False ],

    [ 'redshiftjob', True ],
    [ 'redshiftlocalexport', True ],
    [ 'redshiftpool', False ],
    [ 'redshiftsecondarypool', False ],
    [ 'redshiftgroup', False ],
    [ 'redshiftpriority', True ],
    [ 'redshifttasktimeout', True ],
    [ 'redshiftautotimeout', True ],
    [ 'redshiftconcurrent', True ],
    [ 'redshiftslavelimit', True ],
    [ 'redshiftmachinelimit', True ],
    [ 'redshiftisblacklist', True ],
    [ 'redshiftmachinelist', False ],
    [ 'redshiftlimits', False ],
    [ 'redshiftonjobcomplete', False ],
    [ 'redshiftarguments', False ],

    [ 'tilesenabled', True ],
    [ 'jigsawenabled', True ],
    [ 'tilesinx', True ],
    [ 'tilesiny', True ],
    [ 'tilessingleframeenabled', True ],
    [ 'tilessingleframe', True ],
    [ 'submitdependentassembly', True ],
    [ 'cleanuptiles', False ],
    [ 'erroronmissingtiles', False ],
    [ 'erroronmissingbackground', False ],
    [ 'backgroundoption', False ],
    [ 'backgroundimagelabel', False ],
    [ 'backgroundimage', False ],

    [ 'gpuopenclenable', True],
    [ 'gpuspertask', True],
    [ 'gpudevices', False]
]

submissionInfo = None
maxPriority = 0
homeDir = ""
deadlineSettings = ""
deadlineTemp = ""
configFile = ""
integrationKVPs = {}

jigsawThread = None

valuesToToggle = {
    "mantra" : [],
    "arnold" : [],
    "renderman" : [],
    "redshift" : []
}

def SaveStickyProp( config, stickyProp ):
    global dialog

    config.set( "Sticky", stickyProp, dialog.value( stickyProp + ".val" ) )

def WriteStickySettings():
    global dialog, configFile, stickyProps

    try:
        print("Writing sticky settings...")
        config = ConfigParser.ConfigParser()
        config.add_section( "Sticky" )

        for stickyProp, _ in stickyProps:
            SaveStickyProp( config, stickyProp )

        with open( configFile, "w" ) as fileHandle:
            config.write( fileHandle )
    except:
        print( "Could not write sticky settings" )
        print( traceback.format_exc() )

def SaveSceneFields():
    global dialog, stickyProps

    try:
        currentNode = hou.node( "/out" )

        for stickyProp, _ in stickyProps:
            currentNode.setUserData( "deadline_" + stickyProp, str( dialog.value( stickyProp + ".val" ) ) )
    except:
        print( "Could not write submission settings to scene" )
        print( traceback.format_exc() )

def loadUserData( stickyProp, isInt=False ):
    global dialog

    currentNode = hou.node( "/out" )

    data = currentNode.userData( "deadline_" + stickyProp )
    if data != None:
        if isInt:
            data = int(data)
        dialog.setValue( stickyProp + ".val", data )

def LoadSceneFileSubmissionSettings():
    global dialog, stickyProps

    try:
        for stickyProp, isInt in stickyProps:
            loadUserData( stickyProp, isInt )
    except:
        print( "Could not read submission settings from scene" )
        print( traceback.format_exc() )

def RunSanityChecks():
    global dialog

    try:
        import CustomSanityChecks
        print ( "Running sanity check script" )
        sanityResult = CustomSanityChecks.RunSanityCheck( dialog )
        if not sanityResult:
            print( "Sanity check returned False, exiting" )
            hou.ui.displayMessage( "Sanity check returned False, exiting.", title="Submit Houdini To Deadline" )
            dialog.setValue( "dlg.val", 0 )
            return False
    except ImportError:
        print( "No sanity check found" )
    except:
        hou.ui.displayMessage( "Could not run CustomSanityChecks.py script: " + traceback.format_exc(), title="Submit Houdini To Deadline" )
    return True

def loadStickyProp( config, stickyProp, isInt=False ):
    global dialog

    if config.has_option( "Sticky", stickyProp ):
        data = ""
        if isInt:
            data = config.getint( "Sticky", stickyProp )
        else:
            data = config.get( "Sticky", stickyProp )
        dialog.setValue( stickyProp + ".val", data )

def ReadStickySettings():
    global dialog, deadlineSettings, configFile, stickyProps

    try:
        if os.path.isfile( configFile ):
            config = ConfigParser.ConfigParser()
            config.read( configFile )
            print("Reading sticky settings from %s" % configFile)

            if config.has_section( "Sticky" ):
                for stickyProp, isInt in stickyProps:
                    loadStickyProp( config, stickyProp, isInt )
    except:
        print( "Could not read sticky settings" )
        print( traceback.format_exc() )

def ToggleValues( values, condition ):
    global dialog

    for value in values:
        dialog.enableValue( value, condition )

def InitToggleLists():
    global valuesToToggle

    commonProps = [
        "concurrent.val",
        "group.val",
        "isblacklist.val",
        "limits.val",
        "localexport.val",
        "machinelimit.val",
        "machinelist.val",
        "onjobcomplete.val",
        "pool.val",
        "priority.val",
        "secondarypool.val",
        "tasktimeout.val"
    ]

    for renderer in valuesToToggle:
        valuesToToggle[ renderer ] = [ renderer + jobProp for jobProp in commonProps ]

        # now do the ones that aren't common for every renderer
        if renderer not in ( "mantra", "arnold" ):
            valuesToToggle[ renderer ].append( "%sarguments.val" % renderer )

        if renderer != "renderman":
            valuesToToggle[ renderer ].append( "%sautotimeout.val" % renderer )
            valuesToToggle[ renderer ].append( "%sslavelimit.val" % renderer )

        if renderer != "redshift":
            valuesToToggle[ renderer ].append( "%sthreads.val" % renderer )

def InitializeDialog():
    global dialog, maxPriority, containsWedge, submissionInfo, valuesToToggle

    ropList = []
    bits = ""
    startFrame = 0
    endFrame = 0
    frameStep = 1
    frameString = ""

    # Get maximum priority
    maxPriority = int( submissionInfo.get( "MaxPriority", 100 ) )

    # Get pools
    pools = []
    secondaryPools = [" "] # empty string cannot be reselected
    for pool in submissionInfo[ "Pools" ]:
        pool = pool.strip()
        pools.append( pool )
        secondaryPools.append( pool )

    if len( pools ) == 0:
        pools.append( "none" )
        secondaryPools.append( "none" )

    # Get groups
    groups = []
    for group in submissionInfo[ "Groups" ]:
        groups.append( group.strip() )

    if len( groups ) == 0:
        groups.append( "none" )

    # Find the "64-bitness" of the machine
    is64bit = sys.maxsize > 2**32
    if is64bit:
        bits = "64bit"
    else:
        bits = "32bit"

    # Make the file name the name of the job
    scene = hou.hipFile.name()
    index1 = scene.rfind( "\\" )
    index2 = scene.rfind( "/" )

    name = ""
    if index1 > index2:
        name = scene[index1+1:len(scene)]
    else:
        name = scene[index2+1:len(scene)]

    # Fill the ROP list
    renderers = []

    node = hou.node( "/" )
    allNodes = node.allSubChildren()

    for rop in allNodes:
        if isinstance(rop, hou.RopNode):
            if rop.type().description() != "Deadline":
                renderers.append(rop)

    #if there are no valid ROPs, exit submission script
    if len(renderers) < 1:
        hou.ui.displayMessage( "There are no valid ROPs to render.  Exiting.", title="Submit Houdini To Deadline" )
        dialog.setValue( "dlg.val", 0 )
        return False

    for rop in renderers:
        if rop.type().description() == "Wedge":
            containsWedge = True
        ropList.append( rop.path() )

    renderNode = hou.node( ropList[0] )
    frameString = SHTDFunctions.GetFrameInfo( renderNode )

    #SET INITIAL GUI VALUES
    dialog.setValue( "shotgunoptions.val", 1 )
    dialog.setValue( "joboptions.val", 1 )
    dialog.setValue( "jobname.val", name )
    dialog.setValue( "comment.val", "" )
    dialog.setValue( "department.val", "" )

    dialog.setMenuItems( "pool.val", pools )
    dialog.setMenuItems( "secondarypool.val", secondaryPools )
    dialog.setMenuItems( "group.val", groups )
    dialog.setValue( "priority.val", maxPriority/2 )
    dialog.setValue( "tasktimeout.val", 0 )
    dialog.setValue( "autotimeout.val", 0 )
    dialog.setValue( "concurrent.val", 1 )
    dialog.setValue( "slavelimit.val", 1 )
    dialog.setValue( "machinelimit.val", 0 )
    dialog.setValue( "machinelist.val", "" )
    dialog.setValue( "isblacklist.val", 0 )
    dialog.setValue( "limits.val", "" )
    dialog.setValue( "dependencies.val", "" )
    dialog.setMenuItems( "onjobcomplete.val", ["Nothing", "Archive", "Delete"] )
    dialog.setValue( "jobsuspended.val", 0 )

    shotgun_active = bool(ast.literal_eval(os.environ.get("SHOTGUN_PIPELINE_ACTIVE") or "0"))
    create_sg_review_item = bool(ast.literal_eval(os.environ.get("HOUDINI_CREATE_SG_REVIEW_ITEM") or "0"))

    if shotgun_active and create_sg_review_item:
        dialog.setValue( "upversion.val", 1 )
        dialog.setValue( "upversionwarning.val", "" )
        dialog.setValue( "shotguneviewitem.val", 1 )
        dialog.enableValue( "color_blue.val", True )
    else:
        dialog.setValue( "upversion.val", 1 )
        dialog.setValue( "upversionwarning.val", "" )
        dialog.setValue( "shotguneviewitem.val", 0 )
        dialog.enableValue( "color_blue.val", False )

    dialog.enableValue( "shotguneviewitem.val", False )

    dialog.setMenuItems( "ropoption.val", ["Choose", "Selected", "All"] )
    dialog.setMenuItems( "rop.val", ropList )
    dialog.setValue( "overrideframes.val", 0 )
    dialog.setValue( "framelist.val", frameString )
    dialog.enableValue( "framelist.val", dialog.value( "overrideframes.val" ) )
    dialog.setValue( "ignoreinputs.val", 0 )
    dialog.setValue( "submitscene.val", 0 )

    dialog.setValue( "framespertask.val", 1 )
    dialog.setMenuItems( "bits.val", ["None", "32bit", "64bit"] )
    dialog.setValue( "bits.val", bits )
    dialog.setValue( "separateWedgeJobs.val", 0 )
    dialog.setValue( "automaticDependencies.val", 1 )
    dialog.enableValue( "automaticDependencies.val", False )
    dialog.setValue( "bypassDependencies.val", 1 )

    enabled = 0
    if renderNode.type().description() == "Wedge":
        enabled = 1
    dialog.enableValue("separateWedgeJobs.val", enabled )

    dialog.setValue( "tilesenabled.val", 0 )
    jigsawVersion = False

    currentVersion = hou.applicationVersion()
    if currentVersion[0] > 14:
        jigsawVersion = True
    elif currentVersion[0] == 14:
        if currentVersion[1] >0:
            jigsawVersion = True
        else:
            if currentVersion[2] >= 311:
                jigsawVersion = True

    dialog.setValue( "jigsawenabled.val", 1 )
    dialog.enableValue("jigsawenabled.val", jigsawVersion )

    dialog.setValue( "tilesinx.val", 3 )
    dialog.setValue( "tilesiny.val", 3 )

    dialog.setValue( "tilessingleframe.val", 1 )

    dialog.setValue( "tilessingleframeenabled.val", 1 )
    dialog.setValue( "submitdependentassembly.val", 1 )
    dialog.setValue( "cleanuptiles.val", 1 )
    dialog.setValue( "erroronmissingtiles.val", 1 )
    dialog.setValue( "erroronmissingbackground.val", 0 )
    dialog.setValue( "backgroundoption.val", "Blank Image" )
    dialog.setValue( "backgroundimagelabel.val", "" )
    dialog.setValue( "backgroundimage.val", "" )
    TilesEnabledCallback()

    dialog.setValue( "mantrajob.val", 0 )
    dialog.setValue( "mantrathreads.val", 0 )
    dialog.setMenuItems( "mantrapool.val", pools )
    dialog.setMenuItems( "mantrasecondarypool.val", secondaryPools )
    dialog.setMenuItems( "mantragroup.val", groups )
    dialog.setValue( "mantrapriority.val", maxPriority / 2 )
    dialog.setValue( "mantratasktimeout.val", 0 )
    dialog.setValue( "mantraautotimeout.val", 0 )
    dialog.setValue( "mantraconcurrent.val", 1 )
    dialog.setValue( "mantraslavelimit.val", 1 )
    dialog.setValue( "mantramachinelimit.val", 0 )
    dialog.setValue( "mantramachinelist.val", "" )
    dialog.setValue( "mantraisblacklist.val", 0 )
    dialog.setValue( "mantralimits.val", "" )
    dialog.setValue( "mantralocalexport.val", 0 )
    dialog.setMenuItems( "mantraonjobcomplete.val", ["Nothing", "Archive", "Delete"] )

    dialog.setValue( "arnoldjob.val", 0 )
    dialog.setValue( "arnoldthreads.val", 0 )
    dialog.setMenuItems( "arnoldpool.val", pools )
    dialog.setMenuItems( "arnoldsecondarypool.val", secondaryPools )
    dialog.setMenuItems( "arnoldgroup.val", groups )
    dialog.setValue( "arnoldpriority.val", maxPriority / 2 )
    dialog.setValue( "arnoldtasktimeout.val", 0 )
    dialog.setValue( "arnoldautotimeout.val", 0 )
    dialog.setValue( "arnoldconcurrent.val", 1 )
    dialog.setValue( "arnoldslavelimit.val", 1 )
    dialog.setValue( "arnoldmachinelimit.val", 0 )
    dialog.setValue( "arnoldmachinelist.val", "" )
    dialog.setValue( "arnoldisblacklist.val", 0 )
    dialog.setValue( "arnoldlimits.val", "" )
    dialog.setValue( "arnoldlocalexport.val", 0 )
    dialog.setMenuItems( "arnoldonjobcomplete.val", ["Nothing", "Archive", "Delete"] )

    dialog.setValue( "rendermanjob.val", 0 )
    dialog.setValue( "rendermanlocalexport.val", 0 )
    dialog.setValue( "rendermanthreads.val", 0 )
    dialog.setMenuItems( "rendermanpool.val", pools )
    dialog.setMenuItems( "rendermansecondarypool.val", secondaryPools )
    dialog.setMenuItems( "rendermangroup.val", groups )
    dialog.setValue( "rendermanpriority.val", maxPriority / 2 )
    dialog.setValue( "rendermanconcurrent.val", 1 )
    dialog.setValue( "rendermantasktimeout.val", 0 )
    dialog.setValue( "rendermanmachinelimit.val", 0 )
    dialog.setValue( "rendermanisblacklist.val", 0 )
    dialog.setValue( "rendermanmachinelist.val", "" )
    dialog.setValue( "rendermanlimits.val", "" )
    dialog.setMenuItems( "rendermanonjobcomplete.val", ["Nothing", "Archive", "Delete"] )
    dialog.setValue( "rendermanarguments.val", "" )

    dialog.setValue( "redshiftjob.val", 0 )
    dialog.setValue( "redshiftlocalexport.val", 0 )
    dialog.setMenuItems( "redshiftpool.val", pools )
    dialog.setMenuItems( "redshiftsecondarypool.val", secondaryPools )
    dialog.setMenuItems( "redshiftgroup.val", groups )
    dialog.setValue( "redshiftpriority.val", maxPriority / 2 )
    dialog.setValue( "redshifttasktimeout.val", 0 )
    dialog.setValue( "redshiftautotimeout.val", 0 )
    dialog.setValue( "redshiftconcurrent.val", 1 )
    dialog.setValue( "redshiftslavelimit.val", 1 )
    dialog.setValue( "redshiftmachinelimit.val", 0 )
    dialog.setValue( "redshiftisblacklist.val", 0 )
    dialog.setValue( "redshiftmachinelist.val", "" )
    dialog.setValue( "redshiftlimits.val", "" )
    dialog.setMenuItems( "redshiftonjobcomplete.val", ["Nothing", "Archive", "Delete"] )
    dialog.setValue( "redshiftarguments.val", "" )

    InitToggleLists()
    for renderer in valuesToToggle:
        ToggleValues( valuesToToggle[ renderer ], dialog.value( "%sjob.val" % renderer ) )

    dialog.setValue( "gpuopenclenable.val", 0 )
    dialog.setValue( "gpuspertask.val", 0 )
    dialog.setValue( "gpudevices.val", "" )

def ReadInFile( filename ):
    filename = filename.replace( "\r", "" ).replace( "\n", "" )
    try:
        results = filter( None, [line.strip() for line in open( filename )] )
    except:
        errorMsg = "Failed to read in configuration file " + filename + "."
        print(errorMsg)
        raise Exception(errorMsg)
    return results

def Callbacks():
    dialog.addCallback( "getmachinelist.val", GetMachineListFromDeadline )
    dialog.addCallback( "getlimits.val", GetLimitGroupsFromDeadline )
    dialog.addCallback( "getdependencies.val", GetDependenciesFromDeadline )

    dialog.addCallback( "priority.val", JobPriorityCallback )
    dialog.addCallback( "tasktimeout.val", TaskTimeoutCallback )
    dialog.addCallback( "concurrent.val", ConcurrentTasksCallback )
    dialog.addCallback( "machinelimit.val", MachineLimitCallback )

    dialog.addCallback( "ropoption.val", ROPOptionCallback )
    dialog.addCallback( "rop.val", ROPSelectionCallback )
    dialog.addCallback( "overrideframes.val", FramesCallback )
    dialog.addCallback( "framespertask.val", FramesPerTaskCallback )

    dialog.addCallback( "mantrajob.val", MantraStandaloneCallback )
    dialog.addCallback( "mantrathreads.val", MantraThreadsCallback )

    dialog.addCallback( "mantragetmachinelist.val", MantraGetMachineListFromDeadline )
    dialog.addCallback( "mantragetlimits.val", MantraGetLimitGroupsFromDeadline )

    dialog.addCallback( "mantrapriority.val", MantraJobPriorityCallback )
    dialog.addCallback( "mantratasktimeout.val", MantraTaskTimeoutCallback )
    dialog.addCallback( "mantraconcurrent.val", MantraConcurrentTasksCallback )
    dialog.addCallback( "mantramachinelimit.val", MantraMachineLimitCallback )

    dialog.addCallback( "arnoldjob.val", ArnoldStandaloneCallback )
    dialog.addCallback( "arnoldthreads.val", ArnoldThreadsCallback )
    dialog.addCallback( "arnoldgetmachinelist.val", ArnoldGetMachineListFromDeadline )
    dialog.addCallback( "arnoldgetlimits.val", ArnoldGetLimitGroupsFromDeadline )
    dialog.addCallback( "arnoldpriority.val", ArnoldJobPriorityCallback )
    dialog.addCallback( "arnoldtasktimeout.val", ArnoldTaskTimeoutCallback )
    dialog.addCallback( "arnoldconcurrent.val", ArnoldConcurrentTasksCallback )
    dialog.addCallback( "arnoldmachinelimit.val", ArnoldMachineLimitCallback )

    dialog.addCallback( "rendermanjob.val", RenderManStandaloneCallback )
    dialog.addCallback( "rendermanthreads.val", RenderManThreadsCallback )
    dialog.addCallback( "rendermangetmachinelist.val", RenderManGetMachineListFromDeadline )
    dialog.addCallback( "rendermangetlimits.val", RenderManGetLimitGroupsFromDeadline )
    dialog.addCallback( "rendermanpriority.val", RenderManJobPriorityCallback )
    dialog.addCallback( "rendermantasktimeout.val", RenderManTaskTimeoutCallback )
    dialog.addCallback( "rendermanconcurrent.val", RenderManConcurrentTasksCallback )
    dialog.addCallback( "rendermanmachinelimit.val", RenderManMachineLimitCallback )

    dialog.addCallback( "redshiftjob.val", RedshiftStandaloneCallback )
    dialog.addCallback( "redshiftgetmachinelist.val", RedshiftGetMachineListFromDeadline )
    dialog.addCallback( "redshiftgetlimits.val", RedshiftGetLimitGroupsFromDeadline )
    dialog.addCallback( "redshiftpriority.val", RedshiftJobPriorityCallback )
    dialog.addCallback( "redshifttasktimeout.val", RedshiftTaskTimeoutCallback )
    dialog.addCallback( "redshiftconcurrent.val", RedshiftConcurrentTasksCallback )
    dialog.addCallback( "redshiftmachinelimit.val", RedshiftMachineLimitCallback )

    dialog.addCallback( "tilesenabled.val", TilesEnabledCallback )
    dialog.addCallback( "tilesinx.val", TilesInXCallback )
    dialog.addCallback( "tilesiny.val", TilesInYCallback )
    dialog.addCallback( "jigsawenabled.val", JigsawEnabledCallback )
    dialog.addCallback( "tilessingleframeenabled.val", TilesSingleFrameEnabledCallback )
    dialog.addCallback( "submitdependentassembly.val", SubmitDependentAssemblyCallback )
    dialog.addCallback( "backgroundoption.val", BackgroundOptionCallback)

    dialog.addCallback( "gpuspertask.val", gpusPerTaskCallback )
    dialog.addCallback( "gpudevices.val", gpuDevicesCallback )

    dialog.addCallback( "openjigsaw.val", OpenJigsaw)

    dialog.addCallback( "unifiedintegration.val", openIntegrationWindow )

    dialog.addCallback( "submitjob.val", SubmitJobCallback )
    dialog.addCallback( "closedialog.val", CloseDialogCallback )

def GetROPsFromMergeROP( mergeROP, bypass=False ):
    rops = []

    # Double check that this is a merge node.
    if mergeROP.type().description() == "Merge":
        # Loop through all inputs to get the actual nodes.
        for inputROP in mergeROP.inputs():
            # If the input ROP is a merge node, do some recursion!
            if inputROP.type().description() == "Merge":
                for nestedInputROP in GetROPsFromMergeROP( inputROP, bypass ):
                    # We don't want duplicate ROPs.
                    if nestedInputROP not in rops:
                        rops.append( nestedInputROP )
            else:
                # Ignore bypassed ROPs.
                if not bypass or not inputROP.isBypassed():
                    # We don't want duplicate ROPs.
                    if inputROP not in rops:
                        rops.append( inputROP )

    return rops

def GetROPs( ropOption, bypass=False ):
    jobs = []
    renderNode = hou.node( "/" )
    renderers =[]
    for rop in renderNode.allSubChildren():
        #for rop in allNodes:
        if isinstance(rop, hou.RopNode):
            renderers.append(rop)

    if ropOption == "Selected" and len(renderers) > 0 and len(hou.selectedNodes()) > 0: # A node is selected
        for selectedNodes in hou.selectedNodes():
            if not bypass or not selectedNodes.isBypassed():
                for rop in renderers:
                    if rop.path() == selectedNodes.path():

                        # If this is a merge ROP, we want its input ROPs.
                        if rop.type().description() == "Merge":
                            for inputROP in GetROPsFromMergeROP( rop, bypass ):
                                if inputROP.path() not in jobs:
                                    jobs.append( inputROP.path() )
                        else:
                            if selectedNodes.path() not in jobs:
                                jobs.append( selectedNodes.path() )
                        break

        if jobs == []: # No valid selected Nodes
            print("Selected node(s) are invalid")
            return

    elif ropOption == "All" and len(renderers) > 0:
        for node in renderers:
            # Simply skip over any merge nodes.
            if node.type().description() == "Merge" or  node.type().description() == "Deadline":
                continue

            if not bypass or not node.isBypassed():
                jobs.append( node.path() )

    return jobs

def GetDeadlineValues( deadlineCommand, component ):
    global dialog

    output = CallDeadlineCommand( [deadlineCommand, dialog.value(component)], False ).strip()
    if output != "Action was cancelled by user":
        dialog.setValue( component, output )

def ClampValue( component, min, max ):
    global dialog

    val = dialog.value( component )
    if val > max:
        dialog.setValue( component, max )
    elif val < min:
        dialog.setValue( component, min )

def GetMachineListFromDeadline():
    GetDeadlineValues( "-selectmachinelist", "machinelist.val" )

def GetLimitGroupsFromDeadline():
    GetDeadlineValues( "-selectlimitgroups", "limits.val" )

def GetDependenciesFromDeadline():
    GetDeadlineValues( "-selectdependencies", "dependencies.val" )

def JobPriorityCallback():
    global maxPriority

    ClampValue( "priority.val", 0, maxPriority )

def TaskTimeoutCallback():
    ClampValue( "tasktimeout.val", 0, 1000000 )

def ConcurrentTasksCallback():
    ClampValue( "concurrent.val", 1, 16 )

def MachineLimitCallback():
    ClampValue( "machinelimit.val", 0, 1000000 )

def ROPOptionCallback():
    global dialog, containsWedge

    ropOption = dialog.value( "ropoption.val" )
    dialog.enableValue( "rop.val", ropOption == "Choose" )

    dialog.enableValue( "automaticDependencies.val", ropOption != "Choose" )

    value = 0
    if containsWedge:
        value = 1
    if ropOption == "All":
        dialog.enableValue("separateWedgeJobs.val", value)
    else:
        ROPSelectionCallback()

def ROPSelectionCallback():
    global dialog
    frameString = ""

    ropSelection = dialog.value( "rop.val" )
    renderNode = hou.node( ropSelection )

    frameString = SHTDFunctions.GetFrameInfo( renderNode )
    dialog.setValue( "framelist.val", frameString )

    if renderNode.type().description() == "Wedge":
        dialog.enableValue("separateWedgeJobs.val", 1)
    else:
        dialog.enableValue("separateWedgeJobs.val", 0)

def FramesCallback():
    global dialog

    isOverrideFrames = dialog.value( "overrideframes.val" )
    dialog.enableValue( "framelist.val", isOverrideFrames )

def FramesPerTaskCallback():
    ClampValue( "framespertask.val", 1, 1000000 )

def MantraStandaloneCallback():
    global dialog, valuesToToggle

    isMantraJob = dialog.value( "mantrajob.val" )
    ToggleValues( valuesToToggle[ "mantra" ], isMantraJob )

def MantraThreadsCallback():
    ClampValue( "mantrathreads.val", 0, 256 )

def MantraGetMachineListFromDeadline():
    GetDeadlineValues( "-selectmachinelist", "mantramachinelist.val" )

def MantraGetLimitGroupsFromDeadline():
    GetDeadlineValues( "-selectlimitgroups", "mantralimits.val" )

def MantraGetDependenciesFromDeadline():
    GetDeadlineValues( "-selectdependencies", "mantradependencies.val" )

def MantraJobPriorityCallback():
    global maxPriority

    ClampValue( "mantrapriority.val", 0, maxPriority )

def MantraTaskTimeoutCallback():
    ClampValue( "mantratasktimeout.val", 0, 1000000 )

def MantraConcurrentTasksCallback():
    ClampValue( "mantraconcurrent.val", 1, 16 )

def MantraMachineLimitCallback():
    ClampValue( "mantramachinelimit.val", 0, 1000000 )

def ArnoldStandaloneCallback():
    global dialog, valuesToToggle

    isArnoldJob = dialog.value( "arnoldjob.val" )
    ToggleValues( valuesToToggle[ "arnold" ], isArnoldJob )

def ArnoldThreadsCallback():
    ClampValue( "arnoldthreads.val", 0, 256 )

def ArnoldGetMachineListFromDeadline():
    GetDeadlineValues( "-selectmachinelist", "arnoldmachinelist.val" )

def ArnoldGetLimitGroupsFromDeadline():
    GetDeadlineValues( "-selectlimitgroups", "arnoldlimits.val" )

def ArnoldGetDependenciesFromDeadline():
    GetDeadlineValues( "-selectdependencies", "arnolddependencies.val" )

def ArnoldJobPriorityCallback():
    global maxPriority

    ClampValue( "arnoldpriority.val", 0, maxPriority )

def ArnoldTaskTimeoutCallback():
    ClampValue( "arnoldtasktimeout.val", 0, 1000000 )

def ArnoldConcurrentTasksCallback():
    ClampValue( "arnoldconcurrent.val", 1, 16 )

def ArnoldMachineLimitCallback():
    ClampValue( "arnoldmachinelimit.val", 0, 1000000 )

def RenderManStandaloneCallback():
    global dialog, valuesToToggle

    isRendermanJob = dialog.value( "rendermanjob.val" )
    ToggleValues( valuesToToggle[ "renderman" ], isRendermanJob )

def RenderManThreadsCallback():
    ClampValue( "rendermanthreads.val", 0, 256 )

def RenderManGetMachineListFromDeadline():
    GetDeadlineValues( "-selectmachinelist", "rendermanmachinelist.val" )

def RenderManGetLimitGroupsFromDeadline():
    GetDeadlineValues( "-selectlimitgroups", "rendermanlimits.val" )

def RenderManGetDependenciesFromDeadline():
    GetDeadlineValues( "-selectdependencies", "rendermandependencies.val" )

def RenderManJobPriorityCallback():
    global maxPriority

    ClampValue( "rendermanpriority.val", 0, maxPriority )

def RenderManConcurrentTasksCallback():
    ClampValue( "rendermanconcurrent.val", 1, 16 )

def RenderManTaskTimeoutCallback():
    ClampValue( "rendermantasktimeout.val", 0, 1000000 )

def RenderManMachineLimitCallback():
    ClampValue( "rendermanmachinelimit.val", 0, 1000000 )

def RedshiftStandaloneCallback():
    global dialog, valuesToToggle

    isRedshiftJob = dialog.value( "redshiftjob.val" )
    ToggleValues( valuesToToggle[ "redshift" ], isRedshiftJob )

def RedshiftGetMachineListFromDeadline():
    GetDeadlineValues( "-selectmachinelist", "redshiftmachinelist.val" )

def RedshiftGetLimitGroupsFromDeadline():
    GetDeadlineValues( "-selectlimitgroups", "redshiftlimits.val" )

def RedshiftGetDependenciesFromDeadline():
    GetDeadlineValues( "-selectdependencies", "redshiftdependencies.val" )

def RedshiftJobPriorityCallback():
    global maxPriority

    ClampValue( "redshiftpriority.val", 0, maxPriority )

def RedshiftTaskTimeoutCallback():
    ClampValue( "redshifttasktimeout.val", 0, 1000000 )

def RedshiftConcurrentTasksCallback():
    ClampValue( "redshiftconcurrent.val", 1, 16 )

def RedshiftMachineLimitCallback():
    ClampValue( "redshiftmachinelimit.val", 0, 1000000 )

def TilesEnabledCallback():
    global dialog

    jigsawVersion = False
    currentVersion = hou.applicationVersion()
    if currentVersion[0] >14:
        jigsawVersion = True
    elif currentVersion[0] == 14:
        if currentVersion[1] >0:
            jigsawVersion = True
        else:
            if currentVersion[2] >= 311:
                jigsawVersion = True

    tilesEnabled = (dialog.value( "tilesenabled.val" ) == 1)

    dialog.enableValue( "jigsawenabled.val", tilesEnabled and jigsawVersion )

    dialog.enableValue( "tilessingleframeenabled.val", tilesEnabled )
    dialog.enableValue( "submitdependentassembly.val", tilesEnabled )
    JigsawEnabledCallback()
    TilesSingleFrameEnabledCallback()
    SubmitDependentAssemblyCallback()

def TilesInXCallback():
    global dialog

    val = dialog.value( "tilesinx.val" )
    if val < 1:
        dialog.setValue( "tilesinx.val", 1 )

def TilesInYCallback():
    global dialog
    
    val = dialog.value( "tilesiny.val" )
    if val < 1:
        dialog.setValue( "tilesiny.val" , 1 )

def JigsawEnabledCallback():
    global dialog
    jigsawVersion = False
    currentVersion = hou.applicationVersion()
    if currentVersion[0] >14:
        jigsawVersion = True
    elif currentVersion[0] == 14:
        if currentVersion[1] >0:
            jigsawVersion = True
        else:
            if currentVersion[2] >= 311:
                jigsawVersion = True

    jigsawEnabled = (dialog.value( "jigsawenabled.val" ) == 1) and jigsawVersion
    tilesEnabled = (dialog.value( "tilesenabled.val" ) == 1)

    dialog.enableValue( "tilesinx.val", tilesEnabled and not jigsawEnabled )
    dialog.enableValue( "tilesiny.val", tilesEnabled and not jigsawEnabled )

    dialog.enableValue( "openjigsaw.val", tilesEnabled and jigsawEnabled )

def TilesSingleFrameEnabledCallback():
    global dialog

    tilesEnabled = (dialog.value( "tilesenabled.val" ) == 1)
    tilesSingleFrameEnabled = (dialog.value( "tilessingleframeenabled.val" ) == 1 )
    dialog.enableValue("tilessingleframe.val", tilesEnabled and tilesSingleFrameEnabled)

def SubmitDependentAssemblyCallback():
    global dialog
    tilesEnabled = (dialog.value( "tilesenabled.val" ) == 1)
    submitDependent = (dialog.value( "submitdependentassembly.val") == 1)

    dialog.enableValue("cleanuptiles.val", tilesEnabled and submitDependent)
    dialog.enableValue("erroronmissingtiles.val", tilesEnabled and submitDependent)
    dialog.enableValue("erroronmissingbackground.val", tilesEnabled and submitDependent)
    dialog.enableValue("backgroundoption.val", tilesEnabled and submitDependent)
    BackgroundOptionCallback()

def BackgroundOptionCallback():
    global dialog
    tilesEnabled = (dialog.value( "tilesenabled.val" ) == 1)
    submitDependent = (dialog.value( "submitdependentassembly.val") == 1)
    backgroundType = dialog.value( "backgroundoption.val" )
    if backgroundType == "Selected Image":
        dialog.enableValue("backgroundimagelabel.val", tilesEnabled and submitDependent)
        dialog.enableValue("backgroundimage.val", tilesEnabled and submitDependent)
    else:
        dialog.enableValue("backgroundimagelabel.val", False)
        dialog.enableValue("backgroundimage.val", False)

def gpusPerTaskCallback():
    global dialog

    gpusPerTaskEnabled = (dialog.value( "gpuspertask.val" ) >0)
    dialog.enableValue("gpudevices.val", not gpusPerTaskEnabled)

def gpuDevicesCallback():
    global dialog

    gpuDevicesEnabled = (dialog.value( "gpudevices.val" ) != "")
    dialog.enableValue("gpuspertask.val", not gpuDevicesEnabled)

def OpenJigsaw():
    global dialog
    global jigsawThread

    driver = dialog.value( "rop.val" )
    rop = hou.node( driver )
    camera = rop.parm( "camera" ).eval()
    cameraNode = hou.node(camera)
    if not cameraNode:
        hou.ui.displayMessage( "The selected Driver doesn't have a camera.", title="Submit Houdini To Deadline" )
        return

    if jigsawThread is not None:
        if jigsawThread.isAlive():
            hou.ui.displayMessage( "The Jigsaw window is currently open.", title="Submit Houdini To Deadline" )
            return

    jigsawThread = JigsawThread(name="JigsawThread")
    jigsawThread.driver = driver
    jigsawThread.start()

def openIntegrationWindow():
    global submissionInfo, deadlineTemp
    integrationDir = submissionInfo[ "RepoDirs" ][ "submission/Integration/Main" ].strip()

    try:
        sys.path.append( integrationDir )
        import GetPipelineToolsInfo
        GetPipelineToolsInfo.getInfo( deadlineTemp )
    except:
        print( "Failed to import GetPipelineToolsInfo.py." )
        print( traceback.format_exc() )

    print("Opening Integration window...")
    scriptPath = os.path.join( integrationDir, "IntegrationUIStandAlone.py" )
    integrationOptions = ["Draft", "Shotgun", "FTrack", "NIM", "0"]

    GetIntegrationInfo( scriptPath, integrationOptions )

def GetIntegrationInfo( scriptPath, additionalArgs=[] ):
    global integrationKVPs

    argArray = ["-ExecuteScript", scriptPath, "Houdini"]
    for arg in additionalArgs:
        argArray.append( arg )

    results = CallDeadlineCommand( argArray, False )
    outputLines = results.splitlines()

    keyValuePairs = {}

    for line in outputLines:
        line = line.strip()
        if not line.startswith("("):
            tokens = line.split( "=", 1 )

            if len( tokens ) > 1:
                key = tokens[0]
                value = tokens [1]

                keyValuePairs[key] = value

    if len( keyValuePairs ) > 0:
        integrationKVPs = keyValuePairs

def InputRenderJobs(job, availableJobs):
    dependentJobs = []
    node = hou.node(job)
    try:
        for inputNode in node.inputs():
             # If this is a merge ROP, we want its input ROPs.
            if inputNode.type().description() == "Merge":
                for inputROP in GetROPsFromMergeROP( inputNode ):
                    if inputROP.path() in availableJobs:
                        dependentJobs.append(inputROP.path())
                    else:
                        dependentJobs.extend(InputRenderJobs(inputROP.path(),availableJobs))
            else:
                if inputNode.path() in availableJobs:
                    dependentJobs.append(inputNode.path())
                else:
                    dependentJobs.extend(InputRenderJobs(inputNode.path(),availableJobs))
    except:
        pass
    return dependentJobs

def SubmitRenderJob( job, jobOrdering, batch, jigsawRegionCount, jigsawRegions ):
    global dialog, integrationKVPs

    groupBatch = batch
    autoDependencies = int(dialog.value( "automaticDependencies.val" ))
    if autoDependencies:
        if not jobOrdering[job][0] == "":
            return
    jigsawEnabled = (dialog.value( "jigsawenabled.val" ) == 1)
    dependencies = dialog.value( "dependencies.val" )
    if autoDependencies:
        if len(jobOrdering[job]) >1:
            dependencies = ""
            deps = []
            for i in range(1, len(jobOrdering[job]) ):
                depJobName = jobOrdering[job][i]
                SubmitRenderJob(depJobName,jobOrdering, True, jigsawRegionCount, jigsawRegions )
                deps.append(jobOrdering[depJobName][0])

            dependencies = deps
            groupBatch = True

    jobProperties = {
        "integrationKVPs" : integrationKVPs,
        "batch" : groupBatch,

        "jobname" : dialog.value( "jobname.val" ),
        "comment" : dialog.value( "comment.val" ),
        "department" : dialog.value( "department.val" ),

        "pool" : dialog.value( "pool.val" ),
        "secondarypool" : "" if dialog.value( "secondarypool.val" ) == " " else dialog.value( "secondarypool.val" ),
        "group" : dialog.value( "group.val" ),
        "priority" : dialog.value( "priority.val" ),
        "tasktimeout" : dialog.value( "tasktimeout.val" ),
        "autotimeout" : dialog.value( "autotimeout.val" ),
        "concurrent" : dialog.value( "concurrent.val" ),
        "machinelimit" : dialog.value( "machinelimit.val" ),
        "slavelimit" : dialog.value( "slavelimit.val" ),
        "limits" : dialog.value( "limits.val" ),
        "onjobcomplete" : dialog.value( "onjobcomplete.val" ),
        "jobsuspended" : dialog.value( "jobsuspended.val" ),
        "shotguneviewitem" : dialog.value( "shotguneviewitem.val" ),
        "isblacklist" : dialog.value( "isblacklist.val" ),
        "machinelist" : dialog.value( "machinelist.val" ),
        "overrideframes" : dialog.value( "overrideframes.val" ),
        "framelist" : dialog.value( "framelist.val" ),
        "framespertask" : dialog.value( "framespertask.val" ),
        "bits" : dialog.value( "bits.val" ),
        "submitscene" : dialog.value( "submitscene.val" ),

        "gpuopenclenable" : dialog.value( "gpuopenclenable.val" ),
        "gpuspertask" : int( dialog.value( "gpuspertask.val" ) ),
        "gpudevices" : dialog.value( "gpudevices.val" ),

        "ignoreinputs": dialog.value( "ignoreinputs.val" ),
        "separateWedgeJobs": dialog.value( "separateWedgeJobs.val" ),

        "mantrajob" : dialog.value( "mantrajob.val" ),
        "mantrapool" : dialog.value( "mantrapool.val" ),
        "mantrasecondarypool" : "" if dialog.value( "mantrasecondarypool.val" ) == " " else dialog.value( "mantrasecondarypool.val" ),
        "mantragroup" : dialog.value( "mantragroup.val" ),
        "mantrapriority" : dialog.value( "mantrapriority.val" ),
        "mantratasktimeout" : dialog.value( "mantratasktimeout.val" ),
        "mantraautotimeout" : dialog.value( "mantraautotimeout.val" ),
        "mantraconcurrent" : dialog.value( "mantraconcurrent.val" ),
        "mantramachinelimit" : dialog.value( "mantramachinelimit.val" ),
        "mantraslavelimit" : dialog.value( "mantraslavelimit.val" ),
        "mantralimits" : dialog.value( "mantralimits.val" ),
        "mantraonjobcomplete" : dialog.value( "mantraonjobcomplete.val" ),
        "mantraisblacklist" : dialog.value( "mantraisblacklist.val" ),
        "mantramachinelist" : dialog.value( "mantramachinelist.val" ),
        "mantrathreads" : dialog.value( "mantrathreads.val" ),
        "mantralocalexport" : dialog.value( "mantralocalexport.val" ),

        "arnoldjob" : dialog.value( "arnoldjob.val" ),
        "arnoldpool" : dialog.value( "arnoldpool.val" ),
        "arnoldsecondarypool" : "" if dialog.value( "arnoldsecondarypool.val" ) == " " else dialog.value( "arnoldsecondarypool.val" ),
        "arnoldgroup" : dialog.value( "arnoldgroup.val" ),
        "arnoldpriority" : dialog.value( "arnoldpriority.val" ),
        "arnoldtasktimeout" : dialog.value( "arnoldtasktimeout.val" ),
        "arnoldautotimeout" : dialog.value( "arnoldautotimeout.val" ),
        "arnoldconcurrent" : dialog.value( "arnoldconcurrent.val" ),
        "arnoldmachinelimit" : dialog.value( "arnoldmachinelimit.val" ),
        "arnoldslavelimit" : dialog.value( "arnoldslavelimit.val" ),
        "arnoldonjobcomplete" : dialog.value( "arnoldonjobcomplete.val" ),
        "arnoldlimits" : dialog.value( "arnoldlimits.val" ),
        "arnoldisblacklist" : dialog.value( "arnoldisblacklist.val" ),
        "arnoldmachinelist" : dialog.value( "arnoldmachinelist.val" ),
        "arnoldthreads" : dialog.value( "arnoldthreads.val" ),
        "arnoldlocalexport" : dialog.value( "arnoldlocalexport.val" ),

        "rendermanjob" : dialog.value( "rendermanjob.val" ),
        "rendermanpool" : dialog.value( "rendermanpool.val" ),
        "rendermansecondarypool" : "" if dialog.value( "rendermansecondarypool.val" ) == " " else dialog.value( "rendermansecondarypool.val" ),
        "rendermangroup" : dialog.value( "rendermangroup.val" ),
        "rendermanpriority" : dialog.value( "rendermanpriority.val" ),
        "rendermantasktimeout" : dialog.value( "rendermantasktimeout.val" ),
        "rendermanconcurrent" : dialog.value( "rendermanconcurrent.val" ),
        "rendermanmachinelimit" : dialog.value( "rendermanmachinelimit.val" ),
        "rendermanlimits" : dialog.value( "rendermanlimits.val" ),
        "rendermanonjobcomplete" : dialog.value( "rendermanonjobcomplete.val" ),
        "rendermanisblacklist" : dialog.value( "rendermanisblacklist.val" ),
        "rendermanmachinelist" : dialog.value( "rendermanmachinelist.val" ),
        "rendermanthreads" : dialog.value( "rendermanthreads.val" ),
        "rendermanarguments" : dialog.value( "rendermanarguments.val" ),
        "rendermanlocalexport" : dialog.value( "rendermanlocalexport.val" ),

        "redshiftjob" : dialog.value( "redshiftjob.val" ),
        "redshiftpool" : dialog.value( "redshiftpool.val" ),
        "redshiftsecondarypool" : "" if dialog.value( "redshiftsecondarypool.val" ) == " " else dialog.value( "redshiftsecondarypool.val" ),
        "redshiftgroup" : dialog.value( "redshiftgroup.val" ),
        "redshiftpriority" : dialog.value( "redshiftpriority.val" ),
        "redshifttasktimeout" : dialog.value( "redshifttasktimeout.val" ),
        "redshiftautotimeout" : dialog.value( "redshiftautotimeout.val" ),
        "redshiftconcurrent" : dialog.value( "redshiftconcurrent.val" ),
        "redshiftmachinelimit" : dialog.value( "redshiftmachinelimit.val" ),
        "redshiftslavelimit" : dialog.value( "redshiftslavelimit.val" ),
        "redshiftlimits" : dialog.value( "redshiftlimits.val" ),
        "redshiftonjobcomplete" : dialog.value( "redshiftonjobcomplete.val" ),
        "redshiftisblacklist" : dialog.value( "redshiftisblacklist.val" ),
        "redshiftmachinelist" : dialog.value( "redshiftmachinelist.val" ),
        "redshiftarguments" : dialog.value( "redshiftarguments.val" ),
        "redshiftlocalexport" : dialog.value( "redshiftlocalexport.val" ),

        "tilesenabled": dialog.value( "tilesenabled.val"),
        "tilesinx": dialog.value( "tilesinx.val"),
        "tilesiny": dialog.value( "tilesiny.val"),
        "tilessingleframeenabled": dialog.value( "tilessingleframeenabled.val"),
        "tilessingleframe": dialog.value( "tilessingleframe.val"),

        "jigsawenabled": dialog.value( "jigsawenabled.val"),
        "jigsawregioncount": jigsawRegionCount,
        "jigsawregions": jigsawRegions,
        
        "submitdependentassembly": dialog.value( "submitdependentassembly.val"),

        "backgroundoption" : dialog.value( "backgroundoption.val" ),
        "backgroundimage" : dialog.value( "backgroundimage.val" ),
        "erroronmissingtiles" : dialog.value( "erroronmissingtiles.val" ),
        "erroronmissingbackground" : dialog.value( "erroronmissingbackground.val" ),
        "cleanuptiles" : dialog.value( "cleanuptiles.val" ),
    }
    renderNode = hou.node( job )
    jobIds = SHTDFunctions.SubmitRenderJob( renderNode, jobProperties, ",".join( dependencies ) )

    if autoDependencies:
        jobOrdering[job][0] = ",".join(jobIds)

def SubmitJobCallback():
    global dialog, homeDir, jigsawThread, submissionInfo
    jobs = []
    submissions = []
    jobOrdering = {}

    jobResult = ""
    totalJobs = 0
    ropOption = ""
    localPaths = ""
    missingIFDPaths = ""
    ropOption = dialog.value( "ropoption.val" )

    jigsawRegions = []
    jigsawRegionCount = 0
    # Save the scene file
    if hou.hipFile.hasUnsavedChanges():
        if hou.ui.displayMessage( "The scene has unsaved changes and must be saved before the job can be submitted.\nDo you wish to save?", buttons=( "Yes" , "No" ), title="Submit Houdini To Deadline" ) == 0:
            hou.hipFile.save()
        else:
            return

    bypassNodes = ( int(dialog.value( "bypassDependencies.val" )) == 1 )

    # Find out how many jobs to do
    if ropOption == "Choose":
        jobs = []
        selectedROP = hou.node( dialog.value( "rop.val" ) )

         # If this is a merge ROP, we want its input ROPs.
        if selectedROP.type().description() == "Merge":
            for inputROP in GetROPsFromMergeROP( selectedROP, bypassNodes ):
                if inputROP.path() not in jobs:
                    jobs.append( inputROP.path() )
        else:
            if not bypassNodes or not selectedROP.isBypassed():
                if selectedROP.path() not in jobs:
                    jobs.append( selectedROP.path() )

        totalJobs = len(jobs)
        if totalJobs == 0:
            print("ERROR: Invalid ROPs selected")
            hou.ui.displayMessage( "There are no valid ROPs selected. Check to see if the selected nodes are being bypassed.", title="Submit Houdini To Deadline" )
            return
    else:
        jobs = GetROPs( ropOption, bypassNodes )
        if not jobs:
            print("ERROR: Invalid ROPs selected")
            hou.ui.displayMessage( "There are no valid ROPs selected. Check to see if the selected nodes are being bypassed.", title="Submit Houdini To Deadline" )
            return
        else:
            totalJobs = len(jobs)

    if int(dialog.value( "automaticDependencies.val" )) ==1:
        for job in jobs:
            jobOrdering[job] = [""]
            jobOrdering[job].extend(InputRenderJobs( job, jobs) )

    if dialog.value( "tilesenabled.val" ) == 1:
        if dialog.value( "jigsawenabled.val" ) == 1:
            if jigsawThread is None:
                print("ERROR: Jigsaw window is not open")
                hou.ui.displayMessage( "In order to submit Jigsaw renders the Jigsaw window must be open.", title="Submit Houdini To Deadline" )
                return
            if not jigsawThread.isAlive() or jigsawThread.sockOut is None:
                print("ERROR: Jigsaw window is not open")
                hou.ui.displayMessage( "In order to submit Jigsaw renders the Jigsaw window must be open.", title="Submit Houdini To Deadline" )
                return

            jigsawRegions = jigsawThread.getRegions()
            jigsawRegionCount = int(len(jigsawRegions)/4)

        if dialog.value( "tilessingleframeenabled.val" ) == 1:
            taskLimit = int( submissionInfo.get( "TaskLimit", 5000 ) )
            taskCount = jigsawRegionCount
            if dialog.value( "jigsawenabled.val" ) != 1:
                taskCount = int( dialog.value( "tilesinx.val" ) ) * int( dialog.value( "tilesiny.val" ) )
            if taskCount > taskLimit:
                print("Unable to submit job with " + (str(taskCount)) + " tasks.  Task Count exceeded Job Task Limit of "+str(taskLimit))
                hou.ui.displayMessage( "Unable to submit job with " + (str(taskCount)) + " tasks.  Task Count exceeded Job Task Limit of "+str(taskLimit) )
                return


    # check if the nodes are outputing to local
    for node in jobs:
        outputPath = SHTDFunctions.GetOutputPath( hou.node( node ) )
        if outputPath and outputPath != "COMMAND":
            if SHTDFunctions.IsPathLocal( outputPath.eval() ):
                localPaths += "  %s  (output file)\n" % node
        renderNode = hou.node( node )

        if dialog.value( "tilesenabled.val" ) == 1:
            if dialog.value( "tilessingleframeenabled.val" ) != 1:
                if dialog.value( "jigsawenabled.val" ) == 0:
                    tilesInX = int( dialog.value( "tilesinx.val" ) )
                    tilesInY = int( dialog.value( "tilesiny.val" ) )
                else:
                    tilesInX = jigsawRegionCount
                    tilesInY = 1
                totalJobs += (tilesInX * tilesInY) -1

            if dialog.value( "submitdependentassembly.val" ) == 1:
                totalJobs += 1

        ifdPath = SHTDFunctions.GetExportPath( renderNode )
        isMantra = (renderNode.type().description() == "Mantra")
        isArnold = (renderNode.type().description() == "Arnold")
        isRenderMan = (renderNode.type().description() == "RenderMan" or renderNode.type().description() == "RenderMan RIS" )
        isRedshift = (renderNode.type().description() == "Redshift" )

        if ifdPath != None:
            if SHTDFunctions.IsPathLocal( ifdPath.eval() ):
                localPaths += "  %s  (disk file)\n" % node

            if dialog.value( "mantrajob.val" ) == 1 and dialog.value( "mantralocalexport.val" ) != 1 and isMantra:
                totalJobs += 1

            if dialog.value( "arnoldjob.val" ) == 1 and dialog.value( "arnoldlocalexport.val" ) != 1 and isArnold:
                totalJobs += 1

            if dialog.value( "rendermanjob.val" ) == 1 and dialog.value( "rendermanlocalexport.val" ) != 1 and isRenderMan:
                totalJobs += 1

            if dialog.value( "redshiftjob.val" ) == 1 and dialog.value( "redshiftlocalexport.val" ) != 1 and isRedshift:
                totalJobs += 1

        else:
            missingIFDPaths += "  %s  \n" % node

    if localPaths != "":
        if hou.ui.displayMessage( "The following ROPs have local output/disk paths. Do you wish to continue?\n\n%s" % localPaths, buttons=( "Yes" , "No" ), title="Submit Houdini To Deadline" ) != 0:
            WriteStickySettings()
            SaveSceneFields()
            return

    if missingIFDPaths != "" and dialog.value( "mantrajob.val" ):
        if hou.ui.displayMessage( "The Dependent Mantra Standalone job option is enabled, but the following ROPs don't have the Disk File option enabled to export IFD files. Do you wish to continue?\n\n%s" % missingIFDPaths, buttons=( "Yes" , "No" ), title="Submit Houdini To Deadline" ) != 0:
            WriteStickySettings()
            SaveSceneFields()
            return

    if missingIFDPaths != "" and dialog.value( "rendermanjob.val" ):
        if hou.ui.displayMessage( "The Dependent RenderMan Standalone job option is enabled, but the following ROPs don't have the Disk File option enabled to export RIB files. Do you wish to continue?\n\n%s" % missingIFDPaths, buttons=( "Yes" , "No" ), title="Submit Houdini To Deadline" ) != 0:
            WriteStickySettings()
            SaveSceneFields()
            return

    if missingIFDPaths != "" and dialog.value( "redshiftjob.val" ):
        if hou.ui.displayMessage( "The Dependent Redshift Standalone job option is enabled, but the following ROPs don't have the Disk File option enabled to export RS files. Do you wish to continue?\n\n%s" % missingIFDPaths, buttons=( "Yes" , "No" ), title="Submit Houdini To Deadline" ) != 0:
            WriteStickySettings()
            SaveSceneFields()
            return

    #check if overriding frame range, and empty
    if dialog.value( "overrideframes.val" ) and dialog.value( "framelist.val" ).strip() == "":
        hou.ui.displayMessage( "ERROR: Overriding Frame List, but Frame List is empty, exiting", title="Submit Houdini To Deadline" )
        return

    WriteStickySettings()
    SaveSceneFields()

    for job in jobs:
        # Wedge nodes can have additional jobs submitted
        renderNode = hou.node( job )
        isWedge = renderNode.type().description() == "Wedge"
        if isWedge and dialog.value( "separateWedgeJobs.val" ):
            totalJobs += SHTDFunctions.WedgeTasks( renderNode ) - 1

        SubmitRenderJob(job, jobOrdering, (totalJobs > 1), jigsawRegionCount, jigsawRegions )

    if totalJobs > 1:
        dialog.setValue( "status.val", "100%: All " + str( totalJobs ) + " jobs submitted" )
        print("All %d jobs submitted\n" % totalJobs)
        hou.ui.displayMessage( "All %d jobs submitted. Check log window for more information." % totalJobs, title="Submit Houdini To Deadline" )
    else:
        dialog.setValue( "status.val", "100%: Job submitted" )
        print("Job submitted\n")
        hou.ui.displayMessage( "Finished submitting Job. Check log window for more information.", title="Submit Houdini To Deadline" )

def CloseDialogCallback():
    WriteStickySettings()
    SaveSceneFields()

    if jigsawThread is not None:
        if jigsawThread.isAlive():
            jigsawThread.closeJigsaw()

    print("Closing Submission Dialog...")
    dialog.setValue( "dlg.val", 0 )

def ConvertToolkitNodes():
    # save selection
    selected_node_paths = [i.path() for i in hou.selectedNodes()]

    print("Converting toolkit nodes to regular nodes...")
    engine = sgtk.platform.current_engine()

    if not engine:
        print("Houdini engine is not running, skipping conversion...")
        return

    # create standard arbnold nodes from shotgun write nodes
    app = engine.apps.get("tk-houdini-arnoldnode", False)
    if app:
        app.convert_to_regular_arnold_nodes()
    else:
        print("Could not load toolkit app: 'tk-houdini-arnoldnode'")

    # create standard arbnold nodes from shotgun write nodes
    app = engine.apps.get("tk-houdini-alembicnode", False)
    if app:
        app.convert_to_regular_alembic_nodes()
    else:
        print("Could not load toolkit app: 'tk-houdini-alembicnode'")

    # create standard arbnold nodes from shotgun write nodes
    app = engine.apps.get("tk-houdini-mantranode", False)
    if app:
        app.convert_to_regular_mantra_nodes()
    else:
        print("Could not load toolkit app: 'tk-houdini-mantranode")

    # reselect because converting nodes creates new nodes in place of old ones
    for i in selected_node_paths:
        if hou.node(i):
            hou.node(i).setSelected(True)

def ConvertBackToToolkitNodesCallback():

    if dialog.value("dlg.val") != 0:
        return

    if dialog.value("upversion.val") == 0:
        print("Upversion disabled, will not convert shotgun nodes back...")
        return

    # save selection
    selected_node_paths = [i.path() for i in hou.selectedNodes()]

    print("Converting nodes back to toolkit nodes...")
    engine = sgtk.platform.current_engine()

    if not engine:
        print("Houdini engine is not running, skipping conversion...")
        return

    # create shotgun nodes from regular write nodes
    app = engine.apps.get("tk-houdini-arnoldnode", False)
    if app:
        app.convert_back_to_tk_arnold_nodes()
    else:
        print("Could not load toolkit app: 'tk-houdini-arnoldnode'")

    # create shotgun nodes from regular write nodes
    app = engine.apps.get("tk-houdini-alembicnode", False)
    if app:
        app.convert_back_to_tk_alembic_nodes()
    else:
        print("Could not load toolkit app: 'tk-houdini-alembicnode'")

    # create shotgun nodes from regular write nodes
    app = engine.apps.get("tk-houdini-mantranode", False)
    if app:
        app.convert_back_to_tk_mantra_nodes()
    else:
        print("Could not load toolkit app: 'tk-houdini-mantranode")

    # reselect because converting nodes creates new nodes in place of old ones
    for i in selected_node_paths:
        if hou.node(i):
            hou.node(i).setSelected(True)

def SaveNewIterationCallback():

    if dialog.value("upversion.val") == 0:
        print("Upversion disabled on user request...")
        return

    print("Saving new iteration...")
    engine = sgtk.platform.current_engine()
    app = engine.apps.get("tk-cs-multi-incrementalsave", False)
    if app:
        app.incremental_save()
    else:
        print("Could not load toolkit app: 'tk-cs-multi-incrementalsave")

def ForceCloseDialogCallback():
    print("Closing Submission Dialog...")
    dialog.setValue( "dlg.val", 0 )

def ToolkitCallbacks():
    dialog.addCallback("submitjob.val", SaveNewIterationCallback)
    dialog.addCallback("submitjob.val", ForceCloseDialogCallback)

    dialog.addCallback("dlg.val", ConvertBackToToolkitNodesCallback)


def WarnUserNotToUseOption():

    if dialog.value("upversion.val") == 0:
        dialog.setValue( "upversionwarning.val", "I hope to God you know what you're doing...")
    else:
        dialog.setValue( "upversionwarning.val", "")

def AdditionalCallbacks():
    dialog.addCallback("upversion.val", WarnUserNotToUseOption)

def SubmitToDeadline():

    # prepare shotgun write nodes for submition
    if SGTK_INITIALIZED:
        # convert toolkit nodes to regular nodes
        ConvertToolkitNodes()
        # save file
        hou.hipFile.save()

    global dialog, submissionInfo, deadlineSettings, deadlineTemp, homeDir, configFile, shotgunScript, ftrackScript, nimScript

    print( "Grabbing submitter info..." )
    try:
        output = json.loads( CallDeadlineCommand( [ "-prettyJSON", "-GetSubmissionInfo", "Pools", "Groups", "MaxPriority", "TaskLimit", "UserHomeDir", "RepoDir:submission/Houdini/Main", "RepoDir:submission/Integration/Main", "RepoDirNoCustom:draft", "RepoDirNoCustom:submission/Jigsaw", ] ) )
    except:
        print( "Unable to get submitter info from Deadline:\n\n" + traceback.format_exc() )
        raise

    if output[ "ok" ]:
        submissionInfo = output[ "result" ]
        hou.putenv("Deadline_Submission_Info", json.dumps( submissionInfo ) )
    else:
        print( "DeadlineCommand returned a bad result and was unable to grab the submitter info.\n\n" + output[ "result" ] )
        raise Exception( output[ "result" ] )

    homeDir = submissionInfo[ "UserHomeDir" ].strip()
    path = submissionInfo[ "RepoDirs" ][ "submission/Houdini/Main" ].strip()

    deadlineTemp = os.path.join( homeDir, "temp" )
    deadlineSettings = os.path.join( homeDir, "settings" )
    configFile = os.path.join( deadlineSettings, "houdini_py_submission.ini" )

    uiDir = os.path.join(os.environ["HOUDINI_CONFIG_ROOT"], "deadline", "submitter")
    uiPath = os.path.join( uiDir, "SubmitHoudiniToDeadline.ui" )

    print("Creating Submission Dialog...")
    dialog = hou.ui.createDialog( uiPath )
    InitializeDialog()

    print("Initializing Callbacks...")
    Callbacks()
    AdditionalCallbacks()

    if SGTK_INITIALIZED:
        print("Initializing Toolkit Callbacks...")
        ToolkitCallbacks()

    ReadStickySettings()
    LoadSceneFileSubmissionSettings()
    if not RunSanityChecks():
        return

    ROPSelectionCallback()

    return dialog

class JigsawThread(threading.Thread):
    sockIn = None
    sockOut = None
    tempFile = None
    savedRegions = ""
    usingWidth = 1
    usingHeight = 1
    driver = ""

    def run(self):
        global submissionInfo

        #Create an input socket on an open port
        HOSTin = '' # Symbolic name meaning all available interfaces
        PORTin = self.get_open_port() # Arbitrary non-privileged port
        self.sockIn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockIn.bind((HOSTin, PORTin))
        self.sockIn.listen(1)
        jigsawPath = submissionInfo[ "RepoDirs" ][ "submission/Jigsaw" ].strip()

        #in the main thread get a screen shot
        screenshot = self.getScreenshot()
        info = screenshot.split("=")
        #if the screenshot exists then continue else create the failed message and return
        if len(info) == 1:
            self.failedScreenshot()
            return

        # Get deadlinecommand to execute a script and pass in a screenshot and the port to connect to.
        # After Deadline 10, we can remove the "SHTDFunctions." portion of this call, since the client script will be updated.
        SHTDFunctions.CallDeadlineCommand(["-executescript", os.path.join( jigsawPath, "Jigsaw.py" ), str(PORTin), info[1], "True", "0", "0", "False"], False, False )

        conn, addr = self.sockIn.accept()
        #wait to receive the a message with the port in which to connect to for outgoing messages
        data = recvData(conn)
        if not data:
            #If we do not get one return
            conn.close()
            return
        HostOut = 'localhost'
        PORTout = int(data)
        self.sockOut = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockOut.connect((HostOut, PORTout))
        #constantly listen
        while 1:
            data = recvData(conn)
            #if we do not get data then exit
            if not data:
                break
            #otherwise split the data on =
            command = str(data).split("=")
            #if we got the command exit then break out of the loop
            if command[0].lower() == "exit":
                break
            #if we were told to get the screenshot then retrieve a screenshot and send it to the jigsaw ui
            elif command[0].lower() == "getscreenshot":
                screenshot = self.getScreenshot()
                if(not screenshot):
                    #cmds.confirmDialog(title="No Background", message="Unable to get background. Make sure that the viewport is selected.");
                    self.closeJigsaw()
                else:
                    self.sockOut.sendall(screenshot+"\n")
            #When we are told to fit the region
            elif command[0].lower() == "getselected":
                mode = 0#Vertex
                padding = 0 #percentage based padding
                if len(command)>1:
                    arguments=command[1].split(";")
                    arguments[0].split()
                    if arguments[0].lower() == "tight":
                        mode = 0#vertex
                    elif arguments[0].lower() == "loose":
                        mode = 1#boundingbox
                    padding = float(arguments[1])
                regions = self.getSelectedBoundingRegion(mode, padding)
                regionMessage = ""
                for region in regions:
                    if not regionMessage == "":
                        regionMessage+=";"
                    first = True
                    for val in region:
                        if not first:
                            regionMessage+=","
                        regionMessage += str(val)
                        first = False
                self.sockOut.sendall("create="+regionMessage+"\n")
            #when told to save the regions save them to the scene
            elif command[0].lower() == "saveregions":
                if not len(command)>1:
                    self.saveRegions("")
                else:
                    self.saveRegions(command[1])
            #when told to load the regions send the regions back to Jigsaw
            elif command[0].lower() == "loadregions":
                regions = self.loadRegions()
                self.sockOut.sendall("loadregions="+regions+"\n")

        conn.close()
        try:
            os.remove(self.tempFile)
        except:
            pass
    #if we failed to get the screen shot the first time then let the user know.  This will be run on the main thread
    def failedScreenshot(self):
        pass
        #cmds.confirmDialog( title='Unable to open Jigsaw', message='Failed to get screenshot.\nPlease make sure the current Viewport is selected')
    def requestSave(self):
        self.sockOut.sendall("requestSave\n")
    #Save the regions to the scene
    def saveRegions(self, regions):
        try:
            currentNode = hou.node( "/out")
            regionData = []
            for region in regions.split(";"):
                data = region.split(",")
                if len(data) == 7:
                    regionData.append( str(float(data[0])/float(self.usingWidth)) )#XPos
                    regionData.append( str(float(data[1])/float(self.usingHeight)) )#YPos
                    regionData.append( str(float(data[2])/float(self.usingWidth)) )#Width
                    regionData.append( str(float(data[3])/float(self.usingHeight)) )#Height
                    regionData.append( data[4] )#tiles in x
                    regionData.append( data[5] )#tiles in y
                    regionData.append( data[6] )# enabled

            currentNode.setUserData("deadline_jigsawregions", ','.join(regionData) )
        except:
            print( "Could not write regions to scene" )
            print( traceback.format_exc() )

    #Create a string out of all of the saved regions and return them.
    def loadRegions(self):
        currentNode = hou.node( "/out" )
        results = ""
        try:
            data = currentNode.userData("deadline_jigsawregions")
            if data != None:
                regionData = data.split(",")
                count = 0
                for i in range(0,len(regionData) / 7):
                    if not results == "":
                        results += ";"

                    results += str( int( float(regionData[7*i]) * float(self.usingWidth) ) ) #XPos
                    results += "," + str( int( float(regionData[7*i+1]) * float(self.usingHeight) ) ) #YPos
                    results += "," + str( int( float(regionData[7*i+2]) * float(self.usingWidth) ) ) #Width
                    results += "," + str( int( float(regionData[7*i+3]) * float(self.usingHeight) ) ) #Height
                    results += "," + regionData[7*i+4] #tiles in x
                    results += "," + regionData[7*i+5] #tiles in y
                    results += "," + regionData[7*i+6] #enabled

        except:
            print( "Could not read Jigsaw settings from scene" )
            print( traceback.format_exc() )
        return results

    #Get the Jigsaw UI to return all of the regions and return an array of the ints with the appropriate positions
    def getRegions(self, invert = True):
        self.sockOut.sendall("getrenderregions\n")
        data = recvData(self.sockOut)

        regionString = str(data)
        regionData = regionString.split("=")
        regions = []
        if regionData[0] == "renderregion" and len(regionData) >1:
            regionData = regionData[1]
            regionData = regionData.split(";")
            for region in regionData:
                coordinates = region.split(",")
                if len(coordinates) == 4:
                    regions.append( float(coordinates[0])/self.usingWidth )
                    regions.append( ( float(coordinates[0])+float(coordinates[2] ) )/self.usingWidth )
                    regions.append( 1.0 - (float(coordinates[1])+float(coordinates[3]))/self.usingHeight )
                    regions.append( 1.0 - float(coordinates[1])/self.usingHeight )
        return regions

    def getScreenshot(self):
        if self.tempFile is None:
            filename = str(uuid.uuid4())
            self.tempFile = tempfile.gettempdir()+os.sep+filename+".png"

        rop = hou.node( self.driver )
        camera = rop.parm( "camera" ).eval()
        cameraNode = hou.node(camera)

        width = cameraNode.parm("resx").eval()
        height = cameraNode.parm("resy").eval()

        panel = hou.ui.curDesktop().createFloatingPanel(hou.paneTabType.SceneViewer)
        viewer = panel.paneTabOfType(hou.paneTabType.SceneViewer)
        desktop_name = hou.ui.curDesktop().name()
        pane_name = viewer.name()
        viewport_name = viewer.curViewport().name()
        full_sceneviewer_path = "%s.%s.world.%s" % (desktop_name, pane_name, viewport_name)
        hou.hscript('viewcamera -c '+camera+' ' + full_sceneviewer_path )
        panel.setSize((width+38, height+85))

        hou.hscript('viewwrite '+full_sceneviewer_path+' "'+self.tempFile+'"')

        panel.close()

        modelWidth = width
        modelHeight = height

        renderWidth = width
        renderHeight = height

        if renderWidth < modelWidth and renderHeight<modelHeight:
            self.usingWidth = renderWidth
            self.usingHeight = renderHeight
        else:
            renderRatio = renderWidth/(renderHeight+0.0)
            widthRatio = renderWidth/(modelWidth+0.0)
            heightRatio = renderHeight/(modelHeight+0.0)
            if widthRatio<=1 and heightRatio<=1:
                self.usingWidth = renderWidth
                self.usingHeight = renderHeight
            elif widthRatio > heightRatio:
                self.usingWidth = int(modelWidth)
                self.usingHeight = int(modelWidth/renderRatio)
            else:
                self.usingWidth = int(modelHeight*renderRatio)
                self.usingHeight = int(modelHeight)

        return "screenshot="+self.tempFile

    #Let jigsaw know that we want it to exit.
    def closeJigsaw(self):
        self.sockOut.sendall("exit\n")

    #get the bounding regions of all of the selected objects
    #Mode = False: Tight vertex based bounding box
    #Mode = True: Loose Bounding box based
    def getSelectedBoundingRegion(self, mode=False, padding = 0.0):

        rop = hou.node( self.driver )
        camera = rop.parm( "camera" ).eval()
        cameraNode = hou.node(camera)

        width = cameraNode.parm("resx").eval()
        height = cameraNode.parm("resy").eval()

        panel = hou.ui.curDesktop().createFloatingPanel(hou.paneTabType.SceneViewer)
        viewer = panel.paneTabOfType(hou.paneTabType.SceneViewer)
        desktop_name = hou.ui.curDesktop().name()
        pane_name = viewer.name()
        viewport_name = viewer.curViewport().name()
        full_sceneviewer_path = "%s.%s.world.%s" % (desktop_name, pane_name, viewport_name)
        hou.hscript('viewcamera -c '+camera+' ' + full_sceneviewer_path )
        panel.setSize((width+38, height+85))

        regions = []
        try:
            node = hou.node( "/" )
            allNodes = node.allSubChildren()
            for selectedNode in allNodes:
                minX = 0
                maxX = 0
                minY = 0
                maxY = 0
                if selectedNode.isSelected() and selectedNode.type().name() == "geo":
                    if not mode: #Tight vertex based
                        selectedGeometry = selectedNode.displayNode().geometry()
                        firstPoint = True
                        for point in selectedGeometry.iterPoints():
                            newPos =  point.position() * selectedNode.worldTransform()
                            mappedPos = hou.ui.floatingPanels()[-1].paneTabs()[0].curViewport().mapToScreen(newPos)
                            if firstPoint:
                                firstPoint = False
                                minX = mappedPos[0]
                                minY = mappedPos[1]

                            if mappedPos[0] < minX:
                                minX = mappedPos[0]
                            if mappedPos[0] > maxX:
                                maxX = mappedPos[0]
                            if mappedPos[1] < minY:
                                minY = mappedPos[1]
                            if mappedPos[1] > maxY:
                                maxY = mappedPos[1]
                    else: #Loose bounding box based
                        boundingBox = selectedNode.displayNode().geometry().boundingBox()
                        firstPoint = True
                        minvec = boundingBox.minvec()
                        maxvec = boundingBox.maxvec()
                        xVals = [ minvec[0], maxvec[0] ]
                        yVals = [ minvec[1], maxvec[1] ]
                        zVals = [ minvec[2], maxvec[2] ]

                        for x in xVals:
                            for y in yVals:
                                for z in zVals:
                                    newPos =  hou.Vector3( (x, y, z) ) * selectedNode.worldTransform()
                                    mappedPos = hou.ui.floatingPanels()[-1].paneTabs()[0].curViewport().mapToScreen(newPos)
                                    if firstPoint:
                                        firstPoint = False
                                        minX = mappedPos[0]
                                        minY = mappedPos[1]

                                    if mappedPos[0] < minX:
                                        minX = mappedPos[0]
                                    if mappedPos[0] > maxX:
                                        maxX = mappedPos[0]
                                    if mappedPos[1] < minY:
                                        minY = mappedPos[1]
                                    if mappedPos[1] > maxY:
                                        maxY = mappedPos[1]

                    regions.append([ int( minX + 0.5 ), int( height - maxY + 0.5 ), int( maxX - minX + 0.5 ), int( maxY -minY + 0.5 ) ])
        finally:
            panel.close()

        return regions

    #find a random open port to connect to
    def get_open_port(self):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        port = s.getsockname()[1]
        s.close()
        return port

def recvData(theSocket):
    totalData=[]
    data=''
    while True:
        data=theSocket.recv(8192)
        if not data:
            return
        if "\n" in data:
            totalData.append(data[:data.find("\n")])
            break
        totalData.append(data)
    return ''.join(totalData)

################################################################################
## DEBUGGING
################################################################################
#
# HOWTO: (1) Open Houdini's python shell: Alt + Shift + P   or   Windows --> Python Shell
#        (2) Copy and paste line (A) to import this file (MAKE SURE THE PATH IS CORRECT FOR YOU)
#        (3) Copy and paste line (B) to execute this file for testing
#        (4) If you change this file, copy and paste line (C) to reload this file, GOTO step (3)
#
# (A)
# root = "C:/DeadlineRepository8/";import os;os.chdir(root + "submission/Houdini/Main/");import SubmitHoudiniToDeadline
#
# (B)
# SubmitHoudiniToDeadline.SubmitToDeadline(root)
#
# (C)
# reload(SubmitHoudiniToDeadline)

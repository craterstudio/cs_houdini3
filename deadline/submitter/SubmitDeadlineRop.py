import hou

import SubmitHoudiniToDeadlineFunctions as SHTDFunctions

dlSubmittedIDs = {}

def SubmitToDeadline(): 
    global dlSubmittedIDs
    dlNode = hou.pwd()
    
    if not dlNode.isLocked():
        dependentNodes = dlNode.inputs()
        dlSubmittedIDs = {}
        
        for renderNode in dependentNodes:
            PrepareNodeForSubmission( renderNode, dlNode )
            
def PrepareNodeForSubmission( renderNode, dlNode ):
    global dlSubmittedIDs
    
    bypassed = renderNode.isBypassed()
    locked =  renderNode.isLocked()
    isDeadline = ( renderNode.type().description() == "Deadline" )
    
    depJobIds = []
    
    if not locked:
        dependentNodes = renderNode.inputs()
        futureDlNode = dlNode
        if isDeadline and not bypassed:
            futureDlNode = renderNode
        for depNode in dependentNodes:
            if depNode.path() not in dlSubmittedIDs.keys():
                PrepareNodeForSubmission( depNode, futureDlNode )
                
            depJobIds.extend( dlSubmittedIDs[ depNode.path() ] )
            
    if not renderNode.isBypassed() and not isDeadline:
        dlSubmittedIDs[ renderNode.path() ] =  nodeSubmission( renderNode, dlNode, depJobIds )
    else:
        dlSubmittedIDs[ renderNode.path() ] = depJobIds 
        
def nodeSubmission( renderNode, dlNode, dependencies ):
    jobProperties = {
        "integrationKVPs" : {},
        "batch" : True,

        "jobname" : dlNode.parm( "dl_job_name" ).eval(),
        "comment" : dlNode.parm( "dl_comment" ).eval(),
        "department" : dlNode.parm( "dl_department" ).eval(),
        
        "pool" : dlNode.parm( "dl_pool" ).eval(),
        "secondarypool" : "" if dlNode.parm( "dl_secondary_pool" ).eval() == " " else dlNode.parm( "dl_secondary_pool" ).eval(),
        "group" : dlNode.parm( "dl_group" ).eval(),
        "priority" : dlNode.parm( "dl_priority" ).eval(),
        "tasktimeout" : dlNode.parm( "dl_task_timeout" ).eval(), 
        "autotimeout" : dlNode.parm( "dl_auto_task_timeout" ).eval(),
        "concurrent" : dlNode.parm( "dl_concurrent_tasks" ).eval(),
        "machinelimit" : dlNode.parm( "dl_machine_limit" ).eval(),
        "slavelimit" : dlNode.parm( "dl_slave_task_limit" ).eval(),
        "limits" : dlNode.parm( "dl_limits" ).eval(),
        "onjobcomplete" : dlNode.parm( "dl_on_complete" ).eval(),
        "jobsuspended" : dlNode.parm( "dl_submit_suspended" ).eval(),
        "shotguneviewitem" : dlNode.parm( "dl_create_review_item" ).eval(),
        "isblacklist" : dlNode.parm( "dl_blacklist" ).eval(),
        "machinelist" : dlNode.parm( "dl_machine_list" ).eval(),
        "overrideframes" : False,
        "framespertask" : dlNode.parm( "dl_chunk_size" ).eval(),
        "submitscene" : dlNode.parm( "dl_submit_scene" ).eval(),
        "bits" : "None",
        "gpuopenclenable" : dlNode.parm( "dl_gpu_opencl_enable" ).eval(),
        "gpuspertask" : dlNode.parm( "dl_gpus_per_task" ).eval(),
        "gpudevices" : dlNode.parm( "dl_gpu_devices" ).eval(),

        "tilesenabled": dlNode.parm( "dl_tiles_enabled" ).eval(),
        "tilesinx": dlNode.parm( "dl_tiles_in_x" ).eval(),
        "tilesiny": dlNode.parm( "dl_tiles_in_y" ).eval(),
        "tilessingleframeenabled": dlNode.parm( "dl_tiles_single_frame_enabled" ).eval(),
        "tilessingleframe": dlNode.parm( "dl_tiles_single_frame" ).eval(),
        
        "submitdependentassembly": dlNode.parm( "dl_submit_dependent_assembly" ).eval(),

        "backgroundoption" : dlNode.parm( "dl_background_option" ).eval(),
        "backgroundimage" : dlNode.parm( "dl_background_image" ).eval(),
        "erroronmissingtiles" : dlNode.parm( "dl_error_on_missing_tiles" ).eval(),
        "erroronmissingbackground" : dlNode.parm( "dl_error_on_missing_background" ).eval(),
        "cleanuptiles" : dlNode.parm( "dl_cleanup_tiles" ).eval(),

        "jigsawenabled" : False,
        "jigsawregioncount" : 1,
        "jigsawregions" : [],

        "ignoreinputs" : True,
        "separateWedgeJobs" : True,

        "arnoldjob" : dlNode.parm( "dl_arnold_job" ).eval(),
        "arnoldpool" : dlNode.parm( "dl_arnold_pool" ).eval(),
        "arnoldsecondarypool" : "" if dlNode.parm( "dl_arnold_secondary_pool" ).eval() == " " else dlNode.parm( "dl_arnold_secondary_pool" ).eval(),
        "arnoldgroup" : dlNode.parm( "dl_arnold_group" ).eval(),
        "arnoldpriority" : dlNode.parm( "dl_arnold_priority" ).eval(),
        "arnoldtasktimeout" : dlNode.parm( "dl_arnold_task_timeout" ).eval(),
        "arnoldautotimeout" : dlNode.parm( "dl_arnold_auto_timeout" ).eval(),
        "arnoldconcurrent" : dlNode.parm( "dl_arnold_concurrent" ).eval(),
        "arnoldmachinelimit" : dlNode.parm( "dl_arnold_machine_limit" ).eval(),
        "arnoldslavelimit" : dlNode.parm( "dl_arnold_slave_limit" ).eval(),
        "arnoldlimits" : dlNode.parm( "dl_arnold_limits" ).eval(),
        "arnoldonjobcomplete" : dlNode.parm( "dl_arnold_on_complete" ).eval(),
        "arnoldisblacklist" : dlNode.parm( "dl_arnold_is_blacklist" ).eval(),
        "arnoldmachinelist" : dlNode.parm( "dl_arnold_machine_list" ).eval(),
        "arnoldthreads" : dlNode.parm( "dl_arnold_threads" ).eval(),
        "arnoldlocalexport" : dlNode.parm( "dl_arnold_local_export" ).eval(),

        "mantrajob" : dlNode.parm( "dl_mantra_job" ).eval(),
        "mantrapool" : dlNode.parm( "dl_mantra_pool" ).eval(),
        "mantrasecondarypool" : "" if dlNode.parm( "dl_mantra_secondary_pool" ).eval() == " " else dlNode.parm( "dl_mantra_secondary_pool" ).eval(),
        "mantragroup" : dlNode.parm( "dl_mantra_group" ).eval(),
        "mantrapriority" : dlNode.parm( "dl_mantra_priority" ).eval(),
        "mantratasktimeout" : dlNode.parm( "dl_mantra_task_timeout" ).eval(),
        "mantraautotimeout" : dlNode.parm( "dl_mantra_auto_timeout" ).eval(),
        "mantraconcurrent" : dlNode.parm( "dl_mantra_concurrent" ).eval(),
        "mantramachinelimit" : dlNode.parm( "dl_mantra_machine_limit" ).eval(),
        "mantraslavelimit" : dlNode.parm( "dl_mantra_slave_limit" ).eval(),
        "mantralimits" : dlNode.parm( "dl_mantra_limits" ).eval(),
        "mantraonjobcomplete" : dlNode.parm( "dl_mantra_on_complete" ).eval(),
        "mantraisblacklist" : dlNode.parm( "dl_mantra_is_blacklist" ).eval(),
        "mantramachinelist" : dlNode.parm( "dl_mantra_machine_list" ).eval(),
        "mantrathreads" : dlNode.parm( "dl_mantra_threads" ).eval(),
        "mantralocalexport" : dlNode.parm( "dl_mantra_local_export" ).eval(),

        "redshiftjob" : dlNode.parm( "dl_redshift_job" ).eval(),
        "redshiftpool" : dlNode.parm( "dl_redshift_pool" ).eval(),
        "redshiftsecondarypool" : "" if dlNode.parm( "dl_redshift_secondary_pool" ).eval() == " " else dlNode.parm( "dl_redshift_secondary_pool" ).eval(),
        "redshiftgroup" : dlNode.parm( "dl_redshift_group" ).eval(),
        "redshiftpriority" : dlNode.parm( "dl_redshift_priority" ).eval(),
        "redshifttasktimeout" : dlNode.parm( "dl_redshift_task_timeout" ).eval(),
        "redshiftautotimeout" : dlNode.parm( "dl_redshift_auto_timeout" ).eval(),
        "redshiftconcurrent" : dlNode.parm( "dl_redshift_concurrent" ).eval(),
        "redshiftmachinelimit" : dlNode.parm( "dl_redshift_machine_limit" ).eval(),
        "redshiftslavelimit" : dlNode.parm( "dl_redshift_slave_limit" ).eval(),
        "redshiftlimits" : dlNode.parm( "dl_redshift_limits" ).eval(),
        "redshiftonjobcomplete" : dlNode.parm( "dl_redshift_on_complete" ).eval(),
        "redshiftisblacklist" : dlNode.parm( "dl_redshift_is_blacklist" ).eval(),
        "redshiftmachinelist" : dlNode.parm( "dl_redshift_machine_list" ).eval(),
        "redshiftarguments" : dlNode.parm( "dl_redshift_arguments" ).eval(),
        "redshiftlocalexport" : dlNode.parm( "dl_redshift_local_export" ).eval(),

        "rendermanjob" : dlNode.parm( "dl_renderman_job" ).eval(),
        "rendermanpool" : dlNode.parm( "dl_renderman_pool" ).eval(),
        "rendermansecondarypool" : "" if dlNode.parm( "dl_renderman_secondary_pool" ).eval() == " " else dlNode.parm( "dl_renderman_secondary_pool" ).eval(),
        "rendermangroup" : dlNode.parm( "dl_renderman_group" ).eval(),
        "rendermanpriority" : dlNode.parm( "dl_renderman_priority" ).eval(),
        "rendermantasktimeout" : dlNode.parm( "dl_renderman_task_timeout" ).eval(),
        "rendermanconcurrent" : dlNode.parm( "dl_renderman_concurrent" ).eval(),
        "rendermanmachinelimit" : dlNode.parm( "dl_renderman_machine_limit" ).eval(),
        "rendermanlimits" : dlNode.parm( "dl_renderman_limits" ).eval(),
        "rendermanonjobcomplete" : dlNode.parm( "dl_renderman_on_complete" ).eval(),
        "rendermanisblacklist" : dlNode.parm( "dl_renderman_is_blacklist" ).eval(),
        "rendermanmachinelist" : dlNode.parm( "dl_renderman_machine_list" ).eval(),
        "rendermanthreads" : dlNode.parm( "dl_renderman_threads" ).eval(),
        "rendermanarguments" : dlNode.parm( "dl_renderman_arguments" ).eval(),
        "rendermanlocalexport" : dlNode.parm( "dl_renderman_local_export" ).eval(), 
    }

    jobDeps = SHTDFunctions.SubmitRenderJob( renderNode, jobProperties, ",".join( dependencies ) )
    return jobDeps
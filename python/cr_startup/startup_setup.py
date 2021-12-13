import os
import sys
import hou


def setup_scene_callback():
    import setup_scene
    reload(setup_scene)
    setup_scene.main()


def setup_scene_for_project(project_name):

    if not project_name:
        return

    # get configured projects
    proj_config_folder = os.path.join(os.path.dirname(__file__), "projects")
    configured_projects = [dI for dI in os.listdir(
        proj_config_folder) if os.path.isdir(os.path.join(proj_config_folder, dI))]

    # check if project is configured
    if project_name not in configured_projects:
        print("Note: Project '{}' has no specific startup config (it's safe to ignore this message).".format(
            project_name))
    else:
        # define config folder for current project
        config = os.path.join(proj_config_folder, project_name)

        # append config to sys
        if config not in sys.path:
            sys.path.append(config)

        if hou.isUIAvailable():
            # delay execution if in GUI mode
            import hdefereval
            hdefereval.executeDeferred(setup_scene_callback)
        else:
            print("Note: Per project scene setup is disabled in batch mode.")


def run(project):
    setup_scene_for_project(project)

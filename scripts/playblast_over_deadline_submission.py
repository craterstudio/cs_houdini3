import os
import sys
import socket
import re
import toolutils
from functools import partial

import hou

# import deadline python API
DEADLINE_REPOSITORY = os.environ["DEADLINE_REPOSITORY"]
DEADLINE_WEBSERVICE_URL = os.environ["DEADLINE_WEBSERVICE_URL"]
DEADLINE_WEBSERVICE_PORT = int(os.environ["DEADLINE_WEBSERVICE_PORT"])

DEADLINE_PYTHON_API = os.path.join(DEADLINE_REPOSITORY, "api", "python")
HOUDINI_SCRIPTS = os.path.join(os.environ["REPO_CONFIG_ROOT"], "cs_houdini", "scripts")
NETWORK_HOUDINI_SCRIPTS = os.path.join(os.environ["NETWORK_REPO_CONFIG_ROOT"], "cs_houdini", "scripts")

sys.path.append(DEADLINE_PYTHON_API)
import Deadline.DeadlineConnect as Connect
  

# PySide2
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets


# converts bool values from settingsFile.ini . The value comes as "true". After conversion the value is "True" with upper case
# example: to_bool( settings_obj.value( ini_file_category + "/maskCheckbox")) )
def to_bool(value):
    valid = {'true': True, 't': True, '1': True,
             'false': False, 'f': False, '0': False,
             }

    if isinstance(value, bool):
        return value

    if not isinstance(value, basestring):
        raise ValueError('invalid literal for boolean. Not a string.')

    lower_value = value.lower()
    if lower_value in valid:
        return valid[lower_value]
    else:
        raise ValueError('invalid literal for boolean: "%s"' % value)

def check_deadline_webservice():
    import urllib2
    check = False

    try:
        proxy_handler = urllib2.ProxyHandler({})
        opener = urllib2.build_opener(proxy_handler)
        urllib2.install_opener(opener)
        urllib2.urlopen("http://{}:{}".format(DEADLINE_WEBSERVICE_URL, DEADLINE_WEBSERVICE_PORT))
        check = True
    except urllib2.HTTPError, e:
        print(e.code)
    except urllib2.URLError, e:
        print(e.args)

    return check

class submit_flipbook_to_deadline_window(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent, QtCore.Qt.WindowStaysOnTopHint)

        # self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        # self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)
        # self.setStyleSheet(hou.qt.styleSheet())
        # self.setProperty("houdiniStyle", True)

        # connection to deadline
        Deadline = Connect.DeadlineCon(DEADLINE_WEBSERVICE_URL, DEADLINE_WEBSERVICE_PORT)
        self.deadline = Deadline

        # set settings_path variable
        self.settings_path = os.path.join(os.getenv('HOME'), "settingsFile.ini") 
        self.camera=toolutils.sceneViewer().curViewport().camera().path()

        self.build_UI()

    def build_UI(self):
        # option list is used in reset and setDefault methods
        self.option_list = ['fr_per_task', 'priority', 'pool','machine_limit','resolution','frange']

        # studio default values 
        self.studio_default_values = {'fr_per_task':'10','priority':'50', 'pool':'sim', 'machine_limit':'40','resolution_x':'2048', 'resolution_y':'1152' }

        # frames per task widget
        fr_per_task_Label = QtWidgets.QLabel("frames per task:")
        self.fr_per_task = QtWidgets.QLineEdit(self.studio_default_values['fr_per_task'])
        self.fr_per_task.setValidator(QtGui.QIntValidator())
        
        # resolution widget
        resolution_Label = QtWidgets.QLabel("resolution:")
        self.resolution_x = QtWidgets.QLineEdit(self.studio_default_values['resolution_x'])
        self.resolution_x.setValidator(QtGui.QIntValidator())
        self.resolution_y = QtWidgets.QLineEdit(self.studio_default_values['resolution_y'])
        self.resolution_y.setValidator(QtGui.QIntValidator())
        
        # priority widget
        priority_Label = QtWidgets.QLabel("priority:")
        self.priority = QtWidgets.QLineEdit(self.studio_default_values['priority'])
        self.priority.setValidator(QtGui.QIntValidator())
        
        # pool widget
        pool_Label = QtWidgets.QLabel("pool:")
        self.pool = QtWidgets.QComboBox()
        pools = self.deadline.Pools.GetPoolNames()
        self.pool.addItems(pools)
        # set sim as default pool
        index = self.pool.findText(self.studio_default_values['pool'], QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.pool.setCurrentIndex(index)
        
        # machine limit widget
        machine_limit_Label = QtWidgets.QLabel("machine limit:")
        self.machine_limit = QtWidgets.QLineEdit(self.studio_default_values['machine_limit'])
        self.machine_limit.setValidator(QtGui.QIntValidator())
        
        # frame range widget
        frange_Label = QtWidgets.QLabel("frame range:")
        self.frange_start = QtWidgets.QLineEdit(    str(  int( hou.hscriptExpression('$FSTART') )  )    ) #value gets rounded with int() and then converted to string for QLineEdit
        self.frange_start.setValidator(QtGui.QIntValidator())
        self.frange_end = QtWidgets.QLineEdit(    str(  int( hou.hscriptExpression('$FEND') )  )    ) #value gets rounded with int() and then converted to string for QLineEdit
        self.frange_end.setValidator(QtGui.QIntValidator())

        # button size
        button_width = 20

        # send - button widget
        send_button = QtWidgets.QPushButton("send to deadline")
        # reset all options to default values - button widget
        reset_all_button = QtWidgets.QPushButton("RA")
        reset_all_button.setToolTip('reset all')
        reset_all_button.setMaximumWidth(button_width + 5)
        # roll back to studio defaults - button widget
        studioDefaults_button = QtWidgets.QPushButton("SD")
        studioDefaults_button.setToolTip('roll back to studio defaults')
        studioDefaults_button.setMaximumWidth(button_width + 5)
        #  frame range - buttons widget
        reset_frange_button = QtWidgets.QPushButton("R")
        reset_frange_button.setToolTip('reset to scene frame range')
        reset_frange_button.setMaximumWidth(button_width)
        #  resolution - buttons widget
        reset_res_button = QtWidgets.QPushButton("R")
        reset_res_button.setToolTip('reset')
        reset_res_button.setMaximumWidth(button_width)
        setDefault_res_button = QtWidgets.QPushButton("D")
        setDefault_res_button.setToolTip('set as default') 
        setDefault_res_button.setMaximumWidth(button_width) 
        #  pool - buttons widget
        reset_pool_button = QtWidgets.QPushButton("R")
        reset_pool_button.setToolTip('reset')
        reset_pool_button.setMaximumWidth(button_width)
        setDefault_pool_button = QtWidgets.QPushButton("D")
        setDefault_pool_button.setToolTip('set as default')
        setDefault_pool_button.setMaximumWidth(button_width) 
        #  mlimit - buttons widget
        reset_mlimit_button = QtWidgets.QPushButton("R")
        reset_mlimit_button.setToolTip('reset')
        reset_mlimit_button.setMaximumWidth(button_width)
        setDefault_mlimit_button = QtWidgets.QPushButton("D")
        setDefault_mlimit_button.setToolTip('set as default') 
        setDefault_mlimit_button.setMaximumWidth(button_width)  
        #  priority - buttons widget
        reset_priority_button = QtWidgets.QPushButton("R")
        reset_priority_button.setToolTip('reset')
        reset_priority_button.setMaximumWidth(button_width)
        setDefault_priority_button = QtWidgets.QPushButton("D")
        setDefault_priority_button.setToolTip('set as default')  
        setDefault_priority_button.setMaximumWidth(button_width) 
        #  frTask - buttons widget
        reset_frTask_button = QtWidgets.QPushButton("R")
        reset_frTask_button.setToolTip('reset')
        reset_frTask_button.setMaximumWidth(button_width)
        setDefault_frTask_button = QtWidgets.QPushButton("D")
        setDefault_frTask_button.setToolTip('set as default')  
        setDefault_frTask_button.setMaximumWidth(button_width) 
        
        # check if settingsFile.ini exists
        if os.path.exists(self.settings_path):
            settings_obj = QtCore.QSettings(self.settings_path, QtCore.QSettings.IniFormat)
            list_of_categories = settings_obj.childGroups()

            # SET DEFAULTS  =========================================================================================================================================
            # if there are no default settings in settingsFile.ini in your home directory
            ini_file_category = 'Houdini_playblast_over_deadline_default_settings'

            if not ini_file_category in list_of_categories:
                self.set_defaults()


            # GET PREVIOUS SETTINGS IF THEY EXIST ====================================================================================================================
            # get settings file if exists. If they dont exixt they will be created on close event which is defined in closeEvent method of this class
            ini_file_category = 'Houdini_playblast_over_deadline'

            if ini_file_category in list_of_categories:
                self.fr_per_task.setText(settings_obj.value( ini_file_category + "/fr_per_task"))
                self.priority.setText(settings_obj.value( ini_file_category + "/priority"))

                saved_pool = settings_obj.value( ini_file_category + "/pool")
                index = self.pool.findText(saved_pool, QtCore.Qt.MatchFixedString)
                if index >= 0:
                    self.pool.setCurrentIndex(index)

                self.machine_limit.setText(settings_obj.value( ini_file_category + "/machine_limit"))
                self.resolution_x.setText(settings_obj.value( ini_file_category + "/resolution_x"))
                self.resolution_y.setText(settings_obj.value( ini_file_category + "/resolution_y"))
                self.frange_start.setText(settings_obj.value( ini_file_category + "/frange_start"))
                self.frange_end.setText(settings_obj.value( ini_file_category + "/frange_end"))


        # LAYOUT =================================================================================================================================================
        layout = QtWidgets.QGridLayout()
        
        # frames per task
        layout.addWidget(fr_per_task_Label, 0, 0)
        layout.addWidget(self.fr_per_task, 0, 1)
        layout.addWidget(reset_frTask_button, 0, 2)
        layout.addWidget(setDefault_frTask_button, 0, 3) 
        
        # priority
        layout.addWidget(priority_Label, 1, 0)
        layout.addWidget(self.priority, 1, 1)
        layout.addWidget(reset_priority_button, 1, 2)
        layout.addWidget(setDefault_priority_button, 1, 3)
        
        # pool
        layout.addWidget(pool_Label, 2, 0)
        layout.addWidget(self.pool, 2, 1)
        layout.addWidget(reset_pool_button, 2, 2)
        layout.addWidget(setDefault_pool_button, 2, 3)

        # machine limit
        layout.addWidget(machine_limit_Label, 3, 0)
        layout.addWidget(self.machine_limit, 3, 1)
        layout.addWidget(reset_mlimit_button, 3, 2)
        layout.addWidget(setDefault_mlimit_button, 3, 3)
        
        # resolution
        layout.addWidget(resolution_Label, 4, 0)
        layout.addWidget(self.resolution_x, 5, 0)
        layout.addWidget(self.resolution_y, 5, 1)
        layout.addWidget(reset_res_button, 5, 2)
        layout.addWidget(setDefault_res_button, 5, 3)

        # frame range 
        layout.addWidget(frange_Label, 6, 0)
        layout.addWidget(self.frange_start, 7, 0)
        layout.addWidget(self.frange_end, 7, 1) 
        layout.addWidget(reset_frange_button, 7, 2)
        
        # send button
        layout.addWidget(send_button, 8, 1)

        # reset all button
        layout.addWidget(reset_all_button, 8, 2)

        # roll back to studio defaults button
        layout.addWidget(studioDefaults_button, 8, 3) 
              
        # SET layout
        self.setLayout(layout)
        
        # ASSIGN FUNCTIONS TO BUTTONS =============================================================================================================================
        #submit
        send_button.clicked.connect(self.submit_to_deadline)

        # reset buttons
        reset_frTask_button.clicked.connect(partial(self.reset, 'fr_per_task'))
        reset_priority_button.clicked.connect(partial(self.reset, 'priority'))
        reset_pool_button.clicked.connect(partial(self.reset, 'pool'))
        reset_mlimit_button.clicked.connect(partial(self.reset, 'machine_limit'))
        reset_res_button.clicked.connect(partial(self.reset, 'resolution'))
        reset_frange_button.clicked.connect(partial(self.reset, 'frange'))
        reset_all_button.clicked.connect(partial(self.reset, 'all'))

        # set default buttons
        setDefault_frTask_button.clicked.connect(partial(self.set_defaults, 'fr_per_task'))
        setDefault_priority_button.clicked.connect(partial(self.set_defaults, 'priority'))
        setDefault_pool_button.clicked.connect(partial(self.set_defaults, 'pool'))
        setDefault_mlimit_button.clicked.connect(partial(self.set_defaults, 'machine_limit'))
        setDefault_res_button.clicked.connect(partial(self.set_defaults, 'resolution'))
        # set studio defaults
        studioDefaults_button.clicked.connect(self.set_studio_defaults)


    # SET DEFAULTS ================================================================================================================================================
    def set_defaults(self, option = 'all'):
        settings_obj = QtCore.QSettings(self.settings_path, QtCore.QSettings.IniFormat)
        ini_file_category = 'Houdini_playblast_over_deadline_default_settings'

        if option == 'all':
            option = self.option_list

        if 'fr_per_task' in option:    
            settings_obj.setValue( ini_file_category + "/fr_per_task", self.fr_per_task.text())
        if 'priority' in option:  
            settings_obj.setValue( ini_file_category + "/priority", self.priority.text())
        if 'pool' in option:
            settings_obj.setValue( ini_file_category + "/pool", self.pool.currentText())
        if 'machine_limit' in option:
            settings_obj.setValue( ini_file_category + "/machine_limit", self.machine_limit.text())
        if 'resolution' in option:
            settings_obj.setValue( ini_file_category + "/resolution_x", self.resolution_x.text())
            settings_obj.setValue( ini_file_category + "/resolution_y", self.resolution_y.text())


    # SET STUDIO DEFAULTS ===========================================================================================================================================
    def set_studio_defaults(self, option = 'all'):
        settings_obj = QtCore.QSettings(self.settings_path, QtCore.QSettings.IniFormat)
        ini_file_category = 'Houdini_playblast_over_deadline_default_settings'

        if option == 'all':
            option = self.option_list

        if 'fr_per_task' in option:    
            settings_obj.setValue( ini_file_category + "/fr_per_task", self.studio_default_values['fr_per_task'])
        if 'priority' in option:  
            settings_obj.setValue( ini_file_category + "/priority", self.studio_default_values['priority'])
        if 'pool' in option:
            settings_obj.setValue( ini_file_category + "/pool", self.studio_default_values['pool'])
        if 'machine_limit' in option:
            settings_obj.setValue( ini_file_category + "/machine_limit", self.studio_default_values['machine_limit'])
        if 'resolution' in option:
            settings_obj.setValue( ini_file_category + "/resolution_x", self.studio_default_values['resolution_x'])
            settings_obj.setValue( ini_file_category + "/resolution_y", self.studio_default_values['resolution_y'])

        # reset all options to the studio default values that are set in with this method
        self.reset('all')


    # RESET ================================================================================================================================================================
    def reset(self, option):
        # check if settingsFile.ini exists
        if os.path.exists(self.settings_path):
            settings_obj = QtCore.QSettings(self.settings_path, QtCore.QSettings.IniFormat)

            list_of_categories = settings_obj.childGroups()
            ini_file_category = 'Houdini_playblast_over_deadline_default_settings'

            # reset values with default values from settingsFile.ini 
            if ini_file_category in list_of_categories:
                if option == 'all':
                    option = self.option_list

                if 'fr_per_task' in option:    
                    self.fr_per_task.setText(settings_obj.value( ini_file_category + "/fr_per_task"))
                if 'priority' in option:  
                    self.priority.setText(settings_obj.value( ini_file_category + "/priority"))
                if 'pool' in option:
                    saved_pool = settings_obj.value( ini_file_category + "/pool")
                    index = self.pool.findText(saved_pool, QtCore.Qt.MatchFixedString)
                    if index >= 0:
                        self.pool.setCurrentIndex(index)
                if 'machine_limit' in option:
                    self.machine_limit.setText(settings_obj.value( ini_file_category + "/machine_limit"))
                if 'resolution' in option:
                    self.resolution_x.setText(settings_obj.value( ini_file_category + "/resolution_x"))
                    self.resolution_y.setText(settings_obj.value( ini_file_category + "/resolution_y"))
                if 'frange' in option:
                    self.frange_start.setText(str(  int( hou.hscriptExpression('$FSTART') )  ))
                    self.frange_end.setText(str(  int( hou.hscriptExpression('$FEND') )  ))



    # SUBMIT TO DEADLINE ================================================================================================================================================================
    def submit_to_deadline(self):
        #get values from dialog window
        fr_task = self.fr_per_task.text()
        priority = self.priority.text()
        pool = self.pool.currentText()
        machine_limit = self.machine_limit.text()
        start = self.frange_start.text()
        end = self.frange_end.text()
        rekey_version="v[0-9][0-9][0-9]"
        rxp=re.compile(rekey_version)
        partv=""

        # get scene info
        job_name = "houdini_playblast - {} {}".format(hou.hipFile.basename(), self.camera)
        file_path = hou.hipFile.path()
        file_path = file_path.replace('/','\\')
        dir_path,dir_file=os.path.split(file_path)
        dir_file=dir_file.split(".")[0]
        partv=rxp.findall(dir_file)[0]
        dir_path=os.path.join(dir_path,"review\\playblast\\{TODOversion}\\{TODOcamera}\\{TODOfilehouname}_{TODOcamera}")
        dir_path=dir_path.format(TODOversion=partv,TODOcamera=self.camera.replace("/","_")[1:],TODOfilehouname=dir_file)
        hou_version = hou.applicationVersion()
        hou_version = str(hou_version[0]) + '.' + str(hou_version[1]) + '.' + str(hou_version[2] )
        user = os.getenv('username')
        machine_name=socket.gethostname()
        # TODO check playblast_over_deadline
        playblast_over_deadline = os.path.join(NETWORK_HOUDINI_SCRIPTS, "playblast_over_deadline.py")
        JobInfo = {
            "Name": job_name,
            "UserName": user,
            "Frames": start + "-" + end,
            "Plugin": "CrCustomHoudinifxScript",
            "ChunkSize": fr_task,
            "Pool": pool,
            "Priority": priority,
            "OverrideTaskExtraInfoNames": "False",
            "MachineName": machine_name,
            "MachineLimit": machine_limit,
            "OutputDirectory0":dir_path
            }
    
        # TODO check Camera
        PluginInfo = {
            "Build": "64bit",
            "Version": hou_version,
            "Camera": self.camera,
            "resX": self.resolution_x.text(),
            "resY": self.resolution_y.text(),
            "SceneFile": file_path
        }
    
        try:
            response = self.deadline.Jobs.SubmitJob(JobInfo, PluginInfo)
        except Exception as e:
            print(e.message)
            print("Sorry, Web Service is currently down!")
            
        self.close()

    # SAVE SETTINGS ON CLOSE ================================================================================================================================================================
    def closeEvent(self, event):
        settings_obj = QtCore.QSettings(self.settings_path, QtCore.QSettings.IniFormat)
        ini_file_category = 'Houdini_playblast_over_deadline'

        settings_obj.setValue( ini_file_category + "/fr_per_task", self.fr_per_task.text())
        settings_obj.setValue( ini_file_category + "/priority", self.priority.text())
        settings_obj.setValue( ini_file_category + "/pool", self.pool.currentText())
        settings_obj.setValue( ini_file_category + "/machine_limit", self.machine_limit.text())
        settings_obj.setValue( ini_file_category + "/resolution_x", self.resolution_x.text())
        settings_obj.setValue( ini_file_category + "/resolution_y", self.resolution_y.text())
        settings_obj.setValue( ini_file_category + "/frange_start", self.frange_start.text())
        settings_obj.setValue( ini_file_category + "/frange_end", self.frange_end.text())


# check if file is saved 
if hou.hipFile.basename() == 'untitled.hip':
    print("File needs to be saved whit a name different than \"untitled.hip\"")
else:
    check_deadline = check_deadline_webservice()
    if check_deadline:
        dialog = submit_flipbook_to_deadline_window()
        dialog.show()
    else:
        print("Deadline Webservice not available. Try later or report to technical staff.")

import pyside2uic
import os
import qt_py_convert.run

print pyside2uic.__file__

def name_pattern(py_dir, py_file):
    py_file = os.path.splitext(py_file)[0] + "_UIs" + os.path.splitext(py_file)[1]
    return py_dir, py_file


currentDir = os.path.dirname(os.path.abspath(__file__))

pyside2uic.compileUiDir(currentDir, map=name_pattern)
qt_py_convert.run.process_folder(currentDir)

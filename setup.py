import sys
import os.path
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["tkinter", "mttkinter", "threading", "requests", "lxml", "aiohttp", "asyncio", "selenium"],
    "includes": ["tkinter"],
    'include_files': [
        os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
        os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
        os.path.join(os.path.dirname(__file__), "chromedriver.exe"),
        os.path.join(os.path.dirname(__file__), "showStatus.py"),
        os.path.join(os.path.dirname(__file__), "settings.py"),
        os.path.join(os.path.dirname(__file__), "39kfw.py"),
        os.path.join(os.path.dirname(__file__), "360tsg.py"),
        os.path.join(os.path.dirname(__file__), "hdfzx.py"),
        os.path.join(os.path.dirname(__file__), "xlbw.py"),
        os.path.join(os.path.dirname(__file__), "zyr.py"),
        os.path.join(os.path.dirname(__file__), "zysj.py"),
        os.path.join(os.path.dirname(__file__), "zyzyw.py"),
        os.path.join(os.path.dirname(__file__), "zyzymfw.py"),
        os.path.join(os.path.dirname(__file__), "jfp.py"),
    ]
    }

# GUI applications require a different base on Windows (the default is for a
# console application)
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# "bdist_msi": bdist_msi_options
setup(name="ArticleDownloadTools",
      version="2.0",
      description="ArticleDownloadTools",
      options={"build_exe": build_exe_options},
      executables=[Executable("app.py",
                              shortcutName="ArticleDownloadTools",
                              shortcutDir="DesktopFolder",
                              base=base)])

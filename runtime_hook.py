
import os
import sys
import pathlib
import importlib.machinery
import importlib.util
import logging
import logging.config

# 确保sys._MEIPASS存在于打包环境中
if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
    # 为打包环境添加模块搜索路径
    sys.path.insert(0, os.path.join(base_path, 'model'))
    sys.path.insert(0, os.path.join(base_path, 'utils'))
    
    # 修复工作目录
    os.chdir(base_path)

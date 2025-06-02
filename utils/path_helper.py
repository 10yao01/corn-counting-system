import os
import sys
from pathlib import Path

def get_application_path():
    """
    获取应用程序的根路径，适用于正常运行和PyInstaller打包后的环境
    """
    try:
        # PyInstaller创建临时文件夹并定义_MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # 正常Python环境
        base_path = os.path.dirname(os.path.abspath(__file__))
        # 返回到项目根目录
        base_path = os.path.dirname(base_path)
    
    return base_path

def resource_path(relative_path):
    """
    获取资源文件的绝对路径，适用于开发环境和PyInstaller打包环境
    """
    base_path = get_application_path()
    return os.path.join(base_path, relative_path)

def safe_path(path):
    """
    确保路径存在，如果不存在则创建
    """
    os.makedirs(path, exist_ok=True)
    return path

def get_file_dir(file_path):
    """
    获取文件所在的目录
    """
    return os.path.dirname(os.path.abspath(file_path))

def make_relative_path(path, reference_path=None):
    """
    安全地创建相对路径，处理不同驱动器的情况
    """
    if reference_path is None:
        reference_path = os.getcwd()
    
    try:
        return os.path.relpath(path, reference_path)
    except ValueError:
        # 如果在不同驱动器上，返回绝对路径
        return os.path.abspath(path) 
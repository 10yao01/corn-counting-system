#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
手动创建spec文件，解决编码问题
"""
import os
import sys

def create_spec_file():
    """创建正确编码的spec文件"""
    
    # 创建runtime hook文件
    runtime_hook_content = '''
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
'''

    with open('runtime_hook.py', 'w', encoding='utf-8') as f:
        f.write(runtime_hook_content)
    
    # 创建spec文件
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# 收集静态文件
static_files = []
for root, dirs, files in os.walk('static'):
    for file in files:
        source_path = os.path.join(root, file)
        dest_path = os.path.join('static', os.path.relpath(source_path, 'static'))
        static_files.append((source_path, os.path.dirname(dest_path)))

# 收集模型文件
model_files = []
for root, dirs, files in os.walk('model'):
    for file in files:
        source_path = os.path.join(root, file)
        dest_path = os.path.join('model', os.path.relpath(source_path, 'model'))
        model_files.append((source_path, os.path.dirname(dest_path)))

# 收集工具文件
utils_files = []
for root, dirs, files in os.walk('utils'):
    for file in files:
        source_path = os.path.join(root, file)
        dest_path = os.path.join('utils', os.path.relpath(source_path, 'utils'))
        utils_files.append((source_path, os.path.dirname(dest_path)))

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=static_files + model_files + utils_files,
    hiddenimports=[
        'PIL._tkinter_finder', 'numpy', 'torch', 'cv2', 'model.detect', 
        'utils.path_helper', 'PyQt5.sip', 'logging', 'logging.config', 'logging.handlers',
        'importlib', 'importlib.machinery', 'importlib.util',
        'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends.backend_agg'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=['notebook', 'jupyter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='玉米植株计数系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 控制台模式便于调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/icon.ico' if os.path.exists('static/icon.ico') else None,
)
'''
    
    with open('玉米植株计数系统.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print('已创建spec文件: 玉米植株计数系统.spec')
    print('现在可以运行: pyinstaller 玉米植株计数系统.spec')

if __name__ == '__main__':
    create_spec_file() 
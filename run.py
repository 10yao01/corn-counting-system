#!/usr/bin/env python
"""
玉米植株计数系统 - PyQt5版本启动脚本
"""
import sys
import os
from qt import CornCountingApp
from PyQt5.QtWidgets import QApplication

# 在Windows下隐藏控制台窗口
if os.name == 'nt':
    try:
        import ctypes
        # 获取控制台窗口句柄
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        # 如果有窗口句柄，则隐藏它
        if hwnd != 0:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception as e:
        print(f"隐藏控制台窗口失败: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CornCountingApp()
    sys.exit(app.exec_()) 
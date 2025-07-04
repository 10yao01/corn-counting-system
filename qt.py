import os
import sys
import uuid
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QLabel, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                             QMessageBox, QFrame, QSplashScreen, QSizePolicy,
                             QDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QGraphicsRectItem, QSpinBox, QCheckBox)
from PyQt5.QtGui import QPixmap, QFont, QIcon, QMovie, QPen, QBrush, QPainter
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QRectF
from PIL import Image
from model.detect import detect_image

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

# 确保utils目录在路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, "utils")
if utils_dir not in sys.path:
    sys.path.insert(0, utils_dir)


# 备用方案：定义必要的函数
def get_application_path():
    """获取应用程序的根路径"""
    try:
        # PyInstaller创建临时文件夹并定义_MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # 正常Python环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path

def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    base_path = get_application_path()
    return os.path.join(base_path, relative_path)

def safe_path(path):
    """确保路径存在"""
    os.makedirs(path, exist_ok=True)
    return path

class ImageCropDialog(QDialog):
    """图片裁剪对话框"""
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.crop_rect = None
        
        # 获取图片的原始尺寸
        self.original_image_size = self.get_image_size(image_path)
        if not self.original_image_size:
            QMessageBox.critical(self, "错误", "无法读取图片尺寸")
            self.reject()
            return
            
        self.init_ui()
        
    def get_image_size(self, image_path):
        """获取图片的原始尺寸"""
        try:
            with Image.open(image_path) as img:
                return img.size  # (width, height)
        except Exception as e:
            print(f"获取图片尺寸失败: {e}")
            return None
        
    def init_ui(self):
        self.setWindowTitle('图片裁剪')
        self.setModal(True)
        
        # 设置窗口可以调整大小，并设置最小尺寸
        self.setMinimumSize(800, 600)
        self.resize(1200, 900)  # 增大默认窗口大小
        
        # 允许窗口最大化
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        layout = QVBoxLayout(self)
        
        # 图片信息显示区域
        info_group = QWidget()
        info_group.setStyleSheet("QWidget { border: 1px solid #4CAF50; border-radius: 5px; padding: 10px; background-color: #f0f8f0; }")
        info_layout = QVBoxLayout(info_group)
        
        info_title = QLabel('图片信息')
        info_title.setFont(QFont('Arial', 12, QFont.Bold))
        info_layout.addWidget(info_title)
        
        self.image_info_label = QLabel(f'原始尺寸: {self.original_image_size[0]} x {self.original_image_size[1]} 像素')
        self.image_info_label.setFont(QFont('Arial', 10))
        info_layout.addWidget(self.image_info_label)
        
        layout.addWidget(info_group)
        
        # 裁剪尺寸设置区域
        size_group = QWidget()
        size_group.setStyleSheet("QWidget { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        size_layout = QVBoxLayout(size_group)
        
        # 标题
        size_title = QLabel('裁剪尺寸设置')
        size_title.setFont(QFont('Arial', 12, QFont.Bold))
        size_layout.addWidget(size_title)
        
        # 尺寸控件布局
        size_controls_layout = QHBoxLayout()
        
        # 宽度设置
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel('宽度:'))
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(100, self.original_image_size[0])  # 限制为图片原始宽度
        self.width_spinbox.setValue(min(2048, self.original_image_size[0]))
        self.width_spinbox.setSuffix(' px')
        self.width_spinbox.valueChanged.connect(self.on_size_changed)
        width_layout.addWidget(self.width_spinbox)
        size_controls_layout.addLayout(width_layout)
        
        # 高度设置
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel('高度:'))
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(100, self.original_image_size[1])  # 限制为图片原始高度
        self.height_spinbox.setValue(min(2048, self.original_image_size[1]))
        self.height_spinbox.setSuffix(' px')
        self.height_spinbox.valueChanged.connect(self.on_size_changed)
        height_layout.addWidget(self.height_spinbox)
        size_controls_layout.addLayout(height_layout)
        
        # 保持纵横比选项
        self.keep_aspect_ratio_checkbox = QCheckBox('保持纵横比')
        self.keep_aspect_ratio_checkbox.setChecked(True)
        self.keep_aspect_ratio_checkbox.stateChanged.connect(self.on_aspect_ratio_changed)
        size_controls_layout.addWidget(self.keep_aspect_ratio_checkbox)
        
        # 快速设置按钮
        quick_size_layout = QHBoxLayout()
        quick_size_layout.addWidget(QLabel('快速设置:'))
        
        # 根据图片尺寸动态调整快速设置选项
        quick_sizes = []
        max_dimension = max(self.original_image_size)
        
        for size_value in [1024, 2048, 4096]:
            if size_value <= max_dimension:
                quick_sizes.append((f'{size_value}x{size_value}', size_value))
        
        # 添加适应图片尺寸的选项 - 使用图片的实际长宽
        if self.original_image_size[0] != self.original_image_size[1] or max_dimension not in [1024, 2048, 4096]:
            quick_sizes.append((f'最大尺寸({self.original_image_size[0]}x{self.original_image_size[1]})', max_dimension))
        
        for size_name, size_value in quick_sizes:
            btn = QPushButton(size_name)
            btn.clicked.connect(lambda checked, s=size_value: self.set_quick_size(s))
            quick_size_layout.addWidget(btn)
        
        size_layout.addLayout(size_controls_layout)
        size_layout.addLayout(quick_size_layout)
        layout.addWidget(size_group)
        
        # 说明标签
        info_label = QLabel('操作说明：\n1、 左键点击拖拽选择裁剪区域  2、+/-键或者滚轮缩放图片\n•3、右键或Ctrl+左键拖拽移动视图  4、空格键恢复适应窗口')
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("QLabel { color: #555; font-size: 15px; padding: 8px; font-weight: bold; }")
        layout.addWidget(info_label)
        
        # 创建图形视图 - 设置为可扩展
        self.graphics_view = ImageCropView(self.image_path)
        self.graphics_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.graphics_view.setMinimumSize(400, 300)  # 设置最小尺寸
        self.graphics_view.set_crop_size(self.width_spinbox.value(), self.height_spinbox.value())
        layout.addWidget(self.graphics_view)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.crop_btn = QPushButton('确认裁剪')
        self.crop_btn.clicked.connect(self.accept_crop)
        button_layout.addWidget(self.crop_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 保存纵横比
        self.aspect_ratio = self.width_spinbox.value() / self.height_spinbox.value()
    
    def resizeEvent(self, event):
        """窗口大小改变时重新适应图片显示"""
        super().resizeEvent(event)
        if hasattr(self, 'graphics_view'):
            # 当窗口大小改变时，重新适应图片到视图
            self.graphics_view.fitInView(self.graphics_view.image_item, Qt.KeepAspectRatio)
    
    def on_size_changed(self):
        """当尺寸改变时更新裁剪视图"""
        sender = self.sender()
        
        # 检查输入的尺寸是否超过图片原始尺寸
        current_width = self.width_spinbox.value()
        current_height = self.height_spinbox.value()
        
        size_adjusted = False
        warning_message = ""
        
        if current_width > self.original_image_size[0]:
            self.width_spinbox.blockSignals(True)
            self.width_spinbox.setValue(self.original_image_size[0])
            self.width_spinbox.blockSignals(False)
            size_adjusted = True
            warning_message += f"宽度已限制为图片原始宽度: {self.original_image_size[0]}px\n"
            
        if current_height > self.original_image_size[1]:
            self.height_spinbox.blockSignals(True)
            self.height_spinbox.setValue(self.original_image_size[1])
            self.height_spinbox.blockSignals(False)
            size_adjusted = True
            warning_message += f"高度已限制为图片原始高度: {self.original_image_size[1]}px"
        
        if size_adjusted:
            QMessageBox.information(self, "尺寸调整", warning_message.strip())
        
        if self.keep_aspect_ratio_checkbox.isChecked():
            if sender == self.width_spinbox:
                # 宽度改变，调整高度
                new_height = int(self.width_spinbox.value() / self.aspect_ratio)
                new_height = max(100, min(self.original_image_size[1], new_height))
                self.height_spinbox.blockSignals(True)
                self.height_spinbox.setValue(new_height)
                self.height_spinbox.blockSignals(False)
            elif sender == self.height_spinbox:
                # 高度改变，调整宽度
                new_width = int(self.height_spinbox.value() * self.aspect_ratio)
                new_width = max(100, min(self.original_image_size[0], new_width))
                self.width_spinbox.blockSignals(True)
                self.width_spinbox.setValue(new_width)
                self.width_spinbox.blockSignals(False)
        
        # 更新裁剪视图
        self.graphics_view.set_crop_size(self.width_spinbox.value(), self.height_spinbox.value())
        
    def on_aspect_ratio_changed(self):
        """当纵横比设置改变时"""
        if self.keep_aspect_ratio_checkbox.isChecked():
            # 记录当前纵横比
            self.aspect_ratio = self.width_spinbox.value() / self.height_spinbox.value()
        
    def set_quick_size(self, size):
        """设置快速尺寸"""
        # 临时禁用保持纵横比，避免在快速设置时受到纵横比限制
        original_keep_aspect = self.keep_aspect_ratio_checkbox.isChecked()
        self.keep_aspect_ratio_checkbox.setChecked(False)
        
        # 如果是特殊的最大尺寸标识，使用图片的原始长和宽
        if size == max(self.original_image_size):
            actual_width = self.original_image_size[0]
            actual_height = self.original_image_size[1]
        else:
            # 检查快速设置尺寸是否超过图片原始尺寸
            actual_width = min(size, self.original_image_size[0])
            actual_height = min(size, self.original_image_size[1])
            
            if actual_width != size or actual_height != size:
                QMessageBox.information(
                    self, 
                    "尺寸调整", 
                    f"快速设置尺寸 {size}x{size} 超过图片原始尺寸，已调整为 {actual_width}x{actual_height}"
                )
        
        # 设置宽度和高度
        self.width_spinbox.setValue(actual_width)
        self.height_spinbox.setValue(actual_height)
        
        # 恢复原来的纵横比设置
        self.keep_aspect_ratio_checkbox.setChecked(original_keep_aspect)
        
        # 更新纵横比
        self.aspect_ratio = actual_width / actual_height
    
    def accept_crop(self):
        """确认裁剪"""
        crop_rect = self.graphics_view.get_crop_rect()
        if crop_rect:
            self.crop_rect = crop_rect
            self.accept()
        else:
            QMessageBox.warning(self, "警告", "请先选择裁剪区域")

class ImageCropView(QGraphicsView):
    """支持裁剪选择的图像视图"""
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # 加载图像
        pixmap = QPixmap(image_path)
        self.image_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.image_item)
        
        # 裁剪矩形
        self.crop_rect_item = None
        self.crop_width = 2048  # 可变裁剪宽度
        self.crop_height = 2048  # 可变裁剪高度
        
        # 鼠标操作相关
        self.start_pos = None
        self.is_dragging = False
        self.is_panning = False  # 添加拖拽标识
        self.last_pan_point = None
        
        # 设置视图属性
        self.setDragMode(QGraphicsView.NoDrag)
        self.setRenderHint(QPainter.Antialiasing)
        
        # 启用滚轮缩放
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # 设置缩放限制
        self.min_scale = 0.1
        self.max_scale = 5.0
        
        # 适应图像大小
        self.fitInView(self.image_item, Qt.KeepAspectRatio)
    
    def wheelEvent(self, event):
        """处理滚轮缩放事件"""
        # 获取当前缩放因子
        current_scale = self.transform().m11()
        
        # 计算缩放因子
        if event.angleDelta().y() > 0:
            scale_factor = 1.25  # 放大
        else:
            scale_factor = 0.8   # 缩小
        
        # 检查缩放限制
        new_scale = current_scale * scale_factor
        if new_scale < self.min_scale or new_scale > self.max_scale:
            return
        
        # 应用缩放
        self.scale(scale_factor, scale_factor)
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key_Space:
            # 空格键恢复适应窗口
            self.fitInView(self.image_item, Qt.KeepAspectRatio)
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            # +键放大
            current_scale = self.transform().m11()
            if current_scale < self.max_scale:
                self.scale(1.25, 1.25)
        elif event.key() == Qt.Key_Minus:
            # -键缩小
            current_scale = self.transform().m11()
            if current_scale > self.min_scale:
                self.scale(0.8, 0.8)
        else:
            super().keyPressEvent(event)
    
    def set_crop_size(self, width, height):
        """设置裁剪尺寸"""
        self.crop_width = width
        self.crop_height = height
        
        # 如果当前有裁剪框，更新它的大小
        if self.crop_rect_item:
            current_rect = self.crop_rect_item.rect()
            # 保持中心位置不变，更新尺寸
            center_x = current_rect.center().x()
            center_y = current_rect.center().y()
            
            new_rect = QRectF(
                center_x - self.crop_width / 2,
                center_y - self.crop_height / 2,
                self.crop_width,
                self.crop_height
            )
            
            # 确保新矩形不超出图像边界
            image_rect = self.image_item.boundingRect()
            new_rect = self._constrain_rect_to_image(new_rect, image_rect)
            
            self.crop_rect_item.setRect(new_rect)
    
    def _constrain_rect_to_image(self, rect, image_rect):
        """将矩形限制在图像边界内"""
        # 获取裁剪尺寸
        crop_w = min(self.crop_width, image_rect.width())
        crop_h = min(self.crop_height, image_rect.height())
        
        # 调整位置确保不超出边界
        x = max(image_rect.left(), min(rect.x(), image_rect.right() - crop_w))
        y = max(image_rect.top(), min(rect.y(), image_rect.bottom() - crop_h))
        
        return QRectF(x, y, crop_w, crop_h)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 获取场景坐标
            scene_pos = self.mapToScene(event.pos())
            
            # 检查点击是否在图像内
            if self.image_item.contains(self.image_item.mapFromScene(scene_pos)):
                if event.modifiers() == Qt.ControlModifier:
                    # Ctrl+左键：开始拖拽视图
                    self.is_panning = True
                    self.last_pan_point = event.pos()
                    self.setCursor(Qt.ClosedHandCursor)
                else:
                    # 普通左键：开始裁剪选择
                    self.start_pos = scene_pos
                    self.is_dragging = True
                    
                    # 移除之前的裁剪矩形
                    if self.crop_rect_item:
                        self.scene.removeItem(self.crop_rect_item)
                        self.crop_rect_item = None
        elif event.button() == Qt.RightButton:
            # 右键：开始拖拽视图
            self.is_panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_panning and self.last_pan_point:
            # 拖拽视图
            delta = event.pos() - self.last_pan_point
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pan_point = event.pos()
        elif self.is_dragging and self.start_pos:
            current_pos = self.mapToScene(event.pos())
            
            # 计算裁剪矩形（可变大小）
            image_rect = self.image_item.boundingRect()
            
            # 计算裁剪矩形的位置，使其以点击位置为中心
            rect_x = current_pos.x() - self.crop_width / 2
            rect_y = current_pos.y() - self.crop_height / 2
            
            # 如果图像小于裁剪大小，调整裁剪大小
            actual_crop_width = min(self.crop_width, image_rect.width())
            actual_crop_height = min(self.crop_height, image_rect.height())
            
            # 确保矩形不超出图像边界
            rect_x = max(image_rect.left(), min(rect_x, image_rect.right() - actual_crop_width))
            rect_y = max(image_rect.top(), min(rect_y, image_rect.bottom() - actual_crop_height))
            
            crop_rect = QRectF(rect_x, rect_y, actual_crop_width, actual_crop_height)
            
            # 创建或更新裁剪矩形
            if self.crop_rect_item:
                self.scene.removeItem(self.crop_rect_item)
            
            self.crop_rect_item = QGraphicsRectItem(crop_rect)
            
            # 动态计算边界线宽度 - 根据图片大小和缩放比例
            pen_width = self.calculate_pen_width(image_rect)
            pen = QPen(Qt.red, pen_width)
            pen.setStyle(Qt.DashLine)
            self.crop_rect_item.setPen(pen)
            brush = QBrush(Qt.red)
            brush.setStyle(Qt.NoBrush)
            self.crop_rect_item.setBrush(brush)
            self.scene.addItem(self.crop_rect_item)
        
        super().mouseMoveEvent(event)
    
    def calculate_pen_width(self, image_rect):
        """
        根据图像大小和视图缩放比例动态计算边界线宽度
        
        Args:
            image_rect: 图像在场景中的矩形区域
            
        Returns:
            int: 计算出的边界线宽度
        """
        # 获取图像的实际像素尺寸
        image_width = image_rect.width()
        image_height = image_rect.height()
        image_diagonal = (image_width ** 2 + image_height ** 2) ** 0.5
        
        # 获取视图的当前缩放因子
        view_transform = self.transform()
        scale_factor = (view_transform.m11() + view_transform.m22()) / 2.0
        
        # 基础宽度计算：根据图像大小分级
        if image_diagonal > 8000: 
            base_width = max(image_diagonal / 400.0, 8.0)  # 更大的基础宽度
        elif image_diagonal > 5000: 
            base_width = max(image_diagonal / 500.0, 6.0)
        elif image_diagonal > 3000: 
            base_width = max(image_diagonal / 800.0, 4.0)
        else:  # 小图片 (<1500px对角线)
            base_width = max(image_diagonal / 1000.0, 3.0)
        
        # 根据缩放因子调整：缩放越小（图像看起来越小），线条需要越粗
        scale_adjustment = max(1.0 / scale_factor, 0.3)
        
        # 计算最终宽度
        final_width = base_width * scale_adjustment
        
        # 对于大图片，额外增加宽度保证可见性
        if image_diagonal > 8000:
            final_width *= 2  # 大图片额外增加50%宽度
        
        # 设置合理的范围：最小3像素，最大30像素（增加最大值）
        final_width = max(3, min(int(final_width), 30))
        
        return final_width
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            if self.is_panning:
                self.is_panning = False
                self.setCursor(Qt.ArrowCursor)
        elif event.button() == Qt.RightButton:
            if self.is_panning:
                self.is_panning = False
                self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)
    
    def get_crop_rect(self):
        """获取裁剪矩形在原图像中的坐标"""
        if not self.crop_rect_item:
            return None
        
        # 获取裁剪矩形在场景中的位置
        scene_rect = self.crop_rect_item.rect()
        
        # 转换为图像坐标
        image_rect = self.image_item.boundingRect()
        
        # 计算相对于图像的位置
        rel_x = scene_rect.x() - image_rect.x()
        rel_y = scene_rect.y() - image_rect.y()
        
        return (int(rel_x), int(rel_y), int(scene_rect.width()), int(scene_rect.height()))

class DetectionWorker(QThread):
    finished = pyqtSignal(int, str, str)  # count, result_filename, error_message
    
    def __init__(self, upload_folder, result_folder, filename, model_weights):
        super().__init__()
        self.upload_folder = upload_folder
        self.result_folder = result_folder
        self.filename = filename
        self.model_weights = model_weights
        
    def run(self):
        count, error_message = detect_image(
            self.upload_folder,
            self.result_folder,
            self.filename,
            self.model_weights
        )
        result_filename = 'processed_' + self.filename
        self.finished.emit(count, result_filename, error_message or "")

class ScalableImageLabel(QLabel):
    """可缩放的图片标签，会随着窗口大小自动调整图片尺寸"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(300, 300)
        self.setStyleSheet("border: 1px solid #cccccc; background-color: #f0f0f0;")
        self._pixmap = None
        self.setScaledContents(False)  # 不使用setScaledContents，而是自己处理缩放
        
    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self._update_pixmap()
        
    def _update_pixmap(self):
        if self._pixmap and not self._pixmap.isNull():
            scaled_pixmap = self._pixmap.scaled(
                self.width(), 
                self.height(),
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            super().setPixmap(scaled_pixmap)
    
    def resizeEvent(self, event):
        """当组件大小改变时，重新缩放图片"""
        super().resizeEvent(event)
        self._update_pixmap()

class CornCountingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置基本路径，使用路径辅助模块
        self.base_dir = get_application_path()
        self.UPLOAD_FOLDER = safe_path(os.path.join(self.base_dir, 'static', 'files'))
        self.RESULT_FOLDER = safe_path(os.path.join(self.base_dir, 'static', 'images'))
        self.MODEL_WEIGHTS = resource_path(os.path.join('model', 'yolov5_best.pt'))
        
        # 确保目录存在
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(self.RESULT_FOLDER, exist_ok=True)
        
        # 允许的文件扩展名
        self.ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
        
        # 状态变量
        self.uploaded_file = None
        self.processed_file = None
        self.plant_count = 0
        self.loading_label = None
        self.loading_movie = None
        
        self.init_ui()
    
    def init_ui(self):
        # 设置窗口
        self.setWindowTitle('玉米植株计数系统')
        self.setMinimumSize(800, 600)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 添加标题
        title_label = QLabel('玉米植株计数系统')
        title_label.setFont(QFont('Arial', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel('上传玉米田图片进行自动计数分析')
        subtitle_label.setFont(QFont('Arial', 12))
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # 图像区域
        self.image_layout = QHBoxLayout()
        main_layout.addLayout(self.image_layout)
        
        # 原始图像区域
        self.original_image_container = QWidget()
        original_layout = QVBoxLayout(self.original_image_container)
        self.original_title = QLabel('原始图像')
        self.original_title.setAlignment(Qt.AlignCenter)
        original_layout.addWidget(self.original_title)
        
        # 使用新的可缩放图像标签
        self.original_image = ScalableImageLabel()
        original_layout.addWidget(self.original_image)
        
        # 处理后图像区域
        self.processed_image_container = QWidget()
        processed_layout = QVBoxLayout(self.processed_image_container)
        self.processed_title = QLabel('处理后图像')
        self.processed_title.setAlignment(Qt.AlignCenter)
        processed_layout.addWidget(self.processed_title)
        
        # 使用新的可缩放图像标签
        self.processed_image = ScalableImageLabel()
        processed_layout.addWidget(self.processed_image)
        
        # 添加两个图像区域到布局
        self.image_layout.addWidget(self.original_image_container)
        self.image_layout.addWidget(self.processed_image_container)
        
        # 统计结果区域
        self.stats_container = QWidget()
        stats_layout = QVBoxLayout(self.stats_container)
        self.stats_label = QLabel('植株计数结果')
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setFont(QFont('Arial', 14, QFont.Bold))
        stats_layout.addWidget(self.stats_label)
        
        self.count_label = QLabel('请先上传并处理图片')
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setFont(QFont('Arial', 24, QFont.Bold))
        stats_layout.addWidget(self.count_label)
        
        main_layout.addWidget(self.stats_container)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.upload_btn = QPushButton('选择图片')
        self.upload_btn.clicked.connect(self.upload_image)
        button_layout.addWidget(self.upload_btn)
        
        self.process_btn = QPushButton('开始识别')
        self.process_btn.clicked.connect(self.process_image)
        self.process_btn.setEnabled(False)
        button_layout.addWidget(self.process_btn)
        
        self.save_btn = QPushButton('保存结果')
        self.save_btn.clicked.connect(self.save_result)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        
        # 加载样式
        self.apply_styles()
        
        # 显示窗口
        self.center_window()
        self.show()
    
    def center_window(self):
        """将窗口居中显示"""
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.desktop().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
    
    def apply_styles(self):
        """应用样式表"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f9f9f9;
            }
            QLabel {
                color: #212121;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QStatusBar {
                background-color: #f0f0f0;
                color: #757575;
            }
        """)
    
    def upload_image(self):
        """打开文件对话框并上传图片"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", 
            "图片文件 (*.jpg *.jpeg *.png)", 
            options=options
        )
        
        if file_path:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext[1:] not in self.ALLOWED_EXTENSIONS:
                QMessageBox.warning(self, "格式错误", "只支持JPG和PNG格式的图片文件")
                return
            
            # 生成唯一文件名
            unique_id = uuid.uuid4().hex
            filename = unique_id + '_' + os.path.basename(file_path)
            dest_path = os.path.join(self.UPLOAD_FOLDER, filename)
            
            # 复制文件
            shutil.copy(file_path, dest_path)
            
            # 检查图像尺寸并在需要时调整
            resized = self.resize_image_if_needed(dest_path, max_size=2048)
            if resized:
                self.statusBar().showMessage('图像尺寸过大，已自动调整为适合处理的尺寸')
            
            # 显示原始图像
            pixmap = QPixmap(dest_path)
            if not pixmap.isNull():
                self.original_image.setPixmap(pixmap)
                self.uploaded_file = filename
                self.process_btn.setEnabled(True)
                self.statusBar().showMessage(f'已上传: {os.path.basename(file_path)}')
                
                # 清除处理过的图像（如果有）
                self.processed_image.clear()
                self.processed_file = None
                self.count_label.setText('请先处理图片')
            else:
                QMessageBox.warning(self, "错误", "无法加载图片")
    
    def process_image(self):
        """处理图像并显示结果"""
        if not self.uploaded_file:
            QMessageBox.warning(self, "错误", "请先上传图片")
            return
        
        # 显示处理中的状态
        self.statusBar().showMessage('正在处理图像...')
        
        # 禁用按钮，防止重复处理
        self.process_btn.setEnabled(False)
        self.upload_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        
        # 创建加载动画
        self.loading_label = QLabel()
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.loading_label.setMinimumSize(300, 300)
        self.loading_label.setStyleSheet("border: 1px solid #cccccc; background-color: #f0f0f0;")
        
        loading_gif_path = resource_path("static/loading.gif")
        if os.path.exists(loading_gif_path):
            self.loading_movie = QMovie(loading_gif_path)
            self.loading_label.setMovie(self.loading_movie)
            self.loading_movie.start()
            
            # 替换处理后图像为加载动画
            processed_layout = self.processed_image_container.layout()
            processed_layout.replaceWidget(self.processed_image, self.loading_label)
            self.processed_image.setVisible(False)
            self.loading_label.setVisible(True)
        else:
            # 如果没有加载动画，显示文本
            self.processed_image.setText("处理中...")
        
        # 创建后台线程处理图像
        self.worker = DetectionWorker(
            self.UPLOAD_FOLDER,
            self.RESULT_FOLDER,
            self.uploaded_file,
            self.MODEL_WEIGHTS
        )
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.start()
    
    def on_processing_finished(self, count, result_filename, error_message):
        """图像处理完成回调"""
        # 恢复处理后图像视图
        if self.loading_label and self.loading_movie:
            self.loading_movie.stop()
            processed_layout = self.processed_image_container.layout()
            # 显示回图像标签
            self.processed_image.setVisible(True)
            self.loading_label.setVisible(False)
            processed_layout.replaceWidget(self.loading_label, self.processed_image)
            # 删除加载动画标签
            self.loading_label.deleteLater()
            self.loading_label = None
            self.loading_movie = None
        
        # 重新启用按钮
        self.upload_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        
        if error_message and error_message.strip():
            # 处理过程中出现错误，显示错误信息
            QMessageBox.critical(self, "处理错误", error_message)
            self.statusBar().showMessage("处理失败")
            self.count_label.setText('处理失败，请重试')
            return
        
        # 显示处理后的图像
        result_path = os.path.join(self.RESULT_FOLDER, result_filename)
        if os.path.exists(result_path):
            pixmap = QPixmap(result_path)
            if not pixmap.isNull():
                self.processed_image.setPixmap(pixmap)
                self.processed_file = result_filename
                # 启用保存按钮
                self.save_btn.setEnabled(True)
            else:
                self.processed_image.setText("无法加载处理后的图像")
        else:
            self.processed_image.setText("处理结果文件不存在")
        
        # 更新计数结果
        self.plant_count = count
        self.count_label.setText(f'识别到 {count} 个玉米植株')
        
        # 更新状态栏
        self.statusBar().showMessage(f'处理完成，共识别 {count} 个玉米植株')
    
    def save_result(self):
        """保存处理后的图像"""
        if not self.processed_file:
            QMessageBox.warning(self, "错误", "没有可保存的处理结果")
            return
        
        # 打开保存对话框
        options = QFileDialog.Options()
        default_name = f"result_{self.processed_file.split('_', 2)[-1]}"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果", default_name, 
            "图片文件 (*.jpg *.png)", options=options
        )
        
        if file_path:
            # 复制处理后的图像到选择的路径
            source_path = os.path.join(self.RESULT_FOLDER, self.processed_file)
            shutil.copy(source_path, file_path)
            self.statusBar().showMessage(f'结果已保存到: {file_path}')
    
    def resize_image_if_needed(self, image_path, max_size=2048):
        """调整图像尺寸"""
        try:
            img = Image.open(image_path)
            original_mode = img.mode
            width, height = img.size
            resized = False
            format_converted = False
            
            # 检查图像尺寸是否超过最大尺寸
            if width > max_size or height > max_size:
                # 弹出提示窗口，询问用户是否要进行裁剪
                reply = QMessageBox.question(
                    self, 
                    "图片过大", 
                    f"图片尺寸为 {width}x{height}，请对图片进行处理。\n\n请选择处理方式：\n- 点击'yes'进行图片裁剪\n- 点击'no'自动缩放图片", 
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # 用户选择裁剪，打开裁剪对话框
                    crop_dialog = ImageCropDialog(image_path, self)
                    if crop_dialog.exec_() == QDialog.Accepted:
                        crop_rect = crop_dialog.crop_rect
                        if crop_rect:
                            # 执行裁剪
                            x, y, w, h = crop_rect
                            img = img.crop((x, y, x + w, y + h))
                            resized = True
                    else:
                        # 用户取消裁剪，进行自动缩放
                        ratio = min(max_size / width, max_size / height)
                        new_width = int(width * ratio)
                        new_height = int(height * ratio)
                        img = img.resize((new_width, new_height), Image.LANCZOS)
                        resized = True
                else:
                    # 用户选择自动缩放
                    ratio = min(max_size / width, max_size / height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    resized = True
            
            # 处理图片格式问题
            file_ext = os.path.splitext(image_path)[1].lower()
            
            # 如果是PNG格式且有透明通道
            if img.mode == 'RGBA':
                # 要保存为JPG或需要调整大小，需要转换为RGB
                if file_ext == '.jpg' or file_ext == '.jpeg' or resized:
                    # 创建一个白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    # 将原图与白色背景合成
                    background.paste(img, mask=img.split()[3])  # 使用alpha通道作为蒙版
                    img = background
                    format_converted = True
            # 其他格式转换为RGB（例如P模式等）
            elif img.mode != 'RGB' and (file_ext == '.jpg' or file_ext == '.jpeg' or resized):
                img = img.convert('RGB')
                format_converted = True
            
            # 如果图片被调整大小或格式被转换，保存图片
            if resized or format_converted:
                img.save(image_path)
                return True
            return False
        except Exception as e:
            print(f"调整图像尺寸时出错: {e}")
            return False
    
    def resizeEvent(self, event):
        """窗口大小改变时调用"""
        super().resizeEvent(event)
        # 这里不需要任何代码，因为ScalableImageLabel会自动处理

def resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和PyInstaller打包后的环境"""
    try:
        # PyInstaller创建临时文件夹，定义_MEIPASS属性
        base_path = sys._MEIPASS
    except Exception:
        # 处于正常的Python环境
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CornCountingApp()
    sys.exit(app.exec_())
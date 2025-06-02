import numpy as np
from PIL import Image, ImageDraw
import os

def create_loading_gif(output_path="static/loading.gif", frames=20, size=100, duration=80):
    """创建简单的加载动画GIF"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 创建一系列帧
    images = []
    for i in range(frames):
        # 创建透明背景图像
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # 计算旋转角度
        angle = (i / frames) * 2 * np.pi
        
        # 画圆弧
        arc_radius = size // 2 - 10
        bbox = (10, 10, size - 10, size - 10)
        
        # 计算开始和结束角度，使圆弧动起来
        start_angle = (angle * 180 / np.pi) % 360
        end_angle = (start_angle + 60) % 360
        
        # 画弧
        draw.arc(bbox, start_angle, end_angle, fill=(76, 175, 80, 255), width=5)
        
        # 转换为RGB模式（或保持RGBA）
        images.append(img)
    
    # 保存为GIF
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        transparency=0,
        disposal=2
    )
    
    print(f"加载动画GIF已保存到: {output_path}")

if __name__ == "__main__":
    create_loading_gif() 
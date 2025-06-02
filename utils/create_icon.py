from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(output_path="static/icon.ico", size=256):
    """
    创建一个简单的应用程序图标
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 创建一个正方形图像
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制绿色圆形背景
    radius = size // 2
    draw.ellipse((0, 0, size-1, size-1), fill=(76, 175, 80, 255))
    
    # 绘制简单的玉米图标
    # 玉米柄
    stalk_color = (100, 70, 30, 255)
    stalk_width = size // 20
    stalk_height = size // 3
    stalk_x = size // 2
    stalk_y = size - stalk_height
    draw.line(
        [(stalk_x, size), (stalk_x, stalk_y)], 
        fill=stalk_color, 
        width=stalk_width
    )
    
    # 玉米叶
    leaf_color = (50, 150, 50, 255)
    leaf_width = size // 25
    leaf_start_y = stalk_y + stalk_height // 3
    # 左叶
    draw.arc(
        (stalk_x - size//3, leaf_start_y - size//6, stalk_x, leaf_start_y + size//6),
        180, 270,
        fill=leaf_color,
        width=leaf_width
    )
    # 右叶
    draw.arc(
        (stalk_x, leaf_start_y - size//6, stalk_x + size//3, leaf_start_y + size//6),
        270, 360,
        fill=leaf_color,
        width=leaf_width
    )
    
    # 玉米棒
    corn_color = (250, 220, 50, 255)
    corn_width = size // 2.5
    corn_height = size // 1.8
    corn_x = size // 2 - corn_width // 2
    corn_y = size // 6
    draw.ellipse(
        (corn_x, corn_y, corn_x + corn_width, corn_y + corn_height),
        fill=corn_color
    )
    
    # 玉米粒图案
    grain_color = (250, 180, 30, 255)
    grain_size = size // 30
    for i in range(5):
        for j in range(10):
            if (i + j) % 2 == 0:
                x = corn_x + corn_width // 5 * (i+1)
                y = corn_y + corn_height // 12 * (j+1)
                draw.ellipse(
                    (x - grain_size, y - grain_size, x + grain_size, y + grain_size),
                    fill=grain_color
                )
    
    # 保存为ICO文件
    img.save(output_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"图标已保存到: {output_path}")

if __name__ == "__main__":
    create_icon() 
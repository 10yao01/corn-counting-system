import os
import uuid
import shutil
from flask import Flask, render_template, request, redirect, url_for, session, flash
from PIL import Image
import sys

def resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和PyInstaller打包后的环境"""
    try:
        # PyInstaller创建临时文件夹，定义_MEIPASS属性
        base_path = sys._MEIPASS
    except Exception:
        # 处于正常的Python环境
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# 配置Flask应用
app = Flask(__name__, 
            template_folder=resource_path('templates'),
            static_folder=resource_path('static'))

# 修改上传和结果文件夹路径
base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
UPLOAD_FOLDER = os.path.join(base_dir, 'static', 'files')
RESULT_FOLDER = os.path.join(base_dir, 'static', 'images')
MODEL_WEIGHTS = os.path.join(base_dir, 'model', 'yolov5_best.pt')

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['MODEL_WEIGHTS'] = MODEL_WEIGHTS
app.secret_key = 'ypf1101'  # 设置一个安全的密钥


# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg'}  # 只允许jpg和png

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image_if_needed(image_path, max_size=2048):
    """
    检查图像尺寸，如果超过最大尺寸，则调整到最大尺寸
    
    Args:
        image_path: 图像文件路径
        max_size: 最大尺寸（宽和高）
    
    Returns:
        bool: 是否调整了图像尺寸
    """
    try:
        img = Image.open(image_path)
        original_mode = img.mode
        width, height = img.size
        resized = False
        format_converted = False
        
        # 检查图像尺寸是否超过最大尺寸
        if width > max_size or height > max_size:
            # 计算缩放比例
            ratio = min(max_size / width, max_size / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            # 调整图像尺寸
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 检查是否有文件上传
        if 'file' not in request.files:
            flash('未检测到文件', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('未选择文件', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # 生成唯一文件名
            unique_id = uuid.uuid4().hex
            filename = unique_id + '_' + file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # 检查图像尺寸并在需要时调整
            resized = resize_image_if_needed(file_path, max_size=2048)
            if resized:
                flash('图像尺寸过大，已自动调整为适合处理的尺寸', 'info')
            
            # 将文件名存入session
            session['uploaded_file'] = filename
            if 'uploaded_file' in session:
                session['uploaded_file_preview'] = session['uploaded_file'][33:]
            return redirect(url_for('index'))
        else:
            flash('只允许上传JPG和PNG格式的图片文件', 'error')
            return redirect(request.url)
    
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'uploaded_file' not in session:
        flash('请先上传图片', 'error')
        return redirect(url_for('index'))
    
    # 获取原始文件路径
    src_path = os.path.join(app.config['UPLOAD_FOLDER'], session['uploaded_file'])
    
    # print(src_path) # static/files/b758a20a6d3740dda01556fa7030129d_Seed_0010.jpg

    # 导入detect模块中的detect_image函数
    from model.detect import detect_image
    
    # 调用detect_image函数处理图像，获取植株计数
    count = detect_image(
        app.config['UPLOAD_FOLDER'],
        app.config['RESULT_FOLDER'], 
        session['uploaded_file'],
        app.config['MODEL_WEIGHTS']
    )
    
    # 生成处理后文件名
    result_filename = 'processed_' + session['uploaded_file']
    
    # 保存结果文件名到session
    session['processed_file'] = result_filename
    
    # 保存植株计数结果到session
    session['plant_count'] = count
    
    # 添加成功处理的提示信息
    flash(f'图像处理成功！已识别{count}个玉米植株', 'success')
    
    return redirect(url_for('result'))

@app.route('/result')
def result():
    if 'processed_file' not in session:
        flash('请先上传并处理图片', 'error')
        return redirect(url_for('index'))
    
    image_url = url_for('static', filename=f'images/{session["processed_file"]}')
    # 从session中获取植株计数结果
    plant_count = session.get('plant_count', 0)
    
    return render_template('result.html', image_url=image_url, cnt=plant_count)

if __name__ == '__main__':
    app.run(debug=True)
import os
import uuid
import shutil
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'ypf1101'  # 设置一个安全的密钥

# 配置上传路径
UPLOAD_FOLDER = '/workspace/counting_system/static/files'
RESULT_FOLDER = '/workspace/counting_system/static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg'}  # 只允许jpg和png

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
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
    
    print(src_path) # static/files/b758a20a6d3740dda01556fa7030129d_Seed_0010.jpg

    # 导入detect模块中的detect_image函数
    from model.detect import detect_image
    
    # 调用detect_image函数处理图像，获取植株计数
    count = detect_image(
        app.config['UPLOAD_FOLDER'],
        app.config['RESULT_FOLDER'], 
        session['uploaded_file']
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
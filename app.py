import os
import uuid
import shutil
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'ypf1101'  # 设置一个安全的密钥

# 配置上传路径
UPLOAD_FOLDER = 'static/files'
RESULT_FOLDER = 'static/images'
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
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
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
            flash('只允许上传JPG和PNG格式的图片文件')
            return redirect(request.url)
    
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'uploaded_file' not in session:
        return redirect(url_for('index'))
    
    # 获取原始文件路径
    src_path = os.path.join(app.config['UPLOAD_FOLDER'], session['uploaded_file'])
    
    # 生成处理后文件名
    result_filename = 'processed_' + session['uploaded_file']
    dest_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
    
    # 复制文件模拟处理过程（实际应替换为真实处理逻辑）
    shutil.copy(src_path, dest_path)
    
    # 保存结果文件名到session
    session['processed_file'] = result_filename
    return redirect(url_for('result'))

@app.route('/result')
def result():
    if 'processed_file' not in session:
        return redirect(url_for('index'))
    
    image_url = url_for('static', filename=f'images/{session["processed_file"]}')
    return render_template('result.html', image_url=image_url)



if __name__ == '__main__':
    app.run(debug=True)
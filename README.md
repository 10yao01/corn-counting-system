# corn-counting-system
**corn counting system for the UAV images of field based on Yolov5 by ultralytics**
**基于田间无人机图像的玉米植株计数系统**

## 安装
```bash
# create conda enviroment
conda create -n counting_system python=3.10

# Clone the repository
git clone https://github.com/10yao01/corn-counting-system.git

# Navigate to the cloned directory
cd corn-counting-system

# Install the package
pip install -r requirements.txt
```

## Usage

### 网页运行 (Flask)
```bash
# Run the Flask web application
python app.py
```

### 桌面应用运行 (PyQt5)
```bash
# Run the PyQt5 desktop application
python run.py
```

### 打包

```bash
python manual_spec.py

pyinstaller 玉米植株计数系统.spec
```

## 引用
[ultralytics](https://github.com/ultralytics/ultralytics)
# corn-counting-system
**corn counting system for the UAV images of field based on Yolov5 by ultralytics**

## usage
```
# create conda enviroment
conda create -n counting_system python=3.10

# Clone the repository
git clone https://github.com/10yao01/corn-counting-system.git

# Navigate to the cloned directory
cd corn-counting-system

# Install the package
pip install -r requirements.txt

# run
python app.py
```
[Docker](https://hub.docker.com/) is also recommended to complete the environment configuration,for torch you can access [docker hub for pytorch](https://hub.docker.com/r/pytorch/pytorch) 

I use [pytorch/pytorch:2.0.0-cuda11.7-cudnn8-devel](https://hub.docker.com/layers/pytorch/pytorch/2.0.0-cuda11.7-cudnn8-devel/images/sha256-96ccb2997a131f2455d70fb78dbb284bafe4529aaf265e344bae932c8b32b2a4)

## Citations
[ultralytics](https://github.com/ultralytics/ultralytics)
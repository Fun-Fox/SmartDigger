#!/bin/bash

# 设置环境变量
export FLASK_APP=api_run.py
export FLASK_ENV=production

# 安装依赖
pip install -r requirements.txt

# 启动 Flask 应用
flask run --host=0.0.0.0 --port=5000
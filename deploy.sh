#!/bin/bash

# 设置环境变量
# 安装依赖
pip install -r requirements.txt

# 启动 api 应用
python api_run.py

# 启动 web UI应用
python web_ui.py
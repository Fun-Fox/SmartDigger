import gradio as gr
import requests
import base64
import re
from PIL import Image, ImageDraw
import os

from dotenv import load_dotenv

load_dotenv()


def diagnose(screenshot_file, xml_file, devices_name, resolution):
    # 初始化变量
    processed_screenshot_path = None

    # 读取截图文件并转换为 Base64 编码
    with open(screenshot_file.name, "rb") as f:
        screenshot = base64.b64encode(f.read()).decode('utf-8')
    if xml_file:
        # 读取 XML 文件并转换为字符串
        with open(xml_file.name, "r", encoding='utf-8') as f:
            xml_content = f.read()

    url = "http://localhost:5000/api/v1/diagnose"
    payload = {
        "screenshot": screenshot,
        "xml_file": xml_content if xml_file else "",
        "devices_name": devices_name,
        "resolution": resolution
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        result = response.json()
        print(result)
        msg = result.get("msg", "")
        script = result.get("script", "")
        # 解析 ADB 命令中的点击坐标
        match = re.search(r"跳过的坐标为:\s*\((\d+),\s*(\d+)\)", msg)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            print(f"提取的坐标为: ({x}, {y})")
            # 基于分辨率参数绘制黄星
            # if resolution:
            #     # width, height = map(int, resolution.replace('(', '').replace(')', '').split(','))
            img = Image.open(screenshot_file.name)
            draw = ImageDraw.Draw(img)
            # 绘制黄星
            # 绘制更大的黄色五角星
            draw.polygon([
                (x - 20, y),  # 左顶点
                (x - 6, y - 16),  # 左上内点
                (x, y - 20),  # 上顶点
                (x + 6, y - 16),  # 右上内点
                (x + 20, y),  # 右顶点
                (x + 6, y + 16),  # 右下内点
                (x, y + 20),  # 下顶点
                (x - 6, y + 16)  # 左下内点
            ], fill="yellow", outline="black")

            # 保存处理后的截图到临时文件
            processed_screenshot_path = "processed_screenshot.png"
            img.save(processed_screenshot_path)
        else:
            processed_screenshot_path = None

        # 新增：读取并显示模板图片
        template_image = None
        if result.get("template_file_name") is not None:
            template_file_name = result.get("template_file_name")
            template_dir = os.getenv('TEMPLATE_DIR')
            template_path = os.path.join(template_dir, template_file_name)
            if os.path.exists(template_path):
                template_image = Image.open(template_path)
        else:
            template_image = None
        # 返回处理后的截图和模板图片
        return result.get("msg", ""), script, processed_screenshot_path, template_image
    else:
        return "诊断失败", None, None, None


current_file_path = os.path.abspath(__file__)
project_root = os.path.dirname(current_file_path)

# 使用 Blocks API 自定义布局
with gr.Blocks() as demo:
    gr.Markdown("## SmartDigger 诊断中心-弹窗诊断")
    gr.Markdown("使用 Gradio 调用本地 5000 端口的诊断接口，优化后的界面提供更直观的操作体验。")

    with gr.Row():
        with gr.Column():
            screenshot_input = gr.File(label="手机屏幕截图文件",
                                       value=os.path.join(project_root, "source/test/test-3.jpeg"))
            xml_input = gr.File(label="XML层级结构文件（可选）",
                                value=os.path.join(project_root, "source/test/hierarchy-3.xml"))
            devices_input = gr.Textbox(label="设备名称", value="172.25.13.8:5555")
            resolution_input = gr.Textbox(label="设备分辨率（可选）", value="(1440, 3120)")
            submit_button = gr.Button("提交诊断")

        with gr.Column():
            msg_output = gr.Textbox(label="诊断结果消息")
            script_output = gr.Textbox(label="生成的 ADB 点击脚本")

    # 将两张图片放在同一行
    with gr.Row():
        processed_image_output = gr.Image(label="关闭弹窗坐标点（使用黄色星标识）")
        template_image_output = gr.Image(label="模版库保存的弹窗模板")

    # 绑定提交事件
    submit_button.click(
        diagnose,
        inputs=[screenshot_input, xml_input, devices_input, resolution_input],
        outputs=[msg_output, script_output, processed_image_output, template_image_output]
    )

if __name__ == "__main__":
    demo.launch(server_port=5001)

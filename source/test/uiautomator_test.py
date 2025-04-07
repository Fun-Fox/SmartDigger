import uiautomator2 as u2
from pprint import pprint  # 导入pprint模块

d = u2.connect('S2D0219109002374')
if __name__ == "__main__":
    pprint(d.info)  # 使用pprint格式化输出

    # d
# python uiautomator2 环境搭建
# pip install  uiautomator2
# 手机安装uiautomator apk
# python -m uiautomator2 init
# 卸载  remove minitouch, minicap, atx app etc, from device
# python -m  uiautomator2 purge

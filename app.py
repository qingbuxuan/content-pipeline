# -*- coding: utf-8 -*-
"""Flask 应用入口（所有逻辑已在 pipeline.py）"""
from config import *
from html_converter import *
from utils import *
from wechat import *
from prompts import *
from pipeline import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)

# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/19
# @Author   : fanke.chang
# @File     : mabangConfig.py
# @Desc     :

import os

__dir__ = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(__dir__, '../..'))

download_file_path = os.path.join(project_dir, "shopify_producting/data/mabang_download.csv")
download_file_no_surfix = os.path.splitext(os.path.basename(download_file_path))[0]
download_file_dirname = os.path.dirname(download_file_path)
processed_file_path = os.path.join(download_file_dirname, f"{download_file_no_surfix}_output.csv")

google_category_file_en = os.path.join(project_dir, "shopify_producting/resources/taxonomy-with-ids.en-US.xls")
google_category_file_cn = os.path.join(project_dir, "shopify_producting/resources/taxonomy-with-ids.en-CN.xls")


emoji_code = {'material': '&#x1F48E;',
              'craftsmanship': '&#x1F6E0;',
              'fashion_element': '&#x1F4A5;',
              'style': '&#x1F3B5;',
              'size': '&#x1F50D;',
              'free_shipping': '&#x1F69A;',
              }

#shopify配置参数
# SHOPIFY_SHOP_URL = '34460e.myshopify.com'
# SHOPIFY_API_KEY = '093a3e097bc79f63fe13c683022bc5e2'
# SHOPIFY_PASSWORD = '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'

# SHOPIFY_SHOP_URL = 'bd5910.myshopify.com'
# SHOPIFY_API_KEY = '24a55d491c877f2a39ecf5daaa9bf172'
# # SHOPIFY_API_KEY = '75103bfd38d006ed622eeaf56d2219e2'
# SHOPIFY_PASSWORD='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'


SHOPIFY_SHOP_URL = '075bc9-3.myshopify.com'
SHOPIFY_API_KEY = '6467a608a6a31ace2df1921a8d778dca'
# SHOPIFY_API_KEY = 'c25349fc85d3751d77da6703c7c19c89'
SHOPIFY_PASSWORD = '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'

OPENAI_API_KEY = "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"

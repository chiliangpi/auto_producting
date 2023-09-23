# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/19
# @Author   : fanke.chang
# @File     : mabangConfig.py
# @Desc     :

import os

download_file_path = "./src/shopify_producting/data/mabang_download.csv"
download_file_no_surfix = os.path.splitext(os.path.basename(download_file_path))
download_file_dirname = os.path.dirname(download_file_path)
processed_file_path = os.path.join(download_file_dirname, f"{download_file_dirname}_output.csv")

google_category_file_en = "./src/shopify_producting/resources/taxonomy-with-ids.en-US.xls"
google_category_file_cn = "./src/shopify_producting/resources/taxonomy-with-ids.en-CN.xls"


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

SHOPIFY_SHOP_URL = 'bd5910.myshopify.com'
# SHOPIFY_API_KEY = '75103bfd38d006ed622eeaf56d2219e2'
SHOPIFY_API_KEY = '24a55d491c877f2a39ecf5daaa9bf172'
SHOPIFY_PASSWORD='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'

OPENAI_API_KEY = "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"




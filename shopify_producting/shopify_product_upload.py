# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/18
# @Author   : fanke.chang
# @File     : shopify_product_upload.py
# @Desc     :

import sys
import os

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, '../..')))

import pandas as pd
import json
import re
import time
from shopify_producting.conf import *
from shopify_producting.utils import *
from shopify_producting.logging_config import logger
import shopify

shopify.ShopifyResource.set_site(f"https://{SHOPIFY_API_KEY}:{SHOPIFY_PASSWORD}@{SHOPIFY_SHOP_URL}/admin")

df_input = pd.read_csv(processed_file_path, sep='\t', dtype=str).fillna('')


for i in range(len(df_input)):
    row = df_input.iloc[i, :]
    gpt_result_dict = json.loads(row.gpt_result_json)
    title = gpt_result_dict.get('brief_title')
    body_html = body_html_process(gpt_result_dict, max_listing=4)
    vendor = 'My Store'
    product_type = gpt_result_dict.get('type')
    variants = json.loads(row.variants)
    created_at = row.creat_time
    tags = gpt_result_dict.get('tags')
    options = json.loads(row.options)
    images = [{'position': position, 'src': src} for position, src in enumerate(row.product_images_url.split(','), 1)]

    product_info = {
                        "title": title,
                        "body_html": body_html,
                        "vendor": vendor,
                        "product_type": product_type,
                        "created_at": created_at,
                        "updated_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                        "published_scope": "global",
                        "tags": tags,
                        "status": 'active',
                        "published": True,
                        "variants": variants,
                        "options": options,
                        "images": images,
                    }
    new_product = shopify.Product.create(product_info)
    logger.info(f"product_title={new_product.title} upload succeed")

logger.info(f"total upload {i+1} products")


# products = shopify.Product.find()
# products = shopify.Product.find(limit=5)
# product = products[0]
# json.dumps
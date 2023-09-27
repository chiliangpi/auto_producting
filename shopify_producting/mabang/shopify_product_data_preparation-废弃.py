# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/18
# @Author   : fanke.chang
# @File     : shopify_product_data_preparation-废弃.py
# @Desc     :
import time

import pandas as pd
import json
import re
from collections import OrderedDict
from shopify_producting.conf.config import *
from shopify_producting.utils import *
from googletrans import Translator
import easyocr

translator = Translator()
orcReader = easyocr.Reader(['en', 'ch_sim'])

df_input = pd.read_csv(input_file_path, sep='\t', dtype=str).fillna('')

period_tokens = 0
columns = ['master_sku_id','unique_id','product_url','main_brand','sub_brand','title_cn_ori','title_en_ori','cost_price','weight','video_url','developer','creater','creat_time','product_length','product_width','product_height','minimum_order_quantity','product_master_image_url_ori','product_window_images_url_ori','product_attribute_images_url_ori','product_description_images_url_ori','product_description_cn_ori','product_description_en_ori','supplier_name','purchase_days','varients_ori','options_ori']
columns = columns + ['variants', 'options', 'product_master_image_url', 'product_images_url', 'gpt_result_json']
with open(output_file_path, 'w') as f:
    f.write('\t'.join(columns))
    f.write('\n')
    for i in range(len(df_input)):
        row = df_input.iloc[i, :]
        image_detect_history={}
        translate_history={}
        variants, image_detect_history, translate_history = variants_process(row.varients_ori, orcReader, translator, image_detect_history, translate_history)
        options, translate_history = options_process(row.options_ori, translator, translate_history)

        product_images_url = []
        for images_url in [row.product_master_image_url_ori, row.product_window_images_url_ori, row.product_attribute_images_url_ori]:
            if not images_url:
                continue
            for image_url in images_url.split(','):
                image_detect_result, image_detect_history = image_detect_chinese(orcReader, image_url, image_detect_history)
                if image_detect_result == 'not_contain_chinese':
                    product_images_url.append(image_url)

        product_master_image_url = product_images_url[0] if product_images_url else ''

        gpt_result_json, usage_tokens = gpt_generate_info(row.title_cn_ori, row.product_description_cn_ori, model='gpt-3.5-turbo-0613')
        period_tokens += usage_tokens
        if (i+1) % 3000 == 0 or (period_tokens+1) % 90000 == 0:
            time.sleep(10)

        output = row.astype('str').tolist() + [variants, options, product_master_image_url, ','.join(product_images_url), gpt_result_json]
        f.write("\t".join(output))
        f.write("\n")
print("OVER")
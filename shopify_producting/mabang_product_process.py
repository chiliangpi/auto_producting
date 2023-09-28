# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/16
# @Author   : fanke.chang
# @File     : mabang_product_process.py
# @Desc     :


import sys
import os

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, '..')))
sys.path.insert(1, "/home/aistudio/external-libraries")

import pandas as pd
import json
import re
from collections import OrderedDict
from datetime import datetime
import time
from shopify_producting.conf.config import *
from shopify_producting.utils import *
# from googletrans import Translator
from shopify_producting.logging_config import logger

from shopify_producting.models_utils import ImageStructureOCR, GPTGenerator

def generate_varients(df_group):
    df_group = df_group.reset_index(drop=True)
    df_group['position'] = df_group.index + 1
    df_group['sku'] = df_group.apply(lambda x: x['主sku编号'].strip() + "-" + str(x['position']), axis=1)
    df_group['option1'] = df_group['属性值1']
    df_group['option2'] = df_group['属性值2']
    df_group['option3'] = df_group['属性值3']
    df_group['price'] = df_group['子sku成本价']
    df_group['image_src'] = df_group['子sku多属性图片']
    df_group['grams'] = df_group['子sku重量(克)']
    df_group['weight'] = df_group['子sku重量(克)'].max()
    df_group['weight_unit'] = 'g'
    df_group['varients'] = df_group[['sku','option1','option2','option3','price','position','image_src','grams','weight','weight_unit']].to_dict(orient='records')
    return json.dumps(df_group['varients'].tolist(), ensure_ascii=False)

def generate_options(df_group):
    options_res = []
    for i in range(1,4,1):
        df_option_temp = df_group[~((df_group[f'属性值{i}'].isna()) | (df_group[f'属性值{i}']==''))]
        option_name = df_option_temp[f'属性名{i}'].max()
        option_values = df_option_temp[f'属性值{i}'].unique().tolist()
        if option_name and option_values:
            options_res.append({'name':option_name, 'values':option_values})
        else:
            pass
    return json.dumps(options_res, ensure_ascii=False)

def product_agg(df_group):
    master_sku_id = df_group['主sku编号'].max().strip()
    unique_id = df_group['唯一ID'].max()
    product_url = df_group['对标产品链接'].max()
    main_brand = df_group['品牌'].max()
    sub_brand = df_group['子品牌'].max()
    title_cn_ori = df_group['产品标题(中文)'].max()
    title_en_ori = df_group['产品标题(英文)'].max()
    cost_price = df_group['成本价'].max()
    weight = df_group['产品重量(克)'].max()
    video_url = df_group['视频URL'].max()
    developer = df_group['开发员'].max()
    creater = df_group['创建人'].max()
    creat_time = df_group['创建时间'].max()
    # creat_time = datetime.strftime(datetime.strptime(creat_time, "%Y/%m/%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    product_length = df_group['产品长度'].max()
    product_width = df_group['产品宽度'].max()
    product_height = df_group['产品高度'].max()
    minimum_order_quantity = df_group['起订量'].max()
    product_master_image_url_ori = df_group['产品主图'].max().strip(',')
    product_window_images_url_ori = re.sub(r'[\n\r]', '',df_group['橱窗图'].max()).strip(',')
    product_attribute_images_url_ori = re.sub(r'[\n\r]', '', df_group['多属性图'].max()).strip(',')
    product_description_images_url_ori = re.sub(r'[\n\r]', '',df_group['描述图'].max()).strip(',')
    product_description_cn_ori = df_group['纯文本描述(中文)'].max()
    product_description_cn_ori = re.sub(r'[\n\r]', ';', product_description_cn_ori).strip()
    product_description_en_ori = df_group['纯文本描述(英文)'].max().strip()
    product_description_en_ori = re.sub(r'[\n\r]', ';', product_description_en_ori).strip()
    supplier_name = df_group['供应商名称'].max().strip(',')
    purchase_days = df_group['采购天数'].max()
    varients_ori = generate_varients(df_group)
    options_ori = generate_options(df_group)

    return pd.DataFrame({
                        'master_sku_id': [master_sku_id],
                        'unique_id': [unique_id],
                        'product_url': [product_url],
                        'main_brand': [main_brand],
                        'sub_brand': [sub_brand],
                        'title_cn_ori': [title_cn_ori],
                        'title_en_ori': [title_en_ori],
                        'cost_price': [cost_price],
                        'weight': [weight],
                        'video_url': [video_url],
                        'developer': [developer],
                        'creater': [creater],
                        'creat_time': [creat_time],
                        'product_length': [product_length],
                        'product_width': [product_width],
                        'product_height': [product_height],
                        'minimum_order_quantity': [minimum_order_quantity],
                        'product_master_image_url_ori': [product_master_image_url_ori],
                        'product_window_images_url_ori': [product_window_images_url_ori],
                        'product_attribute_images_url_ori': [product_attribute_images_url_ori],
                        'product_description_images_url_ori': [product_description_images_url_ori],
                        'product_description_cn_ori': [product_description_cn_ori],
                        'product_description_en_ori': [product_description_en_ori],
                        'supplier_name': [supplier_name],
                        'purchase_days': [purchase_days],
                        'varients_ori': [varients_ori],
                        'options_ori': [options_ori],
                        })

if __name__ == '__main__':
    # translator = Translator()
    translator = None
    # orcReader = easyocr.Reader(['en', 'ch_sim'])
    orcReader = ImageStructureOCR()
    gpt_generator = GPTGenerator()

    df_mabang_download = pd.read_csv(download_file_path, dtype=str).fillna('').replace(r'\t', '', regex=True)
    df_mabang_download['唯一ID'] = 'mabang-' + df_mabang_download['唯一ID'].astype(str)
    df_mabang_download['属性名3'] = ''
    df_mabang_download['属性值3'] = ''
    df_mabang_download['position'] = df_mabang_download.groupby('主sku编号').cumcount() + 1
    df_mabang_download['weight_unit'] = 'g'
    df_mabang_download['key'] = df_mabang_download['主sku编号']

    df_product_agg = df_mabang_download.groupby(['key']).apply(lambda df_group: product_agg(df_group)).reset_index(drop=True)

    period_tokens = 0
    # columns = ['master_sku_id','unique_id','product_url','main_brand','sub_brand','title_cn_ori','title_en_ori','cost_price','weight','video_url','developer','creater','creat_time','product_length','product_width','product_height','minimum_order_quantity','product_master_image_url_ori','product_window_images_url_ori','product_attribute_images_url_ori','product_description_images_url_ori','product_description_cn_ori','product_description_en_ori','supplier_name','purchase_days','varients_ori','options_ori']
    columns = list(df_product_agg.columns) + ['variants', 'options', 'product_master_image_url', 'product_images_url', 'gpt_result_json']
    with open(processed_file_path, 'w') as f:
        f.write('\t'.join(columns))
        f.write('\n')
        for i in range(len(df_product_agg)):
            row = df_product_agg.iloc[i, :]
            image_detect_history={}
            translate_history={}
            variants, image_detect_history, translate_history = variants_process(row.varients_ori, orcReader, translator, image_detect_history, translate_history)
            options, translate_history = options_process(row.options_ori, translator, translate_history)

            product_images_url = []
            for images_url in [row.product_master_image_url_ori, row.product_window_images_url_ori, row.product_attribute_images_url_ori]:
                if not images_url:
                    continue
                for image_url in images_url.split(','):
                    image_detect_info, image_detect_history = orcReader.image_detect(images_url, image_detect_history)
                    if image_detect_info.get('is_contain_chinese') == 'not_contain_chinese' or image_detect_info.get('is_contain_table') == 'not_contain_table':
                        product_images_url.append(image_url)

            product_master_image_url = product_images_url[0] if product_images_url else ''

            gpt_result_json, usage_tokens = gpt_generator.openai_generate(row.title_cn_ori, row.product_description_cn_ori, model='gpt-3.5-turbo-0613')
            period_tokens += usage_tokens
            if (i+1) % 3000 == 0 or (period_tokens+1) % 90000 == 0:
                time.sleep(10)

            output = row.astype('str').tolist() + [variants, options, product_master_image_url, ','.join(product_images_url), gpt_result_json]
            f.write("\t".join(output))
            f.write("\n")
            if (i+1)%100==0:
                logger.info(f"{i+1} products over")
    logger.info(f"total process {i+1} products")



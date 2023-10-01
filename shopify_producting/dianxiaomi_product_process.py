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
    df_group['option1'] = df_group['变种属性值1']
    df_group['option2'] = df_group['变种属性值2']
    df_group['option3'] = df_group['变种属性值3']
    df_group['price'] = df_group['价格']
    df_group['image_src'] = df_group['变种图（URL）地址']
    # df_group['grams'] = df_group['子sku重量(克)']
    df_group['weight'] = df_group['重量']
    df_group['weight_unit'] = df_group['重量单位']
    df_group['varients'] = df_group[['sku','option1','option2','option3','price','image_src','position','weight','weight_unit']].to_dict(orient='records')
    return json.dumps(df_group['varients'].tolist(), ensure_ascii=False)

def generate_options(df_group):
    options_res = []
    for i in range(1,4,1):
        df_option_temp = df_group[~((df_group[f'变种属性值{i}'].isna()) | (df_group[f'变种属性值{i}'] == ''))]
        option_name = df_option_temp[f'变种主题{i}'].max()
        option_values = df_option_temp[f'变种属性值{i}'].unique().tolist()
        if option_name and option_values:
            options_res.append({'name':option_name, 'values':option_values})
    return json.dumps(options_res, ensure_ascii=False)

def product_agg(df_group):
    product_id = df_group['SPU（仅用于区分产品）'].max()
    product_url = df_group['来源1（URL）'].max()
    title_cn_ori = df_group['产品标题（必填）'].max()
    cost_price = df_group['价格'].max()
    weight = df_group['重量'].max()
    weight_unit = df_group['重量单位'].max()
    creat_time = df_group['创建时间'].max()
    update_time = df_group['更新时间'].max()
    # creat_time = datetime.strftime(datetime.strptime(creat_time, "%Y/%m/%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    product_master_image_url_ori = df_group['主图（URL）地址'].max().strip(',')
    product_variant_image_urls_ori = re.sub(r'[\n\r]', '',df_group['变种图（URL）地址'].max()).strip(',')
    product_attached_image_urls_ori = re.sub(r'[\n\r]', '', df_group['附图（URL）地址'].max()).strip(',')
    # product_description_image_urls_ori = re.sub(r'[\n\r]', '',df_group['描述图'].max()).strip(',')
    product_description_cn_ori = df_group['产品描述'].max()
    supplier_name = df_group['供货商'].max().strip(',')
    category_name_ori = df_group['分类'].max()
    varients_ori = generate_varients(df_group)
    options_ori = generate_options(df_group)

    return pd.DataFrame({
                        'product_id': [product_id],
                        'product_url': [product_url],
                        'title_cn_ori': [title_cn_ori],
                        'category_name_ori': [category_name_ori],
                        'cost_price': [cost_price],
                        'weight': [weight],
                        'weight_unit': [weight_unit],
                        'creat_time': [creat_time],
                        'update_time': [update_time],
                        'product_master_image_url_ori': [product_master_image_url_ori],
                        'product_variant_image_urls_ori': [product_variant_image_urls_ori],
                        'product_attached_image_urls_ori': [product_attached_image_urls_ori],
                        'product_description_cn_ori': [product_description_cn_ori],
                        'supplier_name': [supplier_name],
                        'varients_ori': [varients_ori],
                        'options_ori': [options_ori],
                        })

if __name__ == '__main__':
    # translator = Translator()
    translator = None
    # orcReader = easyocr.Reader(['en', 'ch_sim'])
    orcReader = ImageStructureOCR()
    gpt_generator = GPTGenerator()

    df_dianxiaomi_download = pd.read_excel(download_file_path, dtype=str).fillna('').replace(r'\t', '', regex=True)
    df_dianxiaomi_download['SPU（仅用于区分产品）'] = 'DXM' + df_dianxiaomi_download['SPU（仅用于区分产品）'].astype(str)
    df_dianxiaomi_download['position'] = df_dianxiaomi_download.groupby('SPU（仅用于区分产品）').cumcount() + 1
    df_dianxiaomi_download['sku'] = df_dianxiaomi_download.apply(
        lambda x: x['SPU（仅用于区分产品）'].strip() + "-" + str(x['position']), axis=1)
    # df_dianxiaomi_download['weight_unit'] = 'g'
    df_dianxiaomi_download['group_key'] = df_dianxiaomi_download['SPU（仅用于区分产品）']

    df_product_agg = df_dianxiaomi_download.groupby(['group_key']).apply(lambda df_group: product_agg(df_group)).reset_index(drop=True)

    period_tokens = 0
    # columns = ['master_sku_id','unique_id','product_url','main_brand','sub_brand','title_cn_ori','title_en_ori','cost_price','weight','video_url','developer','creater','creat_time','product_length','product_width','product_height','minimum_order_quantity','product_master_image_url_ori','product_variant_image_urls_ori','product_attached_image_urls_ori','product_description_image_urls_ori','product_description_cn_ori','product_description_en_ori','supplier_name','purchase_days','varients_ori','options_ori']
    columns = list(df_product_agg.columns) + ['variants', 'options', 'product_master_image_url', 'product_image_urls', 'gpt_result_json']
    with open(processed_file_path, 'w') as f:
        f.write('\t'.join(columns))
        f.write('\n')
        for i in range(len(df_product_agg)):
            row = df_product_agg.iloc[i, :]
            image_detect_history={}
            translate_history={}
            variants, image_detect_history, translate_history = variants_process(row.varients_ori, orcReader, translator, image_detect_history, translate_history)
            options, translate_history = options_process(row.options_ori, translator, translate_history)

            product_image_urls = []
            for image_urls in [row.product_master_image_url_ori, row.product_variant_image_urls_ori, row.product_attached_image_urls_ori]:
                if not image_urls:
                    continue
                for image_url in image_urls.split(','):
                    image_detect_info, image_detect_history = orcReader.image_detect(image_url, image_detect_history)
                    if image_detect_info.get('is_contain_chinese') == 'not_contain_chinese' and image_detect_info.get('is_contain_table') == 'not_contain_table':
                        product_image_urls.append(image_url)

            if len(product_image_urls) <= 1:
                continue
            product_master_image_url = product_image_urls[0]

            gpt_result_json, usage_tokens = gpt_generator.openai_generate(row.title_cn_ori, row.product_description_cn_ori, model='gpt-3.5-turbo-0613')
            period_tokens += usage_tokens
            if (i+1) % 3000 == 0 or (period_tokens+1) % 90000 == 0:
                time.sleep(10)

            output = row.astype('str').tolist() + [variants, options, product_master_image_url, ','.join(product_image_urls), gpt_result_json]
            f.write("\t".join(output))
            f.write("\n")
            if (i+1)%100==0:
                print(f"{i+1} products over")
    print(f"total process {i+1} products")



# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/14
# @Author   : fanke.chang
# @File     : utils.py
# @Desc     :

import os
import pandas as pd
import numpy as np
import json
import re
import itertools
import os
import openai
from fuzzywuzzy import process, fuzz
from shopify_producting.conf.config import *


def json_process(json_info):
    json_info = re.sub(r'[\r\n]+', '', json_info)
    dict_info = json.loads(json_info)
    dict_info_copy = {}
    for key, val in dict_info.items():
        dict_info_copy[key.lower()] = val
    return dict_info_copy


def original_title_process(original_title):
    '''
    商品原始名称中有时带特殊符号，在保存文件夹时，文件夹名称会讲特殊符号改成'_'
    '''
    return re.sub(r"[~]", '_', original_title)


def convert_unit_metric_english(string_value):
    '''
    某些属性名包含公制单位，例如"Gold 40cm"、”51cm-60cm“、”51-60cm“,”0.01kg“
    '''
    conversion_rates = {
        'cm': ('inch', 0.3937),
        'kg': ('lb', 2.2046),
        'g': ('lb', 0.0022046),
    }
    if re.search(r'(\d+(\.\d+)?)(inch(es)?|lb)', string_value.lower()):
        return string_value

    # 解决型如51.0cm-60cm、60cm
    def convert_single(match_obj):
        metric_num = float(match_obj.group(1))
        metric_unit = match_obj.group(3).lower()
        conversion_rate = conversion_rates.get(metric_unit)[1]
        english_num = metric_num * conversion_rate
        english_num = int(english_num) if english_num >= 5 else round(english_num, 2)
        english_unit = conversion_rates.get(metric_unit)[0]
        return f'{english_num}{english_unit}'

    # 解决型如'51.0-60cm'
    def convert_multi(match_obj):
        metric_num1 = float(match_obj.group(1))
        metric_num2 = float(match_obj.group(3))
        metric_unit = match_obj.group(5).lower()
        conversion_rate = conversion_rates.get(metric_unit)[1]
        english_num1 = metric_num1 * conversion_rate
        english_num1 = int(english_num1) if english_num1 >= 5 else round(english_num1, 2)
        english_num2 = metric_num2 * conversion_rate
        english_num2 = int(english_num2) if english_num2 >= 5 else round(english_num2, 2)
        english_unit = conversion_rates.get(metric_unit)[0]
        return f'{english_num1}-{english_num2}{english_unit}'

    pattern = re.compile(r'(\d+(\.\d+)?)-(\d+(\.\d+)?)(cm|kg|g)', re.I)
    string_value = re.sub(pattern, convert_multi, string_value)

    pattern = re.compile(r'(\d+(\.\d+)?)(cm|kg|g)', re.I)
    string_value = re.sub(pattern, convert_single, string_value)

    return string_value


def extract_number_and_unit(number_str):
    '''
    价格、重量的内容是5元、5kg，需要分别提取数字和字符部分
    '''
    if not number_str:
        return ('-1', '')
    pattern = r"([$\￥]?)(\d+(\.\d+)?)([a-zA-Z元$￥]*)"
    match = re.search(pattern, number_str)
    if match:
        prefix = match.group(1)
        number = match.group(2)
        unit = match.group(4)
    if unit:
        return (number, unit.lower())
    elif prefix:
        # 例如$5/￥5
        return (number, prefix.lower())
    else:
        return (number, '')


# # 每个sku做笛卡尔积
# def sku_info_cartesian(sku_details):
#     # sku_details = re.sub(r'[\r\n]+', '', sku_details)
#     # sku_details_dict = json.loads(sku_details)
#     sku_details_dict = sku_details
#     sku_info_list = []
#     for i, (attribute_category, attribute_dict) in enumerate(sku_details_dict.items()):
#         category_info_list = []
#         for attribute_name, price_info in attribute_dict.items():
#             attribute_name = convert_unit_metric_english(attribute_name)
#             price, unit = extract_number_and_unit(price_info)
#             category_info_list.append((attribute_category, attribute_name, float(price)))
#         sku_info_list.append(category_info_list)
#     sku_info_combine = itertools.product(*sku_info_list)
#     sku_info_combine_complete = []
#     for sku_info_single in sku_info_combine:
#         while len(sku_info_single) < 3:
#             sku_info_single = sku_info_single + (('', '', -1),)
#         sku_info_combine_complete.append(sku_info_single)
#     return sku_info_combine_complete


# def extract_attribute_field(sku_cartesian):
#     (attribute_name_1, attribute_value_1, attribute_price_1), (
#     attribute_name_2, attribute_value_2, attribute_price_2), (
#     attribute_name_3, attribute_value_3, attribute_price_3) = sku_cartesian
#     max_price = max([attribute_price_1, attribute_price_2, attribute_price_3])
#     return [attribute_name_1, attribute_value_1, attribute_name_2, attribute_value_2, attribute_name_3,
#             attribute_value_3, max_price]


def body_html_process(gpt_result_dict, max_listing=5):
    '''
    商品描述部分
    '''
    display_attributes = ['material', 'craftsmanship', 'style', 'size', 'fashion_element', 'gender']
    line_list = []
    listing_cnt = 0
    description = gpt_result_dict.get('product_description')
    line = f"""<p><meta charset=""utf-8""><span style="font-size: 15px; font-style: italic;">{description}</span></p>"""
    line_list.append(line)
    for attribute_name in display_attributes:
        attribute_value = gpt_result_dict.get(attribute_name)
        if listing_cnt > max_listing:
            break
        if not attribute_value:
            continue
        if isinstance(attribute_value, list):
            attribute_value = ', '.join(attribute_value)
        attribute_value = convert_unit_metric_english(attribute_value)
        attribute_emoji = emoji_code.get(attribute_name, '')
        attribute_name = ' '.join(attribute_name.split('_')).upper()
        line = f"""<p><meta charset="utf-8"><span data-mce-fragment=""1"">{attribute_emoji} <strong>{attribute_name}:</strong> {attribute_value} </span></p>"""
        line_list.append(line)
        listing_cnt += 1
        # 加上Free Shipping
    attribute_emoji = emoji_code.get('free_shipping')
    attribute_name = 'Free Shipping'
    line = f"""<p><meta charset="utf-8"><span data-mce-fragment=""1"">{attribute_emoji} <strong><em>{attribute_name}</em></strong></span></p>"""
    line_list.append(line)

    return '\n'.join(line_list)


# def title_url_format(title, product_url):
#     '''
#     url中包含商品title信息，但是title中有特殊字符，需要去除
#     '''
#     title = re.sub(r'[^a-z0-9\-_.]', '', title.lower().replace(' ', '-'))
#     url_hash = int(hashlib.md5(product_url.encode()).hexdigest(), 16) % (10 ** 6)
#     return f"{title}-{url_hash}"


# def get_image_urls(directory_path, brief_title, product_url, exist_image_keys, qiniu_auth):
#     upload_image_names = []
#     image_extensions = ('.jpg', '.jpeg', '.png')
#     domain = "http://rzuix5mfd.bkt.clouddn.com/"
#     bucket_name = 'sanchaliushui'
#     storage_dir = '1688'
#     # image的url种带入商品链接的hash值，防止重名
#     url_hash = int(hashlib.md5(product_url.encode()).hexdigest(), 16) % (10 ** 6)
#     with os.scandir(directory_path) as entries:
#         for entry in entries:
#             if entry.is_file and entry.name.endswith(image_extensions):
#                 upload_image_names.append(entry.name)
#     upload_image_names = sorted(upload_image_names, reverse=False)
#     upload_cnt = len(upload_image_names)
#     image_urls = []
#     for i, name in enumerate(upload_image_names, 1):
#         image_local_path = os.path.join(directory_path, name)
#         brief_title = title_url_format(brief_title, product_url)
#         suffix = name.split('.')[-1]
#         image_upload_key = f"{storage_dir}/{brief_title}-{url_hash}-{upload_cnt}-{i}.{suffix}"
#         url = f"{domain}{image_upload_key}"
#         if image_upload_key in exist_image_keys:
#             image_urls.append(url)
#             continue
#         token = qiniu_auth.upload_token(bucket_name, image_upload_key, 36000000)
#         ret, info = put_file(token, image_upload_key, image_local_path, version='v2', keep_last_modified=True)
#         assert info.status_code == 200
#         image_urls.append(url)
#     return image_urls


# def align_array(images_urls, sku_cartesian):
#     '''
#     images_urls和sku_cartesian的数组长度不一样，先使长度一致，然后在explode展开
#     '''
#     max_len = max(len(images_urls), len(sku_cartesian))
#     images_urls += [''] * (max_len - len(images_urls))
#     sku_cartesian += [(('', '', -1), ('', '', -1), ('', '', -1))] * (max_len - len(sku_cartesian))
#     # sku_cartesian += [sku_cartesian[0]] * (max_len-len(sku_cartesian))
#     return [images_urls, sku_cartesian]

def price_strategy(cost_price, lowest_cost_price):
    if isinstance(cost_price, str):
        cost_price = float(cost_price)

    if cost_price <= 20:
        sell_price = 20
    else:
        sell_price = cost_price
    compare_price = sell_price
    return sell_price, compare_price

# def build_prompt(title, body_text, variants):
#     prompt = f"""请根据商品名称和描述信息，总结出商品的标题和商品listing，内容如下：
#     title:{title}
#     body_text:{body_text}
#     以Json格式输出
#     """
#     return prompt

# def image_detect_chinese(orcReader, image_src, image_detect_history):
#     """
#     OCR检测图片是否含有中文，image_detect_history的格式为{image_src1: 'contain_chinese', image_src2: 'not_contain_chinese'}
#     """
#     # response = requests.get(image_src)
#     # img = Image.open(BytesIO(response.content))
#     if image_src in image_detect_history:
#         return image_detect_history.get(image_src), image_detect_history
#     # img_text_list = orcReader.readtext(image_src, detail=0, rotation_info=[90, 180, 270])
#     img_text_list = []
#     if re.search('[\u4e00-\u9fa5]', ' '.join(img_text_list)):
#         image_detect_history[image_src] = 'contain_chinese'
#     else:
#         image_detect_history[image_src] = 'not_contain_chinese'
#
#     return image_detect_history.get(image_src), image_detect_history

def text_translate(translator, text, translate_history):
    if not text:
        return None, translate_history
    if text in translate_history:
        return translate_history.get(text), translate_history
    text_translate = translator.translate(text, src='auto', dest='en').text.title()
    translate_history[text] = text_translate

    return translate_history.get(text), translate_history

def variants_process(variants, orcReader, translator, image_detect_history, translate_history):
    try:
        variants = json.loads(variants)
    except:
        pass
    translate_variants = []
    for variant in variants:
        price_list = []
        price = variant.get('price')
        if isinstance(price, str):
            cost_price, unit = extract_number_and_unit(price)
        price_list.append(float(cost_price))
        lowest_cost_price = min(price_list)

    for variant in variants:
        # title = variant.get('title')
        sku = variant.get('sku')
        price = variant.get('price')
        position = variant.get('position')
        compare_at_price = variant.get('compare_at_price')
        option1 = variant.get('option1')
        option2 = variant.get('option2')
        option3 = variant.get('option3')
        grams = variant.get('grams')
        weight = variant.get('weight')
        weight_unit = variant.get('weight_unit')
        image_src = variant.get('image_src')

        if isinstance(price, str):
            cost_price, unit = extract_number_and_unit(price)
        sell_price, compare_price = price_strategy(cost_price, lowest_cost_price)

        # title_translate, translate_history = text_translate(translator, title, translate_history)
        option1_translate, translate_history = text_translate(translator, option1, translate_history)
        option2_translate, translate_history = text_translate(translator, option2, translate_history)
        option3_translate, translate_history = text_translate(translator, option3, translate_history)

        image_detect_info, image_detect_history = orcReader(image_src, image_detect_history)

        if image_detect_info.get('is_contain_chinese') == 'contain_chinese' or image_detect_info.get('is_contain_table') == 'contain_table':
            image_src = None

        translate_variant = {
                                # 'title': f"{option1_translate}/{option2_translate}/{option3_translate}",
                                'sku': sku,
                                'price': str(sell_price),
                                'position': position,
                                'compare_at_price': str(compare_price),
                                'option1': option1_translate,
                                'option2': option2_translate,
                                'option3': option3_translate,
                                'grams': grams,
                                'weight': weight,
                                'weight_unit': weight_unit,
                                'image_src': image_src,
                                'taxable': True,
                                'requires_shipping': True
                            }
        translate_variants.append(translate_variant)

    return json.dumps(translate_variants, ensure_ascii=False), image_detect_history, translate_history


def options_process(options, translator, translate_history):
    try:
        options = json.loads(options)
    except:
        pass
    translate_options = []
    for option in options:
        id = option.get('id')
        name = option.get('name')
        position = option.get('position')
        values = option.get('values')

        name_translate, translate_history = text_translate(translator, name, translate_history)
        translate_values = []
        for value in values:
            value_translate, translate_history = text_translate(translator, value, translate_history)
            translate_values.append(value_translate)

        translate_option = {
            'id': id,
            'name': name,
            'position': position,
            'values': translate_values
        }
        translate_options.append(translate_option)
    return json.dumps(translate_options, ensure_ascii=False), translate_history


class TrieNode():
    """
    google类目搜索树
    """
    def __init__(self):
        self.nodes = {}
        self.leaf = None

    def insert(self, words: list, target: int):
        curr = self
        for element in words:
            if element not in curr.nodes:
                curr.nodes[element] = TrieNode()
            curr = curr.nodes[element]
        curr.leaf = target

    def search(self, words: list):
        category_levels = []
        curr = self
        for element in words:
            best_match, best_score = process.extractOne(element, curr.nodes.keys())
            if best_score <= 80:
                return category_levels, curr.leaf
            # if element not in curr.nodes:
            #     return None
            curr = curr.nodes[best_match]
            category_levels.append(best_match)
        return category_levels, curr.leaf

def build_category_tree(df_category):
    treeNode = TrieNode()
    for i in range(len(df_category)):
        row = df_category.iloc[i, :]
        category_id = row.category_id
        category_levels = [category for category in row.tolist()[1:] if category]
        treeNode.insert(category_levels, category_id)
    return treeNode

# names = ['category_id'] + [f'category_{i}' for i in range(1, 8, 1)]
# df_category = pd.read_excel(google_category_file_en, names=names).fillna('')
# res = []
# for i in range(len(df_category)):
#     row = df_category.iloc[i, :]
#     category_id = row.category_id
#     category_levels = [category for category in row.tolist()[1:] if category]
#     res.append(category_levels[-1])
#
#
# google_category_treeNode = build_category_tree(df_category)
# # google_category_treeNode.search('Jewelry & Watches > Necklaces'.split(' > '))
# # google_category_treeNode.search(['Apparel & Accessories','Jewelry','Watch Accessories'])
# google_category_treeNode.search('Apparel & Accessories > Clothing > Sweaters & Knits'.split(' > '))
# print('OK')







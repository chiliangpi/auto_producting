# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/14
# @Author   : fanke.chang
# @File     : translate_product.py
# @Desc     :

import pandas as pd
import os
import json
from urllib import parse
from utils import *

from googletrans import Translator
import easyocr
from PIL import Image
from io import BytesIO
import requests

df = pd.read_csv(os.path.join("/Users/fanke.chang/shop/product_info/original_product_info", "test.txt"), sep='\t', dtype=str).fillna('')


from googletrans import Translator

translator = Translator()
orcReader = easyocr.Reader(['en', 'ch_sim'])
orcReader = easyocr.Reader(['en', 'ch_sim'])

text_to_translate = '29.53 英寸'
translated_text = translator.translate(text_to_translate, src='auto', dest='en').text

image_detect_history = {}
translate_history = {}

def variants_process(variants, image_detect_history, translate_history):
    try:
        variants = json.loads(variants)
    except:
        pass
    translate_variants = []
    for variant in variants:
        price_list = []
        price = variant.get('price')
        if isinstance(price, str):
            purchase_price, _ = extract_number_and_unit(price)
        price_list.append(float(purchase_price))
        lowest_purchase_price = min(price_list)

    for variant in variants:
        title = variant.get('title')
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
            purchase_price = extract_number_and_unit(price)
        sell_price, compare_price = price_strategy(purchase_price, lowest_purchase_price)

        title_translate, translate_history = text_translate(translator, title, translate_history)
        option1_translate, translate_history = text_translate(translator, option1, translate_history)
        option2_translate, translate_history = text_translate(translator, option2, translate_history)
        option3_translate, translate_history = text_translate(translator, option3, translate_history)

        image_chinese_info, image_detect_history = image_detect_chinese(orcReader, image_src, image_detect_history)
        if image_chinese_info == 'contain_chinese':
            image_src = None

        translate_variant = {
                                'title': title_translate,
                                'price': sell_price,
                                'position': position,
                                'compare_at_price': compare_price,
                                'option1': option1_translate,
                                'option2': option2_translate,
                                'option3': option3_translate,
                                'grams': grams,
                                'weight': weight,
                                'weight_unit': weight_unit,
                                'image_src': image_src
                            }
        translate_variants.append(translate_variant)

    return json.dumps(translate_variants), image_detect_history, translate_history


def options_process(options, translate_history):
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
    return json.dumps(translate_options), translate_history










prompt = build_prompt(title, body_text, variants)









print(translated_text)
# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/25
# @Author   : fanke.chang
# @File     : models_utils.py
# @Desc     :

import os
import cv2
from paddleocr import PPStructure,save_structure_res,draw_structure_result
import re
from bs4 import BeautifulSoup
import openai
from shopify_producting.conf.config import *
import json
from shopify_producting.utils import *
from shopify_producting.logging_config import logger

class ImageStructureOCR():
    def __init__(self, det_model_dir=None, rec_model_dir=None, table_model_dir=None, layout_model_dir=None):
        self.det_model_dir = "/home/aistudio/work/paddleocr_model/det/ch/ch_PP-OCRv4_det_infer"
        self.rec_model_dir = "/home/aistudio/work/paddleocr_model/rec/ch/ch_PP-OCRv4_rec_infer"
        self.table_model_dir = "/home/aistudio/work/paddleocr_model/table/ch_ppstructure_mobile_v2.0_SLANet_infer"
        self.layout_model_dir = "/home/aistudio/work/paddleocr_model/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer"
        self.table_engine = PPStructure(layout=True, table=True, ocr=True, show_log=True, det_model_dir=self.det_model_dir,
                                   rec_model_dir=self.rec_model_dir, table_model_dir=self.table_model_dir,
                                   layout_model_dir=self.layout_model_dir)

    # def predict(self, image_src, image_detect_history):
    #     if image_src in image_detect_history:
    #         predict_result = image_detect_history.get(image_src).get('predict_result')
    #         return predict_result, image_detect_history
    #     predict_result = self.table_engine(image_src)
    #     image_detect_history[image_src] = {'predict_result': [], 'is_contain_chinese': '', 'is_contain_table': ''}
    #     return predict_result, image_detect_history

    # image_detect_history = {'image_src': {'predict_result': [], 'is_contain_chinese':'', 'is_contain_table':''}}
    def image_detect(self, image_src, image_detect_history):
        if image_src in image_detect_history:
            detect_info = image_detect_history.get(image_src)
            return detect_info, image_detect_history
        image_array = read_image_from_url(image_src)
        if not np.any(image_array):
            detect_info = {'predict_result': '',
                           'is_contain_chinese': 'not open',
                           'is_contain_table': 'not open'
                           }
            image_detect_history[image_src] = detect_info
            return detect_info, image_detect_history

        orc_result = self.table_engine(image_array)
        is_contain_chinese = ''
        is_contain_table = ''
        for res_dict in orc_result:
            bbox_type = res_dict.get('type')
            if bbox_type != 'table':
                res_list = res_dict.get('res')
                for res in res_list:
                    text = res.get('text')
                    confidence = res.get('confidence')
                    text_region = res.get('text_region')
                    if not not text and re.search('[\u4e00-\u9fa5]', text):
                        is_contain_chinese = 'contain_chinese'

            elif bbox_type == 'table':
                is_contain_table = 'contain_table'
                res = res_dict.get('res')
                table_html = res.get('html')
                soup = BeautifulSoup(table_html, "html.parser")
                table_text = soup.get_text(separator="\n")
                if not not table_text and re.search('[\u4e00-\u9fa5]', table_text):
                    is_contain_chinese = 'contain_chinese'

            if is_contain_chinese == 'contain_chinese' and is_contain_table == 'contain_table':
                break

        is_contain_chinese = 'contain_chinese' if is_contain_chinese else 'not_contain_chinese'
        is_contain_table = 'contain_table' if is_contain_table else 'not_contain_table'
        detect_info = {'predict_result': orc_result,
                       'is_contain_chinese': is_contain_chinese,
                       'is_contain_table': is_contain_table
                       }
        image_detect_history[image_src] = detect_info
        return detect_info, image_detect_history

class GPTGenerator():
    def __init__(self):

        self.system_role = """\
        #Role
        E-commerce Operations Specialist
        #Goals
        Extract key product information based on provided product titles and various product details
        #Language
        --English
        #Workflows
        --product_description: Concise and highlighting product features, with a word limit of 50 words
        --brief_title: Summarize a brief and personalized product title within 10 words
        --seo_title: With a word limit of 30 words
        --google_category: Infer the Google product category
        --shopify_category: Infer the Shopify product category
        --type: Infer the product type
        --tags: Infer product tags (up to 5) in descending order of priority, separated by commas
        --gender: Determine the gender of the target audience (choose from male, female, unisex)
        --age_group: Determine the age group of the target audience (choose from child, adult)
        --adword_groups: Infer up to 3 adword groups
        --adword_labels: Infer up to 5 adword labels
        --material
        --craftsmanship
        --fashion_element
        --style
        --size
        #Constraints
        --The extracted information must not contain keywords related to cross-border, dropshipping, wholesale, made in China or the year 2022
        --Google and Shopify product categories should be complete, hierarchical categories
        --If an attribute value is not found, use an empty string ('')
        --If an attribute has multiple values seperated by commas
        #Output
        --Output a JSON result only; no intermediate information is required
        """
        self.openai = openai
        self.openai.api_key = OPENAI_API_KEY

    def openai_generate(self, title, description, model):
        assert model in ['gpt-3.5-turbo', 'gpt-3.5-turbo-0613', 'gpt-4']
        self.user_content = f"title: {title}\ndescription: {description}\nplease output the JSON only"
        # completion = openai.ChatCompletion.create(
        #     model=f"{model}",
        #     messages=[
        #         {"role": "system", "content": f"{self.system_role}"},
        #         {"role": "user", "content": f"{self.user_content}"}
        #     ]
        # )
        # try:
        #     assistant_response = completion.choices[0].message.content
        #     json_result = json.dumps(json.loads(assistant_response), ensure_ascii=False)
        #     usage_tokens = completion.usage.total_tokens
        # except:
        #     json_result = ''
        #     usage_tokens = 0

        json_result = '{"product_description": "Simple and stylish jewelry with a heart-shaped design and zircon inlays. Made of copper. Suitable for any occasion.", "brief_title": "Fashionable Heart-shaped Necklace", "seo_title": "Trendy Heart-shaped Necklace with Zircon Inlays", "google_category": "Jewelry & Watches > Necklaces", "shopify_category": "Jewelry > Necklaces", "type": "", "tags": "necklace, jewelry, heart-shaped, zircon, trendy", "gender": "female", "age_group": "adult", "adword_groups": "jewelry, fashion accessories, gifts", "adword_labels": "heart-shaped, zircon, trendy", "material": "Copper", "craftsmanship": "Zircon Inlays", "fashion_element": "Heart-shaped", "style": "Ins Style", "size": ""}'
        usage_tokens = 0

        return json_result, usage_tokens

    def chatglm_generate(self, title, description, model):
        prompt = f"{self.system_role}\ntitle: {title}\ndescription: {description}\nplease output the JSON only"
        assert model == 'chatglm'
        pass





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
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, '..')))
sys.path.insert(1, "/home/aistudio/external-libraries")

import pandas as pd
import json
import re
import time
import subprocess
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
    created_at = row.creat_time
    tags = gpt_result_dict.get('tags').split(', ')
    options = json.loads(row.options)
    variants = json.loads(row.variants)
    # images = [{'position': position, 'src': src} for position, src in enumerate(row.product_image_urls.split(','), 1)]
    product_image_urls = row.product_image_urls.split(',')


    # options_shopify = []
    # options = json.loads(row.options)
    # for option in options:
    #     name = option.get('name')
    #     values = option.get('values')
    #     # position = option.get('position')
    #     # option_shopify = shopify.Options.create({'product_id': product_id})
    #     options_shopify.append({'name': name, 'values': values})
    #     break

    product_info = {
        "title": title,
        "body_html": body_html,
        "vendor": vendor,
        "product_type": product_type,
        "published_scope": "global",
        "tags": tags,
        "status": 'active',
        "published": True,
        "variants": variants,
        "options": options,
        # "images": images,
    }
    product_info_json = json.dumps({'product': product_info}, ensure_ascii=False)

    # curl_command_template = """curl -d '{"product":{"title":"Burton Custom Freestyle 151","body_html":"<strong>Good snowboard!</strong>","vendor":"Burton","product_type":"Snowboard","variants":[{"option1":"Blue","option2":"155"},{"option1":"Black","option2":"159"}],"options":[{"name":"Color","values":["Blue","Black"]},{"name":"Size","values":["155","159"]}]}}' \
    # -X POST 'https://075bc9-3.myshopify.com/admin/api/2022-10/products.json' \
    # -H 'X-Shopify-Access-Token: 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' \
    # -H 'Content-Type: application/json'"""

    curl_command = """curl -d '%s' \
        -X POST 'https://%s/admin/api/2022-10/products.json' \
        -H 'X-Shopify-Access-Token: %s' \
        -H 'Content-Type: application/json'""" % (product_info_json, SHOPIFY_SHOP_URL, SHOPIFY_PASSWORD)

    result = subprocess.run(curl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        break
    product_info_dict = json.loads(result.stdout).get('product')
    product_id = product_info_dict.get('id')

    new_product = shopify.Product.find(id_=product_id)

    #获取每张图片原始url和shopify图片url的映射关系imageURL2imageID
    shopify_images = []
    imageURL2imageID = {}
    for image_url in product_image_urls:
        image = shopify.Image.create({'product_id': product_id, 'src': image_url})
        image_url_shopify = image.src
        image_id_shopify = image.id
        image_info_shopify = {'image_id_shopify': image_id_shopify, 'image_url_shopify': image_url_shopify}
        imageURL2imageID[image_url] = image_info_shopify
        shopify_images.append(image)
    #获取shopify的image_id和variant_id的映射关系imageID2variantID，并为每个Image添加variants属性
    imageID2variantID = {}
    shopify_variants = new_product.variants
    for variant, shopify_variant in zip(variants, shopify_variants):
        sku = variant.get('sku')
        image_url = variant.get('image_src')
        image_id = imageURL2imageID.get(image_url).get('image_id_shopify')
        variant_id = shopify_variant.id
        shopify_variant._update({'image_id': image_id})
        if image_id not in imageID2variantID:
            imageID2variantID[image_id] = {'skus': [sku], 'variant_ids': [variant_id]}
        else:
            imageID2variantID['image_id']['skus'].append(sku)
            imageID2variantID['image_id']['variant_ids'].append(variant_id)

    for shopify_image in shopify_images:
        image_id = shopify_image.id
        try:
            image_variant_id = imageID2variantID[image_id]['variant_ids']
        except:
            image_variant_id = None
        shopify_image._update({'variant_ids': image_variant_id})

    new_product.images = shopify_images
    new_product.variants = shopify_variants

    new_product.save()

    print(f"row={i}, product={new_product.to_dict()}")











    # new_product = shopify.Product.create(product_info)
    # product_id = new_product.id
    #
    # # new_product.options
    # # option_value_data = {
    # #     "option_id": 11067051147586,
    # #     "value": "高",  # 包含非 ASCII 字符的选项值
    # # }
    #
    #
    # shopify_images = []
    # imageURL2imageID = {}
    # for image_url in row.product_image_urls.split(','):
    #     image = shopify.Image.create({'product_id': product_id, 'src': image_url})
    #     image_url_shopify = image.src
    #     image_id_shopify = image.id
    #     image_info_shopify = {'image_id_shopify': image_id_shopify, 'image_url_shopify': image_url_shopify}
    #     imageURL2imageID[image_url] = image_info_shopify
    #     shopify_images.append(image)
    #
    # variants = json.loads(row.variants)
    # variants_shopify = []
    # for variant in variants:
    #     image_src = variant['image_src']
    #     variant['image_id'] = imageURL2imageID.get(image_src).get('image_id_shopify')
    #     variant['product_id'] = product_id
    #     variant_shopify = shopify.Variant.create(variant)
    #     variants_shopify.append(variant_shopify)
    #
    # new_product.images = shopify_images
    # new_product.variants = variants_shopify
    #
    # # option_shopify = shopify.Option.create({'product_id': product_id, 'name': name})
    # option_shopify = shopify.Option.create({'product_id': product_id, 'name': 'abc', 'values': ['a','b'],'position':3})
    # option_shopify = shopify.Option.create(
    #     {'name': 'abc', 'values': ['a', 'b'], 'position': 2})
    #
    # # options_shopify = []
    # # options = json.loads(row.options)
    # # for option in options:
    # #     name = option.get('name')
    # #     values = option.get('values')
    # #     # position = option.get('position')
    # #     option_shopify = shopify.Options.create({'product_id': product_id, 'name': name, 'values': values})
    # #     options_shopify.append(option_shopify)
    # # new_product.options = options_shopify
    #
    # new_product.save()




    # variants = json.loads(row.variants)
    # images = [{'position': position, 'src': src} for position, src in enumerate(row.product_image_urls.split(','), 1)]
    #
    # #
    # new_variants = []
    # for variant in variants:
    #     variant['image'] = {'src': variant['image_src']}
    #     # variant['image'] = variant['image_src']
    #     del variant['image_src']
    #     new_variants.append(variant)
    #
    #
    # product_info = {
    #                     "title": title,
    #                     "body_html": body_html,
    #                     "vendor": vendor,
    #                     "product_type": product_type,
    #                     "created_at": created_at,
    #                     "updated_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
    #                     "published_scope": "global",
    #                     "tags": tags,
    #                     "status": 'active',
    #                     "published": True,
    #                     "variants": new_variants,
    #                     "options": options,
    #                     "images": images,
    #                 }
    # new_product = shopify.Product.create(product_info)
    #
    # image_infos = new_product.images
    # image_info_dict = {}
    # for image_info in image_infos:
    #     image_id = image_info.id
    #     image_src = image_info.src
    #     image_info_dict[image_src] = image_id
    #
    # variants = json.loads(row.variants)
    # for variant in variants:
    #     variant['image_id'] = image_info_dict.get(variant['image_src'])
    # new_variants = shopify.Variant.create(variants)
    # new_product.variants.update(new_variants)
    #
    # shopify.Variant





#     print(f"product_title={new_product.title} upload succeed")
#
# print(f"total upload {i+1} products")


# products = shopify.Product.find()
# products = shopify.Product.find(limit=5)
# product = products[0]
# json.dumps

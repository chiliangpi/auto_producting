import os
import openai
import json
import pandas as pd
import re
from bs4 import BeautifulSoup
import collections
from datetime import datetime, timezone





import shopify
#shopify账号
SHOP_URL = '34460e.myshopify.com'
API_KEY = '093a3e097bc79f63fe13c683022bc5e2'
PASSWORD = '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'
shopify.ShopifyResource.set_site(f"https://{API_KEY}:{PASSWORD}@{SHOP_URL}/admin")

# #七牛云账号
# from qiniu import Auth, put_file, etag, BucketManager
# import qiniu.config
# access_key = 'XzkCvQGvOaJjSRplhsT_8w1jo2KTmh8JscS_DPrm'
# secret_key = 'BOQtOJeSCbNRV9gtbKS3l0FLCy3M9DI_oKUujyHn'
# bucket_name = 'sanchaliushui'
# qiniu_auth = Auth(access_key, secret_key)
# bucket = BucketManager(qiniu_auth)


products = shopify.Product.find()
product = products

with open(os.path.join("/Users/fanke.chang/shop/product_info/original_product_info", "test.txt"), 'w') as f:
    columns = ['product_id', 'title', 'body_text', 'product_type', 'created_at', 'updated_at', 'variants', 'images', 'options']
    f.write('\t'.join(columns))
    f.write('\n')
    for product in products:
        shopName = 'my_store'
        product_id = f'{shopName}-{product.id}'
        title = product.title

        body_html = product.body_html
        soup = BeautifulSoup(body_html, 'lxml')
        body_text = soup.get_text(strip=True)

        product_type = product.product_type
        created_at = product.created_at
        dt = datetime.fromisoformat(created_at)
        created_at = dt.strftime('%Y-%m-%d %H:%M:%S')
        updated_at = product.updated_at
        dt = datetime.fromisoformat(updated_at)
        updated_at = dt.strftime('%Y-%m-%d %H:%M:%S')

        ori_images = product.images
        new_images_orderDict = collections.OrderedDict()
        for ori_image in ori_images:
            image_dict = {}
            image_dict['id'] = ori_image.id
            image_dict['position'] = ori_image.position
            image_dict['width'] = ori_image.width
            image_dict['height'] = ori_image.height
            image_dict['src'] = ori_image.src
            new_images_orderDict[ori_image.id] = image_dict

        ori_variants = product.variants
        new_variants = []
        for ori_variant in ori_variants:
            new_variant = {}
            new_variant['title'] = ori_variant.title
            new_variant['price'] = ori_variant.price
            new_variant['position'] = ori_variant.position
            new_variant['compare_at_price'] = ori_variant.compare_at_price
            new_variant['option1'] = ori_variant.option1
            new_variant['option2'] = ori_variant.option2
            new_variant['option3'] = ori_variant.option3
            new_variant['grams'] = ori_variant.grams
            new_variant['weight'] = ori_variant.weight
            new_variant['weight_unit'] = ori_variant.weight_unit
            new_variant['image_src'] = new_images_orderDict.get(ori_variant.image_id, {}).get('src')
            new_variants.append(new_variant)

        new_images = list(new_images_orderDict.values())

        ori_master_image = product.image
        new_master_image = {}
        new_master_image['id'] = ori_master_image.id
        new_master_image['position'] = ori_master_image.position
        new_master_image['width'] = ori_master_image.width
        new_master_image['height'] = ori_master_image.height
        new_master_image['src'] = ori_master_image.src

        ori_options = product.options
        new_options = []
        for ori_option in ori_options:
            new_option = {}
            new_option['id'] = ori_option.id
            new_option['name'] = ori_option.name
            new_option['position'] = ori_option.position
            new_option['values'] = ori_option.values
            new_options.append(new_option)

        row = '\t'.join([product_id, title, body_text, product_type, created_at, updated_at, json.dumps(new_variants, ensure_ascii=False),
                         json.dumps(new_images, ensure_ascii=False), json.dumps(new_options, ensure_ascii=False)])
        f.write(row)
        f.write('\n')



print("OK")
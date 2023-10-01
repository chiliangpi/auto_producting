# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/30
# @Author   : fanke.chang
# @File     : url_request.py
# @Desc     :

import subprocess

class customerShopify():
    def __init__(self, shop_url, shop_key, access_token):
        self.shop_url = shop_url
        self.shop_key = shop_key
        self.access_token = access_token

    def create_product(self, product_info):
        curl_command = f"""curl -d {product_info} \
                        -X POST 'https://{self.shop_url}/admin/api/2022-10/products.json' \
                        -H 'X-Shopify-Access-Token: {self.access_token}' \
                        -H 'Content-Type: application/json'"""
        result = subprocess.run(curl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)



class


    SHOPIFY_SHOP_URL = '075bc9-3.myshopify.com'
    SHOPIFY_API_KEY = '6467a608a6a31ace2df1921a8d778dca'
    # SHOPIFY_API_KEY = 'c25349fc85d3751d77da6703c7c19c89'
    SHOPIFY_PASSWORD = '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'

    OPENAI_API_KEY = "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"
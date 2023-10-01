# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/15
# @Author   : fanke.chang
# @File     : test.py
# @Desc     :

import json

import shopify

shopify.Product
from shopify_producting import customerShopify

product_info = json.dumps({'a':'1'})

product = customerShopify.Product()

product.create(product_info)

print('tttt')

# customerShopify.Product.create(product_info)
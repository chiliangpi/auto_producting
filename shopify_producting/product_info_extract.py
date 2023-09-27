import os
import pandas as pd
import numpy as np
import json
import re
import itertools
from qiniu import Auth, put_file, etag, BucketManager
import qiniu.config
import hashlib
#七牛云账号
access_key = 'XzkCvQGvOaJjSRplhsT_8w1jo2KTmh8JscS_DPrm'
secret_key = 'BOQtOJeSCbNRV9gtbKS3l0FLCy3M9DI_oKUujyHn'
bucket_name = 'sanchaliushui'
qiniu_auth = Auth(access_key, secret_key)
bucket = BucketManager(qiniu_auth)


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

    #解决型如51.0cm-60cm、60cm
    def convert_single(match_obj):
        metric_num = float(match_obj.group(1))
        metric_unit = match_obj.group(3).lower()
        conversion_rate = conversion_rates.get(metric_unit)[1]
        english_num = metric_num*conversion_rate
        english_num = int(english_num) if english_num>=5 else round(english_num, 2)
        english_unit = conversion_rates.get(metric_unit)[0]
        return f'{english_num}{english_unit}'
    
    #解决型如'51.0-60cm'
    def convert_multi(match_obj):
        metric_num1 = float(match_obj.group(1))
        metric_num2 = float(match_obj.group(3))
        metric_unit = match_obj.group(5).lower()
        conversion_rate = conversion_rates.get(metric_unit)[1]
        english_num1 = metric_num1*conversion_rate
        english_num1 = int(english_num1) if english_num1>=5 else round(english_num1, 2)
        english_num2 = metric_num2*conversion_rate
        english_num2 = int(english_num2) if english_num2>=5 else round(english_num2, 2)
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
        #例如$5/￥5
        return (number, prefix.lower())
    else:
        return (number, '')

#每个sku做笛卡尔积
def sku_info_cartesian(sku_details):
    # sku_details = re.sub(r'[\r\n]+', '', sku_details)
    # sku_details_dict = json.loads(sku_details)
    sku_details_dict = sku_details
    sku_info_list = []
    for i, (attribute_category, attribute_dict) in enumerate(sku_details_dict.items()):
        category_info_list = []
        for attribute_name, price_info in attribute_dict.items():
            attribute_name = convert_unit_metric_english(attribute_name)
            price, unit = extract_number_and_unit(price_info)
            category_info_list.append((attribute_category, attribute_name, float(price)))
        sku_info_list.append(category_info_list)
    sku_info_combine = itertools.product(*sku_info_list)
    sku_info_combine_complete = []
    for sku_info_single in sku_info_combine:
        while len(sku_info_single) < 3:
            sku_info_single = sku_info_single + (('', '', -1),)
        sku_info_combine_complete.append(sku_info_single)
    return sku_info_combine_complete


def extract_attribute_field(sku_cartesian):
    (attribute_name_1,attribute_value_1,attribute_price_1), (attribute_name_2,attribute_value_2,attribute_price_2), (attribute_name_3,attribute_value_3,attribute_price_3) = sku_cartesian
    max_price = max([attribute_price_1, attribute_price_2, attribute_price_3])
    return [attribute_name_1,attribute_value_1, attribute_name_2,attribute_value_2, attribute_name_3,attribute_value_3, max_price]

def body_info(main_attributes, description):
    '''
    商品描述部分
    '''
    display_attributes = ['material', 'craftsmanship', 'style', 'size']
    emoji_code = {'material': '&#x1F48E;',
                'craftsmanship': '&#x1F6E0;',
                'fashion_element': '&#x1F4A5;',
                'style': '&#x1F3B5;',
                'size': '&#x1F50D;',
                'free_shipping': '&#x1F69A;',
                }
    line_list = []
    line = f"""<p><meta charset=""utf-8""><span style="font-size: 15px; font-style: italic;">{description}</span></p>"""
    line_list.append(line)
    for attribute_name, attribute_value in main_attributes.items():
        if attribute_value and attribute_name.lower() in display_attributes:
            if isinstance(attribute_value, list):
                attribute_value = ', '.join(attribute_value)
            attribute_value = convert_unit_metric_english(attribute_value)
            attribute_emoji = emoji_code.get(attribute_name)
            attribute_name = ' '.join(attribute_name.split('_')).upper()
            # line = f"""<p><meta charset="utf-8"><span data-mce-fragment=""1"">{attribute_emoji} <strong><em>{attribute_name}:</em></strong> {attribute_value} </span></p>"""
            line = f"""<p><meta charset="utf-8"><span data-mce-fragment=""1"">{attribute_emoji} <strong>{attribute_name}:</strong> {attribute_value} </span></p>"""
            line_list.append(line)
    #加上Free Shipping
    attribute_emoji = emoji_code.get('free_shipping')
    attribute_name = 'Free Shipping'
    line = f"""<p><meta charset="utf-8"><span data-mce-fragment=""1"">{attribute_emoji} <strong><em>{attribute_name}</em></strong></span></p>"""
    line_list.append(line)

    return '\n'.join(line_list)

def title_url_format(title, product_url):
    '''
    url中包含商品title信息，但是title中有特殊字符，需要去除
    '''
    title = re.sub(r'[^a-z0-9\-_.]', '', title.lower().replace(' ', '-'))
    url_hash = int(hashlib.md5(product_url.encode()).hexdigest(), 16)%(10**6)
    return f"{title}-{url_hash}"

def get_image_urls(directory_path, brief_title, product_url, exist_image_keys, qiniu_auth):
    upload_image_names = []
    image_extensions = ('.jpg', '.jpeg', '.png')
    domain = "http://rzuix5mfd.bkt.clouddn.com/"
    bucket_name = 'sanchaliushui'
    storage_dir = '1688'
    #image的url种带入商品链接的hash值，防止重名
    url_hash = int(hashlib.md5(product_url.encode()).hexdigest(), 16)%(10**6)
    with os.scandir(directory_path) as entries:
        for entry in entries:
            if entry.is_file and entry.name.endswith(image_extensions):
                upload_image_names.append(entry.name)
    upload_image_names = sorted(upload_image_names, reverse=False)
    upload_cnt = len(upload_image_names)
    image_urls = []
    for i, name in enumerate(upload_image_names, 1):
        image_local_path = os.path.join(directory_path, name)
        brief_title = title_url_format(brief_title, product_url)
        suffix = name.split('.')[-1]
        image_upload_key = f"{storage_dir}/{brief_title}-{url_hash}-{upload_cnt}-{i}.{suffix}"
        url = f"{domain}{image_upload_key}"
        if image_upload_key in exist_image_keys:
            image_urls.append(url)
            continue
        token = qiniu_auth.upload_token(bucket_name, image_upload_key, 36000000)
        ret, info = put_file(token, image_upload_key, image_local_path, version='v2', keep_last_modified=True)
        assert info.status_code == 200
        image_urls.append(url)
    return image_urls

def align_array(images_urls, sku_cartesian):
    '''
    images_urls和sku_cartesian的数组长度不一样，先使长度一致，然后在explode展开
    '''
    max_len = max(len(images_urls), len(sku_cartesian))
    images_urls += [''] * (max_len-len(images_urls))
    sku_cartesian += [(('', '', -1), ('', '', -1), ('', '', -1))] * (max_len-len(sku_cartesian))
    # sku_cartesian += [sku_cartesian[0]] * (max_len-len(sku_cartesian))
    return [images_urls, sku_cartesian]


if __name__ == '__main__':
    #base信息整理
    product_base_file = "/Users/fanke.chang/shop/product/base_info.xlsx"
    df_base = pd.read_excel(product_base_file, dtype='str')
    # df_base['product_info_cn'] = df_base['product_info_cn'].apply(lambda x: json.loads(x))
    # df_base['original_title_cn'] = df_base['product_info_cn'].apply(lambda x: json.loads(x).get('original_title'))
    #英文版json的属性整理
    df_base['product_info'] = df_base['product_info'].apply(lambda x: json.loads(x))
    base_columns = ['original_title', 'description', 'brief_title', 'seo_title', 'google_category', 'type', 'tags', 'gender', 'age_group', 'adword_groups', 'adword_labels', 'mpn_code', 'sku_details', 'highest_price', 'main_attributes']
    for col in base_columns:
        df_base[col] = df_base['product_info'].apply(lambda x: x.get(col))
    df_base['original_title'] = df_base['original_title'].apply(lambda x: original_title_process(x))
    df_base[['unit_weight', 'weight_unit']] = df_base['main_attributes'].apply(lambda x: x.get('unit_weight')).apply(lambda x: convert_unit_metric_english(x)).apply(lambda x: extract_number_and_unit(x)).apply(pd.Series, [['unit_weight', 'weight_unit']])

    #根据Title获取图片url地址
    ret, eof, info = bucket.list(bucket_name, prefix='1688', limit=10**6, delimiter=None, marker = None)
    exist_image_keys = [d.get('key') for d in info.json().get('items')]
    df_base['images_urls'] = df_base.apply(lambda x: get_image_urls(os.path.join('/Users/fanke.chang/shop/product_images', x.original_title), x.brief_title, x.product_url, exist_image_keys, qiniu_auth), axis=1)
    #sku_details各属性做笛卡尔积
    df_base['sku_cartesian'] = df_base['sku_details'].apply(lambda x: sku_info_cartesian(x))
    #将images_urls和sku_cartesian的列表长度对齐，便于explode
    df_base[['images_urls', 'sku_cartesian']] = df_base.apply(lambda x: align_array(x.images_urls, x.sku_cartesian), axis=1).apply(pd.Series, index=['images_urls', 'sku_cartesian'])
    df_base = df_base.explode(['sku_cartesian','images_urls']).reset_index(drop=True)
    df_base[['attribute_name_1','attribute_value_1', 'attribute_name_2','attribute_value_2', 'attribute_name_3','attribute_value_3', 'price']] = df_base['sku_cartesian'].apply(lambda x: extract_attribute_field(x)).apply(pd.Series, index=['attribute_name_1','attribute_value_1', 'attribute_name_2','attribute_value_2', 'attribute_name_3','attribute_value_3', 'price'])

    #template表格生成
    template_columns = ['Handle','Title','Body (HTML)','Vendor','Product Category','Type','Tags','Published','Option1 Name','Option1 Value','Option2 Name','Option2 Value','Option3 Name','Option3 Value','Variant SKU','Variant Grams','Variant Inventory Tracker','Variant Inventory Qty','Variant Inventory Policy','Variant Fulfillment Service','Variant Price','Variant Compare At Price','Variant Requires Shipping','Variant Taxable','Variant Barcode','Image Src','Image Position','Image Alt Text','Gift Card','SEO Title','SEO Description','Google Shopping / Google Product Category','Google Shopping / Gender','Google Shopping / Age Group','Google Shopping / MPN','Google Shopping / AdWords Grouping','Google Shopping / AdWords Labels','Google Shopping / Condition','Google Shopping / Custom Product','Google Shopping / Custom Label 0','Google Shopping / Custom Label 1','Google Shopping / Custom Label 2','Google Shopping / Custom Label 3','Google Shopping / Custom Label 4','Variant Image','Variant Weight Unit','Variant Tax Code','Cost per item','Included / 美国','Included / 国际','Price / International','Compare At Price / International','Status']
    df_template = pd.DataFrame(columns=template_columns)
    df_template['Handle'] = df_base.apply(lambda x: title_url_format(x.brief_title, x.product_url), axis=1)
    df_template['Title'] = df_base['brief_title']
    df_template['Body (HTML)'] = df_base.apply(lambda x: body_info(x.main_attributes, x.description), axis=1)
    df_template['Vendor'] = '我的商店'
    # df_template['Product Category'] = df_base['google_category']
    df_template['Type'] = df_base['type']
    df_template['Tags'] = df_base['tags']
    df_template['Published'] = 'TRUE'
    df_template[['Option1 Name','Option1 Value','Option2 Name','Option2 Value','Option3 Name','Option3 Value']] = df_base[['attribute_name_1','attribute_value_1', 'attribute_name_2','attribute_value_2', 'attribute_name_3','attribute_value_3']]
    df_template['Variant Grams'] = df_base['unit_weight']
    df_template['Variant Inventory Tracker'] = 'shopify'
    df_template['Variant Inventory Qty'] = 20
    df_template['Variant Inventory Policy'] = 'deny'
    df_template['Variant Fulfillment Service'] = 'manual'
    df_template['Variant Price'] = df_base['price'].apply(lambda x: int(x))
    df_template['Variant Compare At Price'] = df_base['price'].apply(lambda x: int(x/0.9))
    df_template['Variant Requires Shipping'] = 'TRUE'
    df_template['Variant Taxable'] = 'TRUE'
    df_template['Image Src'] = df_base['images_urls']
    df_template['Image Position'] = df_template['Image Src'].apply(lambda x: re.search(r'-(\d+)-(\d+)\.', x).group(2) if x else '')
    df_template['SEO Title'] = df_base['seo_title']
    df_template['SEO Description'] = df_base['description']
    df_template['Google Shopping / Google Product Category'] = df_base['google_category']
    df_template['Google Shopping / Gender'] = df_base['gender']
    df_template['Google Shopping / Age Group'] = df_base['age_group']
    df_template['Google Shopping / MPN'] = df_base['mpn_code']
    df_template['Google Shopping / AdWords Grouping'] = df_base['adword_groups']
    df_template['Google Shopping / AdWords Labels'] = df_base['adword_labels']
    df_template['Variant Weight Unit'] = df_base['weight_unit']
    df_template['Included / 美国'] = 'TRUE'
    df_template['Included / 国际'] = 'TRUE'
    df_template['Status'] = 'active'
    df_template['Collection'] = df_base['type']
    review_columns = [col for col in template_columns if col not in ['Handle', 'Image Src', 'Image Position']]
    for col in review_columns:
        df_template[col] = df_template.apply(lambda x: x[col] if any([x['Option1 Name'],x['Option1 Value'],x['Option2 Name'],x['Option2 Value'],x['Option3 Name'],x['Option3 Value']]) else '', axis=1)
    df_template.to_csv('/Users/fanke.chang/shop/product/shopify_upload_sheet.csv', sep=',', index=False)

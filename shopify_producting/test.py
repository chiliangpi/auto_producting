# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/15
# @Author   : fanke.chang
# @File     : test.py
# @Desc     :
import cv2
import pytesseract
import pandas as pd

# # pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
pytesseract.pytesseract.tesseract_cmd = '/Users/fanke.chang/opt/anaconda3/envs/python3.10/bin/pytesseract'
# image_path = '/Users/fanke.chang/shop/image_filter/negative/test.jpg'
image_path = '/Users/fanke.chang/shop/image_filter/negative/test2.jpg'
# 读取图像
img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

# 二值化图像
_, thresh = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

# 检测表格的水平和垂直线
horizontal = thresh.copy()
vertical = thresh.copy()

# 定义水平结构元素并应用形态学操作
horizontal_size = horizontal.shape[1] // 30
horizontal_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
horizontal = cv2.erode(horizontal, horizontal_structure)
horizontal = cv2.dilate(horizontal, horizontal_structure)

# 定义垂直结构元素并应用形态学操作
vertical_size = vertical.shape[0] // 30
vertical_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_size))
vertical = cv2.erode(vertical, vertical_structure)
vertical = cv2.dilate(vertical, vertical_structure)

# 合并水平和垂直线
table_segment = cv2.addWeighted(vertical, 1, horizontal, 1, 0.0)

# 使用反二值化恢复表格区域
_, table_segment = cv2.threshold(table_segment, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

# 使用 OCR 提取表格数据
# extracted_text = pytesseract.image_to_string(table_segment, config='--psm 6')
extracted_text = pytesseract.image_to_string(table_segment)

# 将提取的文本转换为 DataFrame
data = [row.split() for row in extracted_text.split('\n') if row]
df = pd.DataFrame(data)

print(df)


# import cv2
# import numpy as np
# import pytesseract
# from PIL import Image
#
# # 读取图片
# image = cv2.imread(image_path, 0)
#
# # 使用阈值化突出表格结构
# _, thresh = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY_INV)
#
# # 检测水平和垂直线
# horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
# vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
# horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
# vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
#
# # 合并线条
# table_structure = horizontal_lines + vertical_lines
#
# # 查找轮廓来确定单元格位置
# contours, _ = cv2.findContours(table_structure, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#
# # 提取每个单元格的文本
# cell_texts = []
# for contour in contours:
#     x, y, w, h = cv2.boundingRect(contour)
#     cell_image = image[y:y+h, x:x+w]
#     cell_text = pytesseract.image_to_string(cell_image).strip()
#     cell_texts.append(cell_text)
#
# print("OVER")
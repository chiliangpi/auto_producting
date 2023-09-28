#!/bin/bash

## 进入项目的根目录
#cd ~/auto-producting

# 激活虚拟环境（如果有的话）
# source venv/bin/activate

python /home/aistudio/work/auto_producting/shopify_producting/shopify_product_upload.py >> output.log 2>&1 &
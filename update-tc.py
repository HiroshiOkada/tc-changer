#!/usr/bin/env python

import requests
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree as ET
from os import getenv
import argparse
import re
import yaml

# コマンドライン引数解釈

parser = argparse.ArgumentParser(
    description='はてなブログのエントリーのタイトルとカテゴリーを更新')
parser.add_argument('--api-key', help='APIキー')
parser.add_argument('root_endpoint', help='AtomPub ルートエントリーポイント')
parser.add_argument('file_name', help='入力ファイル名')
args = parser.parse_args()

root_endpoint = args.root_endpoint
match = re.fullmatch(
    r'https://blog.hatena.ne.jp/([^/]*)/([^/]*)/atom', root_endpoint)
if match is None:
    print('ルートエントリーポイントが正しくありません')
    exit(1)
hatena_id = match.group(1)
blog_id = match.group(2)

api_key = args.api_key or getenv('API_KEY')
if api_key is None:
    print('環境変数 API_KEY か引数 --api-key で APIキーを設定してください。')
    exit(1)

file_name = args.file_name

# 名前空間の定義

ns = {
    'atom': 'http://www.w3.org/2005/Atom',
    'app': 'http://www.w3.org/2007/app',
    'hatena': 'http://www.hatena.ne.jp/info/xmlns#'}

ET.register_namespace('', 'http://www.w3.org/2005/Atom')
ET.register_namespace('app', 'http://www.w3.org/2007/app')
ET.register_namespace('hatena', 'http://www.hatena.ne.jp/info/xmlns#')


# 認証情報
auth = HTTPBasicAuth(hatena_id, api_key)

with open(file_name, encoding='utf-8') as f:
    modified_entries = yaml.load(f)

for modified_enty in modified_entries:
    entry_id = modified_enty['entry_id']
    url = f'{root_endpoint}/entry/{entry_id}'
    print(url)
    res = requests.get(url, auth=auth)
    if res.status_code != 200:
        print(f'get: {url} => {res.status_code}')
        exit(2)
    root = ET.fromstring(res.text)

    # title を更新
    title = root.find('atom:title', ns)
    title.text = modified_enty['title']

    # category を更新
    for category in root.findall('atom:category', ns):
        root.remove(category)
    for category_name in modified_enty['categories']:
        category = ET.SubElement(
            root,
            'category',
            attrib={'term': category_name})

    data = ET.tostring(root, encoding='unicode').encode('utf-8')
    res = requests.put(
            url,
            data=data,
            headers={'Content-type': 'text/xml; charset=utf-8'},
            auth=auth)
    if res.status_code == 200:
        print(f'{entry_id} {title.text} を更新しました。')
    else:
        print(f'{entry_id} {title.text} の更新に失敗しました。')
        print(f'status_code: {res.status_code}')
        exit(3)

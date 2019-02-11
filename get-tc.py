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
    description='はてなブログの全エントリーのタイトルとカテゴリーを取得')
parser.add_argument('--api-key', help='APIキー')
parser.add_argument('root_endpoint', help='AtomPub ルートエントリーポイント')
parser.add_argument('output_file_name', help='出力ファイル名')
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

output_file_name = args.output_file_name

# 名前空間の定義

ns = {
    'atom': 'http://www.w3.org/2005/Atom',
    'app': 'http://www.w3.org/2007/app',
    'hatena': 'http://www.hatena.ne.jp/info/xmlns#'}


url = f'{root_endpoint}/entry'
auth = HTTPBasicAuth(hatena_id, api_key)
allentries = []

while True:
    res = requests.get(url, auth=auth)
    if res.status_code != 200:
        print(f'文書取得失敗: GET {url} => {res.text}')
        exit(2)

    root = ET.fromstring(res.text)
    entries = root.findall('atom:entry', ns)

    for entry in entries:
        ent = {}
        ent['entry_id'] = entry.find('atom:id', ns).text.split('-')[-1]
        ent['title'] = entry.find('atom:title', ns).text
        ent['summary'] = entry.find('atom:summary', ns).text
        ent['published'] = entry.find('atom:published', ns).text
        ent['link'] = entry.find(
            'atom:link[@rel="alternate"]', ns).attrib['href']
        ent['categories'] = [
            category.attrib['term']
            for category in entry.findall('atom:category', ns)]
        allentries.append(ent)

    # 次の文書
    link = root.find('atom:link[@rel="next"]', ns)
    if link is not None:
        url = link.attrib['href']
    else:
        break

with open(output_file_name, mode='w', encoding='utf8') as f:
    yaml.dump(
        allentries,
        f,
        default_flow_style=False,
        allow_unicode=True)
    print(f'{output_file_name} に書き出しました。')

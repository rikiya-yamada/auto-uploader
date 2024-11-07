import sys
import os
import json
import getpass
import requests
from bs4 import BeautifulSoup, Tag
from tkinter import Tk, filedialog
from contextlib import ExitStack

login_data_file = os.path.join(os.path.expanduser("~"), 'kgu_login_data.json')
login_data_exists = True
if os.path.exists(login_data_file):
    with open(login_data_file, "r") as file:
        login_data = json.load(file)
else:
    login_data = {}
    login_data['username'] = input('ユーザ名:')
    login_data['password'] = getpass.getpass('パスワード:')
    login_data_exists = False

session = requests.Session()
session.auth = (login_data['username'], login_data['password'])
upload_url = input('提出ページURL:')
response = None
try:
    response = session.get(upload_url)
except requests.exceptions.InvalidURL:
    print('無効なURLです')
    sys.exit()
if response.status_code == 401:
    print('認証に失敗しました')
    sys.exit()
if not login_data_exists:
    with open(login_data_file, "w") as file:
        json.dump(login_data, file)

soup = BeautifulSoup(response.text, 'html.parser')
form = soup.find('form')
if not isinstance(form, Tag):
    print('フォームが存在しません')
    sys.exit()

file_inputs = form.find_all('input', {'type': 'file'})
if not file_inputs:
    print('提出できるファイルがありません')
    sys.exit()
required_files = []
for file_input in file_inputs:
    required_files.append(file_input.get('name').split(':')[1])

root = Tk()
root.withdraw()
root.overrideredirect(True)
root.attributes('-topmost', True)
file_directory = filedialog.askdirectory(parent=root)
root.destroy()
if not file_directory:
    print('フォルダが選択されませんでした')
    sys.exit()

with ExitStack() as stack:
    files_to_upload = {}
    files_not_found = []
    for filename in required_files:
        file_path = os.path.join(file_directory, filename)
        if os.path.exists(file_path):
            files_to_upload[f'source_f:{filename}'] = (filename, stack.enter_context(open(file_path, 'rb')))
        else:
            files_not_found.append(filename)

    if files_not_found:
        print('フォルダ内に存在しないためアップロードされないファイル')
        for file in files_not_found:
            print(file)

    hidden_inputs = form.find_all('input', {'type': 'hidden'})
    form_data = {}
    for hidden_input in hidden_inputs:
        form_data[hidden_input.get('name')] = hidden_input.get('value')
    form_data['act_item_upload'] = '下記ファイルをまとめてアップロード'

    response = session.post(upload_url, data=form_data, files=files_to_upload)

    if files_to_upload:
        print('以下のファイルをアップロードしました')
        for (filename, fileobj) in files_to_upload.values():
            print(filename)

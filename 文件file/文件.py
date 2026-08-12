'''
文件的处理，网络requests库的应用，json文件，csv文件
'''

import json
import os
import requests
import csv
import random

def adress(char: str):
    fileDict = {
        'json': 'tem_fileJSON.json',
        'csv': 'tem_fileCSV.csv'
    }
    
    file_name = fileDict[char]
    file_parent = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(file_parent, file_name)
    return file_path

def PracticeRequest_Get():

    url = 'https://jsonplaceholder.typicode.com/posts/1'
    resp = requests.get(url)  # 获取文件

    print(f'状态码: {resp.status_code}')
    data = resp.json() # response对象假设为json字符序列，将其解析为对应数据结构
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    

def PracticeRequest_Post():
    file_parent = os.path.dirname(os.path.abspath(__file__))
    file_name = 'MyLogin.json' # 创建Mylogin的json文件
    file_path = os.path.join(file_parent, file_name)
    
    with open(file_path, 'r') as file:
        login_data = json.load(file) # load，loads反序列化，dump，dumps序列化，针对file的操作
    print(login_data)
    
    myAPI = 'free_user_3HnaakbDLR3igSERtE70N0Kgr6L'
    headers = {
        'x-api-key': myAPI
    }
    
    url = 'https://reqres.in/api/login'
    resp = requests.post(url, json=login_data, headers=headers)
    if resp.status_code == 200:
        print('log in sucessfully!')
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    else:
        print(f'状态码：{resp.status_code}')
        print(resp.text)

       
def PracticeCSV():
    '''纯文本文件
    
1. 纯文本，使用某种字符集（如 ASCII、Unicode、GB2312等）；
2. 由一条条的记录组成（典型的是每行一条记录）；
3. 每条记录被分隔符（如逗号、分号、制表符等）分隔为字段（列）；
4. 每条记录都有同样的字段序列。

csv模块，writer函数返回csvwriter对象，用writeraw写入每一行
reader函数返回csvreader对象，可以用next函数或者for-in循环读取
    '''
    
    file_path = adress('csv')
    with open(file_path, 'w', newline='') as file: # 防止空行
        writer = csv.writer(file)
        writer.writerow(['姓名', '语文', '数学', '英语'])
        idNumber = ['2301', '2393', '2404', '2517']
        for name in idNumber:
            scores = [random.randrange(61, 101) for _ in range(3)]
            scores.insert(0, name)
            writer.writerow(scores)
            
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for item in reader:
            print(reader.line_num, end='\t') # 打印行号
            for element in item:
                print(element, end='\t')
            print()  # 换行    
    


if __name__ == '__main__':
    PracticeCSV()
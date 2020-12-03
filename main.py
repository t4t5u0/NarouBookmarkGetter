import json
import time
from collections import UserDict
from configparser import ConfigParser

import requests
from bs4 import BeautifulSoup

login    = 'https://ssl.syosetu.com/login/login/'
top      = "https://syosetu.com/"
bookmark = "https://syosetu.com/favnovelmain/list/"
query    = "https://syosetu.com/favnovelmain/list/index.php"


config = ConfigParser()
config.read('config.ini')
payload = {"narouid": config['DEFAULT']
           ['narouid'], "pass": config['DEFAULT']['pass']}
print(payload)

ua = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Mobile Safari/537.36"
headers = {"User-Agent": ua}


class SyosetsuInfoDict(UserDict):
    def __init__(self, __ncode: str, __title: str, __total) -> None:
        super().__init__(ncode=__ncode, title=__title,  total=__total)


def get_all_bookmark():
    "全てのブックマークを取得する処理"

    ncodes = []
    titles = []
    totals = []

    ses = requests.Session()
    a = ses.post(login, data=payload, headers=headers)

    try:
        cookies = [dict(hoge.cookies) for hoge in a.history][0]
    except IndexError as e:
        print(e)
        print('narouid と pass を確認してください')
        exit(0)
    for i in range(1, 11):
        tmp = []
        # なんとなく待ってみる
        time.sleep(1)
        for j in range(1, 9):
            param = {"nowcategory": str(i), "order": "new", "p": str(j)}
            page = ses.get(query, headers=headers,
                           params=param, cookies=cookies)
            # ステータスコードが200じゃなかったら処理しない
            if page.status_code != 200:
                continue

            # title: a class=title text -> list[str]
            # ncode: a class=title href をとってくる -> list[str]
            # total: ncodeで検索 -> t := a href[-1] -> t[2:-2]
            soup = BeautifulSoup(page.text, 'lxml')

            contents = soup.find_all('a', class_='title')
            query_with_story = [l.get('href') for l in soup.select('p.no > a')]

            # 1回前と重複してたら処理をしない
            if contents == tmp:
                continue
            tmp = "https://syosetu.com/favnovelmain/list/index.php"

            titles += [content.text.replace('\u3000', ' ')
                       for content in contents]
            ncodes += [content.get('href')[26:-2] for content in contents]
            totals += [l.split('/')[-2] for l in query_with_story]

            return sorted(list(dict(SyosetsuInfoDict(ncode, title, total))
                               for ncode, title, total
                               in zip(ncodes, titles, totals)),
                          key=lambda x: x['ncode'])


if __name__ == "__main__":
    result = get_all_bookmark()
    with open(f'./data/{time.time()}.json', 'a+') as f:
        json.dump(result, f,  ensure_ascii=False, indent=4)

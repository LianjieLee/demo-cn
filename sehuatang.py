#!/usr/bin/python3
import os
import re
import time

import requests
import telegram
from bs4 import BeautifulSoup
from faker import Faker


class sehuatang:
    def __init__(self):
        self.url = 'https://www.sehuatang.net/'
        self.header = {'User-Agent': Faker().user_agent()}
        self.new_posts = []
        self.all_posts = set()
        with open('list.txt', 'r') as f:
            self.old_posts = eval(f.read())

    # 获取帖子列表
    def getPostList(self):
        hd = {'Referer': 'https://www.sehuatang.net/index.php'}
        self.header.update(hd)
        r = requests.get(self.url + 'forum-103-1.html', headers=self.header)
        soup = BeautifulSoup(r.text, 'html.parser')
        thread_list = soup.find('div', {'id': 'threadlist'})
        post_list = thread_list.find_all('tbody', {'id': re.compile(r'normalthread_\d*?')})
        print(self.time(), f'抓取帖子{len(post_list)}个', flush=True)
        for i in post_list:
            thread = i.tr.td.a['href']
            self.all_posts.add(thread)
            if thread not in self.old_posts:
                self.new_posts.append(self.url + thread)
        print(self.time(), f'新帖子{len(self.new_posts)}个', flush=True)

    # 获取帖子全文
    def getPostContent(self, url):
        r = requests.get(url, headers=self.header)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find('h1', {'class': "ts"}).text.strip().replace('\n', ' ')
        title_link = f"<a href='{url}'>" + '<b>' + title + '</b>' + '</a>'
        post = soup.find('div', {'id': re.compile(r"post_\d*?")}).find('div', {'class': 't_fsz'})
        magnet = re.search(r'(magnet:\?xt=urn:btih:[0-9a-fA-F]{40})', post.text).group(1)
        imgs = post.table.find_all('img')
        img = []
        for i in imgs:
            if 'http' in i['file']:
                img.append(i['file'])
            else:
                img.append(self.url + i['file'])
        content = title_link + '\n' + magnet
        print(self.time(), title, "已获取", flush=True)
        return title, content, img

    def time(self):
        strftime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        return strftime

    def updateList(self):
        with open('list.txt', 'w') as f:
            f.write(str(self.all_posts))
        print(self.time(), '列表已更新', flush=True)


if __name__ == '__main__':
    bot_id = os.getenv('BOT_ID')
    chat_id = os.getenv('CHAT_ID')
    se = sehuatang()
    bot = telegram.Bot(bot_id)
    se.getPostList()
    for i in se.new_posts:
        try:
            title,content,img = se.getPostContent(i)
            media_list = [telegram.InputMediaPhoto(media=img[0], caption=content, parse_mode='HTML')]
            # TG limit to 10 pic
            if len(img) > 10:
                for j in range(1, 10):
                    media_list.append(telegram.InputMediaPhoto(media=img[j]))
            else:
                for j in range(1, len(img)):
                    media_list.append(telegram.InputMediaPhoto(media=img[j]))
            bot.send_media_group(chat_id, media=media_list)
            print(se.time(), title, '已发送', flush=True)
            time.sleep(10)
        except Exception as e:
            print(se.time(), title, e, flush=True)
    se.updateList()
#!/usr/bin/python3
import os
import re
import time
import pathlib

import requests
import telegram
from bs4 import BeautifulSoup
from faker import Faker
from urllib import parse


class sehuatang:
    def __init__(self, bot_id, chat_id):
        self.bot_id = bot_id
        self.chat_id = chat_id
        self.url = 'https://www.sehuatang.net/'
        self.header = {'User-Agent': Faker().user_agent(), 'X-Forwarded-For': Faker().ipv4()}
        self.cookies = {'_safe': os.getenv('_SAFE')}
        self.new_posts = []
        self.all_posts = set()
        with open('list.txt', 'r') as f:
            self.old_posts = eval(f.read())

    # 获取帖子列表
    def getPostList(self):
        hd = {'Referer': 'https://www.sehuatang.net/index.php'}
        self.header.update(hd)
        r = requests.get(self.url + 'forum-103-1.html', headers=self.header, cookies=self.cookies)
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

    # 获取帖子内容
    def getPostContent(self, url):
        r = requests.get(url, headers=self.header, cookies=self.cookies)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find('h1', {'class': "ts"}).text.strip().replace('\n', ' ')
        video_id = title.split()[1].replace('-','')
        title_link = f"<a href='{url}'>" + '<b>' + title + '</b>' + '</a>'
        post = soup.find('div', {'id': re.compile(r"post_\d*?")}).find('div', {'class': 't_fsz'})
        magnet = re.search(r'(magnet:\?xt=urn:btih:[0-9a-fA-F]{40})', post.text).group(1)
        content = title_link + '\n' + magnet
        print(self.time(), title, "已获取", flush=True)
        return video_id, title, content

    #video_id SSIS835
    def dmm_info(self, video_id):
        try:
            video_id = video_id.replace('-C','').replace('-','')
            header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0', 'X-Forwarded-For': '104.28.243.105'}
            url = f"https://www.dmm.co.jp/mono/dvd/-/detail/=/cid={video_id}/"
            age_check = f"https://www.dmm.co.jp/age_check/=/declared=yes/?rurl={parse.quote(url)}"
            s = requests.session()
            s.get(age_check, headers=header)
            r = s.get(url, headers=header)
            soup = BeautifulSoup(r.text, "html.parser")
            poster = soup.find('a', {'name': 'package-image'})['href']
            video_info = f'https://www.dmm.co.jp/service/digitalapi/-/html5_player/=/cid={video_id}/mtype=AhRVShI_'
            r = s.get(video_info, headers=header)
            video = re.search(r'"videoType":"mp4","src":"(http.*?mp4)"', r.text).group(1).replace('\\', '')
            vname = video.split('/')[-1]
            with open(vname, 'wb') as vd:
                with s.get(video) as v:
                    vd.write(v.content)
            video = pathlib.Path(vname)
            print(video, 'save!')
        except Exception as e:
            poster = video = None
            print(self.time(), '找不到JAV信息：', e, flush=True)
        return poster, video

    # 推送到TG
    def sendMsg(self, caption, poster, video):
        bot = telegram.Bot(self.bot_id)
        try:
            if poster is None:
                bot.sendMessage(chat_id, caption, parse_mode='HTML', disable_web_page_preview=True)
            else:
                media_list = [telegram.InputMediaPhoto(media=poster, caption=caption, parse_mode='HTML')]
                media_list.append(telegram.InputMediaVideo(media=video))
                bot.send_media_group(self.chat_id, media=media_list)
            print(self.time(), caption, '已发送', flush=True)
        except Exception as e:
            print(self.time(), caption, e, flush=True)        


    # 更新帖子列表
    def updateList(self):
        with open('list.txt', 'w') as f:
            f.write(str(self.all_posts))
        print(self.time(), '列表已更新', flush=True)

    def time(self):
        strftime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        return strftime


if __name__ == '__main__':
    bot_id = os.getenv('BOT_ID')
    chat_id = os.getenv('CHAT_ID')
    sht = sehuatang(bot_id, chat_id)
    sht.getPostList()
    for url in sht.new_posts:
        video_id, title, content = sht.getPostContent(url)
        print('获取帖子内容成功：',video_id, title, content)
        poster, video = sht.dmm_info(video_id)
        print('获取视频信息内容成功：',poster, video)
        sht.sendMsg(content, poster, video)
        time.sleep(10)
    sht.updateList()
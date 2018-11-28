# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request,FormRequest
import json
from pyquery import PyQuery as pq
import requests
import logging
import os
import re


logging.captureWarnings(True)


class PixSpider(scrapy.Spider):
    name = 'pixv'
    allowed_domains = ['pixiv.net']
    start_urls = ['http://pixiv.net/']

    login_url = 'https://accounts.pixiv.net/login'

    headers = {
                'accept': 'application/json',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN, zh;q=0.9',
                'upgrade-insecure-requests': '1',
                'content-type':'application/x-www-form-urlencoded',
                'referer': 'https: // www.pixiv.net /',
                'user-agent': 'Mozilla/5.0(WindowsNT6.1;Win64;x64) AppleWebKit/537.36(KHTML,Gecko) Chrome/70.0.3538.77 Safari/537.36',
    }

    list_url = 'member_illust.php?id={user_id}&type=illust'
    user_id = 作者のID
    all = 'ajax/user/{user_id}/profile/all'

    get_url = 'https://www.pixiv.net/ajax/user/{user_id}/profile/illusts?'
    full_url = None
    page_count = 0
    pic_count = 0

    root_file = '/home/saberno/pixiv/' + str(user_id)

    if not os.path.exists(root_file):
        os.makedirs(root_file)

    #all_url = None

    def start_requests(self):
        yield Request(self.login_url,meta = {'cookiejar':1},callback=self.login_start)


    def login_start(self, response):
        print('start spider')
        post_key = response.xpath('//*[@id="old-login"]/form/input[1]/@value').extract_first()
        print(post_key)
        yield FormRequest.from_response(response,
                                         meta={'cookiejar':response.meta['cookiejar']},
                                         headers = self.headers,
                                         formdata = {
                                             'pixiv_id':'your id',
                                             'captcha':'',
                                             'g_recaptcha_response':'',
                                             'password':'',
                                             'post_key':post_key,
                                             'source':'pc',
                                             'ref':'wwwtop_accounts_index',
                                             'return_to':'https://www.pixiv.net/'
                                         },
                                         callback = self.after_login,
                                         dont_filter = True)


    def after_login(self,response):
        lists_url = response.url + self.list_url.format(user_id = str(self.user_id))
        all_url = response.url+self.all.format(user_id = str(self.user_id))
        yield Request(all_url,meta = {'cookiejar':1},callback=self.full_urlget)


    def full_urlget(self,response):
        results = json.loads(response.text)
        #print(results)
        #full_url = self.get_url.format(user_id=self.user_id)
        all_illusts = results['body']['illusts']
        all_keys = list(all_illusts.keys())
        #print(all_keys)
        page = int(len(all_illusts) / 50) + 1
        for n in range(page):
            page_count = 0
            full_url = self.get_url.format(user_id=self.user_id)
            for result in all_keys:
                full_url += 'ids%5B%5D=' + str(result) +'&'
                all_keys.pop(all_keys.index(result))
                page_count += 1
                if page_count >= 50:
                    break
            complite_url = full_url + 'is_manga_top=0'
            #print(complite_url)
            yield Request(complite_url,meta = {'cookiejar':1},callback=self.parse_page)


    def parse_page(self,response):
        results = json.loads(response.text)
        print('start')
        #print(results)
        result = results['body']['works']
        il_keys = result.keys()
        #print(result)
        for key in il_keys:
            if result[key]['pageCount'] == 1:
                get_pic_url = 'https://www.pixiv.net/ajax/illust/' + result[key]['id']
                yield Request(get_pic_url,meta = {'cookiejar':1},callback=self.pic_get)
            elif result[key]['pageCount'] > 1:
                get_pics_url = 'https://www.pixiv.net/ajax/illust/' + result[key]['id']
                yield Request(get_pics_url, meta={'cookiejar': 1}, callback=self.pics_get)


    def pic_get(self,response):
        results = json.loads(response.text)
        url = results['body']['urls']['original']
        title = results['body']['title']
        user_name = results['body']['userName']
        headers_pic = {
            'accept': 'application/json',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN, zh;q=0.9',
            'upgrade-insecure-requests': '1',
            'content-type': 'application/x-www-form-urlencoded',
            'referer': 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + results['body']['illustId'],
            'user-agent': 'Mozilla/5.0(WindowsNT6.1;Win64;x64) AppleWebKit/537.36(KHTML,Gecko) Chrome/70.0.3538.77 Safari/537.36',
        }
        doc = requests.get(url,headers = headers_pic)
        if 'png' in url:
            with open(self.root_file + '/' + title +'.png','wb') as f:
                f.write(doc.content)
                f.close()
        else:
            with open(self.root_file + '/' + title +'.jpg','wb') as f:
                f.write(doc.content)
                f.close()

        #self.pic_count += 1


    def pics_get(self,response):
        results = json.loads(response.text)
        url = results['body']['urls']['original']
        title = results['body']['title']
        if '/' in title:
            title = title.replace('/',' ')
        page_count = results['body']['pageCount']
        user_name = results['body']['userName']
        headers_pic = {
            'accept': 'application/json',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN, zh;q=0.9',
            'upgrade-insecure-requests': '1',
            'content-type': 'application/x-www-form-urlencoded',
            'referer': 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + results['body']['illustId'],
            'user-agent': 'Mozilla/5.0(WindowsNT6.1;Win64;x64) AppleWebKit/537.36(KHTML,Gecko) Chrome/70.0.3538.77 Safari/537.36',
        }
        for num in range(int(page_count)):
            doc = requests.get(url, headers=headers_pic)
            if 'png' in url:
                with open(self.root_file +'/' + title + '_' + str(num) + '.png', 'wb') as f:
                    f.write(doc.content)
                    f.close()
            else:
                with open(self.root_file +'/' + title + '_' + str(num) + '.jpg', 'wb') as f:
                    f.write(doc.content)
                    f.close()

            #self.pic_count += 1
            p = 'p' + str(num)
            url = url.replace(p,'p'+str(num+1))

# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request,FormRequest
from pyquery import PyQuery as pq
import requests
from bs4 import BeautifulSoup as bs
import re
import datetime
import os

class Top50Spider(scrapy.Spider):
    name = 'top50'
    allowed_domains = ['pixiv.net']
    start_urls = ['http://pixiv.net/']
    big_url = 'https://www.pixiv.net/ranking.php?mode=daily&content=illust'
    login_url = 'https://accounts.pixiv.net/login'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    root_file = '/home/saberno/pixiv/TOP50/' + today + '/'

    if not os.path.exists(root_file):
        os.makedirs(root_file)

    pic_num = 0

    headers = {
                'accept': 'application/json',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN, zh;q=0.9',
                'upgrade-insecure-requests': '1',
                'content-type':'application/x-www-form-urlencoded',
                'referer': 'https: // www.pixiv.net /',
                'user-agent': 'Mozilla/5.0(WindowsNT6.1;Win64;x64) AppleWebKit/537.36(KHTML,Gecko) Chrome/70.0.3538.77 Safari/537.36',
    }


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




    def after_login(self, response):
        yield Request(self.big_url, meta={'cookiejar': 1}, callback=self.page_parse)


    def page_parse(self,response):
        '''
        doc = pq(url = response.url)
        like = doc('.ranking-item .ranking-image-item ._layout-thumbnail img')
        for lik in like:
            get_url = pq(lik).attr('data-src')
            del_str = '/c/240x480'
            if del_str in get_url:
                get_url = get_url.replace(del_str,'')
            print(get_url)
        '''
        #get_id = re.compile('class="_thumbnail ui-scroll-view"data-filter="thumbnail-filter lazy-image"data-src="(.*?)"data-type')
        ids = []
        data_id = response.css('div.ranking-image-item > a > div > img::attr(data-id)').extract()
        for id in data_id:
            ids.append(id)

        titles = []
        title_get = response.css('h2 > a::text').extract()
        for title in title_get:
            titles.append(title)

        for item in response.css('div.ranking-image-item > a > div > img::attr(data-src)').extract():

            del_str = '/c/240x480'
            if del_str in item:
                item = item.replace(del_str, '')
            print(item)
            headers_pic = {
                'accept': 'application/json',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN, zh;q=0.9',
                'upgrade-insecure-requests': '1',
                'content-type': 'application/x-www-form-urlencoded',
                'referer': 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(ids[0]),
                'user-agent': 'Mozilla/5.0(WindowsNT6.1;Win64;x64) AppleWebKit/537.36(KHTML,Gecko) Chrome/70.0.3538.77 Safari/537.36',
            }

            pic_ht = requests.get(item,headers = headers_pic)
            with open(self.root_file + titles[0] + '.jpg','wb') as f:
                f.write(pic_ht.content)
                f.close()
            self.pic_num += 1
            ids.pop(0)
            titles.pop(0)
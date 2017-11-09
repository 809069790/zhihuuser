# -*- coding: utf-8 -*-
from scrapy import Spider, Request
from zhihuuser.items import UserItem
import json

class ZhihuSpider(Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    start_urls = ['http://www.zhihu.com/']
    redis_key = 'user'
    start_user = 'excited-vczh'
    # 个人信息
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'locations,employments,gender,educations,business,voteup_count,thanked_Count,follower_count,following_count,cover_url,following_topic_count,following_question_count,following_favlists_count,following_columns_count,avatar_hue,answer_count,articles_count,pins_count,question_count,columns_count,commercial_question_count,favorite_count,favorited_count,logs_count,included_answers_count,included_articles_count,included_text,message_thread_token,account_status,is_active,is_bind_phone,is_force_renamed,is_bind_sina,is_privacy_protected,sina_weibo_url,sina_weibo_name,show_sina_weibo,is_blocking,is_blocked,is_following,is_followed,is_org_createpin_white_user,mutual_followees_count,vote_to_count,vote_from_count,thank_to_count,thank_from_count,thanked_count,description,hosted_live_count,participated_live_count,allow_message,industry_category,org_name,org_homepage,badge[?(type=best_answerer)].topics'
    # 关注他（她）的人
    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'
    # 他（她）关注的人
    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    # 分别请求
    def start_requests(self):
        yield Request(self.user_url.format(user=self.start_user, include=self.user_query),callback=self.parse_user)

        yield Request(self.follows_url.format(user=self.start_user, include=self.follows_query, offset=0, limit=20),callback=self.parse_followees)

        yield Request(self.follows_url.format(user=self.start_user, include=self.followers_query, offset=0, limit=20),
                      callback=self.parse_followers)
    # 个人信息
    def parse_user(self, response):
        result = json.loads(response.text)
        item = UserItem()
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item
        # 获取关注列表
        yield Request(self.follows_url.format(user=result.get('url_token'), include=self.follows_query, offset=0, limit=20),
                      callback=self.parse_followees)
        # 获取粉丝列表
        yield Request(self.follows_url.format(user=result.get('url_token'), include=self.followers_query, offset=0, limit=20),
                      callback=self.parse_followers)
    # 关注列表
    def parse_followees(self, response):
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                # 调用获取个人信息
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              callback=self.parse_user)
                # 关注列表
                if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
                    next_page = results.get('paging').get('next')
                    yield Request(next_page, self.parse_followees)
    # 粉丝列表
    def parse_followers(self, response):
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                # 调用获取个人信息
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              callback=self.parse_user)
                # 关注列表
                if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
                    next_page = results.get('paging').get('next')
                    yield Request(next_page, self.parse_followers)
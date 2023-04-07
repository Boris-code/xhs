import json
from enum import Enum

import requests

from xhs.exception import DataFetchError

from .help import get_search_id, sign


class FeedType(Enum):
    # 推荐
    RECOMMEND = "homefeed_recommend"
    # 穿搭
    FASION = "homefeed.fashion_v3"
    # 美食
    FOOD = "homefeed.food_v3"
    # 彩妆
    COSMETICS = "homefeed.cosmetics_v3"
    # 影视
    MOVIE = "homefeed.movie_and_tv_v3"
    # 职场
    CAREER = "homefeed.career_v3"
    # 情感
    EMOTION = "homefeed.love_v3"
    # 家居
    HOURSE = "homefeed.household_product_v3"
    # 游戏
    GAME = "homefeed.gaming_v3"
    # 旅行
    TRAVEL = "homefeed.travel_v3"
    # 健身
    FITNESS = "homefeed.fitness_v3"


class XhsClient:
    def __init__(self,
                 cookie=None,
                 user_agent=None,
                 timeout=10,
                 proxies=None):
        """constructor

        :param cookie: get it form your website, defaults to None
        :type cookie: str, optional
        :param user_agent: requests user agent, defaults to None
        :type user_agent: str, optional
        :param timeout: requests timeout, defaults to None
        :type timeout: int, optional
        :param proxies: requests proxies, defaults to None
        :type proxies: dict, optional
        """
        self._user_agent = user_agent or ("Mozilla/5.0 "
                                          "(Windows NT 10.0; Win64; x64) "
                                          "AppleWebKit/537.36 "
                                          "(KHTML, like Gecko) "
                                          "Chrome/111.0.0.0 Safari/537.36")
        self._cookie = cookie
        self._proxies = proxies
        self._session: requests.Session = requests.session()
        self._timeout = timeout
        self._host = "https://edith.xiaohongshu.com"

    def set_cookie(self, cookie: str):
        self._cookie = cookie

    def get_cookie(self):
        return self._cookie

    def get_user_agent(self):
        return self._user_agent

    def set_user_agent(self, user_agent: str):
        self._user_agent = user_agent

    def get_proxies(self):
        return self._proxies

    def set_proxies(self, proxies: dict):
        self._proxies = proxies

    def get_timeout(self):
        return self._timeout

    def set_timeout(self, timeout):
        self._timeout = timeout

    def _pre_headers(self, url: str, data=None):
        assert self._cookie
        signs = sign(url, data)
        return {
            "User-Agent": self._user_agent,
            "cookie": self._cookie,
            "x-s": signs["x-s"],
            "x-t": signs["x-t"],
            "Content-Type": "application/json"
        }

    def request(self, method, url, **kwargs):
        response = self._session.request(
            method, url, timeout=self._timeout,
            proxies=self._proxies, **kwargs)
        data = response.json()
        if data["success"]:
            return data.get("data", data.get("success"))
        else:
            raise DataFetchError(data.get("msg", None))

    def get(self, uri: str, params=None):
        final_uri = uri
        if isinstance(params, dict):
            final_uri = (f"{uri}?"
                         f"{'&'.join([f'{k}={v}'for k,v in params.items()])}")
        headers = self._pre_headers(final_uri)
        return self.request(method="GET", url=f"{self._host}{final_uri}",
                            headers=headers)

    def post(self, uri: str, data: dict):
        headers = self._pre_headers(uri, data)
        json_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        return self.request(method="POST", url=f"{self._host}{uri}",
                            data=json_str.encode("utf-8"),
                            headers=headers)

    def get_note_by_id(self, note_id: str):
        data = {"source_note_id": note_id}
        uri = "/api/sns/web/v1/feed"
        res = self.post(uri, data)
        return res["items"][0]

    def get_self_info(self):
        uri = "/api/sns/web/v1/user/selfinfo"
        res = self.get(uri)
        return res

    def get_user_info(self, user_id: str):
        uri = "/api/sns/web/v1/user/otherinfo"
        params = {
            "target_user_id": user_id
        }
        return self.get(uri, params)

    def get_home_feed(self, feed_type: FeedType):
        uri = "/api/sns/web/v1/homefeed"
        data = {
            "cursor_score": "",
            "num": 40,
            "refresh_type": 1,
            "note_index": 0,
            "unread_begin_note_id": "",
            "unread_end_note_id": "",
            "unread_note_count": 0,
            "category": feed_type.value
        }
        return self.post(uri, data)

    def get_note_by_keyword(self, keyword: str):
        uri = "/api/sns/web/v1/search/notes"
        data = {
            "keyword": keyword,
            "page": 1,
            "page_size": 20,
            "search_id": get_search_id(),
            "sort": "general",
            "note_type": 0
        }
        return self.post(uri, data)

    def get_user_notes(self, user_id: str, cursor: str = ""):
        uri = "/api/sns/web/v1/user_posted"
        params = {
            "num": 30,
            "cursor": cursor,
            "user_id": user_id
        }
        return self.get(uri, params)

    def comment_note(self, note_id: str, content: str):
        """comment a note

        :return: {
            "time": 1680834576180,
            "toast": "评论已发布",
            "comment": {
                "id": "id",
                "note_id": "note_id",
                "status": 2,
                "liked": false,
                "show_tags": [
                "is_author"
                ],
                "ip_location": "ip_location",
                "content": "content",
                "at_users": [],
                "like_count": "0",
                "user_info": {
                "image": "**",
                "user_id": "user_id",
                "nickname": "nickname"
                },
                "create_time": create_time
            }
        }
        :rtype: dict
        """
        uri = "/api/sns/web/v1/comment/post"
        data = {
            "note_id": note_id,
            "content": content,
            "at_users": []
        }
        return self.post(uri, data)

    def delete_note_comment(self, note_id: str, comment_id: str):
        uri = "/api/sns/web/v1/comment/delete"
        data = {
            "note_id": note_id,
            "comment_id": comment_id
        }
        return self.post(uri, data)

    def comment_user(self, note_id: str, comment_id: str, content: str):
        """
        :return: {
            "comment": {
                "like_count": "0",
                "user_info": {
                "user_id": user_id
                "user_id": "user_id",
                "image": "image"
                },
                "show_tags": [
                "is_author"
                ],
                "ip_location": "ip_location",
                "id": "id",
                "content": "content",
                "at_users": [],
                "create_time": 1680847204059,
                "target_comment": {
                "id": "id",
                "user_info": {
                    "user_id": "user_id",
                    "nickname": "nickname",
                    "image": "image"
                }
                },
                "note_id": "note_id",
                "status": 2,
                "liked": false
            },
            "time": 1680847204089,
            "toast": "你的回复已发布"
            }
        """
        uri = "/api/sns/web/v1/comment/post"
        data = {
            "note_id": note_id,
            "content": content,
            "target_comment_id": comment_id,
            "at_users": []
        }
        return self.post(uri, data)

    def follow_user(self, user_id: str):
        uri = "/api/sns/web/v1/user/follow"
        data = {
            "target_user_id": user_id
        }
        return self.post(uri, data)

    def unfollow_user(self, user_id: str):
        uri = "/api/sns/web/v1/user/unfollow"
        data = {
            "target_user_id": user_id
        }
        return self.post(uri, data)

    def collect_note(self, note_id: str):
        uri = "/api/sns/web/v1/note/collect"
        data = {
            "note_id": note_id
        }
        return self.post(uri, data)

    def uncollect_note(self, note_id: str):
        uri = "/api/sns/web/v1/note/uncollect"
        data = {
            "note_ids": note_id
        }
        return self.post(uri, data)

    def like_note(self, note_id: str):
        uri = "/api/sns/web/v1/note/like"
        data = {
            "note_oid": note_id
        }
        return self.post(uri, data)

    def like_comment(self, note_id: str, comment_id: str):
        uri = "/api/sns/web/v1/comment/like"
        data = {
            "note_id": note_id,
            "comment_id": comment_id
        }
        return self.post(uri, data)

    def dislike_note(self, note_id: str):
        uri = "/api/sns/web/v1/note/dislike"
        data = {
            "note_oid": note_id
        }
        return self.post(uri, data)

    def dislike_comment(self, comment_id: str):
        uri = "/api/sns/web/v1/comment/dislike"
        data = {
            "note_oid": comment_id
        }
        return self.post(uri, data)

    def get_qrcode(self):
        """create qrcode, you can trasform response url to qrcode

        :return:
        {
            "qr_id": "87323168**",
            "code": "280148",
            "url": "xhsdiscover://**",
            "multi_flag": 0
        }
        """
        uri = "/api/sns/web/v1/login/qrcode/create"
        data = {}
        return self.post(uri, data)

    def check_qrcode(self, qr_id: str, code: str):
        uri = "/api/sns/web/v1/login/qrcode/status"
        params = {
            "qr_id": qr_id,
            "code": code
        }
        return self.get(uri, params)

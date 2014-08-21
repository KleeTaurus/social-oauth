# -*- coding: utf-8 -*-

from socialoauth.sites.base import OAuth2


class GitHub(OAuth2):
    AUTHORIZE_URL = 'https://github.com/login/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token'

    def build_api_url(self, url):
        return url

    def build_api_data(self, **kwargs):
        data = {
            'access_token': self.access_token
        }
        data.update(kwargs)
        return data

    def http_add_header(self, req):
        req.add_header('Accept', 'application/json')

    def parse_token_response(self, res):
        self.access_token = res['access_token']
        self.expires_in = None
        self.refresh_token = None

        res = self.api_call_get(
            'https://api.github.com/user',
        )

        self.name = res['login']
        self.uid = res['id']
        self.avatar = res['avatar_url']
        self.avatar_large = res['avatar_url']

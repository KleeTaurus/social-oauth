# -*- coding: utf-8 -*-

from urllib import urlencode
import urllib2
import json
from functools import wraps

from socialoauth.exception import SocialAPIError
from socialoauth import socialsites

HTTP_TIMEOUT = 10


def _http_error_handler(func):
    @wraps(func)
    def deco(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except urllib2.HTTPError as e:
            raise SocialAPIError(self.site_name, e.url, e.code, e.reason, e.read())
        except urllib2.URLError as e:
            raise SocialAPIError(self.site_name, None, None, e.reason, e.reason)
    return deco


class OAuth2(object):
    """
    Base OAuth2 class, Sub class must define the following settings:

    AUTHORIZE_URL    - Asking user to authorize and get token
    ACCESS_TOKEN_URL - Get authorized access token

    And the bellowing should define in settings file

    REDIRECT_URI     - The url after user authorized and redirect to
    CLIENT_ID        - Your client id for the social site
    CLIENT_SECRET    - Your client secret for the social site

    Also, If the Website needs scope parameters, your should add it too.

    SCOPE            - A list type contains some scopes

    Details see: http://tools.ietf.org/html/rfc6749



    SubClass MUST Implement the following three methods:

    build_api_url(self, url)
    build_api_data(self, **kwargs)
    parse_token_response(self, res)
    """

    def __init__(self):
        """Get config from settings"""
        key = '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
        configs = socialsites.load_config(key)
        for k, v in configs.iteritems():
            setattr(self, k, v)


    @_http_error_handler
    def http_get(self, url, data, parse=True):
        req = urllib2.Request('%s?%s' % (url, urlencode(data)))
        self.http_add_header(req)
        res = urllib2.urlopen(req, timeout=HTTP_TIMEOUT).read()
        if parse:
            return json.loads(res)
        return res


    @_http_error_handler
    def http_post(self, url, data, parse=True):
        req = urllib2.Request(url, data=urlencode(data))
        self.http_add_header(req)
        res = urllib2.urlopen(req, timeout=HTTP_TIMEOUT).read()
        if parse:
            return json.loads(res)
        return res


    def http_add_header(self, req):
        """Sub class rewiter this function If it's necessary to add headers"""
        pass



    @property
    def authorize_url(self):
        """Rewrite this property method If there are more arguments
        need  attach to the url. Like bellow:

            class NewSubClass(OAuth2):
                @property
                def authorize_url(self):
                    url = super(NewSubClass, self).authorize_url
                    url += '&blabla'
                    return url
        """

        url = "%s?client_id=%s&response_type=code&redirect_uri=%s" % (
            self.AUTHORIZE_URL, self.CLIENT_ID, self.REDIRECT_URI
        )

        if getattr(self, 'SCOPE', None) is not None:
            url = '%s&scope=%s' % (url, '+'.join(self.SCOPE))

        return url



    def get_access_token(self, code, method='POST', parse=True):
        """parse is True means that the api return a json string. 
        So, the result will be parsed by json library.
        Most sites will follow this rule, return a json string.
        But some sites (e.g. Tencent), Will return an non json string,
        This sites MUST set parse=False when call this method,
        And handle the result by themselves.

        This method Maybe raise SocialAPIError.
        Application MUST try this Exception.
        """

        data = {
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'redirect_uri': self.REDIRECT_URI,
            'code': code,
            'grant_type': 'authorization_code'
        }


        if method == 'POST':
            res = self.http_post(self.ACCESS_TOKEN_URL, data, parse=parse)
        else:
            res = self.http_get(self.ACCESS_TOKEN_URL, data, parse=parse)

        self.parse_token_response(res)



    def api_call_get(self, url=None, **kwargs):
        url = self.build_api_url(url)
        data = self.build_api_data(**kwargs)
        return self.http_get(url, data)

    def api_call_post(self, url=None, **kwargs):
        url = self.build_api_url(url)
        data = self.build_api_data(**kwargs)
        return self.http_post(url, data)




    def parse_token_response(self, res):
        """
        Subclass MUST implement this method
        And set the following attributes:

        access_token,
        uid,
        name,
        avatar,
        """
        raise NotImplementedError


    def build_api_url(self, url):
        raise NotImplementedError


    def build_api_data(self, **kwargs):
        raise NotImplementedError


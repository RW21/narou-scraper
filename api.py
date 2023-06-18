from urllib.request import build_opener, HTTPCookieProcessor, Request
import urllib
# Wrapper which does retries
from time import sleep
from http.cookiejar import Cookie, CookieJar
from logger import logger


def request_with_retries(url, max_attempts=5):
    attempts = 0

    success = False
    last_exception = None

    # Create a cookie for the over18 check
    c = Cookie(
        version=0,
        name='over18',
        value='yes',
        port=None,
        port_specified=False,
        domain='.syosetu.com',
        domain_specified=True,
        domain_initial_dot=True,
        path='/',
        path_specified=True,
        secure=False,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={},
        rfc2109=False,
    )

    cj = CookieJar()
    cj.set_cookie(c)

    opener = build_opener(HTTPCookieProcessor(cj))

    while not success and attempts < max_attempts:
        try:
            response = opener.open(url)
            success = True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.warning(f'404 error for {url}')
                return None

            # no need to wait if http error
            last_exception = e
            attempts += 1

        except Exception as e:
            last_exception = e
            # If the request failed, increment the number of attempts
            attempts += 1
            logger.warning(f'Failed to request {url}, retrying...')
            sleep(1)

    if success:
        # Do something with the response
        return response.read()
    else:
        # If the request failed after the maximum number of attempts, print an error message
        logger.error('Error: Unable to complete the request ' + url)

        if isinstance(last_exception, urllib.error.HTTPError):
            logger.warning(f'HTTP Error: {last_exception.code}')
        else:
            logger.error(last_exception)
            raise last_exception

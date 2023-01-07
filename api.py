import urllib.error
import urllib.request
# Wrapper which does retries
from time import sleep

from logger import logger


def request_with_retries(url, max_attempts=5):
    attempts = 0

    success = False
    last_exception = None

    while not success and attempts < max_attempts:
        try:
            response = urllib.request.urlopen(url)
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

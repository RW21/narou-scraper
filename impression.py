import re
import urllib.request
from datetime import datetime
from typing import Generator

from bs4 import BeautifulSoup

from logger import logger
from models import NovelImpressionModel


def extract_impressions(impression_soup: BeautifulSoup) -> list[NovelImpressionModel]:
    impressions = []

    comments = impression_soup.find_all(class_='waku')
    if comments is None:
        return impressions

    datetime_regex_pattern = re.compile(r"\d{4}年 \d{2}月\d{2}日 \d{2}時\d{2}分")

    nid = impression_soup.find('div', id="contents_main").find('a')['href'].split('/')[-2]

    for comment in comments:
        comment_info = comment.find('div', class_='comment_info comment_authorbox')
        try:
            user_id = comment_info.find('a')['href'].split('/')[-2]
            user_id = int(user_id)
        except (ValueError, TypeError):
            # If user has left, it will be none
            # If user is not logged in, also will be none
            user_id = None

        comment_info_text = comment_info.find('div').text
        # extract datetime with regex
        match = datetime_regex_pattern.search(comment_info_text)
        created_datetime = match.group(0)
        created_datetime = datetime.strptime(created_datetime, "%Y年 %m月%d日 %H時%M分")

        try:
            on_part = comment.find('span', class_='no_posted_impression').text
        except AttributeError:
            on_part = None

        impression = NovelImpressionModel(
            nid=nid,
            user_id=user_id,
            created_datetime=created_datetime,
            on_part=on_part
        )

        # Get content of comments
        for comment_header in comment.find_all('div', class_='comment_h2'):
            comment_content = comment_header.find_next_sibling('div').text
            if comment_header.text == '一言':
                impression.impression_hitokoto = comment_content
            elif comment_header.text == '良い点':
                impression.impression_yoiten = comment_content
            elif comment_header.text == '気になる点':
                impression.impression_kininaruten = comment_content

        impressions.append(impression)

    return impressions


def impression_soup_generator(impression_id: int, is_r18=False) -> Generator[BeautifulSoup, None, None]:
    """
    Use generator to save memory
    """
    url = f'https://novelcom.syosetu.com/impression/list/ncode/{impression_id}/'
    if is_r18:
        url = f'https://novelcom18.syosetu.com/impression/list/ncode/{impression_id}/'

    response = urllib.request.urlopen(url)
    first_impression_soup = response.read()
    first_impression_soup = BeautifulSoup(first_impression_soup, 'html.parser')

    # determine number of pages
    nav = first_impression_soup.find(class_='naviall')

    # empty navbar
    if nav is None:
        # check if there is a single impression
        if first_impression_soup.find(class_='comment') is not None:
            max_page = 1
        else:
            return
    else:
        tags = nav.find_all('a')
        # get largest number in navbar
        max_page = max((int(re.search(r'\d+', tag.text).group(0)) for tag in tags if re.search(r'\d+', tag.text)),
                       default=-1)

    yield first_impression_soup

    # get all impression pages
    for page in range(2, max_page + 1):
        logger.info(f'Mass impression; Getting impression page {page} of {max_page}')
        url = f'https://novelcom.syosetu.com/impression/list/ncode/{impression_id}/?p={page}'
        response = urllib.request.urlopen(url)
        impression_page = response.read()
        impression_page = BeautifulSoup(impression_page, 'html.parser')
        yield impression_page


def get_impression_id(detail_page_soup: BeautifulSoup) -> int:
    url = detail_page_soup.select_one('#head_nav').select('a')[2]['href']
    return int(url.split('/')[-2])
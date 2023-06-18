import os
import re
import sqlite3
import urllib.request
from datetime import datetime
from timeit import default_timer
from typing import Optional, Generator

import yaml
from bs4 import BeautifulSoup

from api import request_with_retries
from args import script_args
from logger import logger
from models import NovelInfoModel, NovelImpressionModel, db_name, initialize_db
from nid import Nid


def get_detail_page_soup(nid: str, is_r18=False) -> Optional[BeautifulSoup]:
    url = f'https://ncode.syosetu.com/novelview/infotop/ncode/{nid}/'

    if is_r18:
        url = f'https://novel18.syosetu.com/novelview/infotop/ncode/{nid}/'

    response = request_with_retries(url)
    if response is None:
        return None

    soup = BeautifulSoup(response, 'html.parser')
    return soup


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


# 179,232件 -> 179232
def extract_件_string(s: str) -> int:
    return int(s[:-1].replace(',', ''))


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


def extract_novel_info(detail_page_soup: BeautifulSoup) -> NovelInfoModel:
    """
    Extracts novel info from detail page soup.
    Uses scraped website instead of api to retrieve more information.
    """
    rows = detail_page_soup.find(id='noveltable2').find_all('tr')

    try:
        keywords = detail_page_soup.find('th', text='キーワード').find_next('td').text.replace('\n', ' ').replace("\xa0", '')
    except AttributeError:
        keywords = ''

    nid = detail_page_soup.find('p', title='Nコード').text

    try:
        user_id = detail_page_soup.find('ul', class_='undernavi').find('a')['href'].split('/')[-2]
    except TypeError:
        # Use api to get user id
        # Sometimes there is no hyperlink to user page
        res = request_with_retries("https://api.syosetu.com/novelapi/api/?ncode={}&of=u".format(nid))
        data = yaml.safe_load(res)
        print(data)
        user_id = int(data[1]['userid'])

    cell_to_field = {
        '掲載日': 'released_datetime',
        '最新部分掲載日': 'updated_datetime',
        '感想': 'impression_count',
        '総合評価': 'total_review_point',
        '評価ポイント': 'review_point',
        '文字数': 'character_count',
        'ブックマーク登録': 'bookmark_count',
        'レビュー': 'review_count',
    }

    res = {
        'released_datetime': None,
        'updated_datetime': None,
        'impression_count': None,
        'total_review_point': None,
        'review_point': None,
        'character_count': None,
        'bookmark_count': None,
        'review_count': None,
    }

    for row in rows:
        cell_header = row.find('th').text
        cell_content = row.find('td').text
        field_name = cell_to_field.get(cell_header)

        if field_name:
            if field_name in ['released_datetime', 'updated_datetime']:
                res[field_name] = datetime.strptime(cell_content, '%Y年 %m月%d日 %H時%M分')
            elif field_name in ['impression_count', 'review_count', 'bookmark_count']:
                cell_content = cell_content.split('\n')
                for c in cell_content:
                    if c:
                        cell_content = c
                        break
                res[field_name] = extract_件_string(cell_content)
            elif field_name in ['total_review_point', 'review_point']:
                try:
                    res[field_name] = int(cell_content.replace('pt', '').replace(',', ''))
                # when private
                except ValueError:
                    res[field_name] = None
            elif field_name == 'character_count':
                res[field_name] = int(cell_content[:-2].replace(',', ''))

    novel_info = NovelInfoModel(
        title=detail_page_soup.select_one('h1 a').text,
        summary=detail_page_soup.find('td', class_='ex').text,
        genre=detail_page_soup.find('th', text='ジャンル').find_next('td').text,
        keywords=[kw for kw in keywords.split(' ') if kw.strip()],
        impression_id=get_impression_id(detail_page_soup),
        nid=nid,

        released_datetime=res.get('released_datetime'),
        last_updated_datetime=res.get('updated_datetime'),

        impression_count=res.get('impression_count'),
        review_count=res.get('review_count'),
        bookmark_count=res.get('bookmark_count'),
        total_review_point=res.get('total_review_point'),
        review_point=res.get('review_point'),
        character_count=res.get('character_count'),

        user_id=user_id
    )

    return novel_info


def query_nids_between_time(start_inc: datetime, end_inc: datetime) -> list[str]:
    # convert datetime to uinix timestamp
    start_inc = int(start_inc.timestamp())
    end_inc = int(end_inc.timestamp())

    request_url = f'https://api.syosetu.com/novelapi/api/?lim=500&of=n&lastup={start_inc}-{end_inc}'
    response_data = urllib.request.urlopen(request_url).read()

    data = yaml.safe_load(response_data.decode('utf-8'))
    total_count = int(data[0]['allcount'])

    if total_count == 0:
        return []

    nids = []

    for novel in data[1:]:
        nids.append(novel['ncode'])

    if total_count > 500:
        curr_retrieved = 500

        while curr_retrieved < total_count:
            request_url = f'https://api.syosetu.com/novelapi/api/?lim=500&of=n&lastup={start_inc}-{end_inc}&st={curr_retrieved + 1}'
            response_data = urllib.request.urlopen(request_url).read()

            data = yaml.safe_load(response_data.decode('utf-8'))
            for novel in data[1:]:
                nids.append(novel['ncode'])

            curr_retrieved += 500

    return nids


def is_error_novel(supposed_detail_page: BeautifulSoup) -> bool:
    """
    Checks if the detail page is a deleted novel.
    """
    return supposed_detail_page.find('title').text == 'エラー'


def is_r18_novel(supposed_detail_page: BeautifulSoup) -> bool:
    return supposed_detail_page.find('title').text == '年齢確認'


def scrape(nid: str, connection: sqlite3.Connection):
    soup = get_detail_page_soup(nid)

    if soup is None or is_error_novel(soup):
        logger.info(f'Novel {nid} returned error page')
        return

    is_r18 = is_r18_novel(soup)

    cursor = connection.cursor()

    if is_r18:
        cursor.execute("""
        INSERT OR REPLACE INTO scrape_history (nid, r18) VALUES (?, ?)
        """,
                       (nid, is_r18))
        connection.commit()

    if script_args.skip_r18 and is_r18:
        logger.info(f'Skip R18 novel {nid}')
        return

    if is_r18:
        soup = get_detail_page_soup(nid, is_r18=True)

    novel_info = extract_novel_info(soup)
    novel_info.sqlite_save(cursor)

    for impression_soup in impression_soup_generator(novel_info.impression_id, is_r18=is_r18):
        impressions = extract_impressions(impression_soup)
        for impression in impressions:
            impression.sqlite_save(cursor)

    cursor.execute(
        """
        INSERT OR REPLACE INTO scrape_history (nid, last_info_scrape_datetime, last_impression_scrape_datetime) VALUES (?, ?, ?)
        """,
        (nid, datetime.now(), datetime.now())
    )
    connection.commit()


if __name__ == '__main__':

    if script_args.reset:
        try:
            os.remove(db_name)
        except FileNotFoundError:
            logger.debug("No db file to delete")
            pass
        logger.info('Reset scrape history')
        exit()

    logger.info(f'Starting scraping from {script_args.start_from} to {script_args.end_with}')

    initialize_db()
    conn = sqlite3.connect(db_name)

    start_from, end_with = Nid(script_args.start_from), Nid(script_args.end_with)

    if start_from > end_with:
        gen = start_from.generate_nids(reverse=True)
    else:
        gen = start_from.generate_nids()

    for nid in gen:

        start_time = default_timer()
        logger.info(f"Start scraping {nid}")
        try:
            scrape(nid, conn)
        except Exception as e:
            logger.error(f"Failed {nid} {e}")
            raise e

        end_time = default_timer()
        logger.info(f"Scraped {nid} {end_time - start_time}s elapsed")

        if nid == script_args.end_with:
            break

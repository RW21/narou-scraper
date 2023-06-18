import os
import sqlite3
import urllib.request
from datetime import datetime
from timeit import default_timer
from functools import wraps

import yaml
from bs4 import BeautifulSoup

from args import script_args
from impressions import extract_impressions, impression_soup_generator
from logger import logger
from models import db_name, initialize_db
from nid import Nid
from novel_info import extract_novel_info, get_detail_page_soup


def timing_decorator(func):
    @wraps(func)
    def wrapper(nid, conn):
        start_time = default_timer()
        logger.info(f"Start scraping {nid}")
        try:
            result = func(nid, conn)
        except Exception as e:
            logger.error(f"Failed {nid} {e}")
            raise
        end_time = default_timer()
        logger.info(f"Scraped {nid} {end_time - start_time}s elapsed")
        return result
    return wrapper


# 179,232件 -> 179232
def extract_件_string(s: str) -> int:
    return int(s[:-1].replace(',', ''))


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


@timing_decorator
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

    if script_args.nid:
        scrape(Nid(script_args.nid).id, conn)
        exit()

    start_from, end_with = Nid(script_args.start_from), Nid(script_args.end_with)

    if start_from > end_with:
        gen = start_from.generate_nids(reverse=True)
    else:
        gen = start_from.generate_nids()

    for nid in gen:
        scrape(nid, conn)

        if nid == script_args.end_with:
            break

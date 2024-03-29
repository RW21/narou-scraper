import os
import sqlite3
import urllib.request
from datetime import datetime
from functools import wraps
from timeit import default_timer

import yaml

from args import script_args
from content import novel_content_generator
from impression import extract_impressions, impression_soup_generator
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


@timing_decorator
def scrape(nid: str, connection: sqlite3.Connection):
    soup = get_detail_page_soup(nid)

    is_error = False
    if soup is None:
        is_error = True

    if soup is not None and soup.find('title').text == 'エラー':
        is_error = True

    if is_error:
        logger.info(f'Novel {nid} returned error page')
        return

    cursor = connection.cursor()

    is_r18 = bool(soup.find('span', {'id': 'age_limit'}))

    cursor.execute("SELECT 1 FROM scrape_history WHERE nid = ?", (nid,))
    exists = cursor.fetchone()

    if exists is None:
        cursor.execute(
            """
            INSERT INTO scrape_history (nid, r18) VALUES (?, ?)
            """,
            (nid, is_r18)
        )

    if script_args.skip_r18 and is_r18:
        logger.info(f'Skip R18 novel {nid}')
        return

    cursor.execute("SELECT last_impression_scrape_datetime, last_content_scrape_datetime FROM scrape_history WHERE nid = ?", (nid,))
    result = cursor.fetchone()

    already_scraped_impression, already_scraped_content = map(bool, result)
    will_skip_content = (script_args.skip_existing and already_scraped_content) or script_args.skip_content
    will_skip_impression = (script_args.skip_existing and already_scraped_impression) or script_args.skip_impression

    if will_skip_content:
        logger.info(f'Skip content scraping for {nid}')
    if will_skip_impression:
        logger.info(f'Skip impression scraping for {nid}')

    novel_info = extract_novel_info(soup)
    novel_info.sqlite_save(cursor)

    cursor.execute(
        """
        UPDATE scrape_history SET last_info_scrape_datetime = ? WHERE nid = ?
        """,
        (datetime.now(), nid)
    )

    if not will_skip_impression:
        for impression_soup in impression_soup_generator(novel_info.impression_id, is_r18=is_r18):
            impressions = extract_impressions(impression_soup)
            for impression in impressions:
                impression.sqlite_save(cursor)

        # Here we don't need to check for existence because we know row for nid must exist at this point
        cursor.execute(
            """
            UPDATE scrape_history SET last_impression_scrape_datetime = ? WHERE nid = ?
            """,
            (datetime.now(), nid)
        )

    if not will_skip_content:
        for content in novel_content_generator(nid, novel_info, is_r18=is_r18):
            content.sqlite_save(cursor)

        # Similarly, updating without checking for existence
        cursor.execute(
            """
            UPDATE scrape_history SET last_content_scrape_datetime = ? WHERE nid = ?
            """,
            (datetime.now(), nid)
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

    initialize_db()
    conn = sqlite3.connect(db_name)

    if script_args.nid:
        scrape(Nid(script_args.nid).id, conn)
        exit()

    start_from, end_with = Nid(script_args.start_from), Nid(script_args.end_with)
    logger.info(f'Starting scraping from {script_args.start_from} to {script_args.end_with}')

    if start_from > end_with:
        gen = start_from.generate_nids(reverse=True)
    else:
        gen = start_from.generate_nids()

    for nid in gen:
        scrape(nid, conn)

        if nid == script_args.end_with:
            break

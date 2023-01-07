import sqlite3

import yaml

from api import request_with_retries
from logger import logger
from nid import generate_nids


def scrape_novel_info_from(start_from):
    request_url = f'https://api.syosetu.com/novelapi/api/?lim=500&of=n-gf&order=ncodedesc&st={start_from}'
    response_data = request_with_retries(request_url)
    data = yaml.safe_load(response_data.decode('utf-8'))
    conn = sqlite3.connect('novels.db')
    cur = conn.cursor()

    for novel in data[1:]:
        cur.execute('INSERT OR IGNORE INTO scrape_history (nid, novel_creation_datetime) VALUES (?, ?)',
                    (novel['ncode'], novel['general_firstup']))

    conn.commit()


def get_total_novel_count():
    request_url = f'https://api.syosetu.com/novelapi/api/?lim=1&of=n-gf'
    response_data = request_with_retries(request_url)
    data = yaml.safe_load(response_data.decode('utf-8'))
    return int(data[0]['allcount'])


def scrape_all_novels():
    total_novel_count = get_total_novel_count()
    logger.debug(f'Total novel count: {total_novel_count}')
    start_from = 0
    while start_from < total_novel_count:
        scrape_novel_info_from(start_from)
        # only increase by 450 to avoid missing any
        start_from += 450
        logger.info(f'Scraped {start_from} / {total_novel_count}')


def scrape_backwards(nid_from):
    gen = generate_nids(nid_from, reverse=True)

    request_url = f'https://api.syosetu.com/novelapi/api/?lim=500&of=n-gf&ncode={nid_from}'
    response_data = request_with_retries(request_url)
    data = yaml.safe_load(response_data.decode('utf-8'))
    conn = sqlite3.connect('novels.db')
    cur = conn.cursor()

    for novel in data[1:]:
        cur.execute('INSERT OR IGNORE INTO scrape_history (nid, novel_creation_datetime) VALUES (?, ?)',
                    (novel['ncode'], novel['general_firstup']))

    conn.commit()

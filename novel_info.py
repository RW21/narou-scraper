from datetime import datetime
from typing import Optional

import yaml
from bs4 import BeautifulSoup

from api import request_with_retries
from impression import get_impression_id
from models import NovelInfoModel


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
                res[field_name] = int(cell_content[:-1].replace(',', ''))
            elif field_name in ['total_review_point', 'review_point']:
                try:
                    res[field_name] = int(cell_content.replace('pt', '').replace(',', ''))
                # when private
                except ValueError:
                    res[field_name] = None
            elif field_name == 'character_count':
                res[field_name] = int(cell_content[:-2].replace(',', ''))

    # r18 won't have genre?
    try:
        genre = detail_page_soup.find('th', text='ジャンル').find_next('td').text
    except AttributeError:
        genre = ''

    novel_info = NovelInfoModel(
        title=detail_page_soup.select_one('h1 a').text,
        summary=detail_page_soup.find('td', class_='ex').text,
        genre=genre,
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


def get_detail_page_soup(nid: str, is_r18=False) -> Optional[BeautifulSoup]:
    url = f'https://ncode.syosetu.com/novelview/infotop/ncode/{nid}/'

    if is_r18:
        url = f'https://novel18.syosetu.com/novelview/infotop/ncode/{nid}/'

    response = request_with_retries(url)
    if response is None:
        return None

    soup = BeautifulSoup(response, 'html.parser')
    return soup

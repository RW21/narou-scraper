import unicodedata
from datetime import datetime
from typing import Generator, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from api import request_with_retries
from logger import logger
from models import NovelContentModel, NovelInfoModel


def get_content_string(content_page_soup) -> (Optional[str], str, Optional[str]):
    def get_as_str(soup):
        if soup is None:
            return None
        paragraphs = []
        for p in soup:
            if p.get('id', '').startswith('L'):
                text = p.get_text(strip=True)
                if text == '' or text == '\n':
                    paragraphs.append('\n')
                else:
                    paragraphs.append(text)

        return '\n'.join(paragraphs)

    pre = get_as_str(content_page_soup.select("#novel_p p"))
    content = get_as_str(content_page_soup.select("#novel_honbun p"))
    post = get_as_str(content_page_soup.select("#novel_a p"))

    return pre, content, post


def novel_content_generator(nid: str, info: NovelInfoModel, is_r18=False) -> Generator[NovelContentModel, None, None]:
    """
    Use generator to save memory
    """

    url = f'https://ncode.syosetu.com/{nid}/'
    if is_r18:
        url = f'https://novel18.syosetu.com/{nid}/'

    response = request_with_retries(url)
    list_page_soup = BeautifulSoup(response, 'html.parser')

    chapter_title = None

    num_of_pages = len(list_page_soup.select('.index_box dl.novel_sublist2'))
    count = 0

    # This is when there is no table of content
    if list_page_soup.select_one('.index_box') is None:
        content_page_soup = list_page_soup
        get_content_string(content_page_soup)
        pre, content, post = get_content_string(content_page_soup)

        count += 1
        novel_content = NovelContentModel(
            nid=nid,
            title=info.title,
            last_updated_datetime=info.last_updated_datetime,
            created_datetime=info.released_datetime,
            part=chapter_title,
            content=content,
            pre_content=pre,
            post_content=post,
            page_num=count  # an assumption
        )
        yield novel_content
        return

    for tag in list_page_soup.select_one('.index_box').children:
        if tag.name == 'div' and 'chapter_title' in tag.get('class', []):
            chapter_title = tag.text.strip()
            chapter_title = unicodedata.normalize('NFKD', chapter_title)
        elif tag.name == 'dl' and 'novel_sublist2' in tag.get('class', []):
            url = urljoin(url, tag.dd.a['href'])
            title = tag.dd.a.text.strip()

            created_str = tag.dt.text.split("（")[0].strip()
            created = datetime.strptime(created_str, '%Y/%m/%d %H:%M')
            update_span = tag.dt.span
            if update_span is not None:
                last_update_str = ' '.join(update_span['title'].split(" ")[:2])
                last_update = datetime.strptime(last_update_str, '%Y/%m/%d %H:%M')
            else:
                last_update = None

            response = request_with_retries(url)
            content_page_soup = BeautifulSoup(response, 'html.parser')
            pre, content, post = get_content_string(content_page_soup)

            count += 1
            novel_content = NovelContentModel(
                nid=nid,
                title=title,
                last_updated_datetime=last_update,
                created_datetime=created,
                part=chapter_title,
                content=content,
                pre_content=pre,
                post_content=post,
                page_num=count  # an assumption
            )
            logger.info(f'[{count}/{num_of_pages}] {nid}')
            yield novel_content

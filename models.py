import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union, List, Optional

from logger import logger

db_name = 'novels.db'


class ModelBaseClass:
    # nid must be passed on init
    def __post_init__(self):
        if hasattr(self, 'nid'):
            self.nid = self.nid.upper()


@dataclass
class NovelInfoModel(ModelBaseClass):
    title: str
    summary: str
    keywords: List[str]
    genre: str
    released_datetime: datetime

    impression_count: int
    review_count: int
    bookmark_count: int
    character_count: int

    user_id: int
    nid: str
    impression_id: int

    last_updated_datetime: Union[datetime, None] = field(default=None)
    # 総合評価
    total_review_point: Union[int, None] = field(default=None)
    # 評価ポイント
    review_point: Union[int, None] = field(default=None)

    def sqlite_save(self, cursor: sqlite3.Cursor):
        cursor.execute(
            'INSERT OR REPLACE INTO novel_info VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (self.nid, self.title, self.summary, ','.join(self.keywords), self.genre, self.released_datetime,
             self.last_updated_datetime, self.impression_count, self.review_count, self.bookmark_count,
             self.total_review_point, self.review_point, self.character_count, self.user_id, self.impression_id))


def create_novel_info_table(cur: sqlite3.Cursor):
    cur.execute(
        'CREATE TABLE IF NOT EXISTS novel_info ('
        'nid VARCHAR(7),'
        'title text,'
        'summary text,'
        'keywords text,'
        'genre text,'
        'released_datetime DATETIME,'
        'last_updated_datetime DATETIME NULL,'
        'impression_count integer,'
        'review_count integer,'
        'bookmark_count integer,'
        'total_review_point integer NULL,'
        'review_point integer NULL,'
        'character_count integer,'
        'user_id integer,'
        'impression_id integer,'
        'PRIMARY KEY (nid))')


@dataclass
class NovelContentModel(ModelBaseClass):
    nid: int
    content: str
    created_datetime: datetime
    last_updated_datetime: datetime
    part: Optional[str] = field(default=None)

    class Meta:
        db_table = 'novel_content'

    def sqlite_save(self, cursor: sqlite3.Cursor):
        cursor.execute(
            f'INSERT OR REPLACE INTO {self.Meta.db_table} VALUES (?,?,?,?,?)',
            (self.nid, self.content, self.created_datetime, self.last_updated_datetime, self.part))


def create_novel_content_table(cur: sqlite3.Cursor):
    cur.execute(
        f'CREATE TABLE IF NOT EXISTS novel_content ('
        'nid VARCHAR(7),'
        'content text,'
        'created_datetime DATETIME,'
        'last_updated_datetime DATETIME,'
        'part text NULL,'
        'PRIMARY KEY (nid),'
        'FOREIGN KEY (nid) REFERENCES novel_info(nid))'
    )


@dataclass
class NovelImpressionModel(ModelBaseClass):
    nid: int

    created_datetime: datetime

    on_part: Union[str, None] = field(default=None)

    user_id: Union[int, None] = field(default=None)
    impression_hitokoto: Union[str, None] = field(default=None)
    impression_yoiten: Union[str, None] = field(default=None)
    impression_kininaruten: Union[str, None] = field(default=None)

    class Meta:
        db_table = 'novel_impression'

    def sqlite_save(self, cursor: sqlite3.Cursor):
        cursor.execute(
            f'INSERT OR REPLACE INTO {self.Meta.db_table} VALUES (?,?,?,?,?,?,?)',
            (self.nid, self.user_id, self.created_datetime, self.impression_hitokoto, self.impression_yoiten,
             self.impression_kininaruten, self.on_part))


def create_novel_impression_table(cur: sqlite3.Cursor):
    cur.execute(
        f'CREATE TABLE IF NOT EXISTS novel_impression ('
        'nid VARCHAR(7),'
        'user_id integer NULL,'
        'created_datetime DATETIME,'
        'impression_hitokoto text NULL,'
        'impression_yoiten text NULL,'
        'impression_kininaruten text NULL,'
        'on_part text NULL,'
        'PRIMARY KEY (nid, created_datetime),'
        'FOREIGN KEY (nid) REFERENCES novel_info(nid))'
    )


def initialize_db():
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    cur.execute("""
CREATE TABLE IF NOT EXISTS scrape_history(
nid VARCHAR(7) PRIMARY KEY,
last_info_scrape_datetime DATETIME NULL,
last_impression_scrape_datetime DATETIME NULL,
last_content_scrape_datetime DATETIME NULL,
r18 BOOLEAN,
FOREIGN KEY (nid) REFERENCES novel_info(nid)
)""")

    create_novel_info_table(cur)
    create_novel_impression_table(cur)
    create_novel_content_table(cur)

    conn.commit()
    conn.close()
    logger.debug('Initialized database')

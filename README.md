# narou-scraper
```
usage: main.py [-h] [--reset] [--start-from START_FROM] [--end-with END_WITH]
               [--log-file LOG_FILE] [--skip-r18 SKIP_R18] [--nid NID]
               [--skip-content] [--skip-impression]

    This script will scrape narou novels.
    It will save the files in a sqlite database named novels.db.
    See models.py for the fields it can scrape.
    
    Example Usage:
    1. To scrape a range of novels, specify the starting and ending nids:
    python3 main.py --start-from N1955HZ --end-with N1955HZ 

    2. To scrape a specific novel, specify its nid:
    python3 main.py --nid n6879ig 

    3. To skip scraping R18 novels:
    python3 main.py --skip-r18 true 

    4. To specify the location of the log file:
    python3 main.py --log-file ./logs/scrape.log 
    
    このスクリプトはなろう小説をスクレイピングします。
    novels.dbという名前のsqliteデータベースに保存されます。
    取得できるフィールドは、models.pyを参照してください。
    
    使用例:
    1. 小説の範囲を指定し、スクレイピングするには、開始と終了のnidを設定します:
    python3 main.py --start-from N1955HZ --end-with N1955HZ 

    2. 特定の小説をスクレイピングするには、そのnidを指定します:
    python3 main.py --nid n6879ig 

    3. R18の小説のスクレイピングをスキップするには:
    python3 main.py --skip-r18 true 

    4. ログファイルの場所を指定するには:
    python3 main.py --log-file ./logs/scrape.log 
    
    

optional arguments:
  -h, --help            show this help message and exit
  --reset               Reset scrape history (default: False)
  --start-from START_FROM
                        The starting nid, inclusive (default: N9999ZZ)
  --end-with END_WITH   The ending nid, inclusive (default: N0000AA)
  --log-file LOG_FILE   Location of log file (default: scrape.log)
  --skip-r18 SKIP_R18   Whether to skip R18 novels (default: False)
  --nid NID             The nid to scrape, if this is set, --start-from and --end-with are ignored
  --skip-content        When this is enabled, it will skip scraping novel content (default: False)
  --skip-impression     When this is enabled, it will skip scraping novel impression(default: False)

    

```
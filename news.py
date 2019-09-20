import pymysql
import sys,schedule,time
from bs4 import BeautifulSoup
import requests
from lxml import etree
import re
from urllib.parse import urlparse, urlunparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import crawler.util as util
import json


def crawl_title(conn, browser):
    cursor = conn.cursor()
    category_sql = 'select id,url,xpath,charset from category where category_state = 0'
    cursor.execute(category_sql)
    categories = cursor.fetchall()
    for category in categories:
        url = category[1]
        xpath = category[2]
        charset = category[3]
        print('\n时间：{}，新闻分类：{}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), url))
        browser.get(url)
        html = browser.page_source
        et = etree.HTML(html)
        xpath_res = et.xpath(xpath)
        div = xpath_res[0]
        div = etree.tostring(div, encoding=charset, pretty_print=True, method='html')
        div = div.decode(charset)
        soup = BeautifulSoup(div, features='html.parser')
        news = soup.find_all('a')
        invalid_title = r'^(首页|下一页|上一页|确定|末页|尾页|更多(>>)?|\d+)$'
        invalid_href = r'^(\.\/|\.\.\/)((\.\.\/)+)?$'
        sql_input = []
        for n in news:
            href = n['href']
            title = n.get('title')
            if not title:
                title = n.string
            if re.match(invalid_title, title) or re.match(invalid_href, href):
                continue
            href = util.format(url, href)[util.FORMATTED_URL_ABSOLUTE]
            sql_input.append((href, title, category[0]))
        category_insert_sql = 'insert ignore into news (url,title,category_id) values (%s,%s,%s)'
        print('抓取的结果：', sql_input)
        cursor.executemany(category_insert_sql, sql_input)
        conn.commit()


def crawl_text(conn, browser):
    cursor = conn.cursor()
    news_sql = '''
        select n.id,n.url,n.category_id,c.xpath_text,c.charset 
        from news n 
        join category c on n.category_id = c.id 
        where n.news_state = 0 and n.has_crawl = 0 and c.xpath_text is not null and n.id = 98506 limit 1
        '''
    keyword_sql = '''
        select k.reg_exp 
        from keyword k 
        join web_keyword wk on wk.keyword_id = k.id 
        where wk.category_id = %s
    '''
    text_sql = '''
    insert into texts (news_id,text,keyword_result) values (%s,%s,%s)
    '''
    news_update_sql = '''
    update news set has_crawl = '1' where id = %s
    '''
    cursor.execute(news_sql)
    news = cursor.fetchall()
    c_ks = dict()
    for new in news:
        news_id, url, category_id, xpath, charset = new[0], new[1], new[2], new[3], new[4]
        print('url:{}, xpath:{}, category_id:{}, charset:{}'.format(url, xpath, category_id, charset))
        if category_id not in c_ks:
            cursor.execute(keyword_sql, category_id)
            keywords = cursor.fetchall()
            c_ks[category_id] = [k[0] for k in keywords]
        browser.get(url)
        html = browser.find_element_by_xpath(xpath)
        text = html.get_attribute('innerHTML')
        # text = html.text.strip()
        links = html.find_elements_by_tag_name('a')
        for link in links:
            href = link.get_attribute('href')
            if re.match('.*\.xls|xlsx|doc|docx|pdf', href):
                util.download(util.format(url, href), '')
        print('text:{}'.format(text))
        regexps = c_ks[category_id]
        results = []
        for regexp in regexps:
            regexp = regexp[1:]
            idx = regexp.rfind('/')
            # modifier = regexp[idx+1:]
            # '/\d+(\.\d+)?[亿|万](美)?元/g'  '\\d+(\\.\\d+)?[亿|万](美)?元'
            regexp = regexp[:idx]
            res = re.findall('({})'.format(regexp), text)
            res = [i[0] for i in res]
            results.extend(res)
        print('results:{}'.format(results))
        keyword_result = ','.join(results)
        # cursor.execute(text_sql, (news_id, text, keyword_result))
        # cursor.execute(news_update_sql, news_id)
        # conn.commit()


def crawler():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('blink-settings=imagesEnabled=false')
    chrome_options.add_argument('--disable-gpu')
    browser = webdriver.Chrome(options=chrome_options)
    conn = pymysql.connect(host="47.106.140.189", port=3306, user='test', passwd='root1234', db='python-crawler',
                           charset='utf8')
    try:
        # crawl_title(conn, browser)
        crawl_text(conn, browser)
    except Warning as w:
        print(w)
    except Exception as e:
        print(e)
    finally:
        conn.close()
        browser.close()


crawler()
# schedule.every(30).minutes.do(python-crawler)
# while True:
#     schedule.run_pending()

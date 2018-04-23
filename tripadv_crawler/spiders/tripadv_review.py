# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import TextResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import sys

from tripadv_crawler.items import TripadvCrawlerItem

class TripadvReviewSpider(scrapy.Spider):
    reload(sys)
    sys.setdefaultencoding('utf-8')
    name = 'tripadv_review'
    allowed_domains = [
        'https://www.tripadvisor.com/Attraction_Review-g6643743-d446941-Reviews-Mount_Bromo-Bromo_Tengger_Semeru_National_Park_East_Java_Java.html',
    ]
    start_urls = [
        'https://www.tripadvisor.com/Attraction_Review-g6643743-d446941-Reviews-Mount_Bromo-Bromo_Tengger_Semeru_National_Park_East_Java_Java.html',]

    def __init__(self):
        self.items = TripadvCrawlerItem()
        self.items['indonesian'] = []
        self.items['japanese'] = []

    def parse(self, response):
        ### this part is iterated for each page loaded

        opts = Options()
        opts.add_argument('--headless')
        opts.add_argument('--window-size=1920x1080')
        opts.add_argument('--no-sandbox')
        # opts.add_experimental_option('detach', True)
        wd = webdriver.Chrome(chrome_options=opts)
        wd.get(self.allowed_domains[0])  # initial site
        # wb.maximize_window()
        self.action = ActionChains(wd)
        self.init_crawling(wd, 'Indonesia')
        self.scrap_page(wd, response, self.items, 'indonesian')
        self.action.move_to_element(wd.find_element_by_xpath('//div[@id="REVIEWS"]')).perform()
        self.init_crawling(wd, 'Japanese')
        self.scrap_page(wd, response, self.items, 'japanese')
        wd.close()

        ### end of function

        ### write all the result into the text file
        ### save it into json file separated for each language
        ### if this part is asynchronous then how the heck can I maintain the order of the data on the json file :/
        f = open('teskk.txt', 'wb')
        for i in self.items['indonesian']:
            f.write(i['content'] + '\n')
        for i in self.items['japanese']:
            f.write(i['content'].encode('utf-8') + '\n')
        f.close()

    def scrap_page(self, wd, response, items, language):
        '''
        Scrap all the comment on the target page, the target language can be changed on the items.py class
        :param pycharmItem items: Items container of pycharm
        :param str language: Target language
        '''
        while True:
            next = wd.find_elements_by_xpath(
                '//div[@class="prw_rup prw_common_north_star_pagination responsive"]/div[@class="unified ui_pagination north_star "]/a[@class="nav next taLnk ui_button primary"]')
            # get the new page source after performed actions by selenium
            WebDriverWait(wd, 10).until(
                EC.text_to_be_present_in_element((By.XPATH, '//span[@class="taLnk ulBlueLinks"]'), 'Show less')
            )
            last_response = TextResponse(url=response.url, body=wd.page_source, encoding='utf-8')
            # parse the review
            items[language].extend(self.parse_review(last_response))
            # move to the next page until it cant be clicked
            if (len(next) > 0):
                wd.implicitly_wait(1)
                next[0].click()
                WebDriverWait(wd, 10).until_not(
                    # check whether the element can be clicked
                    EC.presence_of_element_located((By.XPATH,
                                                    '//div[@class="ratings_and_types concepts_and_filters block_wrap responsive loading"]'))
                )
                self.show_reviews(wd)
            else:
                break

    def init_crawling(self, wd, language):
        '''
        Change the language of target page into target language (e.g. Indonesian, Japanese, English, etc.)
        :param str language: Target language
        '''
        # open language option
        select = wd.find_element_by_xpath('//a[@class="taLnk more"]')
        select.click()
        # select target language
        langs = wd.find_elements_by_xpath(
            '//ul[@class="langs"]/li[contains(label,"' + language + '")]/span/input')
        if (not langs[1].get_attribute('checked')):
            langs[1].click()
        else:
            langs_close = wd.find_element_by_xpath('//span/div[@class="ui_close_x"]')
            langs_close.click()
        # wait till the specified language radio button is checked
        WebDriverWait(wd, 10).until_not(
            # check whether the element can be clicked
            EC.presence_of_element_located((By.XPATH,
                                        '//div[@class="ui_backdrop dark"]'))
        )
        self.show_reviews(wd)


    def show_reviews(self, wd):
        # click more to show entire reviews
        more = wd.find_elements_by_xpath('//span[@class="taLnk ulBlueLinks"]')
        if len(more) > 0:
            more[0].click()

    def parse_review(self, response):
        '''
        Parse review for the opened page, populate the items variable with desired information that is extracted from
        the review (name, rating, title, content)
        :param str response: html content
        :return array of dictionary of reviews:
        '''
        items = []
        contents = response.xpath('//div[@class="mainContent"]/div/div[@class="wrap"]')
        for content in contents:
            item = {}
            item['name'] = response.xpath('//h1[@class="heading_title"]/text()').extract()[0]
            item['rating'] = self.parse_rating(
                content.xpath('.//div[@class="rating reviewItemInline"]/span[contains(@class, "ui_bubble_rating")]/@class')[0].extract()
            )
            item['title'] = content.xpath('.//div/a/span[@class="noQuotes"]/text()').extract()[0]
            item['content'] = content.xpath('.//div/div/p[@class="partial_entry"]/text()').extract()[0]
            items.append(item)
        return items

    def parse_rating(self, rating_class_name):
        return int(rating_class_name[-2])

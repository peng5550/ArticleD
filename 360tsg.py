import asyncio
import aiohttp
from lxml import etree
import requests
import random
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
import settings
import os
import re
import json
import time
from showStatus import ShowStatus
from functools import partial


SITE_NAME = "360图书馆"


class Crawler360TSG(ShowStatus):

    def __init__(self):

        super(Crawler360TSG, self).__init__(SITE_NAME)
        self.treeIndex = 1

        self.savePath = settings.FILEPATH.get(SITE_NAME)
        if not self.savePath:
            self.savePath = "./"
        else:
            if not os.path.exists(self.savePath):
                os.makedirs(self.savePath)

    def __creatBrowser(self):
        # 创建driver
        try:
            options = webdriver.ChromeOptions()
            # options.add_experimental_option("debuggerAddress", "127.0.0.1:6001")
            driver = webdriver.Chrome(executable_path=r"F:\projects\articleDownload\chromedriver.exe", chrome_options=options)
            driver.set_page_load_timeout(30)
            driver.set_script_timeout(30)
            self.driver = driver
            self.wait = WebDriverWait(self.driver, 600)
        except Exception as e:
            self.addLog(f"创建driver失败,{e}")
            return

    async def __getContent(self, semaphore, link_, referer=None, img=False):

        # # 代理服务器
        # proxyHost = "http-dyn.abuyun.com"
        # proxyPort = "9020"
        #
        # # 代理隧道验证信息
        # proxyUser = settings.PROXIES[proxy]["proxyUser"]
        # proxyPass = settings.PROXIES[proxy]["proxyPass"]
        #
        # proxyServer = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
        #     "host": proxyHost,
        #     "port": proxyPort,
        #     "user": proxyUser,
        #     "pass": proxyPass,
        # }
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
        }
        if img:
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Referer': referer,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
            }

        conn = aiohttp.TCPConnector(verify_ssl=False)
        async with semaphore:
            async with aiohttp.ClientSession(headers=headers, connector=conn, trust_env=True) as session:
                try:
                    async with session.get(link_, timeout=10) as resp:
                        # async with session.get(link_, proxy=proxyServer, timeout=4) as resp:
                        # if str(resp.status).startswith("2"):
                        if not img:
                            content = await resp.text(encoding="utf-8")
                        else:
                            content = await resp.read()

                        await asyncio.sleep(random.uniform(1, 3))
                        return content, link_

                except Exception as e:
                    print(e)
                    self.addLog(e)
                    self.addToTable(link_, "请求失败")
                    self.saveErrors(link_)
                    return


    def getPdfContent(self, url):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        if not resp.status_code == 200:
            return
        if url.startswith("http://html.360doc.com"):
            html = json.loads(resp.text.strip("(").strip(")")).get("htmlcontent").replace("\\", "")
        else:
            html = resp.text
        return html

    def getPageIndexUrl(self, startUrl):
        self.addLog("正在获取文章链接,请稍等.")
        self.__creatBrowser()
        article_link = []
        self.driver.get(startUrl)
        next_page_btn = self.driver.find_elements_by_xpath("//span/a[contains(text(), '下页')]")
        while next_page_btn:
            for link in self.driver.find_elements_by_css_selector("table.artlist div.list > a"):
                link_ = link.get_attribute("href")
                article_link.append(link_)

            next_page_btn[0].click()
            time.sleep(3)
            next_page_btn = self.driver.find_elements_by_xpath("//span/a[contains(text(), '下页')]")

        return article_link

    def savePdf(self, urlList, cls):
        htmlText = []
        title = ""
        for url, title in urlList:
            html = self.getPdfContent(url)
            htmlText.append(html)
            title = title
        if cls:
            htmlText.append("</body></html>")
        htmlText = "\n".join(htmlText)
        self.saveHtml(htmlText, title)

    def saveErrors(self, url):
        self.errors = f"{settings.ERRORPATH}/{SITE_NAME}/"
        if not os.path.exists(self.errors):
            os.makedirs(self.errors)
        with open(f"{self.errors}errors.txt", "a+", encoding="utf-8")as f:
            f.write(url + "\n")

        self.addLog(f"[{url}]下载失败, 已记录.")

    def indexPage(self, feature):
        result, referer = feature.result()
        html = etree.HTML(result)
        urlList = html.xpath("//span[@class='atc_title']/a/@href")
        self.detailUrlList += urlList

    def detailPage(self, feature):
        content, link_ = feature.result()

        html = etree.HTML(content)
        title = html.xpath("//*[@id='titiletext']/text()")[0]

        pageInfo = re.findall(r"GerLookingUserInfo(\(.*?\));", content)
        if not pageInfo:
            return

        pageTuple = eval(pageInfo[0])
        pageNum = pageTuple[-3]
        if not pageNum:
            pageUrlList = [(link_, title)]
            cls = False
        else:
            url = pageTuple[-4].split("/")
            articleId = url[-1].split("_")[0]
            atricleDate = "".join(url[3:-1])
            pageUrlList = [
                (f"http://html.360doc.com/htmldocument/html11/{atricleDate}/{articleId}_{index}.html", title) for
                index in range(1, int(pageNum) + 1)]
            cls = True
        self.savePdf(pageUrlList, cls)

    def addToTable(self, title, status="下载成功"):
        treeData = [self.treeIndex, title, status]
        self.box.insert("", "end", values=treeData)
        self.treeIndex += 1
        self.box.yview_moveto(1.0)

    def saveHtml(self, htmlText, title):
        path = f"{self.savePath}{title}.html"
        with open(path, "w+", encoding="utf8")as f:
            f.write('<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n')
            f.write(htmlText)
        self.addToTable(title)
        self.addLog(f"[{title}]保存成功.")


    async def taskManager(self, linkList, callbackFunc):
        tasks = []
        semaphore = asyncio.Semaphore(settings.SEMNUM)

        for link_ in linkList:
            task = asyncio.ensure_future(self.__getContent(semaphore, link_))
            task.add_done_callback(callbackFunc)
            tasks.append(task)
        await asyncio.gather(*tasks)

    def crawlDetail(self, startUrl):
        self.addLog(f"获取到{len(startUrl)}个链接.")
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.taskManager(startUrl, self.detailPage))

    def startCrawler(self, startUrl):
        # 翻页部分需要处理
        self.detailUrlList = self.getPageIndexUrl(startUrl)

        if self.detailUrlList:
            self.detailUrlList = list(set(self.detailUrlList))
            self.addLog(f"获取到{len(self.detailUrlList)}个文章链接.")
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self.taskManager(self.detailUrlList, self.detailPage))


    def start(self, start_url, site=False):
        if not site:
            self.createUI(partial(self.startCrawler, start_url))
        else:
            self.createUI(partial(self.crawlDetail, start_url))
        self.root.mainloop()
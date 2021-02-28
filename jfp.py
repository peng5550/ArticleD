import asyncio
import aiohttp
from lxml import etree
import requests
import random
import settings
import os
from showStatus import ShowStatus
from functools import partial

SITE_NAME = "经方派"

class CrawlerJFP(ShowStatus):

    def __init__(self):
        super(CrawlerJFP, self).__init__(SITE_NAME)
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
        }
        self.savePath = settings.FILEPATH.get(SITE_NAME)
        if not self.savePath:
            self.savePath = "./"
        else:
            if not os.path.exists(self.savePath):
                os.makedirs(self.savePath)

        self.treeIndex = 1

    def addToTable(self, title, status="下载成功"):
        treeData = [self.treeIndex, title, status]
        self.box.insert("", "end", values=treeData)
        self.treeIndex += 1
        self.box.yview_moveto(1.0)

    async def __getContent(self, semaphore, link_):

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

        conn = aiohttp.TCPConnector(verify_ssl=False)
        async with semaphore:
            async with aiohttp.ClientSession(headers=self.headers, connector=conn, trust_env=True) as session:
                try:
                    async with session.get(link_, timeout=10) as resp:
                        # async with session.get(link_, proxy=proxyServer, timeout=4) as resp:
                        # if str(resp.status).startswith("2"):
                        content = await resp.text(encoding="utf-8")
                        await asyncio.sleep(random.uniform(1, 3))
                        return content
                except Exception as e:
                    self.saveErrors(link_)
                    return

    def getArticleUrl(self, url):
        self.addLog("正在获取文章链接,请稍等.")
        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.encoding = "utf-8"
        if not resp.status_code == 200:
            return
        html = etree.HTML(resp.text)
        articleUrlList = html.xpath("//li[@class='listing-item']/a/@href")
        return articleUrlList

    def saveErrors(self, url):
        self.errors = f"{settings.ERRORPATH}/{SITE_NAME}/"
        if not os.path.exists(self.errors):
            os.makedirs(self.errors)
        with open(f"{self.errors}errors.txt", "a+", encoding="utf-8")as f:
            f.write(url+"\n")

    def detailPage(self, feature):
        result = feature.result()
        html = etree.HTML(result)
        title = html.xpath("//*[@id='main']/article//h1/a/text()")[0]
        self.saveHtml(result, title)

    def saveHtml(self, htmlText, title):
        path = f"{self.savePath}{title}.html"
        with open(path, "w+", encoding="utf8")as f:
            f.write(htmlText)
        self.addLog(f"[{title}], 保存成功.")
        self.addToTable(title)


    async def taskManager(self, linkList, callbackFunc):
        tasks = []
        semaphore = asyncio.Semaphore(4)
        for link_ in linkList:
            task = asyncio.ensure_future(self.__getContent(semaphore, link_))
            task.add_done_callback(callbackFunc)
            tasks.append(task)
        await asyncio.gather(*tasks)

    def crawlDetail(self, startUrl):
        self.addLog(f"获取到{len(startUrl)}个文章链接.")
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.taskManager(startUrl, self.detailPage))


    def startCrawler(self, startUrl):

        articleUrlList = self.getArticleUrl(startUrl)
        self.addLog(f"获取到{len(articleUrlList)}个文章链接.")
        self.crawlDetail(articleUrlList)

    def start(self, start_url, site=False):
        if not site:
            self.createUI(partial(self.startCrawler, start_url))
        else:
            self.createUI(partial(self.crawlDetail, start_url))
        self.root.mainloop()

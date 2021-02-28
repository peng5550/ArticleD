import asyncio
import aiohttp
from lxml import etree
import requests
import re
import random
import settings
import os
from showStatus import ShowStatus
from functools import partial


SITE_NAME = "好大夫在线"

class CrawlerHDFZX(ShowStatus):

    def __init__(self):
        super(CrawlerHDFZX, self).__init__(SITE_NAME)
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
        }
        self.treeIndex = 1
        self.savePath = settings.FILEPATH.get(SITE_NAME)
        if not self.savePath:
            self.savePath = "./"
        else:
            if not os.path.exists(self.savePath):
                os.makedirs(self.savePath)

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
                        content = await resp.text()
                        await asyncio.sleep(random.uniform(1, 3))
                        return content

                except Exception as e:
                    print(e)
                    print(link_)
                    self.addToTable(link_, "请求失败")
                    self.saveErrors(link_)
                    return

    def getPageIndexUrl(self, url):
        self.addLog("正在获取文章链接,请稍等.")
        resp = requests.get(url, headers=self.headers, timeout=10)
        # resp.encoding = "gb2312"
        if not resp.status_code == 200:
            return
        pageNum = re.findall(r">共(.*?)页<", resp.text)
        pageUrlList = []
        if pageNum:
            pageUrlList += [f"{url}_{index}" for index in range(2, int(pageNum[0].strip("'&nbsp;")) + 1)]
        pageUrlList.insert(0, url)
        print(pageUrlList)
        return pageUrlList

    def saveErrors(self, url):
        self.errors = f"{settings.ERRORPATH}/{SITE_NAME}/"
        if not os.path.exists(self.errors):
            os.makedirs(self.errors)
        with open(f"{self.errors}errors.txt", "a+", encoding="utf-8")as f:
            f.write(url+"\n")

    def addToTable(self, title, status="下载成功"):
        treeData = [self.treeIndex, title, status]
        self.box.insert("", "end", values=treeData)
        self.treeIndex += 1
        self.box.yview_moveto(1.0)

    def indexPage(self, feature):
        result = feature.result()
        html = etree.HTML(result)
        self.detailUrlList += html.xpath("//a[@class='art_t']/@href")


    def detailPage(self, feature):
        result = feature.result()
        html = etree.HTML(result)
        title = html.xpath("//div[@class='bread-crumb']/h1/text()")[0]
        self.saveHtml(result, title.strip(">").strip())

    def saveHtml(self, htmlText, title):
        path = f"{self.savePath}{title}.html"
        with open(path, "w+", encoding="utf8")as f:
            f.write('<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n')
            f.write(htmlText)
        self.addToTable(title)

    async def taskManager(self, linkList, callbackFunc):
        tasks = []
        semaphore = asyncio.Semaphore(4)
        for link_ in linkList:
            task = asyncio.ensure_future(self.__getContent(semaphore, link_))
            task.add_done_callback(callbackFunc)
            tasks.append(task)
        await asyncio.gather(*tasks)

    def crawlDetail(self, detailUrlList):
        self.addLog(f"获取到{len(detailUrlList)}个文章链接.")
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.taskManager(detailUrlList, self.detailPage))


    def startCrawler(self, startUrl):
        pageUrlList = self.getPageIndexUrl(startUrl)
        self.detailUrlList = []
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.taskManager(pageUrlList, self.indexPage))
        if not self.detailUrlList:
            return

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
import asyncio
import aiohttp
from lxml import etree
import requests
import random
import settings
import os
import re
from showStatus import ShowStatus
from functools import partial

SITE_NAME = "新浪博文"


class CrawlerXLBW(ShowStatus):

    def __init__(self):
        super(CrawlerXLBW, self).__init__(SITE_NAME)
        self.treeIndex = 1

        self.savePath = settings.FILEPATH.get(SITE_NAME)
        if not self.savePath:
            self.savePath = "./"
        else:
            if not os.path.exists(self.savePath):
                os.makedirs(self.savePath)

    async def __getContent(self, semaphore, link_, img=False, referer=None):

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
                            # print(content)
                        await asyncio.sleep(random.uniform(1, 3))
                        return content, link_

                except Exception as e:
                    print(e)
                    self.addToTable(link_, "请求失败")
                    self.saveErrors(link_)
                    return

    def getPageIndexUrl(self, url):
        self.addLog("正在获取文章链接,请稍等.")
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        if not resp.status_code == 200:
            return
        pageNum = re.findall(r"共(\d+)页", resp.text)
        if pageNum:
            pageUrlList = [f"http://blog.sina.com.cn/s/articlelist_5325106168_0_{index}.html" for index in
                           range(2, int(pageNum[0]))]
        else:
            pageUrlList = []
        pageUrlList.insert(0, url)
        return pageUrlList

    def saveErrors(self, url):
        self.errors = f"{settings.ERRORPATH}/{SITE_NAME}/"
        if not os.path.exists(self.errors):
            os.makedirs(self.errors)
        with open(f"{self.errors}errors.txt", "a+", encoding="utf-8")as f:
            f.write(url + "\n")

    def indexPage(self, feature):
        result, referer = feature.result()
        html = etree.HTML(result)
        urlList = html.xpath("//span[@class='atc_title']/a/@href")
        self.detailUrlList += urlList

    def detailPage(self, feature):

        result, referer = feature.result()
        html = etree.HTML(result)

        title = html.xpath("//div[@class='articalTitle']/h2/text()")
        if not title:
            title = html.xpath("//h1[@class='h1_tit']/text()")
        self.imgUrlList += [(index, title[0], url, referer) for index, url in
                            enumerate(html.xpath("//*[@id='sina_keyword_ad_area2']//a/img/@real_src"))]
        self.saveHtml(result, title[0])

    def addToTable(self, title, status="下载成功"):
        treeData = [self.treeIndex, title, status]
        self.box.insert("", "end", values=treeData)
        self.treeIndex += 1
        self.box.yview_moveto(1.0)

    def saveHtml(self, htmlText, title):
        self.htmlPath = f"{self.savePath}{title}/"
        if not os.path.exists(self.htmlPath):
            os.makedirs(self.htmlPath)
        path = f"{self.htmlPath}{title}.html"
        with open(path, "w+", encoding="utf8")as f:
            f.write('<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n')
            f.write(htmlText)
        self.addToTable(title)

    def saveImage(self, params, feature):
        index, title = params
        self.imagePath = f"{self.savePath}{title}/IMG/"
        if not os.path.exists(self.imagePath):
            os.makedirs(self.imagePath)
        content, link = feature.result()
        path = f"{self.imagePath}IMG-{index}.jpg"
        with open(path, "wb")as f:
            f.write(content)

        self.addLog(f"当前：{path},下载完成.")

    async def taskManager(self, linkList, callbackFunc, img=False):
        tasks = []
        semaphore = asyncio.Semaphore(4)
        if img:
            for index, title, link_, referer in linkList:
                task = asyncio.ensure_future(self.__getContent(semaphore, link_, img, referer))
                task.add_done_callback(partial(callbackFunc, (index, title)))
                tasks.append(task)
        else:
            for link_ in linkList:
                task = asyncio.ensure_future(self.__getContent(semaphore, link_, img))
                task.add_done_callback(callbackFunc)
                tasks.append(task)
        await asyncio.gather(*tasks)

    def crawlDetail(self, detailUrlList):
        self.imgUrlList = []
        self.addLog(f"获取到{len(detailUrlList)}个文章链接.")
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.taskManager(detailUrlList, self.detailPage))

        if self.imgUrlList:
            self.addLog(f"正在下载图片.")
            self.addLog(f"获取到{len(self.imgUrlList)}个图片链接.")
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self.taskManager(self.imgUrlList, self.saveImage, img=True))

    def startCrawler(self, startUrl):
        self.imgUrlList = []
        pageUrlList = self.getPageIndexUrl(startUrl)
        self.detailUrlList = []
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.taskManager(pageUrlList, self.indexPage))

        if self.detailUrlList:
            self.detailUrlList = list(set(self.detailUrlList))
            self.addLog(f"获取到{len(self.detailUrlList)}个文章链接.")
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self.taskManager(self.detailUrlList, self.detailPage))

        if self.imgUrlList:
            self.addLog(f"正在下载图片.")
            self.addLog(f"获取到{len(self.imgUrlList)}个图片链接.")
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self.taskManager(self.imgUrlList, self.saveImage, img=True))

    def start(self, start_url, site=False):
        if not site:
            self.createUI(partial(self.startCrawler, start_url))
        else:
            self.createUI(partial(self.crawlDetail, start_url))
        self.root.mainloop()

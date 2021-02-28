import asyncio
import aiohttp
from lxml import etree
import requests
import random
import settings
import os
import re
from math import ceil
from showStatus import ShowStatus
from functools import partial

SITE_NAME = "中医中药秘方网"

class CrawlerZYZYMFW(ShowStatus):

    def __init__(self):
        super(CrawlerZYZYMFW, self).__init__(SITE_NAME)
        self.treeIndex = 1
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'
        }

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
                        content = await resp.text(encoding="gb18030")
                        await asyncio.sleep(random.uniform(1, 3))
                        return content

                except Exception as e:
                    print(e)
                    self.addLog(f"网络请求失败：{e}, 已记录.")
                    self.saveErrors(link_)
                    return

    def getPageIndexUrl(self, url):
        self.addLog("正在获取文章链接,请稍等.")
        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.encoding = "gb2312"
        if not resp.status_code == 200:
            return
        html = etree.HTML(resp.text)
        if not url.endswith("/"):
            url += "/"
        base_url = url + html.xpath("//div[@class='pagelist']/li/a[contains(text(), '下一页')]/@href")[0]
        total_page = int(html.xpath("//span[@class='pageinfo']/strong[1]/text()")[0])
        pageUrlList = [re.sub(r'_\d+\.html', '_{}.html'.format(index), base_url) for index in range(1, total_page+1)]
        print(pageUrlList)
        return pageUrlList

    def saveErrors(self, url):
        self.errors = f"{settings.ERRORPATH}/{SITE_NAME}/"
        if not os.path.exists(self.errors):
            os.makedirs(self.errors)
        with open(f"{self.errors}errors.txt", "a+", encoding="utf-8")as f:
            f.write(url + "\n")

        self.addLog(f"[{url}]下载失败, 已记录.")


    def indexPage(self, feature):
        result = feature.result()
        # print(result)
        html = etree.HTML(result)
        urlList = ["http://www.21nx.com"+i for i in html.xpath("//div[@class='chunlist']/ul/li/p/a/@href")]
        self.detailUrlList += urlList

    def detailPage(self, feature):
        result = feature.result()
        html = etree.HTML(result)
        title = html.xpath("//h1/text()")[0]

        self.saveHtml(result, title)

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
        self.addLog(f"[{title}], 保存成功.")


    async def taskManager(self, linkList, callbackFunc):
        tasks = []
        semaphore = asyncio.Semaphore(settings.SEMNUM)
        for link_ in linkList:
            task = asyncio.ensure_future(self.__getContent(semaphore, link_))
            task.add_done_callback(callbackFunc)
            tasks.append(task)
        await asyncio.gather(*tasks)

    def crawlDetail(self, detailUrlList):
        self.addLog(f"共发现[{len(detailUrlList)}]篇文章, 开始下载.")
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.taskManager(detailUrlList, self.detailPage))
        self.addLog("任务结束.")


    def startCrawler(self, start_url):
        pageUrlList = self.getPageIndexUrl(start_url)
        self.detailUrlList = []
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.taskManager(pageUrlList, self.indexPage))
        if not self.detailUrlList:
            return

        self.addLog(f"共发现[{len(self.detailUrlList)}]篇文章, 开始下载.")
        self.detailUrlList = list(set(self.detailUrlList))
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.taskManager(self.detailUrlList, self.detailPage))
        self.addLog("任务结束.")

    def start(self, start_url, site=False):
        if not site:
            self.createUI(partial(self.startCrawler, start_url))
        else:
            self.createUI(partial(self.crawlDetail, start_url))
        self.root.mainloop()
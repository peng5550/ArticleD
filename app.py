from tkinter.messagebox import *
from tkinter import ttk, filedialog
from mttkinter import mtTkinter as mtk
import threading
import settings


class Application:

    def __init__(self, master):
        self.root = master
        self.root.geometry("300x290")
        self.root.title("博客文章下载工具 1.0")
        self.__createUI()

    def __createUI(self):

        # 博轩下载设置
        self.settingsBox = mtk.LabelFrame(self.root, text="下载设置", fg="blue")
        self.settingsBox.place(x=20, y=20, width=260, height=250)
        # 网站选择
        self.siteLable = mtk.Label(self.settingsBox, text="互联网平台：")
        self.siteLable.place(x=25, y=20, width=75, height=25)
        self.siteSelect = ttk.Combobox(self.settingsBox)
        self.siteSelect["values"] = ["360图书馆", "39康复网", "中医世家", "中医人", "中医中药秘方网", "中医中药网", "经方派", "新浪博文", "好大夫在线"]
        self.siteSelect.place(x=115, y=20, width=100, height=25)

        # 页面属性
        self.siteCls = mtk.Label(self.settingsBox, text="页面选择：")
        self.siteCls.place(x=25, y=65, width=65, height=25)
        self.siteClsSelect = ttk.Combobox(self.settingsBox)
        self.siteClsSelect["values"] = ["列表页", "内容页"]
        self.siteClsSelect.place(x=115, y=65, width=100, height=25)

        # 链接
        self.labelUrl = mtk.Label(self.settingsBox, text="链接：")
        self.labelUrl.place(x=25, y=110, width=40, height=25)
        self.urlText = mtk.Text(self.settingsBox)
        self.urlText.place(x=75, y=110, width=160, height=50)
        self.urlText.bind(sequence="<Double-Button-1>", func=lambda x: self.thread_it(self.loadErrors))
        # 任务按钮
        self.startBtn = mtk.Button(self.settingsBox, text="开始", command=lambda: self.thread_it(self.start))
        self.startBtn.place(x=25, y=180, width=80, height=35)
        self.stopBtn = mtk.Button(self.settingsBox, text="停止")
        self.stopBtn.place(x=135, y=180, width=80, height=35)



    def loadErrors(self):
        filePath = filedialog.askopenfilename(title=u"选择文件")
        if filePath:
            try:
                with open(filePath, "r", encoding="utf-8")as f:
                    self.errorUrl = [i.strip() for i in f.readlines()]
                    return self.errorUrl
            except Exception as e:
                showerror("错误信息", "请导入正确的文件!")
        else:
            showerror("错误信息", "请导入ErrorUrl文件!")

    def start(self):
        siteName = self.siteSelect.get()
        if not siteName:
            showerror("错误信息", "请选择您要抓取的网站.")
            return

        siteInfo = settings.SITEINFO.get(siteName)
        if not siteInfo:
            showerror("错误信息", "暂不支持该平台.")
            return

        pageCls = self.siteClsSelect.get()
        if not siteName:
            showerror("提示信息", "页面默认：列表页")
            pageCls = "列表页"

        startUrl = self.urlText.get(1.0, "end").strip()
        if siteName == "列表页":
            if not startUrl:
                showerror("错误信息", "请输入起始链接!")
                return
        fileName, clsName = siteInfo.split("/")
        cls = __import__(fileName)
        clsName = getattr(cls, clsName)
        crawlerCls = clsName()


        if pageCls == "内容页":
            urlInfo = self.urlText.get(1.0, "end")
            if urlInfo:
                urlList = [i.strip() for i in urlInfo.split("\n") if i.strip()]
            else:
                if self.errorUrl:
                    urlList = self.errorUrl
                else:
                    urlList = self.loadErrors()
            if not urlList:
                showerror("错误信息", "未发现文章链接!")
                return
            crawlerCls.start(urlList, True)
        else:
            crawlerCls.start(startUrl)

    @staticmethod
    def thread_it(func, *args):
        t = threading.Thread(target=func, args=args)
        t.setDaemon(True)
        t.start()



if __name__ == '__main__':
    root = mtk.Tk()
    Application(root)
    root.mainloop()

from tkinter.messagebox import *
from tkinter import ttk, filedialog, scrolledtext
from tkinter.ttk import Scrollbar
from mttkinter import mtTkinter as mtk
import threading
import settings
from datetime import datetime


class ShowStatus:
    def __init__(self, title):
        self.root = mtk.Tk()
        self.root.geometry("340x500")
        self.root.title(f"[{title}]下载进度")

    def createUI(self, func):
        # 日志信息
        self.logBox = mtk.LabelFrame(self.root, text="下载进度", fg="blue")
        self.logBox.place(x=20, y=20, width=300, height=280)
        title = ['1', '2', '3']
        self.box = ttk.Treeview(self.logBox, columns=title, show='headings')
        self.box.place(x=15, y=15, width=275, height=225)
        self.box.column('1', width=30, anchor='center')
        self.box.column('2', width=165, anchor='center')
        self.box.column('3', width=80, anchor='center')
        self.box.heading('1', text='序号')
        self.box.heading('2', text='文章标题')
        self.box.heading('3', text='状态')
        self.VScroll1 = Scrollbar(self.box, orient='vertical', command=self.box.yview)
        self.VScroll1.pack(side="right", fill="y")
        self.box.configure(yscrollcommand=self.VScroll1.set)

        self.logInfoBox = mtk.LabelFrame(self.root, text="日志信息", fg="blue")
        self.logInfoBox.place(x=20, y=310, width=300, height=150)
        # 下载进度
        self.logText = scrolledtext.ScrolledText(self.logInfoBox, fg="green")
        self.logText.place(x=15, y=10, width=275, height=110)
        self.logText.bind(sequence="<Double-Button-1>", func=lambda x: self.thread_it(func))


    def addLog(self, msg):
        self.logText.insert(mtk.END, "{} {}\n".format(datetime.now().strftime("%H:%M:%S"), msg))
        self.logText.yview_moveto(1.0)

    def deleteTree(self):
        x = self.box.get_children()
        for item in x:
            self.box.delete(item)

    @staticmethod
    def thread_it(func, *args):
        t = threading.Thread(target=func, args=args)
        t.setDaemon(True)
        t.start()

    # def start(self):
    #     self.root.mainloop()



# if __name__ == '__main__':
#     app = ShowStatus(1111)
#     app.start()
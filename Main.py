#coding:utf8
from Tkinter import *
import tkFileDialog
from TP import TablePicker
import xlwt
import os
import threading
import time


class MainBody:
    def __init__(self):
        self.tp = None
        self.root = Tk()
        self.source_path = StringVar()
        self.dir_path = StringVar()
        self.words = None
        self.img_path = ''
        self.img_name = ''
        self.info = StringVar()
        self.info.set('开始')

        self.thread_count = 0

        #输入框
        Entry(self.root, width='40', textvariable=self.source_path).grid(row=0, column=0)
        Entry(self.root, width='40', textvariable=self.dir_path).grid(row=1, column=0)
        #按钮
        self.chooseSrcBtn = Button(self.root, text='选择文件', width=10, command=self.select_source_path)
        self.chooseSrcBtn.grid(row=0, column=1)
        self.chooseDesBtn = Button(self.root, text='选择存放位置', command=self.select_dir_path)
        self.chooseDesBtn.grid(row=1, column=1)
        self.startBtn = Button(self.root, textvariable=self.info, width=10, command=self.start)
        self.startBtn.grid(row=2, column=1)
        # 创建一个背景色为白色的矩形
        self.canvas = Canvas(self.root, width=200, height=26, bg="white")
        # 创建一个矩形外边框（距离左边，距离顶部，矩形宽度，矩形高度），线型宽度，颜色
        self.canvas.create_rectangle(2, 2, 210, 27, width=1, outline="black")

        self.fill_line = self.canvas.create_rectangle(2, 2, 0, 27, width=0, fill="blue")
        self.canvas.grid(row=2, column=0, ipadx=5)
        self.root.mainloop()

    def select_source_path(self):
        file_type = [("png格式".decode('utf8'), ".png")
            , ("jpg格式".decode('utf8'), ".jpg")]
        path_ = tkFileDialog.askopenfilename(filetypes=file_type)
        print path_
        self.source_path.set(path_)
        img_name = self.source_path.get().split('/')[-1].split('.')[0]
        img_path = self.source_path.get().split(self.source_path.get().split('/')[-1])[0]
        dir_path_ = img_path+img_name+'.xls'
        print 'dir_path_',dir_path_
        self.dir_path.set(dir_path_)

    def select_dir_path(self):
        file_type = [("excel".decode('utf8'), ".xls")]
        path_ = tkFileDialog.asksaveasfilename(filetypes=file_type, )
        if path_ != '':
            self.dir_path.set(path_)
        print self.dir_path.get()

    def loading_progress(self):
        self.canvas.coords(self.fill_line, (0, 0, 0, 30))
        while True:
            progress = self.tp.progress
            n = progress * 210.0
            self.canvas.coords(self.fill_line, (0, 0, n, 30))
            self.root.update()
            if n >= 210:
                break
            time.sleep(0.1)
        pass

    def start(self):
        op_thread = threading.Thread(target=self.get_words, name=str(self.thread_count))
        self.thread_count = self.thread_count + 1
        op_thread.start()

    def get_words(self):
        self.tp = TablePicker(self.source_path.get())
        progress_thread = threading.Thread(target=self.loading_progress, name=str(self.thread_count))
        self.thread_count = self.thread_count + 1
        progress_thread.start()
        table = self.tp.get_table_framework()
        rect = self.tp.get_cell_rect(table)
        words = self.tp.readRect(rect)
        self.write_excel(words, 2)



    def write_excel(self, words, sep):
        # 初始化excel
        my_excel = xlwt.Workbook(encoding='utf-8')
        sheet1 = my_excel.add_sheet(u'钻孔基本情况表', cell_overwrite_ok=True)
        count = 0
        for i in range(sep):
            for cow in words[i]:
                sheet1.write(count%2,count/2,cow)
                count = count+1
        sheet2 = my_excel.add_sheet(u'钻孔地层描述表', cell_overwrite_ok=True)
        w_t = words[sep:]
        for i in range(len(w_t)):
            for j in range(len(w_t[i])):
                sheet2.write(i, j, w_t[i][j])
        xls_name = self.dir_path.get()
        # 文件存在则替换
        if os.path.exists(xls_name):
            os.remove(xls_name)
            my_excel.save(xls_name)
        else:
            my_excel.save(xls_name)

        log_name = self.img_name + str(int(time.time()))+'-log.txt'
        log_file = open(log_name, 'w')
        log_file.write("成功识别记录:"+str(self.tp.success_count)+'条\n')
        log_file.write("失败识别记录:" + str(self.tp.fail_count) + '条')
        log_file.flush()
        log_file.close()

if __name__ == '__main__':
    MainBody()
    pass
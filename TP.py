# coding:utf-8
import numpy as np
import copy
from PIL import Image
from aip import AipOcr
from cStringIO import StringIO
import pytesseract

class TablePicker:
    def __init__(self, img_path):
        self.img_path = img_path
        self.img = self.get_img()
        self.progress = 0
        self.success_count = 0
        self.fail_count = 0
        self.sum_words = 0
        pass

    def start(self):
        self.table = self.get_table_framework(self.img_dot)
        self.clear_table(self.table)
        self.rect = self.get_cell_rect(self.table)
        self.words = self.readRect(self.rect)

    # 1 获取到行列的交点
    def get_img(self):
        # 读取图片，并转灰度图
        '''
        img = io.imread(self.img_path, True)
        # 二值化
        bi_th = 0.81
        img[img <= bi_th] = 0
        img[img > bi_th] = 1
        '''
        img = Image.open(self.img_path).convert('L')
        img_arr = np.asanyarray(img)
        bi_th = img_arr[0][0]
        img_arr.flags['WRITEABLE']=True
        img_arr[img_arr < bi_th] = 0
        img_arr[img_arr >= bi_th] = 1
        return img_arr

    # 判断下一行是否有对应的点
    def has_next_level_left_bottom_point(self, table, lvl, point):
        for td in table[lvl + 1]:
            if abs(td[0] - point[0]) < 6:
                return table[lvl + 1].index(td)
        return None
    #0位黑色 1为白色
    def isIntersection(self, i, j):
        a, b, c, d = 1, 1, 1, 1
        img = self.img
        max_x = len(img[i])
        max_y = len(img)
        default_px = 20
        for x in range(i - default_px, i):
            if img[x][j] == 1:
                a = 0
        for x in range(i, i + default_px if i + default_px < max_y else max_y):
            if img[x][j] == 1:
                b = 0
        for y in range(j - default_px, j):
            if img[i][y] == 1:
                c = 0
        for y in range(j, j + default_px if j + default_px < max_x else max_x):
            if img[i][y] == 1:
                d = 0
        if a + c == 2 or a + d == 2 or b + c == 2 or b + d == 2:
            return True
        else:
            return False

    # 2.1通过关键点 img_dot 获取表格框架table
    def get_table_framework(self):

        table = []
        for i in range(1, len(self.img)):
            row = []
            for j in range(1, len(self.img[i])):
                if self.img[i][j] == 0 and self.isIntersection(i, j) == True:
                    row.append([i, j])
            if len(row) > 0:
                table.append(row)
        table = self.clear_table(table)
        return table

    # 2.2 去除table中长度小于3的行
    def clear_table(self, table):
        t_table = copy.deepcopy(table)
        #移除连续点
        for i in range(len(table)):
            if len(table[i]) == 2 or len(table[i]) == 3:
                t_table.remove(table[i])
                continue
            if i < len(table)-1 and abs(table[i][0][0] - table[i + 1][0][0]) < 3 and abs(table[i][0][1] - table[i + 1][0][1]) < 2:
                t_table.remove(table[i])
                continue
            for j in range(len(table[i]) - 1):
                if abs(table[i][j][1] - table[i][j + 1][1]) < 10:
                    t_table[i + len(t_table) - len(table)].remove(table[i][j])
        #找出渐灭层的y值
        msb_max_y = 0
        for i in range(3, len(t_table) - 1):
            if len(t_table[i]) == 8:
                msb_max_y = t_table[i][-1][1]
                break
        #找出最小的y值
        x, y = 0, 0
        min_y = 9999
        for row in t_table[:10]:
            for cell in row:
                if cell[1] < min_y:
                    min_y = cell[1]
                    x = t_table.index(row)
                    y = row.index(cell)
        jm = []
        unnormal = []
        #如果某一行的起始点既不是最小值也不是最大值 则删掉
        t_table = t_table[x:]
        table = copy.deepcopy(t_table)
        for i in range(len(table)):
            if abs(table[i][0][1] - min_y) > 3 and table[i][0][1] != msb_max_y:
                t_table.remove(table[i])
        #将渐灭层向上补齐
        ''' for i in range(3, len(t_table) - 1):
            #print len(t_table[i])
            if len(t_table[i]) == 7:
                unnormal.append(t_table[i])
            if len(t_table[i]) == 1:
                jm.append(t_table[i])
        #print 'len unnormal=', len(unnormal), ' len jm =', len(jm)
        for i in range(len(unnormal)):
            jm_x = i if i < len(jm) else len(jm) - 1
            unnormal[i].append(jm[jm_x][0])
            if i < len(jm):
                t_table.remove(jm[i])'''
        #描述表的y值集合

        table = copy.deepcopy(t_table)
        msb_ys = []
        for cell in t_table[4]:
            msb_ys.append(cell[1])
        for i in range(5, len(t_table)-1):
            if i > len(t_table)-1:
                break
            #补齐前前几列缺失的点
            if len(t_table[i]) == 1:
                continue
            for j in range(7):
                    if j > len(t_table[i])-1 or abs(t_table[i][j][1] - msb_ys[j]) > 10:
                        t_table[i].insert(j, [t_table[i][0][0], msb_ys[j]])
                        #table[i].insert(j, [t_table[i][0][0], msb_ys[j]])
            #补齐后如果长度小于8，那么渐灭了，补齐渐灭
            if len(t_table[i]) < 8:
                point = []
                for ii in range(i, len(t_table)):
                    if len(t_table[ii]) == 1:
                        point = t_table[ii]
                        t_table.remove(t_table[ii])
                        break
                if point == []:
                    continue
                t_table[i].append(point[0])
        return t_table

    # 2.3通过table获取到每个单元格的坐标
    def get_cell_rect(self, table):
        rect = []
        for i in range(2):
            row = []
            for j in range(len(table[i]) - 1):
                left_top = table[i][j]
                right_bottom = [[]]
                jump_level = 1
                if j == 2 and i == 0:
                    jump_level = 2
                if j == 2 and i == 1:
                    row.append(rect[i - 1][j])
                    left_top[1] = table[i - 1][j + 1][1]

                right = table[i][j + 1][1]
                bottom = 0
                for pntplus in range(len(table[i + jump_level])):
                    if abs(right - table[i + jump_level][pntplus][1]) < 6:
                        bottom = table[i + jump_level][pntplus][0]
                        break
                if bottom == 0:
                    continue
                right_bottom = [bottom, right]
                row.append([left_top, right_bottom])
            if len(row) > 0:
                rect.append(row)

        for i in range(3, len(table) - 2):
            row = []
            if abs(table[i][0][0] - table[i + 1][0][0]) < 5:
                continue
            for j in range(len(table[i]) - 1):
                left_top = [table[i][j][0], table[i][j][1]]
                right_bottom = [[]]
                jump_level = 1
                if abs(table[i][0][1] - table[i + 1][0][1]) > 10:
                    jump_level = 2
                right = table[i][j + 1][1]
                if len(table[i + 1]) < j + 2:
                    continue
                if abs(table[i][j][0] - table[i][j + 1][0]) > 10 and abs(
                        table[i][j + 1][0] - table[i + 1][j + 1][0]) > 10:
                    left_top[0] = table[i][j + 1][0]
                bottom = 0
                for pntplus in range(len(table[i + jump_level])):
                    if abs(right - table[i + jump_level][pntplus][1]) < 10:
                        bottom = table[i + jump_level][pntplus][0]
                        break
                if bottom == 0:
                    continue
                right_bottom = [bottom, right]
                row.append([left_top, right_bottom])
            if len(row) > 0:
                rect.append(row)
        return rect

    # 2.4判断下一行的宽度是否小于当前行，小于则为 岩性描述的扩展层
    def is_next_row_short(self, table, lvl, pnt):
        if pnt != 7:
            return None
        now_x1 = table[lvl][pnt][0]
        now_x2 = table[lvl][pnt + 1][0]
        next_x = table[lvl + 1][0][0]
        if next_x > now_x1 and next_x < now_x2:
            return table[lvl + 1][0][1]
        return None

    # 3.2解析文字
    def read_word(self, image):
        APP_ID = '11747921'
        API_KEY = 'Ies9xP1pGgetjKGh7gLi2HCs'
        SECRET_KEY = 'ML4BegNp5h5TZFi2uMVeZFvbhw3jP6zr'
        client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
        """ 如果有可选参数 """
        """ 读取图片 """
        options = {}
        str = ''
        options["language_type"] = "CHN_ENG"
        options["detect_direction"] = "true"
        options["detect_language"] = "true"
        options["probability"] = "true"
        try:
            a = client.basicGeneral(image, options)
        except Exception as e:
            self.fail_count = self.fail_count + 1
            return str
        if a.has_key('words_result'):
            self.success_count = self.success_count + 1
            for i in a['words_result']:
                str = str + i['words']
        else:
            self.fail_count = self.fail_count + 1
        return str

    # 3.2解析文字
    @staticmethod
    def read_word2(self, image):
        text = pytesseract.image_to_string(self, image, lang='eng')
        print text
        return text

    # 3.1读取单元格中的文字
    def readRect(self, rect):
        image = Image.open(self.img_path)
        words = []
        self.sum_words = sum(len(row) for row in rect)
        count_words = 0
        for row in range(len(rect)):
            row_word = []
            for col in range(len(rect[row])):
                box = (rect[row][col][0][1], rect[row][col][0][0], rect[row][col][1][1], rect[row][col][1][0])
                temp_img = image.crop(box)
                '''if row > 2 and col < 5:
                    result = self.read_word2(temp_img)
                else:'''
                ostr = StringIO()
                temp_img.save(ostr, format='JPEG')
                binary_data = ostr.getvalue()
                result = self.read_word(binary_data)
                row_word.append(result)
                count_words = count_words + 1
                self.progress = float(count_words) / self.sum_words
                print self.progress, '%'
            words.append(row_word)
        image.close()
        return words


    # 将img_dot 显示在图片上
    def save_cell_img(self, rect, path):
        image = Image.open(self.img_path)
        for row in range(len(rect)):
            for col in range(len(rect[row])):
                box = (rect[row][col][0][1], rect[row][col][0][0], rect[row][col][1][1], rect[row][col][1][0])
                temp_img = image.crop(box)
                name = path + 'img' + str(row) + '-' + str(col) + '.png'
                temp_img.save(name)

    # 将交点映射到图片上
    def mapping_on_image(self, table):
        image = Image.open(self.img_path)
        # transfor image to ndarray
        xyArr = np.asarray(image)
        xyArr.flags['WRITEABLE'] = True
        for row in table:
            for cell in row:
                xyArr[cell[0]][cell[1]] = np.array([255, 0, 0])
        image.close()
        return xyArr

import flet as ft
from itertools import permutations, product
from random import randint, choice
from flet_core.border import BorderSide
from flet_core.buttons import RoundedRectangleBorder
from platform import system, release
from time import sleep
from threading import Thread
from expiringdict import ExpiringDict
 
debug = False
my_list = []  # 使用列表来暂存中间数
lst_nums = []  # 使用列表来放卡牌数字
pre_nums = ()  # 预生成的4位数字
pre_result = ""  # 保存程序给出的算法
after_nums = []  # 去掉中间数的剩余数字
score = 0  # 计分牌
seconds = 60  # 倒计时秒
cache = ExpiringDict(max_len=1, max_age_seconds=0.5)  # 按键暂存器，延时0.5s
 
 
def main(page: ft.Page):
    global after_nums, pre_nums, pre_result, my_list, seconds, lst_nums
 
    page.theme_mode = ft.ThemeMode.LIGHT  # change DARK to LIGHT
    page.window_width = 650
    page.window_height = page.window_width * 0.75
    page.window_resizable = True
    page.title = '智力大挑战 - 24点 - ©邵东俊'
 
    # 加了对操作系统的判断,因为小于 win10的系统不支持 flutter 的 audio 组件
    if debug: print(system().lower(), int(release().split(".", 2)[0]))
    try:
        if system().lower() == "windows" and int(release().split(".", 2)[0]) < 8:
            pass
        else:
            pass
        '''
            audio_win = ft.Audio(src="https://test123.upyun.com/win.mp3", autoplay=False)
            audio_fail = ft.Audio(src="https://test123.upyun.com/tack.mp3", autoplay=False)
            page.overlay.append(audio_fail)
            page.overlay.append(audio_win)
        '''
    except Exception as e:
        pass
 
    # 封装一个倒计时的类
    class Countdown(ft.UserControl):
        def __init__(self, seconds):
            super().__init__()
            self.seconds = seconds
 
        def did_mount(self):
            self.running = True
            self.th = Thread(target=self.update_timer, args=(), daemon=True)
            self.th.start()
 
        def will_unmount(self):
            self.running = False
 
        def update_timer(self):
            # 查看界面上是否只剩下最后8个元素，包括最后一张卡
            while self.running and len(lst_nums) > 1:
                mins, secs = divmod(self.seconds, 60)
                self.countdown.value = "{:02d}:{:02d}".format(mins, secs)
                self.update()
                if self.seconds == 0:  # 如果时间到,就提示加油,再开一局
                    self.running = False
                    result_again(result=False)
                else:
                    self.seconds -= 1
                    sleep(1)
 
        def build(self):
            self.countdown = ft.Text(weight=ft.FontWeight.BOLD, color=ft.colors.RED)
            return self.countdown
 
    # 判断随机生成的4个数字是否满足有24点的解法
    def is24():
        nums = []
        pre_24 = [
            ([2, 2, 2, 9], "2 + 2 * ( 2 + 9 )"),
            ([2, 7, 8, 9], "2 * ( 7 + 9 ) - 8"),
            ([1, 2, 7, 7], "( 7 * 7 - 1 ) / 2"),
            ([4, 4, 10, 10], "( 10 * 10 - 4 ) / 4"),
            ([6, 9, 9, 10], "10 * 9 / 6 + 9"),
            ([1, 5, 5, 5], "( 5 - 1 / 5 ) * 5"),
            ([2, 5, 5, 10], "( 5 - 2 / 10 ) * 5"),
            ([1, 4, 5, 6], "4 / ( 1 - 5 / 6 )"),
            ([3, 3, 8, 8], "8 / ( 3 - 8 / 3 )"),
            ([3, 3, 7, 7], "( 3 + 3 / 7 ) * 7 "),
            ([4, 4, 7, 7], "( 4 - 4 / 7 ) * 7 "),
        ]
 
        for i in range(4):
            nums.append(randint(1, 10))
 
        for nums in permutations(nums):  # 四个数
            for ops in product("+-*/", repeat=3):  # 三个运算符（可重复）
                # 构造三种中缀表达式 (bsd)
                bds1 = '( {0} {4} {1} ) {5} ( {2} {6} {3} )'.format(*nums, *ops)  # (a+b)*(c-d)
                bds2 = '( ( {0} {4} {1} ) {5} {2} ) {6} {3}'.format(*nums, *ops)  # (a+b)*c-d
                bds3 = '{0} {4} ( {1} {5} ( {2} {6} {3} ) )'.format(*nums, *ops)  # a/(b-(c/d))
                for bds in [bds1, bds2, bds3]:  # 遍历
                    try:
                        if abs(eval(bds) - 24.0) < 1e-10:  # eval函数
                            return nums, bds
                    except ZeroDivisionError:  # 零除错误！
                        continue
        return choice(pre_24)  # 如果没有，就随机给出默认一组数字
 
    # 判断结果是成功还是失败
    def result_again(result=True):
        global score
        if result:
            score += 10
            str_res = "恭喜挑战成功!"
            #if page.overlay: audio_win.play()
        else:
            score -= 5
            str_res = "加油，再来一次"
            #if page.overlay: audio_fail.play()
        dlg = ft.AlertDialog(
            title=ft.Text(str_res, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD, color=ft.colors.RED),
            on_dismiss=lambda e: new_or_again()
        )
        dlg.open = True
        page.dialog = dlg
        page.update()
 
    # 重新开局 或 复盘重来
    def new_or_again(new=True):
        global after_nums, pre_nums, pre_result, my_list
        my_list.clear()
        if new:
            pre_nums, pre_result = is24()
            after_nums = list(pre_nums)
            if page.controls:
                page.controls.pop(0)  # 重开一局，先清除前面的倒计时和计分
                page.controls.insert(0, ft.Row([ft.Text(f"分数：{score:<10d} "), Countdown(seconds)],
                                               alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        else:
            after_nums = list(pre_nums)
        gen_cards(after_nums)
 
    # 按键点击卡片的事件或者键盘事件
    def on_button_keyboard(e):
        global after_nums, pre_nums, pre_result, my_list
        # 获取卡片按键的信息或者 按键转小写(默认输入都是大写字符)
        data = e.control.data if e.control.data else e.key.lower()
 
        # 屏蔽一些不相关的按键，减少干扰
        if data or data in ['+', '-', 'x', '*', '/'] or data.isdigit():
            data = "*" if data == "x" else data
            data = "//" if data == "/" else data
        else:
            return
 
        if debug: print(e, " ^^^ ", type(data), " ^^^ ", data)
 
        # 如果传递的是: 运算符
        if data in ['+', '-', '*', '//']:
            # 必须保证列表里已经有数字，且最后一个元素也不是运算符
            if my_list:
                my_list.pop() if my_list[-1] in ['+', '-', '*', '//'] else my_list
                my_list.append(data)
        else:  # 如果传递的是非运算符
            # 如果暂存器里的按键没有失效，则拼接
            if cache.get("key"):
                data = cache.get("key") + data
            cache["key"] = data
 
            if e.control.data:
                id, data = map(int, data.split("#"))
            else:
                data = int(data) if data.isdigit() else data
                # 防止按键输入的是非卡片里的数字，做一层筛选
                if data in after_nums:
                    id, data = after_nums.index(data), data
                else:
                    return
 
            if not my_list:  # 如果是空列表，直接添加
                after_nums[id] = None  # 用None这个特殊数字来表示这是一个被选中的卡片
                my_list.append(data)
            else:
                if my_list[-1] not in ['+', '-', '*', '//']:
                    # 把中间变量复原到原来列表中的位置
                    after_nums[after_nums.index(None)] = my_list.pop()
                after_nums[id] = None  # 用None这个特殊数字来表示这是一个被选中的卡片
                my_list.append(data)
 
        if debug: print(my_list, " --- ", after_nums)
 
        if len(my_list) == 3:  # 如果暂存列表里有 3个元素，表示可以计算中间结果了
            try:
                if debug: print(my_list, " <<<")
                result = str(eval(' '.join(map(str, my_list))))
                my_list.clear()
                # 计算出中间结果后，清空暂存列表，并把中间结果放入列表里，重新绘制卡片
                after_nums = [i for i in after_nums if i is not None]
                after_nums.append(int(result))
                gen_cards(after_nums)
            except Exception as e:
                pass
        else:
            gen_cards(after_nums)
 
    # 提交按键
    def submit_button_clicked(e):
        data = e.control.data if e.control.data else e.key.lower()
 
        # 判断提交信息是不是合法字符
        if data in ["new", "again", "result", "escape"]:
            if debug: print(data, " <<< ", pre_nums, " <<< ", pre_result)
            if data == "new":  # 重新开局，重新生成新的数字和绘制卡片
                new_or_again()
            elif data == "again" or data == "escape":  # 如果计算失误，重新来一次
                new_or_again(new=False)
            else:  # 也可以直接点击获取答案
                dlg = ft.AlertDialog(
                    title=ft.Text(pre_result, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD))
                dlg.open = True
                page.dialog = dlg
                if page.overlay: audio_fail.play()
            page.update()
 
    # 发片和绘制卡片的主逻辑
    def gen_cards(slist):
        global after_nums, pre_nums, pre_result, my_list, score, seconds, lst_nums
        # slist.sort()  # 用记住位置的方式来处理，就不需要每次都排序了
        lst_nums = []  # 使用列表来放卡牌数字
        select = False
        if debug: print(slist, ' *** ', my_list, ' *** ', end="")
 
        # 使用循环生成要绘制的卡片，也包括计算过程的中间值
        for i, v in enumerate(slist):
            if v == None and not select:  # 如果是None就表示这个位置已经被选中，就不能点击了
                select = True
                _ = ft.Container(
                    content=ft.ElevatedButton(
                        bgcolor=ft.colors.AMBER,
                        content=ft.Text(value=my_list[0], size=33),
                        disabled=True,
                    ),
                    bgcolor=ft.colors.GREEN,
                    padding=1,
                    width=(page.window_width - 50) // 4,
                    height=(page.window_width - 50) // 4 * 1.6,
                    border=ft.border.all(2)
                )
            else:
                _ = ft.Container(
                    content=ft.ElevatedButton(
                        style=ft.ButtonStyle(
                            animation_duration=500,
                            side={
                                ft.MaterialState.DEFAULT: BorderSide(1, ft.colors.GREEN),
                                ft.MaterialState.HOVERED: BorderSide(15, ft.colors.GREEN),
                            },
                        ),
                        content=ft.Text(value=v, size=35),
                        data=str(i) + "#" + str(v),  # 把位置和数字打包传参过去
                        on_click=on_button_keyboard,
                    ),
                    bgcolor=ft.colors.GREEN,
                    padding=2,
                    width=(page.window_width - 50) // 4,
                    height=(page.window_width - 50) // 4 * 1.6,
                    border=ft.border.all(0)
                )
            lst_nums.append(_)
 
        # 使用循环生成要绘制的运算符
        lst_opts = []
        select2 = False
        for i, v in enumerate(["+", "-", "*", "//"]):
            if v in my_list and not select2:
                if v == "//": v = "/"
                if v == "*": v = "x"
                select2 = True
                _ = ft.Container(
                    content=ft.ElevatedButton(
                        bgcolor=ft.colors.AMBER,
                        content=ft.Text(value=v, size=28),
                        disabled=True,
                    ),
                    bgcolor=ft.colors.BLUE,
                    padding=1,
                    width=(page.window_width - 40) // 8,
                    height=(page.window_width - 40) // 8,
                    border=ft.border.all(0)
                )
            else:
                if v == "//": v = "/"
                if v == "*": v = "x"
                _ = ft.Container(
                    content=ft.ElevatedButton(
                        style=ft.ButtonStyle(
                            animation_duration=500,
                            side={
                                ft.MaterialState.DEFAULT: BorderSide(0, ft.colors.BLUE),
                                ft.MaterialState.HOVERED: BorderSide(8, ft.colors.BLUE),
                            },
                        ),
                        content=ft.Text(value=v, size=28),
                        data=v,
                        on_click=on_button_keyboard,
                    ),
                    bgcolor=ft.colors.BLUE,
                    padding=1,
                    width=(page.window_width - 40) // 8,
                    height=(page.window_width - 40) // 8,
                    border=ft.border.all(0)
                )
            lst_opts.append(_)
 
        lst_menu = []
        opts_btn = {"again": "还原", "new": "开始", "result": "答案"}
        for i, key in enumerate(opts_btn):
            _ = ft.ElevatedButton(
                style=ft.ButtonStyle(
                    bgcolor=ft.colors.RED_400,
                    color=ft.colors.WHITE,
                    padding=18,
                    animation_duration=500,
                    side={
                        ft.MaterialState.DEFAULT: BorderSide(0, ft.colors.BLUE),
                        ft.MaterialState.HOVERED: BorderSide(1, ft.colors.BLUE),
                    },
                    shape={
                        ft.MaterialState.HOVERED: RoundedRectangleBorder(radius=200),
                        ft.MaterialState.DEFAULT: RoundedRectangleBorder(radius=20),
                    }),
                content=ft.Text(value=opts_btn[key], weight=ft.FontWeight.BOLD, size=20),
                data=key,
                on_click=submit_button_clicked,
            )
            lst_menu.append(_)
 
        if debug: print(len(lst_nums), "items")
        if page.controls:
            del page.controls[1:3]  # controls 是个列表,一定要删除对应的才能添加新的
            page.controls = page.controls[0:1] + [
                ft.Row(lst_nums, alignment=ft.MainAxisAlignment.START if len(lst_nums) <4 else ft.MainAxisAlignment.SPACE_AROUND), 
                ft.Row(lst_opts, alignment=ft.MainAxisAlignment.SPACE_AROUND)
                ] + page.controls[1:]
        else:
            page.add(
                ft.Row([ft.Text(f"分数：{score:<10d} "), Countdown(seconds)],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row(lst_nums, alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Row(lst_opts, alignment=ft.MainAxisAlignment.SPACE_AROUND),
                ft.Row(lst_menu, alignment=ft.MainAxisAlignment.SPACE_EVENLY)
            )
 
        # 判断最后一个列表的元素就是24时，表示挑战成功 !
        if len(slist) == 1:
            if slist[0] == 24:
                result_again()
            else:
                result_again(result=False)
        page.update()
 
    page.on_keyboard_event = on_button_keyboard
    page.on_keyboard_event = submit_button_clicked
    pre_nums, pre_result = is24()
    after_nums = list(pre_nums)
    if debug: print(pre_nums, ' --  ', pre_result)
 
    # 第一次发牌
    gen_cards(after_nums)
 
 
ft.app(target=main)
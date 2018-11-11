import send_request_multiproc
import math
from threading import Thread
from multiprocessing import freeze_support
from PIL import Image, ImageTk
from tkinter import Tk, Canvas, CENTER, SW, W, END, ACTIVE, DISABLED, Frame, ALL, IntVar, StringVar, Label as LabelOld
import webbrowser
from tkinter.ttk import Label, Entry, Button, Style, Progressbar
import requests
import io
import sys

hi_res_preview = False


class PixivSort:
    curr_search_result = []
    image_files = []
    images_obj = []
    image_list = []
    current_page = 1
    loading_img = None
    image_raiting_labels = []
    image_pages_labels = []

    def __init__(self):
        self.pth = "./"
        try:
            self.pth = sys._MEIPASS + "/"
        except Exception:
            pass

        self.root = Tk()
        self.root.title('PixivSort by Zettroke')
        self.root.iconbitmap(self.pth[:-1] + "\\" + 'icon.ico')
        self.progress_bar_var = IntVar()
        self.progress_bar_label_var = StringVar()
        self.frame = Frame(self.root, height=100, width=1000, bg='#0094DC')
        self.frame.place(x=0, y=0)
        Style().configure("TButton", padding=1, relief="flat",
                                                background="#0094DC")
        Style().configure("TLabel", background="#0094DC")
        Style().configure("C.TButton", padding=0, relief="flat", font="Arial 12")
        self.root.minsize(1000, 810)
        self.root.maxsize(1000, 810)
        self.canvas = Canvas(self.root, width=1000, height=2000, bg='white')

        self.canvas.place(x=0, y=100)
        self.canvas.bind('<Button-1>', self.press)

        self.progress_bar = Progressbar(self.root, length=915, orient='horizont', variable=self.progress_bar_var, maximum=1000)
        self.progress_bar.place(x=0, y=790)

        self.progress_bar_label = LabelOld(self.root, textvariable=self.progress_bar_label_var, font='Arial 10', bg='white')
        self.progress_bar_label.place(x=915, y=787.5)

        cnv = Canvas(self.root, width=300, height=100, bg='#0094DC', bd=0, highlightthickness=0, relief='ridge')
        cnv.place(x=0, y=0)
        MyLabel = ImageTk.PhotoImage(Image.open(self.pth + 'Label.png').resize((250, 100), Image.BICUBIC))
        cnv.create_image(125, 52.5, image=MyLabel)

        label = Label(self.root, text='Search', anchor=CENTER, font='Arial 16')
        label.place(x=500, y=20)

        self.total_pages_label = Label(self.root, text='/0', anchor=W, font='Arial 14')
        self.total_pages_label.place(x=920, y=70)

        self.button = Button(self.root, text='Go!')
        self.button.place(x=650, y=50)
        self.button.bind('<Button-1>', self.search)

        button_page_inc = Button(self.root, text='>', width=1)
        button_page_dec = Button(self.root, text='<', width=1)
        button_page_dec.place(x=845, y=72)
        button_page_inc.place(x=970, y=72)
        button_page_inc.bind('<Button-1>', self.page_button)
        button_page_dec.bind('<Button-1>', self.page_button)

        self.loading_img = ImageTk.PhotoImage(Image.open(self.pth + 'loading.png').resize((170, 170), Image.BICUBIC))

        self.entry = Entry(self.root, width=18, font='Arial 14')
        self.entry.place(x=430, y=50)
        self.entry.bind('<Return>', self.search)
        self.entry_page = Entry(self.root, width=5, font='Arial 14')
        self.entry_page.place(x=860, y=70)
        self.entry_page.bind('<Return>', self.show_new)

        self.root.mainloop()

    def press(self, event):
        tap = event.widget.find_overlapping(event.x, event.y, event.x+1, event.y+1)
        if len(tap) != 0:
            tap = int(event.widget.gettags(tap[0])[0])
            img = self.image_list[tap-1]
            if img[3] == 1:
                webbrowser.open("https://www.pixiv.net/member_illust.php?mode=medium&illust_id=" + str(img[0]))
            else:
                webbrowser.open("https://www.pixiv.net/member_illust.php?mode=manga&illust_id=" + str(img[0]))

    def set_total_pages(self, total):

        self.total_pages_label.config(text='/' + str(math.ceil(40000/15 if total/15 > 40000/15 else total/15)))
        self.entry_page.delete(0, END)
        self.entry_page.insert(0, '1')
        self.current_page = 1

    def search(self, event):
        event.widget.config(state=DISABLED)
        self.progress_bar_label_var.set('downloading...')

        Thread(target=send_request_multiproc.search, args=(self.entry.get(), self.done, self.progress_update), daemon=True).start()

    def done(self, res):
        self.curr_search_result = res
        self.set_total_pages(len(res))
        self.show()
        self.entry.config(state=ACTIVE)

    def progress_update(self, done, total):
        print("done", round(done/total*100, 2))
        self.root.after_idle(self.change_pbar_value, (done/total))

    def change_pbar_value(self, val):
        self.progress_bar_var.set(val*1000)

    def load_image(self, num):
        if hi_res_preview:
            f = io.BytesIO(requests.get(self.image_list[num][1], headers={"Referer": "https://www.pixiv.net/"}).content)
        else:
            f = io.BytesIO(requests.get(self.image_list[num][2], headers={"Referer": "https://www.pixiv.net/"}).content)
        image = ImageTk.PhotoImage(Image.open(f).resize((170, 170), Image.BICUBIC))
        self.image_files.append(image)
        self.canvas.itemconfig(self.images_obj[num], image=image)

    def show_new(self, event=None):
        self.current_page = int(self.entry_page.get())
        self.show()

    def page_button(self, event):
        if event.widget.cget('text') == '>':
            temp = int(self.entry_page.get())
            self.entry_page.delete(0, END)
            self.entry_page.insert(0, str(temp+1))
            self.show_new()
        elif event.widget.cget('text') == '<' and self.current_page > 1:
            temp = int(self.entry_page.get())
            self.entry_page.delete(0, END)
            self.entry_page.insert(0, str(temp-1))
            self.show_new()

    def show(self, event=None):
        self.button.config(state=ACTIVE)
        for i in self.image_pages_labels:
            i.destroy()
        for i in self.image_raiting_labels:
            i.destroy()
        self.image_pages_labels.clear()
        self.image_raiting_labels.clear()
        self.images_obj.clear()
        self.canvas.delete(ALL)
        try:
            # self.image_list = send_request.show(self.current_page*15-15, self.current_page*15)
            self.image_list = self.curr_search_result[self.current_page*15-15:self.current_page*15]
            y = 0
            x = 35
            for i in range(len(self.image_list)):
                if i % 5 == 0:
                    y += 220
                    x = 35
                self.images_obj.append(self.canvas.create_image(x, y, image=self.loading_img, anchor=SW, tags=str(i+1)))
                label1 = LabelOld(self.root, text='Raiting: ' + str(self.image_list[i][4]), bg='white')
                label1.place(x=x, y=y+100)
                self.image_raiting_labels.append(label1)
                label2 = LabelOld(self.root, text='Pages: ' + str(self.image_list[i][3]), bg='white')
                label2.place(x=x+120, y=y+100)
                self.image_pages_labels.append(label2)
                x += 190
            for i in range(len(self.image_list)):
                # self.image_load_queue.put(i)
                Thread(target=self.load_image, args=(i,), daemon=True).start()
        except Exception:
            pass


if __name__ == '__main__':
    freeze_support()
    PixivSort()

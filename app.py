from tkinter import *
from tkinter import filedialog
from PIL import ImageTk, Image
import subprocess

import encoder
import decoder
import os

#root.attributes('-fullscreen',True)

get_name = ''
def open_file():
   file = filedialog.askopenfile(mode='r')
   if file:
        #Reset
        img_after.image=''
        info_img_after.config(text="")
        
        img = Image.open(file.name)
        size_file = round(os.stat(file.name).st_size / 1048576, 2)
        width, height = img.size
        # #Resize the Image using resize method
        resized_image= img.resize((200,200), Image.Resampling.LANCZOS)
        info_img_init.config(text="Kích thước: {} X {} ~ {} MB".format(width, height, size_file))
        img = ImageTk.PhotoImage(resized_image)
        img_init.configure(image=img, width=200, height=200)
        img_init.image=img
       

        btn_compression.grid(column=0, row=5, columnspan=2, sticky='EW', pady=20)
        global get_name
        get_name = file.name
       

def compresstion_jpege():
  
    # path = os.path.realpath("E:/python/jpeg-python/t3.jpg")
    # os.startfile(path)

    encoder.main(get_name)
    image = decoder.main()
    width, height = image.size
    resized_image= image.resize((200,200), Image.Resampling.LANCZOS)

    img = ImageTk.PhotoImage(resized_image)
  
    size_file = round(os.stat("E:/python/jpeg-python/t3.jpg").st_size / 1048576, 2)
    
    info_img_after.config(text="Kích thước: {} X {} ~ {} MB".format(width, height, size_file))

    img_after.configure(image=img, width=200, height=200)
    img_after.image=img
    
win = Tk()
win.geometry("600x650")
win.title("Nén ảnh JPEG")
label = Label(win, justify='center', text="Chọn ảnh muốn nén", font=('Georgia 13'), padx=30, pady=20)
label.grid(column=0, row=0, columnspan=2, sticky='EW')

# Button choose file
btn_file = Button(win, justify='center', text="File", background='blue', fg='white', font=('Georgia 13', 10, 'bold'), border=2, command=open_file,)
btn_file.grid(column=0, row=1, columnspan=1, sticky='n', ipadx=20, pady=20)

# Image init
label_img_init = Label(win, text="Ảnh ban đầu", font=('Georgia 13'), padx=30)
label_img_init.grid(column=0, row=2, columnspan=1, sticky='EW')

img_init = Label(win, text='')
img_init.grid(column=0, row=3, columnspan=1, sticky='EW')

info_img_init = Label(win, text='')
info_img_init.grid(column=0, row=4, columnspan=1, sticky='EW')

# Image after
label_img_after = Label(win, text="Ảnh sau nén", font=('Georgia 13'), padx=30)
label_img_after.grid(column=1, row=2, columnspan=1, sticky='EW')

img_after = Label(win, text='')
img_after.grid(column=1, row=3, columnspan=1, sticky='EW')

info_img_after = Label(win, text='')
info_img_after.grid(column=1, row=4, columnspan=1, sticky='EW')


# Compression button
btn_compression = Button(win, text="Nén", background='green', font=('Georgia 13', 10, 'bold'), fg='white', command=compresstion_jpege)


Grid.columnconfigure(win,0, weight=1)
Grid.columnconfigure(win,1, weight=1)

win.mainloop()
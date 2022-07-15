# Simple File organizer

'''
Put this script in a messy folder filled with images and video files 
and run it to create a "Years" folder with the media files sorted by months in each year.
You can also change what types of files to look for in your folder
by simply adding to or changing the following lists: `imgFormats` and `videoFormats`.
NOTE: This script can also delete duplicates (by searcing for " 2" at the end of file names) and files starting with "._".
This is disabled by default, to enable set `DELETE` flag to True!
'''

import os
import shutil
from datetime import datetime
import calendar
from PIL import Image
from PIL.ExifTags import TAGS
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from tkinter import ttk
import tkinter as tk
from tkinter.filedialog import askdirectory
from tkinter import messagebox
from collections import Counter
import itertools
from pathlib import Path

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

DATE_TIME_ORIG_TAG = 36867
DELETE = False

imgFormats = ['png', 'jpg', 'jpeg']
videoFormats = ['m4v', 'mov', 'mp4']
options      = [
                "",
                "Year",
                "Month",
                "Day",
                "Custom",
                "None"
            ]
cancel        = False
imgFileList   = []
vidFileList   = []
newFolderLvls = ["year","month","day"]

# root window
root = tk.Tk()
root.eval('tk::PlaceWindow . center')
root.geometry('400x220')
root.title('Simple File Organizer')
root.iconbitmap(resource_path("fav.ico"))
root.resizable(0, 0)

# labels value
progString = tk.StringVar()
infoString1 = tk.StringVar()
infoString2 = tk.StringVar()

# progressbar
pb = ttk.Progressbar(
    root,
    orient='horizontal',
    mode='determinate',
    length=380
)


def setNewFolderLvls(event):
    hide_button(inputField1)
    hide_button(inputField2)
    hide_button(inputField3)
    if folderLvl1.get() == "Custom":
        show_button(inputField1,0.18, 0.3)
        newFolderLvls[0] = str(customFolderLvl1.get())
    elif folderLvl1.get() == "None":
        newFolderLvls[0] = None
    else:
        newFolderLvls[0] = str(folderLvl1.get().lower())

    if folderLvl2.get() == "Custom":
        show_button(inputField2,0.48, 0.3)
        newFolderLvls[1] = str(customFolderLvl2.get())
    elif folderLvl2.get() == "None":
        newFolderLvls[1] = None
    else:
        newFolderLvls[1] = str(folderLvl2.get().lower())

    if folderLvl3.get() == "Custom":
        show_button(inputField3,0.78, 0.3)
        newFolderLvls[2] = str(customFolderLvl3.get())
    elif folderLvl3.get() == "None":
        newFolderLvls[2] = None
    else:
        newFolderLvls[2] = str(folderLvl3.get().lower())
    root.update()
    print(newFolderLvls)

# place the progressbar
pb.grid(column=0, row=0, columnspan=2, padx=10, pady=20)

progLabel = ttk.Label(root, textvariable = progString, font = "TkDefaultFont 9")
progLabel.place(relx=0.5, rely=0.5, anchor='center')

infoLabel1 = ttk.Label(root, textvariable = infoString1, font = "TkDefaultFont 9")
infoLabel1.place(relx=0.5, rely=0.62, anchor='center')

infoLabel2 = ttk.Label(root, textvariable = infoString2, font = "TkDefaultFont 8 italic")
infoLabel2.place(relx=0.5, rely=0.7, anchor='center')

#Folder levels

folderLvl1 = tk.StringVar()
folderLvl2 = tk.StringVar()
folderLvl3 = tk.StringVar()

dropDown1 = ttk.OptionMenu(root, folderLvl1, *options, command=setNewFolderLvls)
dropDown2 = ttk.OptionMenu(root, folderLvl2, *options, command=setNewFolderLvls)
dropDown3 = ttk.OptionMenu(root, folderLvl3, *options, command=setNewFolderLvls)

dropDown1.place(relx=-1, rely=-1, anchor='center', width=110)
dropDown2.place(relx=-1, rely=-1, anchor='center', width=110)
dropDown3.place(relx=-1, rely=-1, anchor='center', width=110)

folderLvl1.set(options[1])
folderLvl2.set(options[2])
folderLvl3.set(options[3])

#Custom foler levels

customFolderLvl1 = tk.StringVar()
customFolderLvl2 = tk.StringVar()
customFolderLvl3 = tk.StringVar()

inputField1 = tk.Entry(root,textvariable = customFolderLvl1, font=('calibre',10,'normal'))
inputField2 = tk.Entry(root,textvariable = customFolderLvl2, font=('calibre',10,'normal'))
inputField3 = tk.Entry(root,textvariable = customFolderLvl3, font=('calibre',10,'normal'))

inputField1.place(relx=-1, rely=-1, anchor='center', width=90)
inputField2.place(relx=-1, rely=-1, anchor='center', width=90)
inputField3.place(relx=-1, rely=-1, anchor='center', width=90)

inputField1.bind('<FocusOut>', setNewFolderLvls)
inputField2.bind('<FocusOut>', setNewFolderLvls)
inputField3.bind('<FocusOut>', setNewFolderLvls)

# place buttons
selectSourceBt = ttk.Button(root, text="Select folder")
selectSourceBt.place(relx=0.4, rely=0.9, anchor='center')

moveFilesBt = ttk.Button(root, text="Move files")
moveFilesBt.place(relx=-1, rely=-1, anchor='center')

canceleBt = ttk.Button(root, text='Cancel')
canceleBt.place(relx=0.6, rely=0.9, anchor='center')

def progress(percentToAdd = 1, maxPercent = 100):
    print(percentToAdd)
    if pb['value'] <= maxPercent:
        pb['value'] += percentToAdd
        infoString1.set("Current Progress: "+str("%0.2f" % pb['value'])+"%")
        root.update()
    else:
        pb['value'] = 0


#Reset all parameters and data
def stop(event):
    global imgFileList
    global vidFileList
    global cancel
    pb.stop()
    cancel = True
    imgFileList = []
    vidFileList = []
    pb['value'] = 0
    progString.set("")
    infoString1.set("")
    infoString2.set("")
    folderLvl1.set(options[1])
    folderLvl2.set(options[2])
    folderLvl3.set(options[3])
    hide_button(moveFilesBt)
    hide_button(dropDown1)
    hide_button(dropDown2)
    hide_button(dropDown3)
    hide_button(inputField1)
    hide_button(inputField2)
    hide_button(inputField3)
    show_button(selectSourceBt,0.4, 0.9)
    root.update()

# show hide buttons
def hide_button(widget):
    # This will remove the widget from toplevel
    widget.place(relx=-1, rely=-1, anchor='center')
  
def show_button(widget,relx=0.5,rely=0.5):
    # This will recover the widget from toplevel
    widget.place(relx=relx, rely=rely, anchor='center')

#Files2Folder application
def getSourceFiles(event):
    global imgFileList
    global vidFileList
    global cancel
    # shows dialog box and return the path
    selectedPath = askdirectory(title='Select Folder Of Files')
    unsupported = 0
    cancel=False
    if selectedPath:
        for path, subdirs, files in os.walk(selectedPath):
            for file in files:
                if file.split('.')[1].lower() in imgFormats:
                    imgFileList.append(str(path)+"/"+str(file))
                elif file.split('.')[1].lower() in videoFormats:
                    vidFileList.append(str(path)+"/"+str(file))
                else:
                    unsupported += 1

        progString.set("Selected source folder: "+selectedPath)
        infoString1.set("Number of files: "+str(len(imgFileList)+len(vidFileList))+" | Images: "+str(len(imgFileList))+" | Videos: "+str(len(vidFileList)))
        infoString2.set("Unsupported files were: "+str(unsupported))
        hide_button(selectSourceBt)
        show_button(moveFilesBt,0.4, 0.9)
        show_button(dropDown1,0.2, 0.3)
        show_button(dropDown2,0.5, 0.3)
        show_button(dropDown3,0.8, 0.3)
        pb['value'] = 0

    else:
        message = "No path was selected. A source patch is required to start organize."
        messagebox.showwarning('No selected path', message)

def createDirLvl(dateobj):
    dirpath = ""
    if dateobj:
        for folderLvl in newFolderLvls:
            if folderLvl == "year":
                dirpath += "/%s" % dateobj.year
            elif folderLvl == "month":
                dirpath += "/%s" % str(dateobj.month).zfill(2)+"-"+str(calendar.month_name[dateobj.month]) 
            elif folderLvl == "day":
                dirpath += "/%s" % "Day-"+str(dateobj.day).zfill(2)
            elif folderLvl != None:
                dirpath += "/%s" % folderLvl
        dirpath += "/"   
    return dirpath

def moveMediaToFolder(event):
    global imgFileList
    global vidFileList
    global cancel
    percentage = (1/(len(imgFileList)+len(vidFileList)))*100
    newpath = askdirectory(title='Select New Destination For Files')
    print(newpath)
    photos = []
    videos = []
    exceptions = []

    if newpath:
        progString.set("Moving files to: "+str(newpath))

        for imgFile, vidFile in itertools.zip_longest(imgFileList, vidFileList):
            if cancel:
                break
            # Extract data if image
            if imgFile:
                filename = os.path.basename(imgFile)
                filepath, file_extension = os.path.splitext(imgFile)
                print("\nProcessing image %s" % filename)
                try:
                    im = Image.open(imgFile)
                    exif = im._getexif()
                    im.close()
                    if exif is not None and DATE_TIME_ORIG_TAG in exif:
                        print("\tHas EXIF: %s" % exif[DATE_TIME_ORIG_TAG])
                        datestr = exif[DATE_TIME_ORIG_TAG].split()
                        dateobj = datetime.strptime(datestr[0], "%Y:%m:%d")
                        dirpath = newpath
                        dirpath += createDirLvl(dateobj)
                        os.makedirs(dirpath, exist_ok=True)
                        #os.rename(imgFile, dirpath + filename)
                        shutil.move(imgFile,dirpath + filename)
                        print("\tReady")
                        photos.append(filename)
                    else:
                        print("\tHas no EXIF! Trying os getmtime instead")
                        datestr = os.path.getmtime(imgFile)
                        dateobj = datetime.fromtimestamp(datestr)
                        dirpath = newpath
                        dirpath += createDirLvl(dateobj)                       
                        os.makedirs(dirpath, exist_ok=True)
                        #os.rename(imgFile, dirpath + filename)
                        shutil.move(imgFile,dirpath + filename)
                        print("\tReady")
                        photos.append(filename)
                except Exception as e:
                    exceptions.append(str(e))
                    print("\t"+str(e))
                progress(percentage) # update progress bar

            # Extract data if video
            if vidFile:
                filename = os.path.basename(vidFile)
                filepath, file_extension = os.path.splitext(vidFile)
                print("\nProcessing video %s" % filename)
                try:
                    parser = createParser(vidFile)
                    if not parser:
                        print("\tUnable to parse file %s" % filename)

                    with parser:
                        try:
                            metadata = extractMetadata(parser)
                        except Exception as err:
                            print("\tMetadata extraction error: %s" % err)
                            metadata = None
                    if not metadata:
                        print("\tUnable to extract metadata")
                    for line in metadata.exportPlaintext():
                        if line.split(':')[0] == '- Creation date':
                            dateobj = datetime.strptime(line.split(':')[1].split()[0], "%Y-%m-%d")
                            if(dateobj.year > 1910):
                                dirpath = newpath
                                dirpath += createDirLvl(dateobj)                                
                                os.makedirs(dirpath, exist_ok=True)
                                #os.rename(vidFile, dirpath + filename)
                                shutil.move(vidFile,dirpath + filename)
                                videos.append(filename)
                                print("\tReady")
                            else:
                                print("\tThe year "+str(dateobj.year)+" is not a credible file creation date. Trying os getmtime instead")
                                datestr = os.path.getmtime(vidFile)
                                dateobj = datetime.fromtimestamp(datestr)
                                dirpath = newpath
                                dirpath += createDirLvl(dateobj)                               
                                os.makedirs(dirpath, exist_ok=True)
                                #os.rename(vidFile, dirpath + filename)
                                shutil.move(vidFile,dirpath + filename)
                                videos.append(filename)
                                print("\tReady")
                except Exception as e:
                    exceptions.append(str(e))
                    print("\t"+str(e))
                progress(percentage) # update progress bar

        #Show exceptions for end-user if any
        if exceptions:
            noOfExeptions = len(exceptions)
            exceptions = Counter(exceptions)
            message = str(noOfExeptions)+" number of and "+str(len(exceptions))+" types of exceptions:\n\n"
            for key, value in Counter(exceptions).items():
                message+=str(value)+": "+key+"\n"
            messagebox.showwarning("Exceptions",message)

        noOfFiles = (len(imgFileList)+len(vidFileList))
        noOfCompletedImg = len(photos)
        noOfCompletedVid = len(videos)

        #reset filelist
        imgFileList = []
        vidFileList = []

        message = str(noOfCompletedImg+noOfCompletedVid)+"/"+str(noOfFiles)+" completed. "+str(noOfCompletedImg)+" photos and "+str(noOfCompletedVid)+" videos were moved and organized."
        messagebox.showinfo('Done', message)

        show_button(selectSourceBt,0.4, 0.9)
        folderLvl1.set(options[1])
        folderLvl2.set(options[2])
        folderLvl3.set(options[3])
        hide_button(moveFilesBt)
        hide_button(dropDown1)
        hide_button(dropDown2)
        hide_button(dropDown3)
        hide_button(inputField1)
        hide_button(inputField2)
        hide_button(inputField3)
        root.update()

    else:
        message = "No path was selected. The program requires a destination path to start organize."
        messagebox.showwarning('No selected destination', message)


# Bild functions to buttons
selectSourceBt.bind("<Button-1>", getSourceFiles)
moveFilesBt.bind("<Button-1>", moveMediaToFolder)
canceleBt.bind("<Button-1>", stop)

root.mainloop()
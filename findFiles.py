#!/usr/bin/env python3

import sys, shutil, readchar, traceback
import hashlib, os
import textdistance
from pathlib import PurePath, Path
from itertools import filterfalse
from tkinter import *
from tkinter import filedialog


def printExceptionDetails(inst, message, object):
    if message:
        print("Error processing '{}':".format(message, object))

    print(type(inst))  # the exception instance
    print(inst.args)  # arguments stored in .args
    print(inst)  # __str__ allows args to be printed directly, but may be overridden in exception subclasses


def writeToMD5File(md5File, md5hashes):
    with open(md5File, "a+") as afile:
        for md5hash in md5hashes:
            afile.write("{} *.\\{}\n".format(md5hash[0], md5hash[1]))


def lisItems(baseSourcePath, targetPath, verbose=0, silent=0):
    items = []
    beforeItem = ""
    baseSourcePathConcrete = Path(baseSourcePath)
    for item in baseSourcePathConcrete.iterdir():
        #        print("ItemType: '{}'".format(type(item)))
        try:
            items.append(item.name)
            print("'{}'/'{}':{},{},{},{},{},{}".format(beforeItem, item.name,
                                                       textdistance.hamming(beforeItem, item.name),
                                                       textdistance.levenshtein(beforeItem, item.name),
                                                       round(textdistance.jaro(beforeItem, item.name), 2),
                                                       #                                           round(textdistance.jaro_winkler(beforeItem, item.name),2),
                                                       textdistance.needleman_wunsch(beforeItem, item.name),
                                                       textdistance.smith_waterman(beforeItem, item.name),
                                                       round(textdistance.strcmp95(beforeItem, item.name), 2)
                                                       ))
            if 1 - textdistance.strcmp95(beforeItem, item.name) < 0.2:
                print("'{}'/'{}'".format(beforeItem, item.name))
            beforeItem = item.name
        except Exception as inst:
            printExceptionDetails(inst, "Error copying", item)
            print("inst:{}".format(inst))

    return items


def main(argv):
    verbose = 2
    silent = 1

    # Pruebas
    sourcePath = "y:\\romstest\\amstradcpc\\"
    targetPath = "y:\\romstest\\amstradcpc\\media\\images\\"

    textdistance.hamming('test', 'text')

    items = lisItems(sourcePath, targetPath)

    print("----------------------------------------------------------------------------------------------------")
    print("items:\n{}".format(items))
    print("\n----------------------------------------------------------------------------------------------------")


# -----------------constants---------------------

defaultSrcDir = "d:/MP3s"
defaultTargetDir = "d:/MP3s/NUEVOS"


# -----------------functions---------------------

def chooseSrcDir():
    srcDir = filedialog.askdirectory(title="Open", initialdir=root.srcDir.get())
    root.srcDir.set(srcDir)
    lstBoxSrcItems.delete(0, END)
    lstBoxSrcItems.insert(0, *os.listdir(srcDir))


def chooseTargetDir():
    targetDir = filedialog.askdirectory(title="Open", initialdir=root.targetDir.get())
    root.targetDir.set(targetDir)
    lstBoxTargetItems.delete(0, END)
    lstBoxTargetItems.insert(0, *os.listdir(targetDir))


root = Tk()
root.title("DiffFiles")
root.resizable(True,True)

root.srcDir = StringVar()
root.targetDir = StringVar()

#mainFrame = Frame(root, padx=5, pady=5, width=1000, height=500)

sourceGroup = LabelFrame(root, text="Source", padx=5, pady=5)
sourceGroup.grid(row=0, column=0, columnspan=1, padx=5, pady=5, sticky=E+W+N+S)
targetGroup = LabelFrame(root, text="Target",padx=5, pady=5)
targetGroup.grid(row=0, column=1, columnspan=1, padx=5, pady=5, sticky=E+W+N+S)

lblSrcDir = Label(sourceGroup, textvariable=root.srcDir, anchor="w")
lblSrcDir.grid(row=0, column=0, padx=5, pady=5, columnspan=1, sticky="w")
btnChooseSrcDir = Button(sourceGroup, text="Source", command=chooseSrcDir)
btnChooseSrcDir.grid(row=0, column=1, padx=5, pady=5, columnspan=1, sticky="e")

lblTargetDir = Label(targetGroup, textvariable=root.targetDir, anchor="w")
lblTargetDir.grid(row=0, column=0, padx=5, pady=5, columnspan=1, sticky="w")
btnChooseTargetDir = Button(targetGroup, text="Target", command=chooseTargetDir)
btnChooseTargetDir.grid(row=0, column=1, padx=5, pady=5, columnspan=1, sticky="e")

lstBoxSrcItems = Listbox(sourceGroup, width=50, height=25)
scrlBarBoxSrcItems = Scrollbar(sourceGroup, command=lstBoxSrcItems.yview)
scrlBarBoxSrcItems.grid(row=1, column=2, sticky="ns")
lstBoxSrcItems.grid(row=1, column=0, columnspan=2, sticky="nsew")
lstBoxSrcItems.config(yscrollcommand=scrlBarBoxSrcItems.set)

lstBoxTargetItems = Listbox(targetGroup, width=50, height=25)
scrlBarBoxTargetItems = Scrollbar(targetGroup, command=lstBoxTargetItems.yview)
scrlBarBoxTargetItems.grid(row=1, column=2, sticky="ns")
lstBoxTargetItems.grid(row=1, column=0, columnspan=2, sticky="nsew")
lstBoxTargetItems.config(yscrollcommand=scrlBarBoxTargetItems.set)


root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

#mainFrame.columnconfigure(0, weight=1)
#mainFrame.rowconfigure(0, weight=1)

sourceGroup.columnconfigure(0, weight=1)
sourceGroup.columnconfigure(1, weight=0)
sourceGroup.columnconfigure(2, weight=0)
sourceGroup.rowconfigure(0, weight=0)
sourceGroup.rowconfigure(1, weight=1)

targetGroup.columnconfigure(0, weight=1)
targetGroup.columnconfigure(1, weight=0)
targetGroup.columnconfigure(2, weight=0)
targetGroup.rowconfigure(0, weight=0)
targetGroup.rowconfigure(1, weight=1)



root.srcDir.set(defaultSrcDir)
root.targetDir.set(defaultTargetDir)

#mainFrame.pack()

root.mainloop()

# if __name__ == "__main__":
#    main(sys.argv)


#!/usr/bin/env python3

import sys, shutil, readchar, traceback
import hashlib, os
import tkinter

import textdistance
import more_itertools
from pathlib import PurePath, Path
from itertools import filterfalse
from tkinter import *
from tkinter import filedialog
from tkinter import ttk


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

def sourceItemSelected(event):
    selection = event.widget.curselection()
#    self.listbox.curselection()
    if selection:
        index = selection[0]
        data = event.widget.get(index)
        print(data)
#        table.delete(*table.get_children())
#        table.insert(parent='', index='end', id=len(table.get_children()), text='', values=(data, '1.000000'))
        items = os.listdir(targetDir)
        itemsEvaluated = {}
        for item in items:
            itemsEvaluated[item]=textdistance.strcmp95(data.lower(), item.lower())
#        for item in itemsEvaluated:
#            print("Item:{} - Distance:{}".format(item,itemsEvaluated.get(item)))
        itemsEvaluated = dict(sorted(itemsEvaluated.items(), key=lambda item: item[1], reverse=True))
        best_itemsEvaluated = dict(more_itertools.take(5,itemsEvaluated.items()))
        table.delete(*table.get_children())
        for item in best_itemsEvaluated:
            table.insert(parent='', index='end', id=len(table.get_children()), text='', values=(item,best_itemsEvaluated.get(item)))
            print("Item:{} - Distance:{}".format(item,best_itemsEvaluated.get(item)))
        print("---------------------------------------------------------------")

root = Tk()
root.title("DiffFiles")
root.resizable(True,True)
root.geometry('1700x1000')

root.srcDir = StringVar()
root.targetDir = StringVar()
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=1)
root.rowconfigure(0, weight=1)

# Source
sourceGroup = LabelFrame(root, text="Source", padx=5, pady=5)
sourceGroup.grid(row=0, column=0, columnspan=1, padx=5, pady=5, sticky="ewns")
sourceGroup.columnconfigure(0, weight=1)
sourceGroup.rowconfigure(1, weight=1)

lblSrcDir = Label(sourceGroup, textvariable=root.srcDir, anchor="w")
lblSrcDir.grid(row=0, column=0, padx=5, pady=5, columnspan=1, sticky="w")
btnChooseSrcDir = Button(sourceGroup, text="Source", command=chooseSrcDir)
btnChooseSrcDir.grid(row=0, column=1, padx=5, pady=5, columnspan=1, sticky="e")

lstBoxSrcItems = Listbox(sourceGroup, exportselection=0, width=60, height=40)
scrlBarBoxSrcItems = Scrollbar(sourceGroup, command=lstBoxSrcItems.yview)
scrlBarBoxSrcItems.grid(row=1, column=2, sticky="ns")
scrlBarBoxSrcItemsH = Scrollbar(sourceGroup, command=lstBoxSrcItems.xview, orient=tkinter.HORIZONTAL)
scrlBarBoxSrcItemsH.grid(row=2, column=0, columnspan=2, sticky="we")
lstBoxSrcItems.grid(row=1, column=0, columnspan=2, sticky="nsew")
lstBoxSrcItems.config(yscrollcommand=scrlBarBoxSrcItems.set,xscrollcommand=scrlBarBoxSrcItemsH.set)
lstBoxSrcItems.bind("<<ListboxSelect>>", sourceItemSelected)

# Target
targetGroup = LabelFrame(root, text="Target",padx=5, pady=5)
targetGroup.grid(row=0, column=1, columnspan=1, padx=5, pady=5, sticky="ewns")
targetGroup.columnconfigure(0, weight=1)
targetGroup.rowconfigure(1, weight=1)

lblTargetDir = Label(targetGroup, textvariable=root.targetDir, anchor="w")
lblTargetDir.grid(row=0, column=0, padx=5, pady=5, columnspan=1, sticky="w")
btnChooseTargetDir = Button(targetGroup, text="Target", command=chooseTargetDir)
btnChooseTargetDir.grid(row=0, column=1, padx=5, pady=5, columnspan=1, sticky="e")

lstBoxTargetItems = Listbox(targetGroup, exportselection=0, width=60, height=40)
scrlBarBoxTargetItems = Scrollbar(targetGroup, command=lstBoxTargetItems.yview)
scrlBarBoxTargetItems.grid(row=1, column=2, sticky="ns")
scrlBarBoxTargetItemsH = Scrollbar(targetGroup, command=lstBoxTargetItems.xview, orient=tkinter.HORIZONTAL)
scrlBarBoxTargetItemsH.grid(row=2, column=0, columnspan=2, sticky="we")
lstBoxTargetItems.grid(row=1, column=0, columnspan=2, sticky="nsew")
lstBoxTargetItems.config(yscrollcommand=scrlBarBoxTargetItems.set,xscrollcommand=scrlBarBoxTargetItemsH.set)

# Data
tableGroup = LabelFrame(root, text="Data",padx=5, pady=5)
tableGroup.grid(row=0, column=2, columnspan=1, padx=5, pady=5, sticky="ewn")
tableGroup.columnconfigure(0, weight=1)
tableGroup.rowconfigure(1, weight=1)

# Table
table = ttk.Treeview(tableGroup)
table['columns']= ('name', 'distance')
table.column("#0", width=0,  stretch=NO)
table.column("name",anchor="w", width=300)
table.column("distance",anchor="w", width=50)
table.heading("#0",text="",anchor=CENTER)
table.heading("name",text="Name",anchor=CENTER)
table.heading("distance",text="Distance",anchor=CENTER)
#table.columnconfigure(0, weight=1)
table.columnconfigure(0, weight=1)
table.columnconfigure(1, weight=1)
table.rowconfigure(0,weight=1)
table.grid(row=0, column=0, sticky="nwe")
scrlBarTable = Scrollbar(tableGroup, command=table.yview)
scrlBarTable.grid(row=0, column=1, sticky="ns")
#scrlBarTableH = Scrollbar(tableGroup, command=table.xview, orient=tkinter.HORIZONTAL)
#scrlBarTableH.grid(row=1, column=0, columnspan=2, sticky="we")
table.config(yscrollcommand=scrlBarTable.set) #,xscrollcommand=scrlBarTableH.set)


# Init data
root.srcDir.set(defaultSrcDir)
root.targetDir.set(defaultTargetDir)

# Init components data
lstBoxSrcItems.insert(0, *os.listdir(defaultSrcDir))
lstBoxTargetItems.insert(0, *os.listdir(defaultTargetDir))

sourceDir=defaultSrcDir
targetDir=defaultTargetDir


if __name__ == "__main__":
#    main(sys.argv)
    root.mainloop()


#!/usr/bin/env python3

import sys, shutil, readchar, traceback
import hashlib, os
import textdistance
from pathlib import PurePath,Path
from itertools import filterfalse


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
            print("'{}'/'{}':{},{},{},{},{},{}".format(beforeItem,item.name,
                                           textdistance.hamming(beforeItem,item.name),
                                           textdistance.levenshtein(beforeItem,item.name),
                                           round(textdistance.jaro(beforeItem, item.name),2),
#                                           round(textdistance.jaro_winkler(beforeItem, item.name),2),
                                           textdistance.needleman_wunsch(beforeItem, item.name),
                                           textdistance.smith_waterman(beforeItem, item.name),
                                           round(textdistance.strcmp95(beforeItem, item.name),2)
                  ))
            if 1-textdistance.strcmp95(beforeItem, item.name) < 0.2 :
                print("'{}'/'{}'".format(beforeItem,item.name))
            beforeItem=item.name
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


if __name__ == "__main__":
    main(sys.argv)

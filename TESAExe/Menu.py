from .String import *
from .DataString import *
import struct

def externalPointersFromXML(xNodes):
    titlePointers = []
    shortcutsPointers = []
    itemPointersPointers = []

    for xExternalPointers in xNodes:
        titleString = xExternalPointers.getAttribute("title")
        shortcutsString = xExternalPointers.getAttribute("shortcuts")
        itemPointersString = xExternalPointers.getAttribute("item_pointers")

        if titleString != "":
            titlePointers.append(ExternalPointer(titleString))

        if shortcutsString != "":
            shortcutsPointers.append(ExternalPointer(shortcutsString))

        if itemPointersString != "":
            itemPointersPointers.append(ExternalPointer(itemPointersString))

    return (titlePointers, shortcutsPointers, itemPointersPointers)

def externalPointersToXML(doc, titlePointers, shortcutsPointers, itemPointersPointers):
    def getPointerString(array, index):
        if array and index < len(array):
            return array[index].pointer

        return None

    pointersLen = []

    if titlePointers:
        pointersLen.append(len(titlePointers))

    if shortcutsPointers:
        pointersLen.append(len(shortcutsPointers))

    if itemPointersPointers:
        pointersLen.append(len(itemPointersPointers))

    externalPointers = []

    if len(pointersLen) > 0:

        maxLen = max(pointersLen)

        for i in xrange(maxLen):
            title = getPointerString(titlePointers, i)
            shortcuts = getPointerString(shortcutsPointers, i)
            itemPointers = getPointerString(itemPointersPointers, i)

            xExternalPointers = doc.createElement("external_pointers")

            if title:
                xExternalPointers.setAttribute("title", title)

            if shortcuts:
                xExternalPointers.setAttribute("shortcuts", shortcuts)

            if itemPointers:
                xExternalPointers.setAttribute("item_pointers", itemPointers)

            externalPointers.append(xExternalPointers)

    return externalPointers

def pointersDataStringForItems(items):

    pointers = []
    offset = 0

    for item in items:
        pointers.append(Pointer(item.id, offset))
        offset += 2

    data = "\x00" * (len(items) + 1) * 2

    return DataString(data, pointers)

class Menu:

    @staticmethod
    def fromXML(xMenu, idGen):
        ipAddress = xMenu.getAttribute("ip_address")
        id = int(xMenu.getAttribute("id"))

        xNodes = xMenu.getElementsByTagName("external_pointers")
        titlePointers, shortcutsPointers, itemPointersPointers = externalPointersFromXML(xNodes)

        xItems = xMenu.getElementsByTagName("items")[0]
        items = []

        for xMi in xItems.getElementsByTagName("mi"):

            itemAddress = xMi.getAttribute("address")
            item = DataString.fromXML(xMi)
            itemString = String(itemAddress, idGen(), False, [], [], item)
            items.append(itemString)

        pointersDataString = pointersDataStringForItems(items)
        pointerString = String(ipAddress, idGen(), True, itemPointersPointers, [], pointersDataString)

        titleString = None
        xTitles = xMenu.getElementsByTagName("title")

        if len(xTitles) > 0:
            xTitle = xTitles[0]
            titleDataString = DataString.fromXML(xTitle)
            titleAddress = xTitle.getAttribute("address")
            titleString = String(titleAddress, idGen(), False, titlePointers, [], titleDataString)

        xShortcuts = xMenu.getElementsByTagName("shortcuts")[0]
        shortcutsDataString = DataString.fromXML(xShortcuts)
        shortcutsAddress = xShortcuts.getAttribute("address")
        shortcutsString = String(shortcutsAddress, idGen(), False, shortcutsPointers, [], shortcutsDataString)

        return Menu(id, pointerString, titleString, shortcutsString, items)

    def __init__(self, id, pointers, title, shortcuts, items):
        self.id = id
        self.pointers = pointers
        self.title = title
        self.shortcuts = shortcuts
        self.items = items

    def toXML(self, doc):
        xMenu = doc.createElement("menu")

        xMenu.setAttribute("id", str(self.id))
        xMenu.setAttribute("ip_address", self.pointers.address)

        titlePointers = self.title and self.title.externalPointers or None
        shortcutsPointers = self.shortcuts and self.shortcuts.externalPointers or None
        itemPointers = self.pointers.externalPointers

        externalPointers = externalPointersToXML(doc, titlePointers, shortcutsPointers, itemPointers)
        for externalPointer in externalPointers:
            xMenu.appendChild(externalPointer)

        if self.title:
            xTitle = doc.createElement("title")

            xTitle.setAttribute("address", self.title.address)

            for xNode in self.title.data.toXML(doc):
                xTitle.appendChild(xNode)

            xMenu.appendChild(xTitle)

        if self.shortcuts:
            xShortcuts = doc.createElement("shortcuts")

            xShortcuts.setAttribute("address", self.shortcuts.address)

            for xNode in self.shortcuts.data.toXML(doc):
                xShortcuts.appendChild(xNode)

            xMenu.appendChild(xShortcuts)

        xItems = doc.createElement("items")

        for item in self.items:
            xMi = doc.createElement("mi")
            xMi.setAttribute("address", item.address)

            for xNode in item.data.toXML(doc):
                xMi.appendChild(xNode)

            xItems.appendChild(xMi)

        xMenu.appendChild(xItems)

        return xMenu

    def getAddress(self):
        return self.pointers.absoluteOffset

    def getStrings(self):

        strings = self.items[:]
        strings.append(self.pointers)

        if self.title:
            strings.append(self.title)

        if self.shortcuts:
            strings.append(self.shortcuts)

        return strings

import os, sys, re, struct
from xml.dom.minidom import parse, Document
from .Segment import *
from .IDGenerator import IDGenerator
from .DataString import *
from .DataResolver import getUsedStrings, getUnusedStrings
from .Translation import mergedTable

def openExe(exeFilename):
    """
    Opens exe with given filename.
    Return an object which represent TES Arena executable.

    Keyword arguments:
    exeFilename -- Filename of TES Arena unpacked executable.
    """

    basepath = os.path.dirname(__file__)
    doc = parse(os.path.join(basepath, "exe.xml"))
    xExe = doc.documentElement
    assert xExe.tagName == "exe"

    version = xExe.getAttribute("version")

    segments = []

    xSegments = xExe.getElementsByTagName("segment")

    idGen = IDGenerator(10000)

    for xSegment in xSegments:
        segments.append(Segment.fromXML(xSegment, idGen))

    exeData = open(exeFilename, "rb").read()

    for i in xrange(len(segments) - 1):
        segments[i].length = segments[i + 1].absoluteOffset - segments[i].absoluteOffset

    segments[len(segments) - 1].length = len(exeData) - segments[len(segments) - 2].absoluteOffset

    return Exe(version, segments, exeData)

class Exe:
    def __init__(self, version, segments, exeData):
        self.version = version
        self.segments = segments
        self.exeData = exeData
        self.resultExeData = exeData[:]

    def toXML(self, doc):
        xExe = doc.createElement("exe")
        xExe.setAttribute("version", self.version)

        for segment in self.segments:
            xExe.appendChild(segment.toXML(doc))

        return xExe

    def getSegmentAddress(self, absoluteOffset):
        for segment in self.segments:
            address = segment.getSegmentAddress(absoluteOffset)

            if address != None:
                return address

    def createEntryMap(self):
        idMap = {}

        for segment in self.segments:
            for string in segment.strings:
                idMap[string.id] = string

            for menu in segment.menus:
                idMap[menu.id] = menu

        return idMap

    def importLocale(self, xLocale, localeTable):

        translationTable = mergedTable(standardTable(), localeTable)

        assert xLocale.tagName == "locale"

        entryMap = self.createEntryMap()

        name = xLocale.getAttribute("name")
        version = xLocale.getAttribute("version")

        xStrings = xLocale.getElementsByTagName("string")

        for xString in xStrings:
            id = xString.getAttribute("id")
            data = DataString.fromXML(xString, translationTable)
            string = entryMap[int(id)]
            string.locale[name] = data

        xMenus = xLocale.getElementsByTagName("menu")

        for xMenu in xMenus:
            id = xMenu.getAttribute("id")
            menu = entryMap[int(id)]

            xTitles = xMenu.getElementsByTagName("title")

            if len(xTitles) > 0:
                xTitle = xTitles[0]
                titleData = DataString.fromXML(xTitle, translationTable)
                menu.title.locale[name] = titleData

            xShortcuts = xMenu.getElementsByTagName("shortcuts")[0]
            shortcutsData = DataString.fromXML(xShortcuts, translationTable)
            menu.shortcuts.locale[name] = shortcutsData

            itemDatas = []

            xItems = xMenu.getElementsByTagName("items")[0]

            for xMi in xItems.getElementsByTagName("mi"):
                itemData = DataString.fromXML(xMi, translationTable)
                itemDatas.append(itemData)

            for i in xrange(len(itemDatas)):
                itemData = itemDatas[i]
                menu.items[i].locale[name] = itemData

    def createLocaleTemplate(self, name):

        doc = Document()
        xLocale = doc.createElement("locale")
        xLocale.setAttribute("name", name)
        xLocale.setAttribute("version", self.version)

        for segment in self.segments:
            for string in getUsedStrings(segment.strings):
                if not string.binary:
                    xString = doc.createElement("string")
                    xString.setAttribute("id", str(string.id))

                    for xNode in string.data.toXML(doc):
                        xString.appendChild(xNode)

                    xLocale.appendChild(xString)


            for menu in segment.menus:
                if (menu.pointers.externalPointers) > 0:
                    xMenu = doc.createElement("menu")
                    xMenu.setAttribute("id", str(menu.id))

                    if menu.title:
                        xTitle = doc.createElement("title")

                        for xNode in menu.title.data.toXML(doc):
                            xTitle.appendChild(xNode)

                        xMenu.appendChild(xTitle)

                    if menu.shortcuts:
                        xShortcuts = doc.createElement("shortcuts")

                        for xNode in menu.shortcuts.data.toXML(doc):
                            xShortcuts.appendChild(xNode)

                        xMenu.appendChild(xShortcuts)

                    xItems = doc.createElement("items")

                    for item in menu.items:
                        xMi = doc.createElement("mi")

                        for xNode in item.data.toXML(doc):
                            xMi.appendChild(xNode)

                        xItems.appendChild(xMi)

                    xMenu.appendChild(xItems)

                    xLocale.appendChild(xMenu)

        return xLocale

    def patch(self, patchFilename, revert=False, checkForOldValues=False):
        """Patches exe with given patch."""

        patchFile = open(patchFilename, "rb")
        patchPattern = re.compile(r'^([0-9A-Fa-f]{8}): ([0-9A-Fa-f]{2}) ([0-9A-Fa-f]{2})')
        patchData = patchFile.read()
        patchFile.close()

        bytesPatched = 0
        patchedExeData = self.resultExeData[:]

        for patch in [patch for patch in patchData.split("\n") if len(patch) > 0 and patch[0] != '#']:
            searchResult = patchPattern.search(patch)
            if searchResult != None:
                address = int(searchResult.groups()[0], 16)
                previous = chr(int(searchResult.groups()[1], 16))
                new = chr(int(searchResult.groups()[2], 16))

                if revert:
                    tmp = new
                    new = previous
                    previous = tmp

                if not checkForOldValues or patchedExeData[address] == previous:
                    patchedExeData = patchedExeData[:address] + new + patchedExeData[address + 1:]
                    bytesPatched += 1
                else:
                    raise Exception("%s: Current values doesn't match with old value in (%s)" % (patchFilename, patch))

        self.resultExeData = patchedExeData

        return bytesPatched

    def exportAddressMap(self, addressMap):

        doc = Document()
        xAddressMap = doc.createElement("address_map")
        xAddressMap.setAttribute("version", self.version)

        for segment in self.segments:
            for string in segment.strings:
                xString = doc.createElement("string")
                xString.setAttribute("id", str(string.id))
                address = string.id in addressMap and "%08X" % addressMap[string.id] or "None"
                xString.appendChild(doc.createTextNode(address))

                xAddressMap.appendChild(xString)


            for menu in segment.menus:
                xMenu = doc.createElement("menu")
                xMenu.setAttribute("id", str(menu.id))

                if menu.title:
                    xTitle = doc.createElement("title")

                    id = menu.title.id
                    address = id in addressMap and "%08X" % addressMap[id] or "None"
                    xTitle.appendChild(doc.createTextNode(address))

                    xMenu.appendChild(xTitle)

                if menu.shortcuts:
                    xShortcuts = doc.createElement("shortcuts")

                    id = menu.shortcuts.id
                    address = id in addressMap and "%08X" % addressMap[id] or "None"
                    xShortcuts.appendChild(doc.createTextNode(address))

                    xMenu.appendChild(xShortcuts)

                xItems = doc.createElement("items")

                for item in menu.items:
                    xMi = doc.createElement("mi")

                    id = item.id
                    address = id in addressMap and "%08X" % addressMap[id] or "None"
                    xMi.appendChild(doc.createTextNode(address))


                    xItems.appendChild(xMi)

                xMenu.appendChild(xItems)

                xAddressMap.appendChild(xMenu)

        return xAddressMap

    def getSegmentByAbsoluteOffset(self, absoluteOffset):
        for segment in self.segments:
            if segment.containsOffset(absoluteOffset):
                return segment

        return None

    def getSegmentById(self, id):
        for segment in self.segments:
            if segment.id == id:
                return segment

        return None

    def getLink(self, absoluteOffset):
        segment = self.getSegmentByAbsoluteOffset(absoluteOffset)
        return str(segment.id) + "." + "%08X" % segment.getSegmentAddress(absoluteOffset)

    def getAbsoluteOffset(self, link):
        components = link.split('.')
        segmentId = int(components[0])
        segmentOffset = int(components[1], 16)
        segment = self.getSegmentById(segmentId)
        return segment.getAbsoluteOffset(segmentOffset)

    def getItemById(self, id):
        for segment in self.segments:
            for string in segment.strings:
                if string.id == id:
                    return string
            for menu in segment.menus:
                if menu.id == id:
                    return menu

    def getItemSegment(self, item):
        absoluteOffset = self.getAbsoluteOffset(item.address)
        return self.getSegmentByAbsoluteOffset(absoluteOffset)

    def addSpecialPreFixes(self, locale):
        item = self.getItemById(1522).items[0]
        data = item.getDataWithLocaleIfAvailable(locale).data
        first = data.find('\x09')
        second = data.find('\x09', first + 2)
        item.externalPointers.append(ExternalPointer("1.00006413", first + 1))
        item.externalPointers.append(ExternalPointer("1.0000641F", first + 1))
        item.externalPointers.append(ExternalPointer("1.00006418", second + 1))
        item.externalPointers.append(ExternalPointer("1.00006424", second + 1))

        item = self.getItemById(1076)
        data = item.getDataWithLocaleIfAvailable(locale).data
        first = data.find('%')
        item.externalPointers.append(ExternalPointer("1.00007C83", first + 1))

    def importNewString(self, xmlString, segment, localeTable):
        table = mergedTable(standardTable(), localeTable)
        newString = String.fromXML(minidom.parseString(xmlString).documentElement, table)
        segment.strings.append(newString)

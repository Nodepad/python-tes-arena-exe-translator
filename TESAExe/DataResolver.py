from .DataPool import *

def getUsedStringIds(strings):

    usedStringIds = set()

    for string in strings:
        if len(string.externalPointers) > 0:
            usedStringIds.add(string.id)

            if string.data.pointers:
                for pointer in string.data.pointers:
                    usedStringIds.add(pointer.id)

    return usedStringIds

def getUnusedStrings(strings):
    return [string for string in strings if string.id not in getUsedStringIds(strings)]

def getUsedStrings(strings):
    return [string for string in strings if string.id in getUsedStringIds(strings)]

class DataResolver:
    def __init__(self, exe):
        self.exe = exe

    def resolve(self, locale=None):

        def translateLink(link):
            return exe.getAbsoluteOffset(link)

        newExeData = self.exe.resultExeData[:]
        resultAddressMap = {}

        for segment in self.exe.segments:

            if len(segment.strings) == 0 and len(segment.menus) == 0:
                continue

            idMap = {}
            sizeMap = {}
            dataPool = DataPool()
            strings = []

            usedStrings = getUsedStrings(segment.strings)
            strings.extend(usedStrings)

            for usedString in usedStrings:
                data = usedString.getDataWithLocaleIfAvailable(locale)
                dataId = dataPool.addDataString(data, usedString.binary)
                if dataId in idMap:
                    ids = idMap[dataId]
                    ids.append(usedString.id)
                else:
                    idMap[dataId] = [usedString.id]
                # idMap[dataId] = usedString.id
                sizeMap[usedString.id] = data.length

            menuStrings = []

            for menu in segment.menus:
                menuStrings.extend(menu.getStrings())

            usedStrings = getUsedStrings(menuStrings)
            strings.extend(usedStrings)

            for usedString in usedStrings:
                data = usedString.getDataWithLocaleIfAvailable(locale)
                dataId = dataPool.addDataString(data, False)
                if dataId in idMap:
                    ids = idMap[dataId]
                    ids.append(usedString.id)
                else:
                    idMap[dataId] = [usedString.id]
                # idMap[dataId] = usedString.id
                sizeMap[usedString.id] = data.length

            blocks = [(block.length, self.exe.getAbsoluteOffset(block.address)) for block in segment.blocks]

            try:
                dataMap = dataPool.createDataMap(blocks)
            except Exception as e:
                requiredBytes = e[1]
                requiredBytes = (requiredBytes + 15) & 0xFFF0

                newExeData = self.addSpaceToSegment(newExeData, segment, requiredBytes)

                blocks.append((requiredBytes, segment.absoluteOffset + segment.length))

                segment.length += requiredBytes

                segmentIndex = self.exe.segments.index(segment)

                for i in xrange(segmentIndex + 1, len(self.exe.segments)):
                    adjustSegment = self.exe.segments[i]
                    adjustSegment.absoluteOffset += requiredBytes

                dataMap = dataPool.createDataMap(blocks)

            segmentPointerMap = {}

            for dataId in dataMap:
                for stringId in idMap[dataId]:
                    segmentPointerMap[stringId] = self.exe.getSegmentAddress(dataMap[dataId])

            newExeData = dataPool.createNewExe(newExeData, dataMap, segmentPointerMap)
            newExeData = self.remapExternalPointers(newExeData, strings, segmentPointerMap)
            newExeData = self.remapExternalSizes(newExeData, strings, sizeMap)

            for dataId in idMap:
                for stringId in idMap[dataId]:
                    resultAddressMap[stringId] = dataMap[dataId]

        self.exe.resultExeData = newExeData

        return resultAddressMap

    def remapExternalPointers(self, exeData, strings, offsetMap):
        # offsetMap: string.id -> new string segment offset

        for string in strings:
            segmentOffset = offsetMap[string.id]

            for externalPointer in string.externalPointers:
                pointer = struct.pack("<H", segmentOffset + externalPointer.addition)
                exeOffset = self.exe.getAbsoluteOffset(externalPointer.pointer)
                exe = exeData[:exeOffset] + pointer + exeData[exeOffset + 2:]
                exeData = exe

        return exeData

    def remapExternalSizes(self, exeData, strings, sizeMap):
        # sizeMap: string.id -> string size

        for string in strings:
            size = sizeMap[string.id]

            for externalSize in string.externalSizes:
                sizeString = struct.pack("<B", size + externalSize.addition)
                exeOffset = self.exe.getAbsoluteOffset(externalSize.pointer)
                exe = exeData[:exeOffset] + sizeString + exeData[exeOffset + 1:]
                exeData = exe

        return exeData

    def addSpaceToSegment(self, exeData, segment, spaceLength):

        exe = exeData[:]

        def unpackLongPointer(offset):
            off, seg = struct.unpack("<HH", exe[offset:offset + 4])
            return (seg << 4) + off

        def packLongPointer(exe, offset, pointer):
            off = pointer % 0x4A0
            seg = (pointer - off) >> 4
            exe = exe[:offset] + struct.pack("<HH", off, seg) + exe[offset + 4:]
            return exe

        spaceParagraphLength = (spaceLength + 15) / 16
        nextSegment = segment.absoluteOffset + segment.length

        low, high = struct.unpack("<HH", exe[0x02:0x06])
        exeSize = high * 0x200 + low
        exeSize += spaceLength
        low, high = exeSize % 0x200, exeSize / 0x200
        exe = exe[:0x02] + struct.pack("<HH", low, high) + exe[0x06:]

        stackPointer = struct.unpack("<H", exe[0x0E:0x10])[0]
        stackPointer += spaceParagraphLength
        pointer = struct.pack("<H", stackPointer)
        exe = exe[:0x0E] + pointer + exe[0x10:]

        exeHeaderSize = struct.unpack("<H", exe[0x08:0x0A])[0] << 4
        relocationEntryCount = struct.unpack("<H", exe[0x06:0x08])[0]

        for i in xrange(relocationEntryCount):
            pointer = unpackLongPointer(i * 4 + 0x1C)
            pointer += exeHeaderSize
            offset = struct.unpack("<H", exe[pointer:pointer + 2])[0]

            if pointer >= nextSegment:
                newPointer = pointer + spaceLength - exeHeaderSize
                exe = packLongPointer(exe, i * 4 + 0x1C, newPointer)

            if offset >= (nextSegment - exeHeaderSize) >> 4:
                offset += spaceParagraphLength
                offsetString = struct.pack("<H", offset)
                exe = exe[:pointer] + offsetString + exe[pointer + 2:]

        exe = exe[:nextSegment] + "\x00" * spaceLength + exe[nextSegment:]

        return exe

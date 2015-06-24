import struct
from .DataString import *
from .IDGenerator import IDGenerator

class DataStringPoolEntry:
    def __init__(self, data, mutable=False):
        self.data = data
        self.mutable = mutable

class DataPool:
    def __init__(self, idGenerator=IDGenerator(1)):
        self.dataStrings = {}
        self.idGenerator = idGenerator

    def addDataString(self, dataString, mutable):

        entryId = None

        if not mutable:
            entryId = self.__findDataStringEntry(dataString)

        if not entryId:
            entry = DataStringPoolEntry(dataString, mutable)

            entryId = self.idGenerator()
            self.dataStrings[entryId] = entry

        return entryId

    def getDataString(self, id):
        return self.dataStrings[id].data

    # @return Key for entry in self.dataStrings
    def __findDataStringEntry(self, dataString):
        def dataStringEqual(x):
            entry = self.dataStrings[x]
            if not entry.mutable and entry.data == dataString:
                return True

            return False

        search = filter(dataStringEqual, self.dataStrings)

        if len(search):
            return search[0]

        return None

    def createDataMap(self, blocks):

        dataMap = {}

        blocks = sorted(blocks, key=lambda block: block[0], reverse=True)

        lengthMap = [(self.dataStrings[dId].data.length, dId) for dId in self.dataStrings]
        lengthMap = sorted(lengthMap, key=lambda entry: entry[0], reverse=True)

        for block in blocks:
            bestSet = iterative(lengthMap, block[0])
            dataStringIds = [lengthMap[index][1] for index in bestSet]

            bestSet.reverse()

            for i in bestSet:
                del lengthMap[i]

            currentOffset = block[1]

            for dataStringId in dataStringIds:
                dataMap[dataStringId] = currentOffset
                currentOffset += self.dataStrings[dataStringId].data.length

        if len(lengthMap) > 0:
            requiredSize = 0

            for entry in lengthMap:
                requiredSize += entry[0]

            raise Exception("Not enough space (requires more %d byte)" % requiredSize, requiredSize)

        return dataMap

    def createNewExe(self, exeData, dataMap, offsetMap):
        # offsetMap: string.id -> new string segment offset

        for entry in dataMap:
            dataString = self.dataStrings[entry].data

            offset = dataMap[entry]
            exe = exeData[:offset] + dataString.data + exeData[offset + dataString.length:]
            exeData = exe

            for pointer in dataString.pointers:
                segmentPointer = offsetMap[pointer.id]
                currentOffset = offset + pointer.offset
                pointer = struct.pack("<H", segmentPointer)
                exe = exeData[:currentOffset] + pointer + exeData[currentOffset + 2:]
                exeData = exe

        return exeData

def iterative(lMap, length):
    bestLength = 0
    bestSet = None
    currentSet = []
    lengthToFind = length
    currentIndex = 0

    while True:

        for i in xrange(currentIndex, len(lMap)):
            if lMap[i][0] <= lengthToFind:
                currentIndex = i
                break
        else:
            currentIndex = len(lMap)

        leftLen = getLen(lMap, currentIndex)

        if leftLen <= lengthToFind:

            currentDifference = lengthToFind - leftLen

            if currentDifference <= length - bestLength:
                newSet = currentSet[:]
                newSet.extend(range(currentIndex, len(lMap)))

                bestLength = length - currentDifference
                bestSet = newSet

                if currentDifference == 0:
                    break

            if len(currentSet) == 0:
                break

            prevIndex = currentSet.pop()
            currentIndex = prevIndex + 1

            lengthToFind += lMap[prevIndex][0]
            continue
            # backtrack

        if lMap[currentIndex][0] == lengthToFind:
            currentSet.append(currentIndex)

            bestLength = length
            bestSet = currentSet
            break
            # return

        if lMap[currentIndex][0] < lengthToFind:
            currentSet.append(currentIndex)
            lengthToFind -= lMap[currentIndex][0]
            currentIndex += 1

    resultLen = 0

    for index in bestSet:
        resultLen += lMap[index][0]

    return bestSet

def getLen(lMap, index):
    result = 0

    for i in xrange(index, len(lMap)):
        result += lMap[i][0]

    return result

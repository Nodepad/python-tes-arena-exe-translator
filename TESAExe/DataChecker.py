import struct

knownGoodInstructions = ['\x68', '\xBE', '\xBF', '\xBB', '\xBD', '\xB8', '\x81\xFE', '\x81\xFA', '\x65\x88\x16', '\xC7\x06\xE8\x05', '\x81\x3E\xE8\x05', '\xC6\x06']
knownGoodBinInstructions = ['\xBB', '\x0F\xBE\x87', '\x8B\x87', '\x8A\x87', '\x8B\xB7', '\x26\x8B\x9F', '\x0F\xB6\x87', '\x3A\x8F', '\x66\x0F\xB7\x87', '\xF6\x87', '\x80\xB7', '\x66\xA3', '\x3A\x87', '\x0F\xB6\x9F', '\x0F\xB6\x8F', '\x0F\xBE\x9F', '\x26\x8B\x1E', '\xA3', '\x65\x8A\x97', '\xC6\x06', '\xF6\x06', '\x8A\x9F', '\xFF\xB7', '\x8B\xB4']
allKnownInstructions = knownGoodInstructions + knownGoodBinInstructions

class DataChecker:

    def __init__(self, exe):
        self.exe = exe

    def check(self):

        for segment in self.exe.segments:
            strings = segment.strings[:]

            for menu in segment.menus:
                strings.extend(menu.getStrings())

            for string in strings:
                data = string.data
                address = self.exe.getAbsoluteOffset(string.address)
                segmentAddress = self.exe.getSegmentAddress(address)
                stringData = self.resolveData(data, strings)
                stringSize = len(data.data)

                exeData = self.exe.exeData[address:address + stringSize]

                if exeData != stringData:
                    print "Wrong data position for string with id %d" % string.id

                for externalPointer in string.externalPointers:
                    pointer = self.exe.getAbsoluteOffset(externalPointer.pointer)

                    trueData = struct.pack("<H", segmentAddress + externalPointer.addition)
                    exeData = self.exe.exeData[pointer:pointer + 2]

                    if exeData != trueData:
                        print "Wrong pointer for string with id %d (%s)" % (string.id, externalPointer.pointer)

                    pointerValid = False

                    pointerSegment = self.exe.getSegmentByAbsoluteOffset(pointer)

                    if pointerSegment.type == "data":
                        pointerValid = True

                    if not pointerValid:
                        for goodInstr in knownGoodInstructions:
                            length = len(goodInstr)
                            exeData = self.exe.exeData[pointer - length:pointer]

                            if exeData == goodInstr:
                                pointerValid = True

                    if not pointerValid and string.binary:
                        for goodInstr in knownGoodBinInstructions:
                            length = len(goodInstr)
                            exeData = self.exe.exeData[pointer - length:pointer]

                            if exeData == goodInstr:
                                pointerValid = True

                    if not pointerValid:
                        print "Wrong instruction with pointer for string with id %d (%s)" % (string.id, externalPointer.pointer)

                for externalSize in string.externalSizes:
                    sizePointer = self.exe.getAbsoluteOffset(externalSize.pointer)

                    trueSize = struct.pack("<B", stringSize + externalSize.addition)
                    exeSize = self.exe.exeData[sizePointer:sizePointer + 1]

                    if exeSize != trueSize:
                        print "Wrong size for string with id %d (%s)" % (string.id, externalSize.pointer)

                # self.tryToFindOtherPointers(strings, string, segmentAddress)

    def tryToFindOtherPointers(self, strings, string, segmentAddress):
        pointers = []
        start = 0
        addressString = struct.pack("<H", segmentAddress)

        while True:
            start = self.exe.exeData.find(addressString, start)

            if start == -1:
                break

            pointers.append(start)
            start += len(addressString)

        validPointers = []

        for pointer in pointers:

            pointerSegment = self.exe.getSegmentByAbsoluteOffset(pointer)

            if pointerSegment == None:
                break

            if pointerSegment.type == "data" and not self.isInternalPointer(strings, pointer):
                # validPointers.append(pointer)
                break

            for instr in allKnownInstructions:
                length = len(instr)
                exeData = self.exe.exeData[pointer - length:pointer]

                if exeData == instr:
                    validPointers.append(pointer)
                    break

        validUnknownPointers = []

        for pointer in validPointers:

            for externalPointer in string.externalPointers:
                aPointer = self.exe.getAbsoluteOffset(externalPointer.pointer)

                if pointer == aPointer:
                    break
            else:
                validUnknownPointers.append("%08X" % pointer)

        if len(validUnknownPointers) > 0:
            print "Found unknown pointers for string with id %d = %s" % (string.id, validUnknownPointers)

    def isInternalPointer(self, strings, internalPointer):

        for string in strings:

            for pointer in string.data.pointers:
                address = pointer.offset
                address += self.exe.getAbsoluteOffset(string.address)

                if internalPointer == address:
                    return True

        return False

    def resolveData(self, data, strings):

        def findString(id):
            for string in strings:
                if string.id == id:
                    return string

        newDataString = data.data[:]

        for pointer in data.pointers:
            string = findString(pointer.id)
            address = self.exe.getAbsoluteOffset(string.address)
            segmentAddress = self.exe.getSegmentAddress(address)

            offset = pointer.offset

            newDataString = newDataString[:offset] + struct.pack("<H", segmentAddress) + newDataString[offset + 2:]

        return newDataString

    def findMisplacedVariables(self, locale):
        resultStrings = []

        for segment in self.exe.segments:
            strings = segment.strings[:]

            for string in strings:
                if not locale in string.locale:
                    continue

                def createVariableString(data):
                    result = ""
                    index = data.find("%")

                    while index != -1:
                        result += data[index + 1]
                        index = data.find("%", index + 1)

                    return result

                localeVar = createVariableString(string.locale[locale].data)
                originalVar = createVariableString(string.data.data)

                if localeVar != originalVar:
                    resultStrings.append(string)

        return resultStrings

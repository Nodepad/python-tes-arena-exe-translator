from .DataString import *

class ExternalPointer:
    def __init__(self, pointer, addition = 0):
        self.pointer = pointer
        self.addition = addition

class ExternalSize:
    def __init__(self, pointer, addition = 0):
        self.pointer = pointer
        self.addition = addition

class String:

    @staticmethod
    def fromXML(xString, translationTable=standardTable()):

        address = xString.getAttribute("address")
        id = int(xString.getAttribute("id"))

        binaryAttribute = xString.getAttribute("binary")
        binary = False

        if binaryAttribute and binaryAttribute == "true":
            binary = True

        externalPointers = []

        for xExternalPointer in xString.getElementsByTagName("external_pointer"):
            additionString = xExternalPointer.getAttribute("addition")
            addition = additionString != "" and int(additionString) or 0

            pointerString = xExternalPointer.firstChild.nodeValue
            externalPointers.append(ExternalPointer(pointerString, addition))

        externalSizes = []

        for xExternalSize in xString.getElementsByTagName("external_size"):
            additionString = xExternalSize.getAttribute("addition")
            addition = additionString != "" and int(additionString) or 0

            sizeString = xExternalSize.firstChild.nodeValue
            externalSizes.append(ExternalSize(sizeString, addition))

        xContent = xString.getElementsByTagName("content")[0]
        data = DataString.fromXML(xContent, translationTable)

        return String(address, id, binary, externalPointers, externalSizes, data)

    def __init__(self, address, id, binary, externalPointers, externalSizes, data):
        self.address = address
        self.id = id
        self.binary = binary
        self.externalPointers = externalPointers
        self.externalSizes = externalSizes
        self.data = data
        self.locale = {}

    def getLength(self):
        return self.data.length

    def getEndAbsoluteOffset(self):
        return self.absoluteOffset + self.getLength()

    def getDataWithLocaleIfAvailable(self, locale):

        if locale in self.locale:
            return self.locale[locale]
        else:
            return self.data

    def toXML(self, doc):
        xString = doc.createElement("string")
        xString.setAttribute("id", str(self.id))
        xString.setAttribute("address", self.address)
        xString.setAttribute("binary", self.binary and "true" or "false")

        for externalPointer in self.externalPointers:
            xExternalPointer = doc.createElement("external_pointer")

            if externalPointer.addition != 0:
                xString.setAttribute("addition", str(externalPointer.addition))

            externalPointerString = externalPointer.pointer
            xExternalPointer.appendChild(doc.createTextNode(externalPointerString))

            xString.appendChild(xExternalPointer)

        for externalSize in self.externalSizes:
            xExternalSize = doc.createElement("external_size")

            xExternalSize.appendChild(doc.createTextNode(externalSize))

            xString.appendChild(xExternalSize)

        xContent = doc.createElement("content")

        for xNode in self.data.toXML(doc):
            xContent.appendChild(xNode)

        xString.appendChild(xContent)

        return xString

    def getAddress(self):
        return self.absoluteOffset

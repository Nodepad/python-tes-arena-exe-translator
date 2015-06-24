from xml.dom.minidom import Node
from .Translation import *

class Pointer:
    def __init__(self, id, offset):
        self.id = id
        self.offset = offset

    def __eq__(self, other):
        return self.id == other.id and self.offset == other.offset

class DataString:

    @staticmethod
    def fromXML(xNode, translationTable=standardTable()):
        child = xNode.firstChild
        translate = translation(translationTable)
        dataString = ""
        pointers = []

        while child:
            if child.nodeType == Node.TEXT_NODE:
                data = translate(child.nodeValue)
                dataString += data
            elif child.nodeType == Node.ELEMENT_NODE and child.tagName == "pointer":
                tid = int(child.getAttribute("id"))
                pointers.append(Pointer(tid, len(dataString)))
                dataString += "\x00\x00"
            else:
                raise Exception()

            child = child.nextSibling

        return DataString(dataString, pointers)

    def __init__(self, data, pointers=None):
        self.data = data
        self.length = len(data)
        self.pointers = pointers

    def __eq__(self, other):
        if self.data == other.data:
            selfPointers = sorted(self.pointers, key=lambda pointer: pointer.offset)
            otherPointers = sorted(other.pointers, key=lambda pointer: pointer.offset)

            return selfPointers == otherPointers
        return False

    def toXML(self, doc):
        xNodes = []

        ranges = [(0, len(self.data))]

        for pointer in self.pointers:
            offset = pointer.offset
            pRng = None
            nRng = None

            for i in xrange(len(ranges)):
                rng = ranges[i]

                if offset >= rng[0] and offset < rng[0] + rng[1]:
                    ranges.pop(i)

                    pRng = (rng[0], offset - rng[0])
                    nRng = (offset + 2, rng[1] - (offset + 2 - rng[0]))

                    if pRng[1] > 0:
                        ranges.insert(i, pRng)

                    if nRng[1] > 0:
                        ranges.insert(i, nRng)

                    break

        current = 0

        translate = translation(reverseTable(standardTable()))

        while current != self.length:
            for rng in ranges:
                if rng[0] == current:
                    data = translate(self.data[rng[0]:rng[1]])
                    xNodes.append(doc.createTextNode(data))
                    current += rng[1]

                    break

            for pointer in self.pointers:
                if pointer.offset == current:
                    xPointer = doc.createElement("pointer")
                    xPointer.setAttribute("id", str(pointer.id))
                    xNodes.append(xPointer)
                    current += 2

                    break

        return xNodes

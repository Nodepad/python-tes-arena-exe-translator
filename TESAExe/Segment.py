from .String import *
from .Menu import *
from .DataPool import *
from .IDGenerator import IDGenerator
import re
from xml.dom import minidom

class Block:

    @staticmethod
    def fromXML(xBlock):
        address = xBlock.getAttribute("address")
        length = int(xBlock.getAttribute("length"), 16)
        id = int(xBlock.getAttribute("id"))

        return Block(id, address, length)

    def __init__(self, id, address, length):
        self.address = address
        self.length = length
        self.id = id

    def toXML(self, doc):
        xBlock = doc.createElement("block")
        xBlock.setAttribute("id", str(self.id))
        xBlock.setAttribute("address", self.address)
        xBlock.setAttribute("length", "%04X" % self.length)

        return xBlock

    def getAddress(self):
        return self.absoluteOffset

class Segment:

    @staticmethod
    def fromXML(xSegment, idGenerator):
        id = int(xSegment.getAttribute("id"))
        absoluteOffset = int(xSegment.getAttribute("absolute_offset"), 16)
        length = int(xSegment.getAttribute("length"), 16)
        segmentType = xSegment.getAttribute("type")
        blocks = []
        strings = []
        menus = []

        xBlocks = xSegment.getElementsByTagName("block")

        for xBlock in xBlocks:
            blocks.append(Block.fromXML(xBlock))

        xStrings = xSegment.getElementsByTagName("string")

        for xString in xStrings:
            strings.append(String.fromXML(xString))

        xMenus = xSegment.getElementsByTagName("menu")

        for xMenu in xMenus:
            menus.append(Menu.fromXML(xMenu, idGenerator))

        return Segment(id, absoluteOffset, length, segmentType, blocks, strings, menus)

    def __init__(self, id, absoluteOffset, length, type, blocks, strings, menus):
        self.id = id
        self.absoluteOffset = absoluteOffset
        self.length = length
        self.type = type
        self.blocks = blocks
        self.strings = strings
        self.menus = menus

    def containsOffset(self, absoluteOffset):
        return self.getSegmentAddress(absoluteOffset) != None

    def findBlocks(self):
        strings = self.strings[:]

        for menu in self.menus:
            strings.extend(menu.getStrings())

        blocks = []

        def appendRange(start, end):
            for i in xrange(len(blocks)):
                block = blocks[i]

                blkBeg = block[0]
                blkEnd = block[1]

                if start == blkEnd:
                    blocks.remove(block)
                    appendRange(blkBeg, end)
                    break
                elif end == blkBeg:
                    blocks.remove(block)
                    appendRange(start, blkEnd)
                    break
            else:
                blocks.append((start, end))

        for string in strings:
            strBeg = string.absoluteOffset
            strEnd = strBeg + string.data.length

            appendRange(strBeg, strEnd)

        blocks = [(block[0], block[1] - block[0]) for block in blocks]

        return blocks

    def getAbsoluteOffset(self, segmentOffset):
        return (self.absoluteOffset & 0xFFFFFFF0) + segmentOffset

    def getSegmentAddress(self, absoluteOffset):
        segmentOffset = absoluteOffset - (self.absoluteOffset & 0xFFFFFFF0)

        if segmentOffset > 0 and segmentOffset < self.length:
            return segmentOffset

        return None

    def toXML(self, doc):
        xSegment = doc.createElement("segment")
        xSegment.setAttribute("id", str(self.id))
        xSegment.setAttribute("absolute_offset", "%08X" % self.absoluteOffset)
        xSegment.setAttribute("length", "%08X" % self.length)
        xSegment.setAttribute("type", self.type)

        for block in self.blocks:
            xSegment.appendChild(block.toXML(doc))

        for string in self.strings:
            xSegment.appendChild(string.toXML(doc))

        for menu in self.menus:
            xSegment.appendChild(menu.toXML(doc))

        return xSegment

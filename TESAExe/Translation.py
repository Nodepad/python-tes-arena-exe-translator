# coding: utf-8

import string

def mergedTable(table1, table2):
    table = table1.copy()
    table.update(table2)
    return table

def standardTable():
    table = {}

    for i in xrange(256):
        table[chr(i)] = u"\\x%02X" % i

    for char in string.digits + string.letters + string.punctuation:
        table[char] = unicode(char)

    table[' '] = u' '
    table['\\'] = u'\\\\'
    table['\r'] = u'\\r'
    table['\n'] = u'\\n'

    return reverseTable(table)

def reverseTable(table):
    rTable = {}

    for char in table:
        rTable[table[char]] = char

    return rTable

def translation(table):

    def translate(string):
        result = ""

        if isinstance(table.keys()[0], unicode):
            tmp = unicode(string)
        else:
            tmp = string

        stringPos = 0

        while len(tmp) > 0:
            for key in table:
                value = table[key]

                if len(tmp) >= len(key):
                    if key == tmp[:len(key)]:
                        result += value
                        tmp = tmp[len(key):]
                        stringPos += len(key)
                        break
            else:
                raise Exception("Wrong character in string at position %d" % stringPos)

        return result

    return translate

Python library for translation of executable for game The Elder Scrolls - Arena

####Tip####
Right now it is only support executable of game version 1.6.

##Installation##

To install library execute following commands with your command shell inside main directory:

```Bash
python setup.py build
python setup.py install
```

##Exe translation##

Load exe file. Function `openExe` takes file path to unpacked game executable (size of our unpacked executable is 320304 bytes, it's highly desirable to use executable with same size to prevent different issues).

```Python
import TESAExe

exe = TESAExe.openExe("A.EXE")
```

Then export locale file. Locale file is human-readable xml file with strings to translate. Open this file with preferred text editor and translate strings to needed language.

```Python
localeFile = open("locale.xml", "w")
localeFile.write(exe.createLocaleTemplate("locale_name").toprettyxml())
localeFile.close()
```

After translation of locale file import it back. Create dictionary which contains unicode symbols of your language for keys and corresponding symbols which should be written to executable for values (we patched executable and fonts to support extended ASCII table with 256 symbols instead of 127 so we just use symbols from cyrillic charset `windows-1251`) and send it to `importLocale` method as second argument.

```Python
# coding: utf-8

from xml.dom import minidom

localeTable = {}
russian = u"АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя"
for char in russian:
    localeTable[char] = char.encode('windows-1251')

locale = minidom.parse("locale.xml").documentElement
exe.importLocale(locale, localeTable)
```

Then execute `addSpecialPreFixes` method for adding special fixes to translation.
```
exe.addSpecialPreFixes("locale_name")
```

Create `DataResolver` object with executable and call method `resolve` to map localized text within executable. Use `resultExeData` property of exe to export translated executable data.

```Python
res = TESAExe.DataResolver(exe)
res.resolve("locale_name")

exeFile = open("a_new.exe", "wb")
exeFile.write(exe.resultExeData)
exeFile.close()
```

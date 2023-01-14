#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2023 Josep Torra
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# pylint: disable=too-many-instance-attributes,too-few-public-methods,global-statement

"""
Script to generate spells.db in FoundryVTT/OSE module format.
"""


import json
import string
import random

from bs4 import BeautifulSoup as bs

KLASS = "Magic-User"


def genid():
    """Generate a random Id"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))


def remove_all_attributes(soup):
    """Remove class attribute from all html tags"""
    for tags in soup.find_all():
        for key in list(tags.attrs):
            del tags.attrs[key]
    return soup


def remove_class(soup):
    """Remove class attribute from all html tags"""
    for tags in soup.find_all():
        try:
            del tags.attrs['class']
        except IndexError:
            pass
    return soup


def make_th(soup):
    """Convert first row into a header"""
    if soup.name != "table":
        return soup
    tr = soup.find("tr")
    for td in tr.find_all("td"):
        td.name = "th"
    return soup


class SpellData():
    """SpellData"""

    f_lvl: str
    f_class: str
    f_duration: str
    f_range: str
    f_roll: str
    f_description: str
    f_memorized: int
    f_cast: int
    f_save: str

    def __init__(self, soup, lvl: int = 1):
        details = soup[0].text.split(".")
        self.f_lvl = lvl
        self.f_class = KLASS
        self.f_duration = details[0].replace("Durada:\xa0", "")
        self.f_range = details[1].replace("Abast:\xa0", "")
        self.f_type = "spell"
        self.describe(soup[1:])
        self.f_memorized = 0
        self.f_cast = 0
        self.f_save = ""
        if "tirada de salvació contra encanteris" in self.f_description:
            self.f_save = "spell"
        elif "tirada de salvació contra mort" in self.f_description:
            self.f_save = "dead"
        elif "tirada de salvació contra paràlisi" in self.f_description:
            self.f_save = "paralysis"

    def describe(self, soup):
        """Convert soup into a spell description"""
        desc = ""
        for sdata in soup:
            if sdata.name == "table":
                sdesc = str(make_th(remove_all_attributes(sdata)))
                sdesc = sdesc.replace("<span>", "")
                sdesc = sdesc.replace("</span>", "")
                sdesc = sdesc.replace("<p>", "")
                sdesc = sdesc.replace("</p>", "")
            elif sdata.name == "h4":
                sdesc = sdata.text.strip()
                if sdesc:
                     sdesc = f"<h3>{sdesc}</h3>\n"
            else:
                sdesc = sdata.text.replace("⦿", "<span style='color:#4a86e8'>⦿</span> ")
                if sdesc:
                     sdesc = f"<p>{sdesc.strip()}</p>\n"
            desc += sdesc
        self.f_description = desc

    def jdata(self):
        """return a json string"""
        res = dict()
        for (key, value) in self.__dict__.items():
            if key.startswith('f_'):
                res[key[2:]] = value
        return res


class Spell():
    """Spell"""
    f_name: str
    f_permission: dict
    f_type: str
    f_data: SpellData
    f_img: str
    f__id: str

    def __init__(self, soup, lvl, num):
        self.f_name = f"{KLASS[0]}{lvl}.{num:02d} {soup[0].text}"
        self.f_permission = {"default": 0, "fBZINKCGziZzc3CU": 3}
        self.f_type = "spell"
        self.f_data = SpellData(soup[1:], lvl)
        self.f_img = "systems/ose/assets/default/spell.png"
        self.f__id = genid()

    def __str__(self):
        """return a json string"""
        jdata = dict()
        for (key, value) in self.__dict__.items():
            if key == 'f_data':
                jdata["data"] = value.jdata()
            elif key.startswith('f_'):
                jdata[key[2:]] = value
        return json.dumps(jdata, ensure_ascii=False)


def split_by_tagname(soup, tagname):
    """split soup list by header"""
    res = []
    for sit in soup:
        if sit.name == tagname:
            if res:
                yield res
            res = []
        res.append(sit)
    yield res


def generate_spells(ohandle, soup, lvl):
    """Loop on soup an generate a spell for each occurrence"""
    num = 1
    for sdata in split_by_tagname(soup, "h3"):
        spell = Spell(sdata, lvl, num)
        ohandle.write(str(spell)+"\n")
        num = num + 1


def process(ihandle, ohandle):
    """process"""
    soup = bs("".join(ihandle.readlines()), 'html.parser')
    start = soup.find('h2')
    if not start:
        start = soup.find('table')
        generate_spells(ohandle, start.find_next_siblings(), 0)
        return

    lvl = 0
    for sdata in split_by_tagname(start.find_next_siblings(), "h2"):
        if sdata and lvl > 0:
            generate_spells(ohandle, sdata[1:], lvl)
        lvl = lvl + 1


def main():
    """main"""
    global KLASS
    filenames = [f"beb_spell{n}.html" for n in range(1, 5)]
    klasses = ["Cleric", "Druid", "Illusionist", "Magic-User"]
    with open("spells.db", "w") as ohandle:
        for filename, KLASS in zip(filenames, klasses):
            with open(filename, "r") as ihandle:
                process(ihandle, ohandle)


if __name__ == '__main__':
    main()

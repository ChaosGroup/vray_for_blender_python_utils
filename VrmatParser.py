#
# V-Ray Python Tools
#
# http://chaosgroup.com
#
# Author: Andrei Izrantcev
# E-Mail: andrei.izrantcev@chaosgroup.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# All Rights Reserved. V-Ray(R) is a registered trademark of Chaos Software.
#

import os

from xml.etree import ElementTree

def _convertToXML(filepath):
    import shutil
    import subprocess

    vrmatconvert = os.path.join(os.path.dirname(__file__), "..", "bin", "vrmatconvert.exe")

    bakFile = "%s.bak" % (filepath)

    shutil.copyfile(filepath, bakFile)

    subprocess.call([vrmatconvert, bakFile, filepath])

def _parseTree(filepath):
    tree = None
    try:
        tree = ElementTree.parse(filepath)
    except:
        pass
    return tree

def _parserConvertTree(filepath):
    if not os.path.exists(filepath):
        return None

    tree = _parseTree(filepath)
    if tree is None:
        _convertToXML(filepath)
        tree = _parseTree(filepath)

    return tree

def GetXMLMaterialsNames(filepath):
    tree = _parserConvertTree(filepath)
    if tree is None:
        print("Failed to parse VRmat file!")
        return []

    vrmat = tree.getroot()

    materialPluginNames = []

    for asset in vrmat.iter('Asset'):
        assetType = asset.attrib['type']
        if assetType not in {'material'}:
            continue

        url = asset.attrib['url']
        if url.startswith("/"):
            url = url[1:]

        materialPluginNames.append(url)

    return materialPluginNames

def ParseVrmat(filepath):
    def _getColorValue(rawValue):
        return (
            float(rawValue.find('r').text),
            float(rawValue.find('g').text),
            float(rawValue.find('b').text),
        )

    sceneDesc = []

    tree = _parserConvertTree(filepath)
    if tree is None:
        print("Failed to parse VRmat file!")
        return {}

    vrmat = tree.getroot()

    for asset in vrmat.iter('Asset'):
        assetType = asset.attrib['type']

        vrayPluginName = asset.attrib['url']

        for vrayplugin in asset.iter('vrayplugin'):
            vrayPluginID = vrayplugin.attrib['name']

            vrayPluginAttributes = {}

            for parameter in vrayplugin.iter('parameter'):
                attrName  = parameter.attrib['name']
                attrType  = parameter.attrib['type']
                attrValue = None

                # print("Found attribute: %s [%s]" % (attrName, attrType))

                rawValue = parameter.find('value')
                if rawValue is None:
                    continue

                if attrType == 'integer':
                    attrValue = int(rawValue.text)

                elif attrType == 'float':
                    attrValue = float(rawValue.text)

                elif attrType == 'bool':
                    attrValue = bool(rawValue.text)

                elif attrType == 'color':
                    if rawValue.find('r') is not None:
                        attrValue = _getColorValue(rawValue)

                elif attrType == 'float texture':
                    if rawValue.text:
                        if rawValue.text.replace('.','',1).isdigit():
                            attrValue = float(rawValue.text)
                        else:
                            attrValue = rawValue.text

                elif attrType == 'acolor texture':
                    if rawValue.text:
                        if rawValue.find('r') is None:
                            attrValue = rawValue.text
                        else:
                            attrValue = _getColorValue(rawValue)

                elif attrType in {'plugin', 'string'}:
                    attrValue = rawValue.text

                elif attrType == 'list':
                    attrValue = [v.text for v in rawValue.find('list').iter('entry')]

                if attrValue is not None:
                    vrayPluginAttributes[attrName] = attrValue

            sceneDesc.append({
                "ID"         : vrayPluginID,
                "Name"       : vrayPluginName,
                "Attributes" : vrayPluginAttributes,
            })

    sceneDesc.append({
        "ID" : 'ImportSettings',
        "Name" : "Import Settings",
        "Attributes" : {
            'filepath' : filepath,
            'dirpath'  : os.path.dirname(filepath),
        },
    })

    return sceneDesc


if __name__ == '__main__':
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser()
    parser.add_argument('filepath', nargs='?')
    args = parser.parse_args()

    vrsceneDict = ParseVrmat(args.filepath)

    for pluginDesc in vrsceneDict:
        print("Name:", pluginDesc['Name'])
        print("ID:  ", pluginDesc['ID'])
        print("Attributes:")
        pprint(pluginDesc['Attributes'], indent=4)

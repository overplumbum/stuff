# coding: utf-8

# @todos:
# looks like NextComponentID refer
#

import os, sys
from xml.etree import ElementTree
import shutil
from json import dumps, loads
from hashlib import md5

from base64 import b64decode, b64encode
import string

ENCODERS = {
    'b64': (b64decode, b64encode, 'dat')
}

EXTRACT = [
    # xpath, is_text, decoding: {(dec, enc, extension) | None}
    ('Sequence/Node/Properties/MZ.Prefs.Export.LastExportedPreset', True, None),
    ('Project/Node/Properties/ProjectViewState.List', False, None),
    ('Project/Node/Properties/*[@Encoding=\'base64\']', True, 'b64'),
    ('Sequence/Node/Properties/Seq.Metadata', True, None),
    ('WorkspaceSettings/WorkspaceDefinition', True, None),
    ('Media/ImporterPrefs', True, 'b64'),
]

def bom_xml_escape(s):
    return s.replace("\xEF\xBB\xBF", '&amp;#239;&amp;#187;&amp;#191;')

def parse(path):
    f = open(path, 'rb')
    s = f.read()
    f.close()

    s = bom_xml_escape(s)
    doc = ElementTree.ElementTree(ElementTree.fromstring(s))
    doc.parent_map = dict((c, p) for p in doc.getiterator() for c in p)
    return doc

def get_tags_path(tree, e):
    parts = [e.tag]
    pm = tree.parent_map
    while e in pm:
        e = pm[e]
        parts.insert(0, e.tag)
    return "/".join(parts)

def normalize_ids(tree):
    id_attributes = ('ObjectID', 'ObjectRef')

    map = {}
    for attribute in id_attributes:
        elements = tree.findall('.//*[@'+attribute+']')
        for e in elements:
            path = get_tags_path(tree, e)
            if not path in map:
                map[path] = [1, {}]

            v = e.attrib[attribute]
            if not v in map[path][1]:
                map[path][1][v] = map[path][0]
                map[path][0] += 1
            m = md5()
            m.update(path)
            e.attrib[attribute] = m.hexdigest()[:6] + '-' + str(map[path][1][v])

def get_item_full_xpath(doc, item):
    pm = doc.parent_map
    parts = [get_item_xpath(item, True)]
    while item in pm:
        item = pm[item]
        xpath = get_item_xpath(item, True)
        parts.insert(0, xpath)
    return ("/".join(parts))

def xpath2filename(xpath):
    path = xpath.translate(string.maketrans('@=', '--'), "[]''")
    return os.path.join(*path.split('/'))

class NoIdException(Exception):
    pass

def get_item_xpath(item, allow_empty_id = False):
    for n in ('ObjectUID', 'ObjectID', 'ObjectRef', ):
        if n in item.attrib:
            return item.tag + '[@' + n + '=\'' + item.attrib[n] + "']"
    if allow_empty_id:
        return item.tag
    raise NoIdException()

def write_element(output_path, item, is_text = False, encoder = None):
    extension = 'xml'
    if is_text:
        content = item.text
        if not encoder is None:
            encoder = ENCODERS[encoder]
            content = encoder[0](content)
            extension = encoder[2]
    else:
        content = ElementTree.tostring(item, encoding = 'utf-8', method = 'xml')

    f = open(output_path + '.' + extension, 'wb')
    f.write(content)
    f.close()

def get_output_directory(project_file):
    output_directory_name = ".".join(os.path.basename(project_file).split(".")[:-1]) + '.unpacked'
    return os.path.join(os.path.dirname(project_file), output_directory_name)

def decompose(project_file):
    doc = parse(project_file)
    normalize_ids(doc)

    output_directory = get_output_directory(project_file)
    if os.path.exists(output_directory):
        shutil.rmtree(output_directory)
    os.mkdir(output_directory)

    decompositions = []

    items2remove = []
    for xpath, is_text, encoder in EXTRACT:
        for item in doc.findall(xpath):
            full_xpath = get_item_full_xpath(doc, item)
            full_filename = xpath2filename(full_xpath)
            full_path = os.path.join(output_directory, full_filename)
            if not os.path.exists(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))

            parent = doc.parent_map[item]

            write_element(full_path, item, is_text, encoder)
            decompositions.append((full_xpath, is_text, encoder))
            if is_text:
                item.text = ''
                item.attrib.pop('Checksum', False)
            else:
                items2remove.append((parent, item))

    for parent, element in items2remove:
        parent.remove(element)

    items2remove = []
    parent = doc.getroot()
    for item in doc.getroot():
        xpath = get_item_full_xpath(doc, item)
        full_path = os.path.join(output_directory, xpath2filename(xpath))
        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))

        write_element(full_path, item)
        decompositions.append((xpath, False, None))
        items2remove.append((parent, item))

    for parent, element in items2remove:
        parent.remove(element)

    parent = doc.getroot()
    write_element(os.path.join(output_directory, parent.tag), parent)

    f = open(os.path.join(output_directory, 'decompositions.txt'), 'wb')
    f.writelines(map(lambda s: dumps(s) + "\n", decompositions))
    f.close()

def compose(project_file):
    output_directory = get_output_directory(project_file)
    f = open(os.path.join(output_directory, 'decompositions.txt'), 'r')
    decompositions = map(tuple, map(loads, f.readlines()))
    f.close()

    doc = ElementTree.parse(os.path.join(output_directory, 'PremiereData.xml'))
    for xpath, is_text, encoder in decompositions:
        extension = 'xml'
        if not encoder is None:
            extension = ENCODERS[encoder][2]
        path = os.path.join(output_directory, xpath2filename(xpath) + '.' + extension)

        if is_text:
            node = doc.getroot().find(xpath)
            f = open(path, 'rb')
            content = f.read()
            f.close()
            if not encoder is None:
                content = ENCODERS[encoder][1](content)
            node.text = content
        else:
            xpath_parent = "/".join(("./" + xpath).split("/")[:-1])
            parent = doc.getroot().find(xpath_parent)
            element = ElementTree.parse(path).getroot()
            parent.append(element)

    if os.path.exists(project_file + '.bak'):
        os.remove(project_file + '.bak')
    os.rename(project_file, project_file + '.bak')
    doc.write(project_file)

def process_arguments(argv):
    op = argv[1]
    if op == 'd':
        for project_file in argv[2:]:
            decompose(project_file)
    elif op == 'c':
        for project_file in argv[2:]:
            compose(project_file)
    else:
        print "Usage:", os.path.basename(__file__), "{d|c} file1.pproj file2.pproj ..."
        sys.exit(1)

process_arguments(sys.argv)

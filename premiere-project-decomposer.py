# coding: utf-8
import os, sys
from xml.etree import ElementTree
import shutil
from json import dumps, loads

from base64 import b64decode, b64encode
import string

ENCODERS = {
    'b64': (b64decode, b64encode, 'dat')
}

EXTRACT = [
    # xpath, is_text, decoding: {(dec, enc, extension) | None}
    ('./Sequence/Node/Properties/Seq.Metadata', True, None),
    ('./Sequence/Node/Properties/MZ.Prefs.Export.LastExportedPreset', True, None),
    ('./WorkspaceSettings/WorkspaceDefinition', True, None),
    ('./Project/Node/Properties/ProjectViewState.List', False, None),
    ('./Media/ImporterPrefs', True, 'b64'),
    ('./Project/Node/Properties/*[@Encoding=\'base64\']', True, 'b64'),
]

def bom_xml_escape(s):
    return s.replace("\xEF\xBB\xBF", '&amp;#239;&amp;#187;&amp;#191;')

def parse(path):
    f = open(path, 'rb')
    s = f.read()
    f.close()

    s = bom_xml_escape(s)
    return ElementTree.ElementTree(ElementTree.fromstring(s))

def get_item_full_xpath(stack):
    parts = []
    for item in stack[1:]:
        try:
            xpath = get_item_xpath(item)
        except NoIdException:
            xpath = item.tag

        parts.append(xpath)
    return "./" + ("/".join(parts))

def xpath2filename(xpath):
    path = xpath.translate(string.maketrans('@=', '--'), "[]''")
    return os.path.join(*path.split('/'))

class NoIdException(Exception):
    pass

def get_item_xpath(item):
    for n in ('ObjectID', 'ObjectRef', 'ObjectUID'):
        if n in item.attrib:
            return item.tag + '[@' + n + '=\'' + item.attrib[n] + "']"
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

def get_stack(doc, xpath):
    top = xpath.split('/')[-1]
    rest = "/".join(xpath.split('/')[:-1])
    if len(rest):
        for stack in get_stack(doc, rest):
            parent = stack[-1]
            for item in parent.findall('./' + top):
                yield stack + (item,)
    else:
        yield (doc.getroot(),)


def decompose(project_file):
    doc = parse(project_file)

    output_directory_name = ".".join(os.path.basename(project_file).split(".")[:-1]) + '.unpacked'
    output_directory = os.path.join(os.path.dirname(project_file), output_directory_name)
    if os.path.exists(output_directory):
        shutil.rmtree(output_directory)
    os.mkdir(output_directory)

    decompositions = []

    items2remove = []
    for xpath, is_text, encoder in EXTRACT:
        for stack in get_stack(doc, xpath):
            full_xpath = get_item_full_xpath(stack)
            full_filename = xpath2filename(full_xpath)
            full_path = os.path.join(output_directory, full_filename)
            if not os.path.exists(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))

            parent, element = stack[-2:]

            write_element(full_path, element, is_text, encoder)
            decompositions.append((full_xpath, is_text, encoder))
            if is_text:
                element.text = None
            else:
                items2remove.append((parent, element))

    for parent, element in items2remove:
        parent.remove(element)

    parent = doc.getroot()
    items2remove = []
    for item in doc.getroot():
        xpath = get_item_xpath(item)
        output_path = os.path.join(output_directory, xpath2filename(xpath))
        write_element(output_path, item)
        decompositions.append((xpath, False, None))
        items2remove.append(item)

    for item in items2remove:
        parent.remove(item)

    write_element(os.path.join(output_directory, parent.tag), parent)

    f = open(os.path.join(output_directory, 'decompositions.txt'), 'w')
    f.writelines(map(lambda s: dumps(s) + "\n", decompositions))
    f.close()

def process_arguments(argv):
    op = argv[1]
    if op == 'd':
        for project_file in argv[2:]:
            decompose(project_file)
    #elif op == 'c':
    #    for project_file in argv[2:]:
    #        compose(project_file)
    else:
        print "Usage:", os.path.basename(__file__), "{d|c} file1.pproj file2.pproj ..."
        sys.exit(1)

process_arguments(sys.argv)

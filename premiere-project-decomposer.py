import os, sys
from xml.etree import ElementTree
import shutil

OUTERTAG = 'PremiereData'

def parse(path):
    return ElementTree.parse(path)

def get_item_id(item):
    for n in ('ObjectID', 'ObjectRef', 'ObjectUID'):
        if n in item.attrib:
            return n + '-' + item.attrib[n]
    print 'unable to generate item id', item
    sys.exit(2)

def save_section(output_directory, item, has_id = True):
    if has_id:
        item_id = get_item_id(item)
        item_id = '-' + item_id
    else:
        item_id = ''
    output_path = os.path.join(output_directory, item.tag + item_id  + '.xml')
    f = open(output_path, 'w')
    f.write(ElementTree.tostring(item, encoding = 'utf-8', method = 'xml'))
    f.close()


def decompose(project_file):
    doc = parse(project_file)

    output_directory = ".".join(os.path.basename(project_file).split(".")[:-1]) + '.unpacked'
    output_directory = os.path.join(os.path.dirname(project_file), output_directory)
    if os.path.exists(output_directory):
        shutil.rmtree(output_directory)
    os.mkdir(output_directory)

    for item in doc.iterfind('./*'):
        save_section(output_directory, item)

    outer = ElementTree.Element(doc.getroot().tag)
    outer.attrib.update(doc.getroot().attrib)
    save_section(output_directory, outer, False)

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

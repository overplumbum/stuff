import os, sys
from xml.etree import ElementTree

sections = [
    ('Project', lambda x: x),
]

def parse(path):
    return ElementTree.parse(path)

def extract_section(doc, section):
    return doc.iter(section)

def get_item_id(item):
    for n in ('ObjectID', 'ObjectRef'):
        if n in item.attrib:
            return n + '-' + item.attrib[n]

def save_section(project_file, section_name, section_items):
    output_directory = ".".join(os.path.basename(project_file).split(".")[:-1]) + '.unpacked'
    output_directory = os.path.join(os.path.dirname(project_file), output_directory)
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    for item in section_items:
        item_id = get_item_id(item)
        output_path = os.path.join(output_directory, section_name + '-' + item_id  + '.xml')
        f = open(output_path, 'w')
        f.write(ElementTree.tostring(item, encoding = 'utf-8', method = 'xml'))
        f.close()


def decompose(project_file):
    doc = parse(project_file)
    #todo: drop dest directory contents
    for section_name, render in sections:
        section_items = extract_section(doc, section_name)
        section_items = render(section_items)
        save_section(project_file, section_name, section_items)
    # todo: save the rest + outer tag


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

from rpw import db
from not_found_exception import NotFoundException


def get_element(revit_document, name):
    collector = db.Collector(of_class='FamilySymbol')
    elements = collector.get_elements()
    for e in elements:
        if e.name == name:
            return revit_document.GetElement(e.Id)
    raise NotFoundException("Element not found", name)


def get_element_family(element):
    if element.Family:
        return element.Family
    raise NotFoundException("Element family not found", element)


def get_families():
    collector = db.Collector(of_class='Family')
    return collector.get_elements()


def format_list_to_string(list):
    content = ''
    for element in list:
        content += element + '\n'
    return content

# -*- coding: utf-8 -*-
from Autodesk.Revit import DB
from rpw import db
from rpw.ui.forms import TextInput, Alert
from not_found_exception import NotFoundException

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
uiapp = __revit__.Application


def create_construction_family(family_element_name, new_family_name):
    print('Creating construction family')
    child_family_element = get_element(family_element_name)
    existing_family = get_element_family(child_family_element)
    family_doc = doc.EditFamily(existing_family)
    add_construction_parameters(family_doc)
    options = DB.SaveAsOptions()
    options.OverwriteExistingFile = True
    try:
        transaction.Start('CREATE CONSTRUCTION FAMILY')
        family_doc.SaveAs(new_family_name, options)
        transaction.Commit()
    except Exception as e:
        transaction.RollBack()
        raise Exception("Couldn't create family", e)


def get_element(name):
    collector = db.Collector(of_class='FamilySymbol')
    elements = collector.get_elements()
    for e in elements:
        if e.name == name:
            return doc.GetElement(e.Id)
    raise NotFoundException("Element not found", name)


def get_element_family(element):
    if element.Family:
        return element.Family
    raise NotFoundException("Element family not found", element)


def add_construction_parameters(family_doc):
    parameters_tuples = load_construction_parameters()
    for p in parameters_tuples:
        parameter_name = p[0]
        parameter_type = p[1]
        add_identity_parameter(family_doc, parameter_name, parameter_type)


def load_construction_parameters():
    return [
        ('Selbstbohranker', DB.ParameterType.Text),
        ('SN Mörtelanker', DB.ParameterType.Text),
        ('Ortsbrustanker', DB.ParameterType.Text),
        ('Baustahlgitter 1. Lage, ohne Bogen', DB.ParameterType.Text),
        ('Baustahlgitter 1. Lage, mit Bogen', DB.ParameterType.Text),
        ('Baustahlgitter 2. Lage, mit Bogen', DB.ParameterType.Text),
        ('Rammspieß', DB.ParameterType.Text),
        ('Selbstbohrspieß', DB.ParameterType.Text),
        ('Spritzbeton Kalotte und Strosse', DB.ParameterType.Text),
        ('Spritzbeton Ortsbrust', DB.ParameterType.Text),
        ('Spritzbeton Teilflächen', DB.ParameterType.Text),
        ('Bogen', DB.ParameterType.Text),
        ('Verpressung', DB.ParameterType.Text),
        ('Teilflächen', DB.ParameterType.Text),
        ('Sprengstoff', DB.ParameterType.Text),
    ]


def add_identity_parameter(family_doc, parameter_name, parameter_type):
    family_manager = family_doc.FamilyManager
    family_doc_transaction = DB.Transaction(family_doc)
    try:
        family_doc_transaction.Start("ADD PARAMETER")
        family_manager.AddParameter(parameter_name, DB.BuiltInParameterGroup.PG_IDENTITY_DATA, parameter_type, True)
        family_doc_transaction.Commit()
    except Exception as e:
        print(e)
        family_doc_transaction.RollBack()


def load_construction_family(family_name):
    print('Loading construction family')
    try:
        transaction.Start('LOAD CONSTRUCTION FAMILY')
        result = doc.LoadFamily(family_name)
        if not result:
            print('Family already loaded, using loaded family')
        transaction.Commit()
    except Exception as e:
        transaction.RollBack()
        raise Exception("Could not load family", e)


def create_tunnel_curve():
    as_designed_tunnel_curve, fam_doc = get_existing_tunnel_curve()
    new_xyz = DB.XYZ(200, -200, 0)
    try:
        transaction.Start('CREATE TUNNEL CURVE')
        new_tunnel_curve_ids = DB.ElementTransformUtils.CopyElement(doc, as_designed_tunnel_curve.Id, new_xyz)
        new_tunnel_curve = doc.GetElement(new_tunnel_curve_ids[0])
        transaction.Commit()
    except Exception as e:
        transaction.RollBack()
        raise Exception(e)
    return new_tunnel_curve


def get_existing_tunnel_curve():
    result = search_for_tunnel_curve(doc)
    if result:
        return result, doc
    else:
        search_families_having_tunnel_curve()


def search_for_tunnel_curve(document):
    elements_collector = DB.FilteredElementCollector(document).WhereElementIsNotElementType().ToElements()
    for element in elements_collector:
        try:
            if (str(element.GetType())) == 'Autodesk.Revit.DB.CurveByPoints':
                return element
        except Exception:
            pass
    return None


def search_families_having_tunnel_curve():
    available_families = []
    for family in get_families():
        family = doc.GetElement(family.Id)
        if family.IsEditable:
            fam_doc = doc.EditFamily(family)
            result = search_for_tunnel_curve(fam_doc)
            if result:
                available_families.append(family.Name)
                # TODO how to do it without pathName?
                # uidoc2 = uiapp.OpenDocumentFile(fam_doc.PathName)
                # uidoc.RefreshActiveView()
    content = families_to_content(available_families)
    Alert(title='Error',
          header='Could not locate tunnel curve, please open one of the family documents with the tunnel curve',
          content=content)


def get_families():
    collector = db.Collector(of_class='Family')
    return collector.get_elements()


def families_to_content(families):
    content = ''
    for f in families:
        content += f + '\n'
    return content


def create_section_block(section_element_type_name, tunnel_curve, beginning_meter, ending_meter):
    section_family_element_type = get_as_built_element(section_element_type_name)

    try:
        transaction.Start("CREATE SECTION BLOCK")
        section_family_element_type.Activate()
        new_section_block = DB.AdaptiveComponentInstanceUtils.CreateAdaptiveComponentInstance(doc,section_family_element_type)
        placement_point_a, placement_point_b = get_element_placement_points(new_section_block)
        placement_point_a.SetPointElementReference(create_new_point_on_edge(tunnel_curve, beginning_meter))
        placement_point_b.SetPointElementReference(create_new_point_on_edge(tunnel_curve, ending_meter))
        transaction.Commit()
    except Exception as e:
        transaction.RollBack()
        raise Exception("Couldn't create section block", e)

    return new_section_block


def get_as_built_element(name):
    collector = db.Collector(of_class='FamilySymbol')
    elements = collector.get_elements()
    for e in elements:
        if e.name == name and e.Family.Name == 'as-built':
            return doc.GetElement(e.Id)
    raise NotFoundException("Element not found", name)


def get_element_placement_points(element):
    try:
        placement_points = DB.AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(element)
        return doc.GetElement(placement_points[0]), doc.GetElement(placement_points[1])
    except Exception as e:
        raise Exception("Couldn't get placement points", e)


def create_new_point_on_edge(edge, position_meter):
    return doc.Application.Create.NewPointOnEdge(
        edge.GeometryCurve.Reference,
        DB.PointLocationOnCurve(
            DB.PointOnCurveMeasurementType.SegmentLength,
            millimeter_to_feet(meter_to_millimeter(position_meter)),
            DB.PointOnCurveMeasureFrom.Beginning
        )
    )


def meter_to_millimeter(meter_value):
    return meter_value * 1000


def millimeter_to_feet(millimeter_value):
    return millimeter_value / 304.8


def load_sections():
    return [
        (0,1),
        (1,2),
        (2,3),
        (4,6),
        (6,9),
        (9,13),
    ]


def load_section_material(section):
    return [
        ('Selbstbohranker', 50),
        ('Station Anfang', section[0]),
        ('Station Ende', section[1]),
    ]


def set_element_parameter(element, parameter_name, parameter_value):
    try:
        transaction.Start('SET PARAMETER')
        parameter = get_element_parameter(element, parameter_name)
        parameter.Set(parameter_value)
        transaction.Commit()
    except Exception as e:
        transaction.RollBack()
        raise Exception("Couldn't set section parameter", e)


def get_element_parameter(element, parameter_name):
    for p in element.Parameters:
        if p.Definition.Name == parameter_name:
            return p
    raise NotFoundException("Parameter not found!", parameter_name)


def create_sections():
    print('Creating sections')
    for section in load_sections():
        start_meter = section[0]
        end_meter = section[1]
        section_element = create_section_block(as_designed_element_name, as_built_tunnel_curve, start_meter, end_meter)
        add_section_material(section, section_element)
        set_section_position(section, section_element)


def add_section_material(section, section_element):
    print('Adding section material')
    for material in section.material:
        set_element_parameter(section_element, material.name, material.type)


def set_section_position(section, section_element):
    print('Setting section position')
    position_parameters = approximate_section_position_parameters(section)
    for parameter in position_parameters:
        parameter_name = parameter[0]
        parameter_value = parameter[1]
        set_element_parameter(section_element, parameter_name, parameter_value)


def approximate_section_position_parameters(section):
    start_meter = section[0]
    end_meter = section[1]
    type = 'EBO_K'
    overlap_elements = find_as_designed_elements_that_overlap_element(start_meter, end_meter, type)

    return [
        ('Gradientenhöhe_A', millimeter_to_feet(approximate_parameter(overlap_elements, 'Gradientenhöhe_A'))),
        ('Gradientenhöhe_B', millimeter_to_feet(approximate_parameter(overlap_elements, 'Gradientenhöhe_B'))),
        ('Querneigung', DB.UnitUtils.ConvertToInternalUnits(approximate_parameter(overlap_elements, 'Querneigung'),
                                                            get_degree_forge_type())),
        ('rotXY_A', DB.UnitUtils.ConvertToInternalUnits(approximate_parameter(overlap_elements, 'rotXY_A'),
                                                        get_degree_forge_type())),
        ('rotXY_B', DB.UnitUtils.ConvertToInternalUnits(approximate_parameter(overlap_elements, 'rotXY_B'),
                                                        get_degree_forge_type())),
    ]


def find_as_designed_elements_that_overlap_element(start_meter, end_meter, type):
    as_designed_elements = []
    collector = db.Collector(of_class='FamilyInstance')
    elements = collector.get_elements()
    for e in elements:
        if e.name == type and e.Symbol.Family.Name != 'as-built':
            element_start_meter, element_end_meter = find_as_designed_model_position(e)
            if element_overlap(element_start_meter, element_end_meter, start_meter, end_meter):
                as_designed_elements.append(doc.GetElement(e.Id))
    return as_designed_elements


def find_as_designed_model_position(element):
    p = get_element_parameter(element, 'Blocknummer')
    blocknummer = int(p.AsValueString())
    element_start_meter = blocknummer - 1
    element_end_meter = blocknummer
    return element_start_meter, element_end_meter


def element_overlap(element_A_start, element_A_end, element_B_start, element_B_end):
    if is_position_between(element_A_start, element_B_start, element_B_end) or is_position_between(element_A_end,
                                                                                                   element_B_start,
                                                                                                   element_B_end):
        return True
    return False


def is_position_between(current_position, start_position, end_position):
    if start_position <= current_position <= end_position:
        return True
    return False


def approximate_parameter(elements, parameter_name):
    parameter_values = []
    avg_value = 0
    for element in elements:
        parameter = get_element_parameter(element, parameter_name)
        parameter_value = extract_double_from_string(clean_string(parameter.AsValueString()))
        parameter_values.append(parameter_value)
    if len(parameter_values) > 0:
        avg_value = sum(parameter_values) / len(parameter_values)
    return avg_value


def clean_string(value):
    value = value.replace("°", "")
    return value


def extract_double_from_string(string_number):
    for t in string_number.split():
        try:
            return float(t)
        except ValueError:
            return 0


def get_degree_forge_type():
    for u in DB.UnitUtils.GetAllUnits():
        if DB.UnitUtils.GetTypeCatalogStringForUnit(u) == 'DEGREES':
            return u


# Transactions are context-like objects that guard any changes made to a Revit model
transaction = DB.Transaction(doc)

try:
    as_built_tunnel_curve = create_tunnel_curve()
    as_designed_element_name = TextInput('Name of the used as-designed model')
    create_construction_family(as_designed_element_name, 'as-built.rfa')
    load_construction_family('as-built.rfa')
    create_sections()
except Exception as error:
    Alert(str(error), header="User error occured", title="Message")

# TODO database connection

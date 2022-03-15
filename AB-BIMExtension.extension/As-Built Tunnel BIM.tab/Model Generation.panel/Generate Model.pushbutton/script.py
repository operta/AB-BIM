# -*- coding: utf-8 -*-
from Autodesk.Revit import DB
from Autodesk.Revit import UI
from rpw import db
from rpw.ui.forms import TextInput, Alert, SelectFromList
from not_found_exception import NotFoundException
from pyrevit import forms
from pyrevit import script
import json
import utils as Utils


uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
uiapp = __revit__.Application

TUNNEL_AXIS_ELEMENT_TYPES = ['Autodesk.Revit.DB.CurveByPoints']


def create_construction_family(new_family_name):
    print('Creating construction family')
    existing_family = locate_as_designed_family()
    family_doc = doc.EditFamily(existing_family)
    add_construction_parameters(family_doc)
    options = DB.SaveAsOptions()
    options.OverwriteExistingFile = True
    try:
        family_doc.SaveAs(new_family_name, options)
    except Exception as e:
        print('Overriding Revit file permissions')
        loadFamilyCommandId = UI.RevitCommandId.LookupCommandId('ID_FAMILY_LOAD')
        UI.UIApplication(uiapp).PostCommand(loadFamilyCommandId)
        raise Exception("Couldn't create family due to Revit file permissions, please close the dialog and try again.")


def locate_as_designed_family():
    as_designed_element_name = TextInput('Loading As-designed Family', default='EBO_K',
                                         description='Please enter the name of an used as-designed model.')
    child_family_element = Utils.get_element(doc, as_designed_element_name)
    return Utils.get_element_family(child_family_element)


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
        ('Kommentar', DB.ParameterType.Text),
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
    print('Creating tunnel curve')
    as_designed_tunnel_curve = get_existing_tunnel_curve()
    new_xyz = DB.XYZ(200, -200, 0)
    try:
        transaction.Start('CREATE TUNNEL CURVE')
        new_tunnel_curve_ids = DB.ElementTransformUtils.CopyElement(
            doc,
            as_designed_tunnel_curve.Id,
            new_xyz
        )
        new_tunnel_curve = doc.GetElement(new_tunnel_curve_ids[0])
        transaction.Commit()
    except Exception as e:
        transaction.RollBack()
        raise Exception(e)
    return new_tunnel_curve


def get_existing_tunnel_curve():
    result = search_for_tunnel_curve(doc)
    if result:
        return result
    else:
        search_families_having_tunnel_curve()


def search_for_tunnel_curve(document):
    elements_collector = DB.FilteredElementCollector(document)\
        .WhereElementIsNotElementType()\
        .ToElements()
    for element in elements_collector:
        if element.GetType() and \
                str(element.GetType()) in TUNNEL_AXIS_ELEMENT_TYPES:
            return element
    return None


def search_families_having_tunnel_curve():
    available_families = []
    for family in Utils.get_families():
        family = doc.GetElement(family.Id)
        if family.IsEditable:
            fam_doc = doc.EditFamily(family)
            result = search_for_tunnel_curve(fam_doc)
            if result:
                available_families.append(family.Name)
    content = Utils.format_list_to_string(available_families)
    Alert(title='Error',
          header='Could not locate tunnel curve, '
                 'please open one of the family documents'
                 ' with the tunnel curve',
          content=content)


def create_section_block(
        section_element_type_name,
        tunnel_curve,
        beginning_meter,
        ending_meter
    ):
    section_family_element_type = Utils.get_as_built_element(doc, section_element_type_name)

    try:
        transaction.Start("CREATE SECTION BLOCK")
        section_family_element_type.Activate()
        new_section_block = DB.AdaptiveComponentInstanceUtils.\
            CreateAdaptiveComponentInstance(
            doc,
            section_family_element_type
        )
        placement_point_a, placement_point_b = get_element_placement_points(
            new_section_block
        )
        placement_point_a.SetPointElementReference(
            create_new_point_on_edge(tunnel_curve, beginning_meter)
        )
        placement_point_b.SetPointElementReference(
            create_new_point_on_edge(tunnel_curve, ending_meter)
        )
        transaction.Commit()
    except Exception as e:
        transaction.RollBack()
        raise Exception("Couldn't create section block", e)

    return new_section_block


def get_element_placement_points(element):
    try:
        placement_points = DB.AdaptiveComponentInstanceUtils.\
            GetInstancePlacementPointElementRefIds(element)
        return doc.GetElement(placement_points[0]), doc.GetElement(placement_points[1])
    except Exception as e:
        raise Exception("Couldn't get placement points", e)


def create_new_point_on_edge(edge, position_meter):
    return doc.Application.Create.NewPointOnEdge(
        edge.GeometryCurve.Reference,
        DB.PointLocationOnCurve(
            DB.PointOnCurveMeasurementType.SegmentLength,
            Utils.meter_to_feet(position_meter),
            DB.PointOnCurveMeasureFrom.Beginning
        )
    )


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


def add_tunnel_element(start_meter, end_meter, material, comment):
    as_designed_element_name = find_as_designed_element_name(start_meter, end_meter)
    if as_designed_element_name is None:
        as_designed_element_name = TextInput('Could not find element at position start:' + str(start_meter) +' , end:' + str(end_meter) +
                                             ', Please enter the as-designed element name')
    section_element = create_section_block(as_designed_element_name, as_built_tunnel_curve, start_meter, end_meter)
    set_element_parameter(section_element, 'Kommentar', comment)
    add_section_material(material, section_element)
    set_section_position(start_meter, end_meter, section_element)


def add_section_material(material, section_element):
    print('Adding section material')
    for item in material:
        set_element_parameter(section_element, item['name'], str(item['value']) + ' ' + item['value_type'])


def set_section_position(start_meter, end_meter, section_element):
    print('Setting section position')
    position_parameters = approximate_section_position_parameters(start_meter, end_meter, section_element.Name)
    for parameter in position_parameters:
        parameter_name = parameter[0]
        parameter_value = parameter[1]
        set_element_parameter(section_element, parameter_name, parameter_value)


def approximate_section_position_parameters(start_meter, end_meter, element_type):
    overlap_elements = find_as_designed_elements_that_overlap_element(start_meter, end_meter, element_type)
    return [
        ('Gradientenhöhe_A', Utils.millimeter_to_feet(approximate_parameter(overlap_elements, 'Gradientenhöhe_A'))),
        ('Gradientenhöhe_B', Utils.millimeter_to_feet(approximate_parameter(overlap_elements, 'Gradientenhöhe_B'))),
        ('Querneigung', DB.UnitUtils.ConvertToInternalUnits(approximate_parameter(overlap_elements, 'Querneigung'),
                                                            get_degree_forge_type())),
        ('rotXY_A', DB.UnitUtils.ConvertToInternalUnits(approximate_parameter(overlap_elements, 'rotXY_A'),
                                                        get_degree_forge_type())),
        ('rotXY_B', DB.UnitUtils.ConvertToInternalUnits(approximate_parameter(overlap_elements, 'rotXY_B'),
                                                        get_degree_forge_type())),
    ]


def find_as_designed_element_name(start_meter, end_meter):
    collector = db.Collector(of_class='FamilyInstance')
    elements = collector.get_elements()
    for e in elements:
        try:
            if e.Symbol.Family.Name != 'as-built' and has_blocknummer(e):
                element_start_meter, element_end_meter = find_as_designed_model_position(e)
                if element_overlap(element_start_meter, element_end_meter, start_meter, end_meter):
                    return e.name
        except Exception as e:
            continue
    return None


def has_blocknummer(element):
    try:
        p = get_element_parameter(element, 'Blocknummer')
        return True
    except Exception as e:
        return False


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


def load_construction_data():
    print('Loading construction data')
    Alert("Click button \'Load data from TIMS\' to generate current data snapshot from TIMS. You are also able to add your own construction data",
          header="Adding Construction Data",
          title="Information")
    file_path = forms.pick_file(title='Please select a file containing construction information', file_ext='json')
    data = open(file_path, 'r').read()
    return json.loads(data)


def add_construction_data(construction_data):
    print('Adding construction data')
    cross_section_type = SelectFromList('Select cross section type of tunnel rounds you want to generate',
                                        ["Kalotte", "Strosse", "Sohle"])
    for item in construction_data['sections']:
        for round in item['rounds']:
            if round['cross_section_type'] == cross_section_type:
                add_tunnel_element(round['start_meter'], round['end_meter'], round['material'], round['comment'])


# Transactions are context-like objects that guard any changes made to a Revit model
transaction = DB.Transaction(doc)

try:
    create_construction_family('as-built.rfa')
    load_construction_family('as-built.rfa')
    as_built_tunnel_curve = create_tunnel_curve()
    data = load_construction_data()
    add_construction_data(data)
except Exception as error:
    Alert(str(error), header="User error occured", title="Message")


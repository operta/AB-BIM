from Autodesk.Revit import DB
from rpw import db
from rpw.ui.forms import TextInput, Alert, TaskDialog, CommandLink
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
        ('SN Mortelanker', DB.ParameterType.Text),
        ('Ortsbrustanker', DB.ParameterType.Text),
        ('Baustahlgitter 1. Lage, ohne Bogen', DB.ParameterType.Text),
        ('Baustahlgitter 1. Lage, mit Bogen', DB.ParameterType.Text),
        ('Baustahlgitter 2. Lage, mit Bogen', DB.ParameterType.Text),
        ('Rammspiess', DB.ParameterType.Text),
        ('Selbstbohrspiess', DB.ParameterType.Text),
        ('Spritzbeton Kalotte und Strosse', DB.ParameterType.Text),
        ('Spritzbeton Ortsbrust', DB.ParameterType.Text),
        ('Spritzbeton Teilflachen', DB.ParameterType.Text),
        ('Bogen', DB.ParameterType.Text),
        ('Verpressung', DB.ParameterType.Text),
        ('Teilflachen', DB.ParameterType.Text),
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
        new_section_block = DB.AdaptiveComponentInstanceUtils.CreateAdaptiveComponentInstance(doc, section_family_element_type)
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
        (0,145),
    ]


def load_section_parameters(section):
    return [
        ('Material 1', 50),
        ('Station Anfang', section[0]),
        ('Station Ende', section[1]),
    ]


def set_section_parameters_values(section_element, parameter_name, parameter_value):
    try:
        transaction.Start('SET PARAMETERS')
        for p in section_element.Parameters:
            if p.Definition.Name == parameter_name:
                p.Set(str(parameter_value))
        transaction.Commit()
    except Exception as e:
        transaction.RollBack()
        raise Exception("Couldn't set section parameters", e)


# Transactions are context-like objects that guard any changes made to a Revit model
transaction = DB.Transaction(doc)

try:
    as_built_tunnel_curve = create_tunnel_curve()
    as_designed_element_name = TextInput('Name of the used as-designed model')
    create_construction_family(as_designed_element_name, 'as-built.rfa')
    load_construction_family('as-built.rfa')
    sections = load_sections()
    for id, s in enumerate(sections):
        section_element = create_section_block(as_designed_element_name, as_built_tunnel_curve, s[0],s[1])
        section_parameters = load_section_parameters(s)
        for p in section_parameters:
            set_section_parameters_values(section_element, p[0], p[1])
except Exception as error:
    Alert(str(error), header="User error occured", title="Message")


# TODO database connection, + include lib in revit

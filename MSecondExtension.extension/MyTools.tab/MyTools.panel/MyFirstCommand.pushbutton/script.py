from Autodesk.Revit import DB
from rpw import db

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
uiapp = __revit__.Application


def get_family_model(name, family_name='EBO_mitNische'):
    collector = db.Collector(of_class='FamilySymbol')
    element_types = collector.get_elements()
    for elem in element_types:
        if elem.name == name and elem.Family.Name == family_name:
            return doc.GetElement(elem.Id)


def add_identity_parameter(transaction, family_manager, parameter_name, parameter_type):
    try:
        transaction.Start("ADD PARAMETER")
        family_manager.AddParameter(parameter_name, DB.BuiltInParameterGroup.PG_IDENTITY_DATA, parameter_type, True)
        transaction.Commit()
    except Exception as e:
        print('error')
        print(e)
        transaction.RollBack()


def create_construction_family(family_name, parameters_tuples, child_family_model_name='EBO_K'):
    child_family_element = get_family_model(child_family_model_name)
    family = child_family_element.Family
    family_doc = doc.EditFamily(family)
    family_manager = family_doc.FamilyManager
    family_doc_transaction = DB.Transaction(family_doc)

    for p in parameters_tuples:
        add_identity_parameter(family_doc_transaction, family_manager, p[0], p[1])

    try:
        family_doc.SaveAs(family_name)
        family_doc.Close(True)
    except Exception as e:
        print('error')
        print(e)


def get_tunnel_curve():
    elements_collector = DB.FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
    for element in elements_collector:
        try:
            if (str(element.GetType())) == 'Autodesk.Revit.DB.CurveByPoints':
                return element
        except:
            print('ERROR')


def get_tunnel_element(type):
    elements_collector = DB.FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
    for element in elements_collector:
        try:
            if element.Name == type and str(element.GetType()) == 'Autodesk.Revit.DB.FamilyInstance':
               return element
        except Exception as e:
            print('ERROR')
            print(e)


def get_element_placement_points(element):
    placement_points = DB.AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(element)
    try:
        return doc.GetElement(placement_points[0]), doc.GetElement(placement_points[1])
    except:
        print('ERROR')


def create_new_point_on_edge(edge, position_meter):
    return doc.Application.Create.NewPointOnEdge(
        edge.GeometryCurve.Reference,
        DB.PointLocationOnCurve(
            DB.PointOnCurveMeasurementType.SegmentLength,
            position_meter,
            DB.PointOnCurveMeasureFrom.Beginning
        )
    )


def create_tunnel_curve(transaction, base_tunnel_curve, new_xyz):
    transaction.Start('CREATE TUNNEL CURVE')
    new_tunnel_curve_ids = DB.ElementTransformUtils.CopyElement(doc, base_tunnel_curve.Id, new_xyz)
    new_tunnel_curve = doc.GetElement(new_tunnel_curve_ids[0])
    transaction.Commit()
    return new_tunnel_curve


def create_section_block(transaction, section_element_type_name, family_name, tunnel_curve, beginning_meter, ending_meter, tunnel_curve_xyz):
    transaction.Start("CREATE SECTION BLOCK")
    child_family_element = get_family_model(section_element_type_name, family_name)
    child_family_element.Activate()
    new_section_block = doc.FamilyCreate.NewFamilyInstance(DB.XYZ(50, 0, 0), child_family_element, DB.Structure.StructuralType.NonStructural)

    placement_point_a, placement_point_b = get_element_placement_points(new_section_block)
    placement_point_a.SetPointElementReference(create_new_point_on_edge(tunnel_curve, beginning_meter))
    placement_point_b.SetPointElementReference(create_new_point_on_edge(tunnel_curve, ending_meter))
    transaction.Commit()

    return new_section_block


def set_section_parameters_values(transaction, section_element, parameter_name, parameter_value):
    transaction.Start('SET PARAMS')
    for p in section_element.Parameters:
        if p.Definition.Name == parameter_name:
            p.Set(str(parameter_value))
    transaction.Commit()


def load_section_parameters(section):
    return [
        ('Material 1', 50),
        ('Station Anfang', section[0]),
        ('Station Ende', section[1]),
    ]


as_designed_tunnel_curve = get_tunnel_curve()

transaction = DB.Transaction(doc)

as_built_tunnel_curve_xyz = DB.XYZ(200,0,0)
as_built_tunnel_curve = create_tunnel_curve(transaction, as_designed_tunnel_curve, as_built_tunnel_curve_xyz)


create_construction_family('construction.rfa', [('Material 1', DB.ParameterType.Text)], 'EBO_K')


transaction.Start('LOAD CONSTRUCTION FAMILY')
doc.LoadFamily('construction.rfa')
transaction.Commit()


sections = [
    (0,10),
    (10.1,15),
    (15.1,20),
]
for id, s in enumerate(sections):
    section_element = create_section_block(transaction, 'EBO_K', 'construction', as_built_tunnel_curve, s[0], s[1], as_built_tunnel_curve_xyz)
    section_parameters = load_section_parameters(s)
    for p in section_parameters:
        set_section_parameters_values(transaction, section_element, p[0], p[1])































"""Calculates total volume of all walls in the model."""

from Autodesk.Revit import DB
from Autodesk.Revit import Creation
from Autodesk.Revit.UI import UIApplication
# from Autodesk.Revit.DB.IFC import ExporterIFCUtils

from rpw import db


# current document
uidoc = __revit__.ActiveUIDocument
print(uidoc)
doc = __revit__.ActiveUIDocument.Document
uiapp = __revit__.Application
print(doc)
print('DOCUMENT UNIT SYSTEM')
print(doc.DisplayUnitSystem)
print(DB.ExtensibleStorage.Schema.ApplicationGUID)
# Units
# u = new Units(UnitSystem.Metric);
# print(doc.GetUnits().GetFormatOptions(DB.UnitSystem.Metric))

def getFamilySymbol(elementName):
    collector = db.Collector(of_class='FamilySymbol')
    element_types = collector.get_elements()
    for elem in element_types:
        if elem.name == elementName:
            return elem

def getTunnelElement(type):
    elements_collector = DB.FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
    for element in elements_collector:
        try:
            if element.Name == type and str(element.GetType()) == 'Autodesk.Revit.DB.FamilyInstance':
               return element, element.Category
        except:
            print('ERROR')


def getTunnelCurve():
    elements_collector = DB.FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
    for element in elements_collector:
        try:
            if (str(element.GetType())) == 'Autodesk.Revit.DB.CurveByPoints':
                return element, element.GetPoints()
        except:
            print('ERROR')

# ELEMENTS COLLECTOR
def getTunnelElementInfo(types, fields):
    elements_collector = DB.FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
    for element in elements_collector:
        try:
            if element.Name in types and str(element.GetType()) == 'Autodesk.Revit.DB.FamilyInstance':
                print('Name')
                print(element.Name)
                for param in element.Parameters:
                    if param.Definition.Name in fields:
                        print(param.Definition.Name)
                        print(param.AsValueString())
        except:
            print('ERROR')


# getTunnelElementInfo(['EBO_So', 'EBO_K', 'EBO_ST'], ['Station Anfang', 'Blocknummer', 'Station Ende'])

tunnelCurve, tunnelCurvePoints = getTunnelCurve()
print(tunnelCurve)
print(tunnelCurve.Name)
print(tunnelCurve.GetPoints())
print('BASE CURVE POINTS')
for p in tunnelCurve.GetPoints():
    print(p.Position)


print('CREATE NEW CURVE')
t = DB.Transaction(doc)
t.Start('CREATE NEW CURVE')

# print(tunnelCurve)
# for param in tunnelCurve.Parameters:
#     print(param.Definition.Name)
#     print(param.AsValueString())
#     print(param.AsInteger())

newCurveIds = DB.ElementTransformUtils.CopyElement(doc, tunnelCurve.Id, xyz)
print(newCurveIds)
newCurve = doc.GetElement(newCurveIds[0])
print(newCurve)
print("POINTS")
points = newCurve.GetPoints()
for point in newCurve.GetPoints():
    print(point.Position)
t.Commit()





print('CREATE SECTION BLOCK')
curveReference = DB.Reference(newCurve)

t.Start('CREATE SECTION BLOCK')
element, element_category = getTunnelElement('EBO_K')


newSectionIds = DB.ElementTransformUtils.CopyElement(doc, element.Id, xyz)
print(newSectionIds)
newSection = doc.GetElement(newSectionIds[0])
ec = DB.AdaptiveComponentInstanceUtils.GetInstancePlacementPointElementRefIds(newSection)
for p in ec:
    print(p)
point = doc.GetElement(ec[0])
po = doc.Application.Create.NewPointOnEdge(newCurve.GeometryCurve.Reference, DB.PointLocationOnCurve(DB.PointOnCurveMeasurementType.SegmentLength, 10, DB.PointOnCurveMeasureFrom.Beginning  ))
point.SetPointElementReference(po)


point = doc.GetElement(ec[1])
po2 = doc.Application.Create.NewPointOnEdge(newCurve.GeometryCurve.Reference, DB.PointLocationOnCurve(DB.PointOnCurveMeasurementType.SegmentLength, 100, DB.PointOnCurveMeasureFrom.Beginning  ))

point.SetPointElementReference(po2)
print(point.Position)

t.Commit()















# t.Start('add points')
#
# # TODO these need to be reference points
# startPoint = DB.XYZ(0, 0, 0)
# endPoint = DB.XYZ(100, 0, 0)
#
# rpa = DB.ReferencePointArray()
# rpa.Insert(points[1], 0)
# rpa.Insert(points[0], 1)
# newCurve.SetPoints(rpa)
# t.Commit()

# // TODO create function to create point of section length
# plc = DB.PointLocationOnCurve(
#     DB.PointOnCurveMeasurementType.SegmentLength,
#     50,
#     DB.PointOnCurveMeasureFrom.Beginning
# )
# newCurveRef = DB.Reference(newCurve)
# newPoint = uiapp.Create.NewPointOnEdge(newCurveRef, plc)
#
#
# print("NEW POINTS")
# for point in newCurve.GetPoints():
#     print(point.Position)
#     print(point.GetCoordinateSystem())













# elements_collector = DB.FilteredElementCollector(doc).WhereElementIsElementType().ToElements()
# for element in elements_collector:
#     # print(element.GetType())
#     # try:
#     #     print(element.FamilyName)
#     # except:
#     #     print('fail')
#     # SharedParameterElements are user defined
#     # TODO i think we should check also OST_SECTIONS
#     # if str(element.GetType()) == 'Autodesk.Revit.DB.SharedParameterElement':
#     if 'EBO' in str(element.FamilyName):
#         print(element.FamilyName)
#         print(element.GetSubelements())
#         # for param in element.Parameters:
#         #     print(param.Definition.Name)
#         #     print(param.AsValueString())
#         #     print(param.AsInteger())


    # try:
    #     if "tation" in element.Name:
    #         print(element.GetType())
    #         print(element.GetSubelements())
    #         print(element.Name)
    #         print(element.GroupId)
    # except:
    #     print('ERROR')

    # if element.Name == 'Station Anfang':
    #     print(element.Category)
    #     print(element.GetType())
    #     print(element.GetAnalyticalModel())
    #     for param in element.Parameters:
    #         print(param.Definition.Name)
    #         print(param.AsValueString())
    #         print(param.AsInteger())
    # try:
    #
    # except:
    #     print('ERROR')
#
# wall_instance = DB.Wall.Create(doc)

# project_id = doc.Close(doc)
#
# print(project_id)

#
# section_collector = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Sections).WhereElementIsNotElementType()
# for section in section_collector:
#     print('hehe')
#
# print("TEST")
#
# # Creating collector instance and collecting all the walls from the model
# wall_collector = DB.FilteredElementCollector(doc)\
#                    .OfCategory(DB.BuiltInCategory.OST_Walls)\
#                    .WhereElementIsNotElementType()
#
#
# # Iterate over wall and collect Volume data
# total_volume = 0.0
#
# for wall in wall_collector:
#     vol_param = wall.Parameter[DB.BuiltInParameter.HOST_VOLUME_COMPUTED]
#     if vol_param:
#         total_volume = total_volume + vol_param.AsDouble()
#
# # now that results are collected, print the total
# print("Total Volume is: {}".format(total_volume))4






# ELEMENT TYPES COLLECTOR
# elements_collector = DB.FilteredElementCollector(doc).WhereElementIsElementType().ToElements()
# for element in elements_collector:
#
#     try:
#         print('family name')
#         print(element)
#         print(element.FamilyName)
#     except:
#         continue











# t.Start('create eboK')
# famS = getFamilySymbol('EBO_K')

# t.Commit()
# Creation.Document.NewFamilyInstance(curveReference, xyz, xyz2, famS)

# t.Start('create eboK')
# element, element_category =  getTunnelElement('EBO_K')
# print(element_category)
# print(element)
#
# newSectionIds = DB.ElementTransformUtils.CopyElement(doc, element.Id ,xyz)
# print(newSectionIds)
# newSection = doc.GetElement(newSectionIds[0])
# print(newSection.GetFamilyPointPlacementReferences())
# # ei = DB.DirectShape.CreateElementInstance(doc, element.Id, element_category.Id, "TEST", DB.Transform.Identity)
# # ei2 = DB.DirectShape.CreateElement(doc, element_category.Id)
# #
# # print(ei2)
# # ei2.AddReferencePoint(points[0].Position)
# # ei2.AddReferencePoint(points[1].Position)
# # print(ei2.ViewSpecific)
# # print(ei2.Document)
# t.Commit()

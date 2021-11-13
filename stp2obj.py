"""
author: cmsacco + njohnson
A script to test reformatting OCC tesselation objects to .obj files
and transform them into .glb files for use in Google's Sceneform 
"""


from io import DEFAULT_BUFFER_SIZE
from numpy.lib.index_tricks import _fill_diagonal_dispatcher
from OCC.Core.Tesselator import ShapeTesselator
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
import re
import os
from OCC.Core.TDF import TDF_LabelSequence, TDF_Label
from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool_ShapeTool, XCAFDoc_DocumentTool_ColorTool
from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
from typing import Union, Tuple, List, Any, Optional, Iterator, Iterable, Set
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.GCE2d import GCE2d_MakeLine
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCC.Core.gp import gp_Pnt2d
from OCC.Core.BOPAlgo import BOPAlgo_GlueOff, BOPAlgo_Splitter
from OCC.Core.BRep import BRep_Tool, BRep_Builder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Section
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Copy, BRepBuilderAPI_Sewing
from OCC.Core.BRepClass import BRepClass_FClassifier, BRepClass_FaceExplorer
from OCC.Core.BRepFeat import BRepFeat_SplitShape
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.BRepLib import breplib_ExtendFace
from OCC.Core.GeomAPI import GeomAPI_Interpolate, GeomAPI_ProjectPointOnSurf
from OCC.Core.GeomAdaptor import GeomAdaptor_Surface
from OCC.Core.ShapeAnalysis import *
from OCC.Core.ShapeFix import ShapeFix_ShapeTolerance, ShapeFix_Shell
from OCC.Core.TColStd import TColStd_HArray1OfBoolean
from OCC.Core.TColgp import TColgp_HArray1OfPnt, TColgp_Array1OfVec
from OCC.Core.TopAbs import *
from OCC.Core.TopExp import topexp
from OCC.Core.TopTools import *
from OCC.Core.TopoDS import TopoDS_Face, TopoDS_Wire, TopoDS_Shell, TopoDS_Edge, TopoDS_Shape, TopoDS_Compound
from OCC.Core.gp import *
from OCC.Core.AIS import *
from OCC.Core.Aspect import *
from OCC.Core.Graphic3d import *
from OCC.Core.Prs3d import *
from OCC.Core.PrsMgr import *
from OCC.Core.Quantity import *
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Extend.ShapeFactory import scale_shape, make_face
from OCC.Core.ShapeFix import ShapeFix_Wire
from Utilities.Logger import logger
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from shapely.geometry import Polygon, MultiPolygon
from shapely.errors import TopologicalError
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
import json



def read_step_file(filename):
    """ read the STEP file and returns a compound
    """
    step_reader = STEPControl_Reader()
    status = step_reader.ReadFile(filename)

    if status == IFSelect_RetDone:  # check status
        failsonly = False
        step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
        step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)
        step_reader.TransferRoot(1)
        a_shape = step_reader.Shape(1)
    else:
        print("Error: can't read file.")
        sys.exit(0)
    return a_shape


def buildShell(faces, shell=None) -> TopoDS_Shell:
    """
    * This function builds a shell
    :param faces: faces to build shell out of
    :param shell: Used to detect if shell is already made, and make one if needed
    """
    builder = BRep_Builder()
    if shell is None: shell = TopoDS_Shell()
    builder.MakeShell(shell)
    for face in faces:
        builder.Add(shell, face)
    return shell

def splitShellByWire(shell: TopoDS_Shell, wire: TopoDS_Wire) -> Tuple[TopoDS_Shell, TopoDS_Shell]:
    if isinstance(shell, TopoDS_Face):
        shell = buildShell([shell])

    sfs = ShapeFix_Shell(shell)
    sfs.FixFaceOrientation(shell, True, True)
    sfs.SetFixFaceMode(True)
    sfs.SetFixOrientationMode(True)
    sfs.Perform()
    shell = sfs.Shell()

    # fix the shape here, very important it is closed
    sfw = ShapeFix_Wire()
    sfw.Load(wire)
    sfw.FixReorder()
    sfw.FixConnected()
    sfw.FixClosed()
    sfw.FixSmall(False, 1)
    sfw.FixShifted()
    sfw.FixNotchedEdges()
    sfw.FixTails()
    sfw.Perform()
    wire = sfw.Wire()

    # do not continue if the wire isn't closed
    # assert wire.Closed()

    # correct tolerances before splitting
    sfst = ShapeFix_ShapeTolerance()

    sfst.SetTolerance(shell, 2, TopAbs_FACE)
    sfst.SetTolerance(shell, 1e-2, TopAbs_EDGE)
    sfst.SetTolerance(shell, 1e-2, TopAbs_VERTEX)

    sfst.SetTolerance(wire, 1e-2, TopAbs_EDGE)

    splitter = BOPAlgo_Splitter()
    splitter.AddArgument(shell)
    splitter.AddTool(wire)
    splitter.SetRunParallel(True)
    splitter.SetCheckInverted(True)
    splitter.Perform()
    split_shape = splitter.Shape()

    if splitter.HasWarnings(): logger.debug(splitter.DumpWarningsToString())  # make this a debug line
    assert not splitter.HasErrors(), splitter.DumpErrorsToString()  # if has errors, try changing the tolerances

    edge_face_map = TopTools_IndexedDataMapOfShapeListOfShape()
    topexp.MapShapesAndAncestors(split_shape, TopAbs_EDGE, TopAbs_FACE, edge_face_map)

    face_edge_map = TopTools_IndexedDataMapOfShapeListOfShape()
    topexp.MapShapesAndAncestors(split_shape, TopAbs_FACE, TopAbs_EDGE, face_edge_map)

    for edge in TopologyExplorer(wire).edges():
        for m_edge in iterListOfShapes(splitter.Modified(edge)):
            edge_face_map.RemoveKey(m_edge)

    def recurse(edges: Iterable[TopoDS_Edge], outer_faces: Set[TopoDS_Face] = None):
        if outer_faces is None: outer_faces = set()
        outer_front: Set[TopoDS_Face] = set()
        for edge in edges:
            if not edge_face_map.Contains(edge): continue
            for face in iterListOfShapes(edge_face_map.FindFromKey(edge)):
                if not face_edge_map.Contains(face): continue
                outer_front.add(face)
            edge_face_map.RemoveKey(edge)

        if not outer_front: return outer_faces

        next_edges: Set[TopoDS_Edge] = set()
        for face in outer_front:
            for edge in TopologyExplorer(face).edges():
                if not edge_face_map.Contains(edge): continue
                next_edges.add(edge)
            face_edge_map.RemoveKey(face)

        outer_faces.update(outer_front)

        return recurse(next_edges, outer_faces)

    outerWires = ShapeAnalysis_FreeBounds(shell).GetClosedWires()
    outer_faces = recurse(TopologyExplorer(outerWires).edges())

    inner_faces = set()
    for face in TopologyExplorer(split_shape).faces():
        if face_edge_map.Contains(face): inner_faces.add(face)

    outer_shell = buildShell(outer_faces)
    inner_shell = buildShell(inner_faces)

    return inner_shell, outer_shell

    #return list(TopologyExplorer(split_shape).faces())[1]

def iterListOfShapes(listOfShapes: TopTools_ListOfShape) -> Iterator[TopoDS_Face]:
    """
    * Adds the current shape to the list of shapes
    :param listOfShapes: List of shapes
    """
    for _ in range(listOfShapes.Size()):
        shape = listOfShapes.First()
        yield shape
        listOfShapes.RemoveFirst()
        listOfShapes.Append(shape)  # do not change data in list

def readDefectJSON(filepath):
    f = open(filepath, 'r')

    defect_data = json.load(f)
    f.close()

    accumulator = []

    for defect in defect_data.keys():
        p = Polygon(defect_data[defect][0])
        c = defect_data[defect][1]
        if(p.is_valid and (type(p) != MultiPolygon)):
            accumulator.append([p.buffer(0),c])

    return accumulator


def getAllofType(def_list: list, def_class):

    reduced_list = []

    for defect in def_list:
        if(defect[1] == def_class):
            reduced_list.append(defect[0])

    if(len(reduced_list) != 0):
        polygons = MultiPolygon(reduced_list).buffer(0)
        return polygons
    else:
        return MultiPolygon()
        


def cutPolygonFromSurface(defect: Polygon, surface):
    
    uv_polygon_list = list(defect.exterior.coords)
    
    #create edges between the uv vertices
    edges = []
    for i in range(len(uv_polygon_list) - 1):
        edges.append(Edge_from_UV(uv_polygon_list[i], uv_polygon_list[i + 1], surface.BSpline()))

    w = BRepBuilderAPI_MakeWire()
    for edge in edges: #traverse the edges to make a wire
        w.Add(edge)
    wire = w.Wire()
            
    inner, outer = splitShellByWire(surface.Face(), wire)

    return inner


def Edge_from_UV(p1, p2, surf):
    uv1 = gp_Pnt2d(p1[0], p1[1])
    uv2 = gp_Pnt2d(p2[0], p2[1])

    aline = GCE2d_MakeLine(uv1, uv2).Value()
    edge = BRepBuilderAPI_MakeEdge(aline, surf, 0., uv1.Distance(uv2)).Edge()

    return edge

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False

# create the shape
box_s = BRepPrimAPI_MakeBox(10, 20, 30).Shape() 

#Need to ask the user for the directory to stp file below -- will implement later 
#toolname = str(input('What is the name of the tool file (.stp) that you want to use? \n')) 
#could make this a nice GUI 
#wd = str(input('Where does this file live? \n'))
#toolfile = os.path.join(wd, toolname)
toolfile = os.path.join("C:\\Users\\Owner\\Desktop\\testfileforconversion", "curvedtool_originalcad_originzero_stp.step")


tool = read_step_file(toolfile)
faces = TopologyExplorer(tool).faces()
t_face = list(faces)[0]
surf = BRepAdaptor_Surface(t_face, True)


preRework = "PreReworkUVDefects_fixedNames.json" 
defects = readDefectJSON(preRework)

#list of types of defects // not all are present in this specific JSON file -- those not present are marked with a '#'
Overlap = getAllofType(defects, "Overlap")
Gap = getAllofType(defects, "Gap")
Wrinkle = getAllofType(defects, "Wrinkle")
MissingTow = getAllofType(defects, "MissingTow")
SurfaceSeparation = getAllofType(defects, "SurfaceSeparation")
LooseTow = getAllofType(defects, "LooseTow")
Bridging = getAllofType(defects, "Bridging")
types_of_defects = {'Overlap' : Overlap, 'Gap' : Gap, 'Wrinkle' : Wrinkle, 'MissingTow' : MissingTow, 'SurfaceSeparation' : SurfaceSeparation, 'LooseTow' : LooseTow, 'Bridging' : Bridging}
                   
i=0
for dft, dftData in types_of_defects.items():
    vs = []
    faces = []

    faces.append("g front {}\n".format(i))
    faces.append("usemtl " + dft + "\n")
    i+=1

    vertex_counter = 0
    if(type(dftData) == MultiPolygon):

        for i in range(len(dftData.geoms)):
            #if(i < 2):
            d = cutPolygonFromSurface(dftData[i], surf)

            tess = ShapeTesselator(d)
            tess.Compute()
            vertices_position = tess.GetVerticesPositionAsTuple()
            vertices = np.array(vertices_position).reshape(int(len(vertices_position) / 3), 3)

            for j in range(vertices.shape[0]):
                vs.append("v " + str((vertices[j][0])) + " " + str((vertices[j][1])) + " " + str((vertices[j][2])) + "\n")

            for j in range(int((vertex_counter + 1)/3), int(vertices.shape[0] / 3) + int((vertex_counter + 1)/3)):
                faces.append("f " + str(3*j + 1) + " " + str(3*j + 2) + " " +  str(3*j + 3) + "\n")
            

            vertex_counter += vertices.shape[0]
    elif(type(dftData) == Polygon):
        d = cutPolygonFromSurface(dftData, surf)

        tess = ShapeTesselator(d)
        tess.Compute()
        vertices_position = tess.GetVerticesPositionAsTuple()
        vertices = np.array(vertices_position).reshape(int(len(vertices_position) / 3), 3)

        for j in range(vertices.shape[0]):
            vs.append("v " + str((vertices[j][0])) + " " + str((vertices[j][1])) + " " + str((vertices[j][2])) + "\n") 

        for j in range(int((vertex_counter + 1)/3), int(vertices.shape[0] / 3) + int((vertex_counter + 1)/3)):
            faces.append("f " + str(3*j + 1) + " " + str(3*j + 2) + " " +  str(3*j + 3) + "\n")

    f = open("curvedtool_" + str.lower(dft) + ".obj", 'w')

    #write obj file
    f.writelines("mtllib master_namesChanged.mtl \n")
    for line in vs:
        f.writelines(line)

    for line in faces:
        f.writelines(line)

    f.close()

##################################Copy/Paste to make .obj file with ALL DEFECTS in one######################################
faces_all = []
v_all = []
for dft, dftData in types_of_defects.items():
    vs = []
    faces = []

    faces_all.append("g front {}\n".format(i))
    faces_all.append("usemtl " + dft + "\n")
    vs.append("v 0 0 0\n")
    vs.append("v 0 0 0\n")
    vs.append("v 0 0 0\n")
    vs.append("v 0 0 0\n")
    vs.append("v 0 0 0\n")
    vs.append("v 0 0 0\n")

    i+=1

    vertex_counter = 0
    if(type(dftData) == MultiPolygon):

        for i in range(len(dftData.geoms)):
            #if(i < 2):
            d = cutPolygonFromSurface(dftData[i], surf)

            tess = ShapeTesselator(d)
            tess.Compute()
            vertices_position = tess.GetVerticesPositionAsTuple()
            vertices = np.array(vertices_position).reshape(int(len(vertices_position) / 3), 3)

            for j in range(vertices.shape[0]):
                vs.append("v " + str((vertices[j][0])) + " " + str((vertices[j][1])) + " " + str((vertices[j][2])) + "\n") 

            last_num = (len(faces_all) - 2) * 3

            for j in range(int((vertex_counter + 1)/3), int(vertices.shape[0] / 3) + int((vertex_counter + 1)/3)):
                faces.append("f " + str(3*j + 1 + last_num) + " " + str(3*j + 2 + last_num) + " " +  str(3*j + 3 + last_num) + "\n")
           
            vertex_counter += vertices.shape[0]

    elif(type(dftData) == Polygon):
        d = cutPolygonFromSurface(dftData, surf)
        tess = ShapeTesselator(d)
        tess.Compute()
        vertices_position = tess.GetVerticesPositionAsTuple()
        vertices = np.array(vertices_position).reshape(int(len(vertices_position) / 3), 3)

        for j in range(vertices.shape[0]):
            vs.append("v " + str((vertices[j][0])) + " " + str((vertices[j][1])) + " " + str((vertices[j][2])) + "\n") 
        
        last_num = (len(faces_all) - 2) * 3

        for j in range(int((vertex_counter + 1)/3), int(vertices.shape[0] / 3) + int((vertex_counter + 1)/3)):
            faces.append("f " + str(3*j + 1 + last_num) + " " + str(3*j + 2 + last_num) + " " +  str(3*j + 3 + last_num) + "\n")
        
    v_all.extend(vs)                    
    faces_all.extend(faces)
   
f = open("curvedtool_alldefects.obj", 'w')
#write obj file
f.writelines("mtllib master_namesChanged.mtl \n")
for line in v_all:
    f.writelines(line)

for line in faces_all:
    f.writelines(line)

f.close()

#write glb file
#os.system("obj2gltf -i curvedtool_alldefects_obj.obj -o curvedtool_alldefects_glb.glb")

#######################################################################################################################
## File to take in .stp file and return .obj file as the output
    #that .obj file output will be used as an input to 
    #covert to the final output .glb file 

## This is using Sacco's stp2obj then
    #cesium's obj2gltf from the command line 

## From pyoccenv environment in conda prompt, run stp2obj
## From windows command prompt, run obj2gltf
#################################python#################################################################################
import bpy
from bpy.props import *
from . utils.depsgraph import getEvaluatedID
from . operators.callbacks import executeCallback
from . utils.depsgraph import getActiveDepsgraph
from . data_structures import (Vector3DList, EdgeIndicesList, PolygonIndicesList,
                               FloatList, UShortList, UIntegerList, Vector2DList,
                               ColorList, DoubleList, LongList, BooleanList)

def register():
    bpy.types.Context.getActiveAnimationNodeTree = getActiveAnimationNodeTree
    bpy.types.Operator.an_executeCallback = _executeCallback
    bpy.types.Mesh.an = PointerProperty(type = MeshProperties)
    bpy.types.Object.an = PointerProperty(type = ObjectProperties)
    bpy.types.ID.an_data = PointerProperty(type = IDProperties)

def unregister():
    del bpy.types.Context.getActiveAnimationNodeTree
    del bpy.types.Operator.an_executeCallback
    del bpy.types.Mesh.an
    del bpy.types.Object.an
    del bpy.types.ID.an_data

def getActiveAnimationNodeTree(context):
    if context.area.type == "NODE_EDITOR":
        tree = context.space_data.node_tree
        if getattr(tree, "bl_idname", "") == "an_AnimationNodeTree":
            return tree

def _executeCallback(operator, callback, *args, **kwargs):
    executeCallback(callback, *args, **kwargs)

class MeshProperties(bpy.types.PropertyGroup):
    bl_idname = "an_MeshProperties"

    def getVertices(self):
        vertices = Vector3DList(length = len(self.mesh.vertices))
        self.mesh.vertices.foreach_get("co", vertices.asMemoryView())
        return vertices

    def getEdgeIndices(self):
        edges = EdgeIndicesList(length = len(self.mesh.edges))
        self.mesh.edges.foreach_get("vertices", edges.asMemoryView())
        return edges

    def getPolygonIndices(self):
        polygons = PolygonIndicesList(
                        indicesAmount = len(self.mesh.loops),
                        polygonAmount = len(self.mesh.polygons))
        self.mesh.polygons.foreach_get("vertices", polygons.indices.asMemoryView())
        self.mesh.polygons.foreach_get("loop_total", polygons.polyLengths.asMemoryView())
        self.mesh.polygons.foreach_get("loop_start", polygons.polyStarts.asMemoryView())
        return polygons

    def getVertexNormals(self):
        normals = Vector3DList(length = len(self.mesh.vertices))
        self.mesh.vertices.foreach_get("normal", normals.asMemoryView())
        return normals

    def getPolygonNormals(self):
        normals = Vector3DList(length = len(self.mesh.polygons))
        self.mesh.polygons.foreach_get("normal", normals.asMemoryView())
        return normals

    def getPolygonCenters(self):
        centers = Vector3DList(length = len(self.mesh.polygons))
        self.mesh.polygons.foreach_get("center", centers.asMemoryView())
        return centers

    def getPolygonAreas(self):
        areas = FloatList(length = len(self.mesh.polygons))
        self.mesh.polygons.foreach_get("area", areas.asMemoryView())
        return areas

    def getPolygonMaterialIndices(self):
        indices = UIntegerList(length = len(self.mesh.polygons))
        self.mesh.polygons.foreach_get("material_index", indices.asMemoryView())
        return indices

    def getLoopEdges(self):
        loopEdges = UIntegerList(length = len(self.mesh.loops))
        self.mesh.loops.foreach_get("edge_index", loopEdges.asMemoryView())
        return loopEdges

    def getUVMap(self, name):
        uvLayer = self.mesh.uv_layers[name]
        uvMap = Vector2DList(length = len(self.mesh.loops))
        uvLayer.data.foreach_get("uv", uvMap.asMemoryView())
        return uvMap

    def getVertexColorLayer(self, name):
        vertexColorLayer = self.mesh.vertex_colors[name]
        vertexColors = ColorList(length = len(vertexColorLayer.data))
        vertexColorLayer.data.foreach_get("color", vertexColors.asNumpyArray())
        return vertexColors

    def getEdgeCreases(self):
        edgeCreases = DoubleList(length = len(self.mesh.edges))
        self.mesh.edges.foreach_get("crease", edgeCreases.asNumpyArray())
        return edgeCreases

    def getBevelEdgeWeights(self):
        bevelEdgeWeights = DoubleList(length = len(self.mesh.edges))
        self.mesh.edges.foreach_get("bevel_weight", bevelEdgeWeights.asNumpyArray())
        return bevelEdgeWeights

    def getBevelVertexWeights(self):
        bevelVertexWeights = DoubleList(length = len(self.mesh.vertices))
        self.mesh.vertices.foreach_get("bevel_weight", bevelVertexWeights.asNumpyArray())
        return bevelVertexWeights

    def getCustomAttribute(self, name):
        attribute = self.mesh.attributes.get(name)

        if attribute.domain == "POINT":
            amount = len(self.mesh.vertices)
        elif attribute.domain == "EDGE":
            amount = len(self.mesh.edges)
        elif attribute.domain == "FACE":
            amount = len(self.mesh.polygons)
        else:
            amount = len(self.mesh.loops)

        if attribute.data_type == "FLOAT":
            data = DoubleList(length = amount)
        elif attribute.data_type == "INT":
            data = LongList(length = amount)
        elif attribute.data_type == "FLOAT2":
            data = Vector2DList(length = amount)
        elif attribute.data_type == "FLOAT_VECTOR":
            data = Vector3DList(length = amount)
        elif attribute.data_type in ("FLOAT_COLOR", "BYTE_COLOR"):
            data = ColorList(length = amount)
        else:
            data = BooleanList(length = amount)

        if attribute.data_type in ("FLOAT", "INT", "BOOLEAN"):
            attribute.data.foreach_get("value", data.asNumpyArray())
        elif attribute.data_type in ("FLOAT2", "FLOAT_VECTOR"):
            attribute.data.foreach_get("vector", data.asNumpyArray())
        else:
            attribute.data.foreach_get("color", data.asNumpyArray())

        return data

    @property
    def mesh(self):
        return self.id_data

class ObjectProperties(bpy.types.PropertyGroup):
    bl_idname = "an_ObjectProperties"

    def getMesh(self, applyModifiers = False):
        object = self.id_data

        if not applyModifiers and object.type == "MESH":
            return object.data
        else:
            try:
                if applyModifiers: return getEvaluatedID(object).to_mesh()
                else: return object.to_mesh()
            except: return None

    def getCurve(self, applyModifiers = False):
        bObject = self.id_data

        if bObject is None: return None
        if bObject.type not in ("CURVE", "FONT"): return None

        if not applyModifiers and bObject.type == "CURVE":
            return bObject.data

        return bObject.to_curve(getActiveDepsgraph(), apply_modifiers = applyModifiers)

class IDProperties(bpy.types.PropertyGroup):
    bl_idname = "an_IDProperties"

    removeOnZeroUsers: BoolProperty(default = False,
        description = "Data block should be removed when it has no users")

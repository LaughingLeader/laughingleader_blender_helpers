from __future__ import division
import bpy
import bmesh
import math

from bpy.types import Operator, PropertyGroup
from bpy.props import CollectionProperty, PointerProperty, BoolProperty

bl_info = {
    "name": "UV Helpers",
    "author": "LaughingLeader",
    "blender": (2, 7, 9),
    "api": -1,
    "location": "Edit Mode > UV / Image Editor > UVs",
    "description": ("Helpers for cleaning up UVs, checking for errors, and more"),
    "warning": "",
    "wiki_url": (""),
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "UV"
}

class UVError:
    def __init__(self, vert1, vert2, loop1, loop2):
        self.vert1 = vert1
        self.vert2 = vert2
        self.loop1 = loop1
        self.loop2 = loop2

class UVErrorv2:
    def __init__(self, face, vert1, vert2, vert3, uvloop1, uvloop2, uvloop3):
        self.face = face
        self.vert1 = vert1
        self.vert2 = vert2
        self.vert3 = vert3
        self.loop1 = uvloop1
        self.loop2 = uvloop2
        self.loop3 = uvloop3

class UVUnwrappedChecker(Operator):
    """Check for UVs that will cause tangent/binormal issues.\nThese are UV faces that fail to form a mathematical triangle"""
    bl_idname = "uvhelpers.unwrappedchecker"
    bl_label = "Check UV Triangles"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')

    def uv_error(self, vert1, vert2, uv1, uv2):
        return vert1 != vert2 and uv1 == uv2

    def uv_checkforerrors(self, context, node):
        if node.type == "MESH":
            if (node.data is not None):

                #os.system("cls")

                mesh = node.data

                bm = bmesh.from_edit_mesh(mesh)
                bm.select_mode = {"VERT"}
                #bm.select_mode = {"VERT"}
                bm.select_flush(False)
                uv_layer = bm.loops.layers.uv.active

                uv_errors = []

                for face in bm.faces:
                    for loop in face.loops:
                        vert = loop.vert
                        vert.select_set(False)
                        #loop.select(False)

                        #print("  Vert: (%f,%f,%f)" % vert.co[:])
                        uv_loop = loop[uv_layer]
                        uv = uv_loop.uv
                        #print("    UV: %f, %f" % uv[:])
                        ux = uv[0]
                        uy = uv[1]

                        for checkloop in face.loops:
                            if checkloop == loop:
                                break

                            vert2 = checkloop.vert
                            checkuv_loop = checkloop[uv_layer]
                            checkuv = checkuv_loop.uv

                            if self.uv_error(vert, vert2, uv, checkuv):
                                uv_error_entry = UVError(vert, vert2, uv_loop, checkuv_loop)
                                uv_errors.append(uv_error_entry)

                total_errors = len(uv_errors)

                if total_errors > 0:
                    can_select = True
                    for uv_error in uv_errors:
                        print("[ERROR]: UV problem detected!")
                        print("  Vert1: (%f,%f,%f)" % uv_error.vert1.co[:])
                        print("  Vert2: (%f,%f,%f)" % uv_error.vert2.co[:])
                        print("  UV1: (%f,%f)" % uv_error.loop1.uv[:])
                        print("  UV2: (%f,%f)" % uv_error.loop2.uv[:])

                        if can_select:
                            uv_error.vert1.select_set(True)
                            uv_error.vert2.select_set(True)
                            uv_error.loop1.select = True
                            uv_error.loop2.select = True
                            if self.select_all == False:
                                can_select = False

                    self.report({"WARNING"}, "[LL-UV-Helper] {} total problems found on UV map. Check selected vertices for wrapping issues.".format(total_errors))
                else:
                    self.report({"INFO"}, "[LL-UV-Helper] No UV problems found.")
                    
                bm.select_flush(True)
                bmesh.update_edit_mesh(mesh)

    def uv_error_v2(self, uv1, uv2, uv3):
        s1 = float(uv2[0] - uv1[0]) # x
        s2 = float(uv3[0] - uv1[0])
        t1 = float(uv2[1] - uv1[1]) # y
        t2 = float(uv3[1] - uv1[1])
        
        check1 = float(s1 * t2 - s2 * t1)

        return abs(check1) < 0.0000001

    def uv_checkforerrors_v2(self, context, node):
        if node.type == "MESH":
            if (node.data is not None):

                select_mode = context.user_preferences.addons["laughingleader_blender_helpers"].preferences.uvhelpers_errorchecker_select_mode

                if select_mode == "FACE":
                    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
                elif select_mode == "EDGE":
                    bpy.context.tool_settings.mesh_select_mode = (False, True, False)
                else:
                    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                #py.context.tool_settings.mesh_select_mode = (False, False, True)

                mesh = node.data

                bm = bmesh.from_edit_mesh(mesh)
                bm.select_flush(False)
                uv_layer = bm.loops.layers.uv.active

                uv_errors = []

                for face in bm.faces:
                    if face in uv_errors:
                        continue

                    face.select = False
                    
                    if(len(face.loops) == 3):
                        vloop1 = face.loops[0]
                        vloop2 = face.loops[1]
                        vloop3 = face.loops[2]

                        vert1 = vloop1.vert
                        vert2 = vloop2.vert
                        vert3 = vloop3.vert

                        vert1.select_set(False)
                        vert2.select_set(False)
                        vert3.select_set(False)
                        
                        uvloop1 = vloop1[uv_layer]
                        uvloop2 = vloop2[uv_layer]
                        uvloop3 = vloop3[uv_layer]

                        uv1 = uvloop1.uv
                        uv2 = uvloop2.uv
                        uv3 = uvloop3.uv

                        #uv1 = vert1.co.xy
                        #uv2 = vert2.co.xy
                        #uv3 = vert3.co.xy

                        if self.uv_error_v2(uv1, uv2, uv3):
                            uv_error_entry = UVErrorv2(face, vert1, vert2, vert3, uvloop1, uvloop2, uvloop3)
                            uv_errors.append(uv_error_entry)
                        
                total_errors = len(uv_errors)
                if total_errors > 0:
                    can_select = True
                    select_all = context.user_preferences.addons["laughingleader_blender_helpers"].preferences.uvhelpers_errorchecker_select_all is True
                    for uv_error in uv_errors:
                        print("[ERROR]: UV problem detected!")
                        print("  Vert1: (%f,%f,%f)" % uv_error.vert1.co[:])
                        print("  Vert2: (%f,%f,%f)" % uv_error.vert2.co[:])
                        print("  Vert3: (%f,%f,%f)" % uv_error.vert3.co[:])
                        print("  UV1: (%f,%f)" % uv_error.loop1.uv[:])
                        print("  UV2: (%f,%f)" % uv_error.loop2.uv[:])
                        print("  UV3: (%f,%f)" % uv_error.loop3.uv[:])

                        if can_select:
                            uv_error.vert1.select_set(True)
                            uv_error.vert2.select_set(True)
                            uv_error.vert3.select_set(True)
                            uv_error.loop1.select = True
                            uv_error.loop2.select = True
                            uv_error.loop3.select = True
                            if select_all == False:
                                can_select = False
                                break

                    self.report({"WARNING"}, "[LL-UV-Helper] {} total problems found on UV map. Check selected vertices for wrapping issues.".format(total_errors))
                else:
                    self.report({"INFO"}, "[LL-UV-Helper] No UV problems found.")
                
                #total_errors.clear()

                bm.select_flush(True)
                bmesh.update_edit_mesh(mesh)

    def execute(self, context):        # execute() is called when running the operator.

        # The original script
        scene = context.scene

        if bpy.context.scene.objects.active is None:
            self.report({"WARNING"}, "[LL-UV-Helper] Select a mesh before checking UVs!")
            return {'FINISHED'}

        node = bpy.context.scene.objects.active

        bpy.ops.object.mode_set(mode="EDIT")
        self.uv_checkforerrors_v2(context, node)

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

def selectedUVs(mesh, bmesh=None, uvlayer=None, sync=False):
    '''Get the vertices visible and selected in the UV view.'''
    uvs = {}
    if bmesh is None:
        uvlayer = uvlayer or mesh.uv_layers.active
        for f, uv in zip(mesh.loops, uvlayer.data):
            #print("UVLayer: {} | f: {} uv: {}".format(uvlayer.name, f, uv))
            if mesh.vertices[f.vertex_index].select and (sync or uv.select):
                uvs[f.vertex_index] = uv.uv
                #uvs.append(uv.uv)
    else:
        uv_layer = uvlayer or bmesh.loops.layers.uv.active

        for face in bmesh.faces:
            for loop in face.loops:
                luv = loop[uv_layer]
                if (luv.select or sync) and loop.vert.select:
                    print(loop.index)
                    uvs[loop.index] = luv
                    #uvs.append(luv)
    return uvs

last_selected_uvs = []
last_selection = None

class UVSelectCursorHelper(Operator):
    """Move the cursor to the last selected UV"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "uvhelpers.3dcursortolastuv"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Cursor to Last UV"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')

    def execute(self, context):        # execute() is called when running the operator.

        print("Looking for selected UVs...")

        node = bpy.context.scene.objects.active

        if node.type == "MESH":
            if (node.data is not None):

                mesh = node.data
                bm = bmesh.from_edit_mesh(mesh)

                selected = selectedUVs(mesh=mesh, bmesh=bm, sync=context.scene.tool_settings.use_uv_select_sync)
                total = len(selected)
                if len(selected) > 0:

                    global last_selected_uvs
                    global last_selection

                    selection = 0
                    for key in selected.keys():
                        selection += key
                    
                    if selection == last_selection:
                        last_total = len(last_selected_uvs)
                        if last_total == total:
                            last = last_selected_uvs[-1]
                            last_selected_uvs.clear()
                            last_selected_uvs.append(last)
                    else:
                        last_selected_uvs.clear()

                    for i, uvdata in selected.items():
                        if not i in last_selected_uvs:
                            bpy.ops.uv.cursor_set(location=uvdata.uv)
                            last_selected_uvs.append(i)
                            break

                    last_selection = selection
                
                # uv_layer = bm.loops.layers.uv.active
                # for f in bm.faces:
                #     for l in f.loops:
                #         luv = l[uv_layer]
                #         if luv.select:
                #             bpy.ops.uv.cursor_set(location=luv.uv)
                #             print(luv.uv)
                #             break

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

class UVSharpSelector(Operator):
    """Selects all seams"""
    bl_idname = "uvhelpers.sharpselecter"
    bl_label = "Select Sharps Edges"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')

    def execute(self, context):
        scene = context.scene

        if context.object is None:
            self.report({"WARNING"}, "[LL-UV-Helper] No object selected!")
            return {'FINISHED'}

        node = bpy.context.scene.objects.active

        bpy.ops.object.mode_set(mode="EDIT")
        if node.type == "MESH":
            if (node.data is not None):
                mesh = node.data

                bm = bmesh.from_edit_mesh(mesh)
                for edge in bm.edges:
                    if edge.smooth == False:
                        if bm.select_mode == "VERT":
                            for v in edge.verts:
                                v.select = True
                        else:
                            edge.select = True
                bmesh.update_edit_mesh(mesh)

        return {'FINISHED'}

class UVSeamSelector(Operator):
    """Selects all seams"""
    bl_idname = "uvhelpers.seamselecter"
    bl_label = "Select Seams"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')

    def execute(self, context):
        scene = context.scene

        if bpy.context.scene.objects.active is None:
            self.report({"WARNING"}, "[LL-UV-Helper] Select a mesh before selecting seams!")
            return {'FINISHED'}

        node = bpy.context.scene.objects.active

        bpy.ops.object.mode_set(mode="EDIT")
        if node.type == "MESH":
            if (node.data is not None):
                mesh = node.data

                bm = bmesh.from_edit_mesh(mesh)
                for edge in bm.edges:
                    #edge.select_set(False)
                    if edge.seam:
                        if bm.select_mode == "VERT":
                            for v in edge.verts:
                                v.select = True
                        else:
                            edge.select = True

                #bm.select_flush(False)
                bmesh.update_edit_mesh(mesh)

        return {'FINISHED'}

class UVImageReloader(Operator):
    """Reloads all images from their source"""
    bl_idname = "uvhelpers.reloadimages"
    bl_label = "Reload All Images"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import os

        updated_image = False
        for image in context.blend_data.images:
            if image.filepath != "":
                path_check = bpy.path.abspath(image.filepath, library=image.library)
                if os.path.exists(path_check):
                    image.reload()
                    print("[LL-UV-Helper] Reloaded image: \"{}\"".format(path_check))
                    updated_image = True
                else:
                    print("[LL-UV-Helper] Skipped reloading image (file does not exist): \"{}\"".format(path_check))

        if updated_image:
            for area in bpy.context.screen.areas:
                if area.type in ['IMAGE_EDITOR']:
                    area.tag_redraw()

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

class UVHelperPanel(bpy.types.Panel):
    bl_label = "Helpers"
    bl_idname = "IMAGE_MT_ll_uvhelpers"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = 'Helpers'

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    def draw(self, context):
        layout = self.layout
        layout.label("UV Errors")
        box = layout.box()
        #layout.prop(self, "select_all")
        box.prop(context.user_preferences.addons["laughingleader_blender_helpers"].preferences, "uvhelpers_errorchecker_select_all")
        box.prop(context.user_preferences.addons["laughingleader_blender_helpers"].preferences, "uvhelpers_errorchecker_select_mode")
        uv_helper_op = box.operator(UVUnwrappedChecker.bl_idname)

        layout.label("Misc")
        layout.operator(UVSelectCursorHelper.bl_idname)
        layout.operator(UVSeamSelector.bl_idname)
        layout.operator(UVSharpSelector.bl_idname)
        layout.operator(UVImageReloader.bl_idname)

def draw_snap_addon(self, context):
    self.layout.operator(UVSelectCursorHelper.bl_idname, icon="PLUGIN")

def register():
    #bpy.utils.register_module(__name__)
    bpy.types.IMAGE_MT_uvs_snap.append(draw_snap_addon)
    return

def unregister():
    #bpy.utils.unregister_module(__name__)
    bpy.types.IMAGE_MT_uvs_snap.remove(draw_snap_addon)
    return

if __name__ == "__main__":
    register()
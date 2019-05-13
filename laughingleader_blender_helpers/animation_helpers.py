import bpy
from bpy.types import Operator, PropertyGroup, UIList, Panel
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty

from bl_ui import space_dopesheet

from . import leader

def action_set():
    return (bpy.context.object is not None and
        bpy.context.object.animation_data is not None
        and bpy.context.object.animation_data.action is not None)

class LLAnimHelpers_DeleteOperator(Operator):
    """Delete this action"""
    bl_label = "Delete Action"
    bl_idname = "llhelpers.action_delete"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return action_set()

    def execute(self, context):
        ob = bpy.context.object
        action_name = (ob.animation_data.action.name
            if ob.animation_data is not None and
            ob.animation_data.action is not None
            else "")

        msg = ""
        msg_type = "INFO"

        if action_name != "":
            try:
                index = bpy.data.actions.find(action_name)
                if index > -1:
                    action = bpy.data.actions[index]
                    bpy.data.actions.remove(action)
                    msg = "[LeaderHelpers:AnimHelpers:Delete] Deleted action '{}'. Undo to reverse.".format(action_name)
                    context.scene.update()
            except Exception as e:
                msg = "[LeaderHelpers:AnimHelpers:Delete] Error deleting action:\n\t{}".format(e)
                msg_type = "ERROR"
        else:
            msg = "[LeaderHelpers:AnimHelpers:Delete] Failed to find the current action. Select an armature with an action."
            msg_type = "WARNING"

        if msg != "":
            self.report({msg_type}, msg)
        return {'FINISHED'}

    def invoke(self, context, _event):
        return self.execute(context)

#Override the default draw function, so we can add the delete button right after the action template
def DOPESHEET_HT_header_draw(self, context):
    layout = self.layout

    st = context.space_data
    toolsettings = context.tool_settings

    row = layout.row(align=True)
    row.template_header()

    bpy.types.DOPESHEET_MT_editor_menus.draw_collapsible(context, layout)

    layout.prop(st, "mode", text="")

    if st.mode in {'ACTION', 'SHAPEKEY'}:
        row = layout.row(align=True)
        row.operator("action.layer_prev", text="", icon='TRIA_DOWN')
        row.operator("action.layer_next", text="", icon='TRIA_UP')

        layout.template_ID(st, "action", new="action.new", unlink="action.unlink")
        preferences = leader.get_preferences(context)
        if preferences is not None and st.mode == "ACTION" and preferences.general_enable_deletion and action_set():
                layout.operator(LLAnimHelpers_DeleteOperator.bl_idname, icon="CANCEL", text="", emboss=False)

        row = layout.row(align=True)
        row.operator("action.push_down", text="Push Down", icon='NLA_PUSHDOWN')
        row.operator("action.stash", text="Stash", icon='FREEZE')

    layout.prop(st.dopesheet, "show_summary", text="Summary")

    if st.mode == 'DOPESHEET':
        space_dopesheet.dopesheet_filter(layout, context)
    elif st.mode == 'ACTION':
        # 'genericFiltersOnly' limits the options to only the relevant 'generic' subset of
        # filters which will work here and are useful (especially for character animation)
        space_dopesheet.dopesheet_filter(layout, context, genericFiltersOnly=True)
    elif st.mode == 'GPENCIL':
        row = layout.row(align=True)
        row.prop(st.dopesheet, "show_gpencil_3d_only", text="Active Only")

        if st.dopesheet.show_gpencil_3d_only:
            row = layout.row(align=True)
            row.prop(st.dopesheet, "show_only_selected", text="")
            row.prop(st.dopesheet, "show_hidden", text="")

        row = layout.row(align=True)
        row.prop(st.dopesheet, "use_filter_text", text="")
        if st.dopesheet.use_filter_text:
            row.prop(st.dopesheet, "filter_text", text="")
            row.prop(st.dopesheet, "use_multi_word_filter", text="")

    row = layout.row(align=True)
    row.prop(toolsettings, "use_proportional_action",
                text="", icon_only=True)
    if toolsettings.use_proportional_action:
        row.prop(toolsettings, "proportional_edit_falloff",
                    text="", icon_only=True)

    # Grease Pencil mode doesn't need snapping, as it's frame-aligned only
    if st.mode != 'GPENCIL':
        layout.prop(st, "auto_snap", text="")

    row = layout.row(align=True)
    row.operator("action.copy", text="", icon='COPYDOWN')
    row.operator("action.paste", text="", icon='PASTEDOWN')
    if st.mode not in ('GPENCIL', 'MASK'):
        row.operator("action.paste", text="", icon='PASTEFLIPDOWN').flipped = True

DOPESHEET_HT_header_draw_original = None

def register():
    global DOPESHEET_HT_header_draw_original
    DOPESHEET_HT_header_draw_original = bpy.types.DOPESHEET_HT_header.draw
    bpy.types.DOPESHEET_HT_header.draw = DOPESHEET_HT_header_draw

def unregister():
    try:
        global DOPESHEET_HT_header_draw_original
        if DOPESHEET_HT_header_draw_original is not None:
            bpy.types.DOPESHEET_HT_header.draw = DOPESHEET_HT_header_draw_original
            DOPESHEET_HT_header_draw_original = None
    except: pass

if __name__ == "__main__":
    register()
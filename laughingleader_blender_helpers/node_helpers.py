import bpy

from bpy.types import NodeCustomGroup

""" 
class TextureNodeInputLoop(NodeCustomGroup):
    bl_name="TextureInputNode"
    bl_label="Texture Input Node"

	def operators(self, context):
		nt=context.space_data.edit_tree
		list=[("ADD","Add","Addition"),("SUBTRACT", "Subtract", "Subtraction"), ("MULTIPLY", "Multiply", "Multiplication"), ("DIVIDE", "Divide", "Division"), ("MAXIMUM","Max","Maximum"),("MINIMUM","Min","Minimum") ]
		return list """
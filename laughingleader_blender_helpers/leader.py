import bpy

def get_preferences(context):
	if "laughingleader_blender_helpers" in context.user_preferences.addons:
		return context.user_preferences.addons["laughingleader_blender_helpers"].preferences
	return None

def is_visible(scene, obj, layers=True):
	if layers:
		if obj.hide == True:
			return False
		for i in range(20):
			if scene.layers[i]:
				if obj.layers[i]:
					return True
		return False
	else:
		return obj.hide == False
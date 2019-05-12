

def get_preferences(context):
	if "laughingleader_blender_helpers" in context.user_preferences.addons:
		return context.user_preferences.addons["laughingleader_blender_helpers"].preferences
	return None
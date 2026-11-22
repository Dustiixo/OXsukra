extends SceneTree

## Optional actual Godot viewport capture. Run with a working display/rendering
## backend. Dummy headless rendering may yield a black image.

func _initialize() -> void:
	call_deferred("capture")


func capture() -> void:
	var scene: Control = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	var tabs: TabContainer = scene.get("view_stack")
	tabs.current_tab = 3
	var lab = scene.get("fracture_lab")
	lab.select_address(9, 7)
	for i in range(16):
		await process_frame
	if DisplayServer.get_name() == "headless":
		print("CAPTURE UNAVAILABLE / headless display uses a dummy rendering backend.")
		scene.queue_free()
		await process_frame
		quit(2)
		return
	var texture := root.get_texture()
	if texture == null:
		print("CAPTURE UNAVAILABLE / renderer exposes no viewport texture (headless dummy backend).")
		scene.queue_free()
		await process_frame
		quit(2)
		return
	var image := texture.get_image()
	if image == null:
		print("CAPTURE UNAVAILABLE / graphics backend returned no image.")
		scene.queue_free()
		await process_frame
		quit(2)
		return
	var out := ProjectSettings.globalize_path("user://DEEPBREW_FRACTURE_G0_2.png")
	var result := image.save_png(out)
	print("CAPTURE / ", out, " / ", image.get_size(), " / code=", result)
	scene.queue_free()
	await process_frame
	quit(0 if result == OK else 1)

class_name DeepbrewVesselView
extends SubViewportContainer

## Native Godot mesh visualization of the 200 actual COLOCRYPT PLY faces.
## It reads signed-off fixture bytes through FractureProbe, not fabricated
## procedural scenery. Drag to orbit; scroll to zoom.

var viewport: SubViewport
var body: Node3D
var camera: Camera3D
var instance: MeshInstance3D
var triangles_loaded := 0
var vertex_count_loaded := 0
var orbiting := false
var auto_turn := true


func _ready() -> void:
	stretch = true
	custom_minimum_size = Vector2(390, 310)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	mouse_filter = Control.MOUSE_FILTER_STOP
	viewport = SubViewport.new()
	viewport.size = Vector2i(700, 480)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.msaa_3d = Viewport.MSAA_4X
	add_child(viewport)
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("0b0c0f")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("9ea9bf")
	environment.ambient_light_energy = 0.65
	world.environment = environment
	viewport.add_child(world)
	body = Node3D.new()
	viewport.add_child(body)
	instance = MeshInstance3D.new()
	body.add_child(instance)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-38, -25, 12)
	key.light_energy = 1.4
	viewport.add_child(key)
	camera = Camera3D.new()
	viewport.add_child(camera)
	camera.position = Vector3(6.2, 4.7, 6.9)
	camera.fov = 38
	camera.look_at(Vector3(0, 2.48, 0))
	camera.current = true


func load_ply(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {"ok": false, "reason": "Vessel mesh does not exist."}
	var lines := FileAccess.get_file_as_string(path).split("\n", false)
	if lines.is_empty() or lines[0] != "ply":
		return {"ok": false, "reason": "Not an ASCII PLY mesh."}
	var vertex_total := 0
	var face_total := 0
	var cursor := 1
	var ended := false
	while cursor < lines.size():
		var line := lines[cursor].strip_edges()
		cursor += 1
		if line.begins_with("element vertex "):
			vertex_total = int(line.get_slice(" ", 2))
		elif line.begins_with("element face "):
			face_total = int(line.get_slice(" ", 2))
		elif line == "end_header":
			ended = true
			break
	if not ended or vertex_total != 102 or face_total != 200:
		return {"ok": false, "reason": "Unexpected closed-Vessel topology."}
	if cursor + vertex_total + face_total > lines.size():
		return {"ok": false, "reason": "Incomplete PLY body."}
	var vertices: Array[Vector3] = []
	var colours: Array[Color] = []
	for i in range(vertex_total):
		var parts := lines[cursor + i].strip_edges().split(" ", false)
		if parts.size() != 6:
			return {"ok": false, "reason": "Invalid PLY vertex."}
		vertices.append(Vector3(float(parts[0]), float(parts[2]), float(parts[1])))
		colours.append(Color(float(parts[3]) / 255.0, float(parts[4]) / 255.0, float(parts[5]) / 255.0))
	cursor += vertex_total
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(face_total):
		var fields := lines[cursor + i].strip_edges().split(" ", false)
		if fields.size() != 4 or fields[0] != "3":
			return {"ok": false, "reason": "Expected triangulated PLY faces."}
		for j in range(1, 4):
			var index := int(fields[j])
			if index < 0 or index >= vertex_total:
				return {"ok": false, "reason": "PLY face exceeds vertex bounds."}
			surface.set_color(colours[index])
			surface.add_vertex(vertices[index])
	surface.generate_normals()
	var mesh := surface.commit()
	var material := StandardMaterial3D.new()
	material.vertex_color_use_as_albedo = true
	material.metallic = 0.24
	material.roughness = 0.48
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	mesh.surface_set_material(0, material)
	instance.mesh = mesh
	triangles_loaded = face_total
	vertex_count_loaded = vertex_total
	return {"ok": true, "triangles": triangles_loaded, "vertices": vertex_count_loaded}


func _process(delta: float) -> void:
	if auto_turn and body != null:
		body.rotate_y(delta * 0.16)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			orbiting = event.pressed
			auto_turn = false
		if event.pressed and camera != null:
			if event.button_index == MOUSE_BUTTON_WHEEL_UP:
				camera.position *= 0.91
			elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				camera.position *= 1.09
	elif event is InputEventMouseMotion and orbiting and body != null:
		body.rotate_y(event.relative.x * 0.008)
		body.rotate_x(event.relative.y * 0.004)

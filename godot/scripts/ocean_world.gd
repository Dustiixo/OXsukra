extends Node3D
## ECHOFOLD Ocean G0.1: native read-only spatial projection of real IXO G0.4 records.
## Intentional controller standby, no global hooks, no external program dispatch.

const SNAPSHOT := "res://data/ocean_snapshot.json"
const RESUME := "user://ocean_navigation_state.json"
const MOVE_SPEED := 6.0
const ACCEL := 13.0
const LOOK_SPEED := 1.65
const DEADZONE := 0.22

var snapshot: Dictionary = {}
var objects: Dictionary = {}
var spheres: Dictionary = {}
var visual_links: Array[MeshInstance3D] = []
var rig: Node3D
var camera: Camera3D
var ui_status: Label
var ui_target: Label
var ui_detail: PanelContainer
var ui_detail_text: Label
var controller_armed := false
var sonar_active := false
var mouse_looking := false
var current_detail := ""
var current_focus := ""
var selected_id := ""
var velocity := Vector3.ZERO
var breadcrumbs: Array[Dictionary] = []
var last_target := ""


func _ready() -> void:
    # Godot 4.6 may deliver gamepad events to unfocused windows; every handler
    # explicitly checks focus, and controller motion is separately armed.
    _create_ocean()
    _create_player()
    _create_hud()
    if not _load_snapshot():
        ui_status.text = "NO VERIFIED SNAPSHOT — export one from a G0.4 data directory."
        return
    _create_records()
    _create_links()
    _restore_breadcrumbs()
    _update_hud()
    print("OCEAN_READY projects=%d entries=%d state=%s" % [
        snapshot.get("projects", []).size(), snapshot.get("entries", []).size(),
        str(snapshot.get("state_id", "unknown"))])


func _create_ocean() -> void:
    var env_node := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.009, 0.029, 0.057)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.18, 0.42, 0.52)
    env.ambient_light_energy = 0.55
    env.fog_enabled = true
    env.fog_light_color = Color(0.025, 0.13, 0.20)
    env.fog_density = 0.012
    env_node.environment = env
    add_child(env_node)

    var light := DirectionalLight3D.new()
    light.light_color = Color(0.37, 0.74, 0.95)
    light.light_energy = 1.4
    light.rotation_degrees = Vector3(-35, -25, 0)
    add_child(light)

    _create_motes()
    _create_current_ring(11.0, Vector3.UP)
    _create_current_ring(20.0, Vector3.RIGHT)
    _create_current_ring(28.0, Vector3.BACK)

    # Fixed registration markers act as a compass without imposing gravity.
    for i in range(3):
        var axis := Vector3.RIGHT if i == 0 else (Vector3.UP if i == 1 else Vector3.BACK)
        var col := Color(0.18, 0.57, 0.72, 0.25)
        _create_segment(Vector3.ZERO, axis * 32.0, col, false)
        _create_segment(Vector3.ZERO, -axis * 32.0, col, false)


func _create_motes() -> void:
    # An inexpensive, fixed bioluminescent volume. No camera-linked fake scenery.
    var points := MultiMesh.new()
    points.transform_format = MultiMesh.TRANSFORM_3D
    var mesh := SphereMesh.new()
    mesh.radius = 0.045
    mesh.height = 0.09
    points.mesh = mesh
    points.instance_count = 180
    var rng := RandomNumberGenerator.new()
    rng.seed = 181105
    for index in range(points.instance_count):
        var at := Vector3(rng.randf_range(-42, 42), rng.randf_range(-42, 42),
                          rng.randf_range(-42, 42))
        points.set_instance_transform(index, Transform3D(Basis(), at))
    var glow := StandardMaterial3D.new()
    glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    glow.albedo_color = Color(0.18, 0.53, 0.67)
    glow.emission_enabled = true
    glow.emission = Color(0.18, 0.53, 0.67)
    var node := MultiMeshInstance3D.new()
    node.multimesh = points
    node.material_override = glow
    add_child(node)


func _create_current_ring(radius: float, axis: Vector3) -> void:
    var basis := Basis(Quaternion(Vector3.UP, axis)) if axis != Vector3.UP else Basis()
    var segments := 64
    var mesh := ImmediateMesh.new()
    mesh.surface_begin(Mesh.PRIMITIVE_LINES)
    for index in range(segments):
        var a := TAU * float(index) / float(segments)
        var b := TAU * float(index + 1) / float(segments)
        mesh.surface_add_vertex(basis * Vector3(cos(a) * radius, 0, sin(a) * radius))
        mesh.surface_add_vertex(basis * Vector3(cos(b) * radius, 0, sin(b) * radius))
    mesh.surface_end()
    var line := MeshInstance3D.new()
    line.mesh = mesh
    var mat := StandardMaterial3D.new()
    mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    mat.albedo_color = Color(0.12, 0.40, 0.59)
    line.material_override = mat
    add_child(line)


func _create_player() -> void:
    rig = Node3D.new()
    rig.name = "Swimmer"
    rig.position = Vector3(0, 0, 28)
    add_child(rig)
    camera = Camera3D.new()
    camera.name = "Eyes"
    camera.current = true
    camera.near = 0.04
    camera.far = 140.0
    camera.fov = 80
    rig.add_child(camera)


func _create_hud() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    var frame := Control.new()
    frame.set_anchors_preset(Control.PRESET_FULL_RECT)
    frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
    layer.add_child(frame)

    ui_status = Label.new()
    ui_status.set_anchors_preset(Control.PRESET_TOP_WIDE)
    ui_status.offset_left = 18
    ui_status.offset_top = 12
    ui_status.offset_right = -20
    ui_status.offset_bottom = 80
    ui_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    ui_status.add_theme_font_size_override("font_size", 18)
    ui_status.add_theme_color_override("font_color", Color(0.81, 0.94, 0.98))
    frame.add_child(ui_status)

    var reticle := Label.new()
    reticle.text = "+"
    reticle.set_anchors_preset(Control.PRESET_CENTER)
    reticle.position = Vector2(-8, -16)
    reticle.add_theme_font_size_override("font_size", 28)
    reticle.add_theme_color_override("font_color", Color(0.82, 0.94, 0.96))
    frame.add_child(reticle)

    ui_target = Label.new()
    ui_target.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
    ui_target.offset_left = 18
    ui_target.offset_right = -20
    ui_target.offset_top = -74
    ui_target.offset_bottom = -10
    ui_target.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    ui_target.add_theme_color_override("font_color", Color(0.77, 0.93, 0.93))
    frame.add_child(ui_target)

    ui_detail = PanelContainer.new()
    ui_detail.set_anchors_preset(Control.PRESET_CENTER)
    ui_detail.position = Vector2(-330, -195)
    ui_detail.custom_minimum_size = Vector2(660, 390)
    ui_detail.visible = false
    ui_detail.mouse_filter = Control.MOUSE_FILTER_IGNORE
    frame.add_child(ui_detail)
    var pad := MarginContainer.new()
    pad.add_theme_constant_override("margin_left", 20)
    pad.add_theme_constant_override("margin_right", 20)
    pad.add_theme_constant_override("margin_top", 20)
    pad.add_theme_constant_override("margin_bottom", 20)
    ui_detail.add_child(pad)
    ui_detail_text = Label.new()
    ui_detail_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    ui_detail_text.custom_minimum_size = Vector2(610, 320)
    ui_detail_text.add_theme_font_size_override("font_size", 16)
    pad.add_child(ui_detail_text)


func _snapshot_path() -> String:
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--ocean-snapshot="):
            return argument.trim_prefix("--ocean-snapshot=")
    return SNAPSHOT


func _load_snapshot() -> bool:
    var path := _snapshot_path()
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        push_error("Ocean snapshot unavailable: " + path)
        return false
    var parsed = JSON.parse_string(file.get_as_text())
    if typeof(parsed) != TYPE_DICTIONARY:
        push_error("Ocean snapshot must be a JSON object")
        return false
    if parsed.get("schema", "") != "echofold.ocean.snapshot.g0.1" or \
            parsed.get("source_integrity", "") != "VERIFIED_SELECTED_ENTRIES":
        push_error("Ocean snapshot is not a verified G0.1 projection")
        return false
    if typeof(parsed.get("projects")) != TYPE_ARRAY or typeof(parsed.get("entries")) != TYPE_ARRAY:
        push_error("Ocean snapshot lacks project and entry arrays")
        return false
    snapshot = parsed
    return true


func _create_records() -> void:
    for project in snapshot["projects"]:
        _create_record(project, true)
    for entry in snapshot["entries"]:
        _create_record(entry, false)


func _create_record(record: Dictionary, project: bool) -> void:
    if not record.has("id") or not record.has("position"):
        return
    var identifier := str(record["id"])
    var point: Array = record["position"]
    if point.size() != 3:
        return
    var world_pos := Vector3(float(point[0]), float(point[1]), float(point[2]))
    var anchor := Node3D.new()
    anchor.name = ("Project_" if project else "Entry_") + identifier.substr(0, 8)
    anchor.position = world_pos
    add_child(anchor)
    objects[identifier] = record
    spheres[identifier] = anchor

    var sphere := MeshInstance3D.new()
    var shape := SphereMesh.new()
    shape.radius = 0.95 if project else 0.46
    shape.height = shape.radius * 2.0
    sphere.mesh = shape
    var mat := StandardMaterial3D.new()
    mat.albedo_color = Color(0.13, 0.76, 0.46) if project else \
        (Color(0.95, 0.24, 0.26) if str(record.get("state", "")) == "blocked" else Color(0.27, 0.68, 0.96))
    mat.metallic = 0.23
    mat.roughness = 0.30
    mat.emission_enabled = true
    mat.emission = mat.albedo_color
    mat.emission_energy_multiplier = 0.45
    sphere.material_override = mat
    anchor.add_child(sphere)

    var label := Label3D.new()
    label.text = str(record.get("name", record.get("title", "IXO object"))).substr(0, 32)
    label.position = Vector3(0, 1.35 if project else 0.85, 0)
    label.font_size = 36
    label.pixel_size = 0.012
    label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
    label.modulate = Color(0.87, 0.95, 1.0)
    anchor.add_child(label)


func _create_segment(start: Vector3, finish: Vector3, color: Color, approved: bool) -> void:
    var mesh := ImmediateMesh.new()
    mesh.surface_begin(Mesh.PRIMITIVE_LINES)
    mesh.surface_add_vertex(start)
    mesh.surface_add_vertex(finish)
    mesh.surface_end()
    var node := MeshInstance3D.new()
    node.mesh = mesh
    var mat := StandardMaterial3D.new()
    mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    mat.albedo_color = color
    mat.no_depth_test = false
    node.material_override = mat
    add_child(node)
    if approved:
        visual_links.append(node)
        node.visible = false


func _create_links() -> void:
    for entry in snapshot["entries"]:
        var project_id := str(entry.get("project_id", ""))
        var entry_id := str(entry.get("id", ""))
        if spheres.has(project_id) and spheres.has(entry_id):
            _create_segment(spheres[project_id].position, spheres[entry_id].position,
                            Color(0.11, 0.60, 0.49, 0.60), false)
    for link in snapshot.get("approved_links", []):
        var left := str(link.get("from", ""))
        var right := str(link.get("to", ""))
        if spheres.has(left) and spheres.has(right):
            _create_segment(spheres[left].position, spheres[right].position,
                            Color(0.33, 0.77, 0.98), true)


func _deadzone(value: float) -> float:
    return 0.0 if absf(value) < DEADZONE else value


func _process(delta: float) -> void:
    if snapshot.is_empty() or not get_window().has_focus():
        velocity = velocity.move_toward(Vector3.ZERO, ACCEL * delta)
        return
    if current_detail != "":
        velocity = Vector3.ZERO
        return
    var local_move := Vector3(
        float(Input.is_key_pressed(KEY_D)) - float(Input.is_key_pressed(KEY_A)),
        float(Input.is_key_pressed(KEY_E)) - float(Input.is_key_pressed(KEY_Q)),
        float(Input.is_key_pressed(KEY_S)) - float(Input.is_key_pressed(KEY_W)))
    var look := Vector2(
        float(Input.is_key_pressed(KEY_RIGHT)) - float(Input.is_key_pressed(KEY_LEFT)),
        float(Input.is_key_pressed(KEY_DOWN)) - float(Input.is_key_pressed(KEY_UP)))
    var roll := float(Input.is_key_pressed(KEY_C)) - float(Input.is_key_pressed(KEY_Z))

    var pads := Input.get_connected_joypads()
    if controller_armed and not pads.is_empty():
        var pad: int = pads[0]
        local_move.x += _deadzone(Input.get_joy_axis(pad, JOY_AXIS_LEFT_X))
        local_move.z += _deadzone(Input.get_joy_axis(pad, JOY_AXIS_LEFT_Y))
        local_move.y += maxf(0.0, Input.get_joy_axis(pad, JOY_AXIS_TRIGGER_RIGHT))
        local_move.y -= maxf(0.0, Input.get_joy_axis(pad, JOY_AXIS_TRIGGER_LEFT))
        look.x += _deadzone(Input.get_joy_axis(pad, JOY_AXIS_RIGHT_X))
        look.y += _deadzone(Input.get_joy_axis(pad, JOY_AXIS_RIGHT_Y))
        roll += float(Input.is_joy_button_pressed(pad, JOY_BUTTON_RIGHT_SHOULDER))
        roll -= float(Input.is_joy_button_pressed(pad, JOY_BUTTON_LEFT_SHOULDER))

    local_move = local_move.limit_length(1.0)
    velocity = velocity.move_toward(local_move * MOVE_SPEED, ACCEL * delta)
    rig.position += rig.basis * velocity * delta
    rig.rotate_object_local(Vector3.UP, -look.x * LOOK_SPEED * delta)
    rig.rotate_object_local(Vector3.RIGHT, -look.y * LOOK_SPEED * delta)
    rig.rotate_object_local(Vector3.FORWARD, roll * LOOK_SPEED * delta)
    selected_id = _aimed_object()
    if selected_id != last_target:
        last_target = selected_id
        _update_hud()


func _aimed_object() -> String:
    var forward := -camera.global_transform.basis.z.normalized()
    var origin := camera.global_position
    var chosen := ""
    var nearest := 80.0
    for identifier in spheres:
        var delta: Vector3 = spheres[identifier].global_position - origin
        var distance := delta.length()
        if distance < 0.01 or distance > 80.0:
            continue
        # Larger nodes can be selected slightly farther off-centre.
        var aim := forward.dot(delta.normalized())
        var tolerance := 0.94 if objects[identifier].get("kind", "") == "project" else 0.975
        if aim >= tolerance and distance < nearest:
            chosen = identifier
            nearest = distance
    return chosen


func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT:
        mouse_looking = event.pressed and get_window().has_focus()
    elif event is InputEventMouseMotion and mouse_looking and get_window().has_focus() and current_detail == "":
        rig.rotate_object_local(Vector3.UP, -event.relative.x * 0.0024)
        rig.rotate_object_local(Vector3.RIGHT, -event.relative.y * 0.0024)
    elif event is InputEventJoypadButton and event.pressed and get_window().has_focus():
        var pads := Input.get_connected_joypads()
        if pads.is_empty() or event.device != pads[0]:
            return
        if event.button_index == JOY_BUTTON_START:
            controller_armed = not controller_armed
            _update_hud()
            return
        if not controller_armed:
            return
        match event.button_index:
            JOY_BUTTON_A: _enter_object()
            JOY_BUTTON_B: _go_back()
            JOY_BUTTON_X: _toggle_sonar()
            JOY_BUTTON_Y: _overview()
    elif event is InputEventKey and event.pressed and not event.echo and get_window().has_focus():
        match event.keycode:
            KEY_F, KEY_ENTER: _enter_object()
            KEY_BACKSPACE, KEY_ESCAPE: _go_back()
            KEY_X: _toggle_sonar()
            KEY_G: _overview()
            KEY_TAB:
                controller_armed = not controller_armed
                _update_hud()


func _save_pose() -> Dictionary:
    var t := rig.transform
    return {"origin": _vec(t.origin), "x": _vec(t.basis.x),
            "y": _vec(t.basis.y), "z": _vec(t.basis.z)}


func _vec(value: Vector3) -> Array:
    return [value.x, value.y, value.z]


func _to_vec(value: Array) -> Vector3:
    if value.size() != 3:
        return Vector3.ZERO
    return Vector3(float(value[0]), float(value[1]), float(value[2]))


func _restore_pose(pose: Dictionary) -> void:
    if not pose.has("origin") or not pose.has("x") or not pose.has("y") or not pose.has("z"):
        return
    var basis := Basis(_to_vec(pose["x"]), _to_vec(pose["y"]), _to_vec(pose["z"]))
    if basis.determinant() < 0.5:
        return
    rig.transform = Transform3D(basis.orthonormalized(), _to_vec(pose["origin"]))


func _push_breadcrumb() -> void:
    breadcrumbs.append({"pose": _save_pose(), "focus": current_focus, "detail": current_detail})
    if breadcrumbs.size() > 50:
        breadcrumbs.pop_front()


func _enter_object() -> void:
    if selected_id == "" or not objects.has(selected_id):
        return
    _push_breadcrumb()
    var record: Dictionary = objects[selected_id]
    current_focus = selected_id
    if record.get("kind", "") == "project":
        var anchor: Node3D = spheres[selected_id]
        rig.position = anchor.position + rig.basis.z * 5.5
        current_detail = ""
        ui_detail.visible = false
    else:
        current_detail = selected_id
        var excerpt := str(record.get("original_excerpt", "[Private original text omitted; re-export with explicit consent]"))
        var source := str(record.get("source_sha256", ""))
        ui_detail_text.text = "%s\n\nState: %s  •  Kind: %s\n\nNext: %s\n\nOriginal:\n%s\n\nSource SHA-256: %s\n\nB / Backspace: swim back" % [
            str(record.get("title", "IXO record")), str(record.get("state", "")),
            str(record.get("entry_kind", "")), str(record.get("next_step", "")),
            excerpt, source]
        ui_detail.visible = true
    _save_breadcrumbs()
    _update_hud()


func _go_back() -> void:
    if breadcrumbs.is_empty():
        current_detail = ""
        ui_detail.visible = false
        _update_hud()
        return
    var previous: Dictionary = breadcrumbs.pop_back()
    _restore_pose(previous.get("pose", {}))
    current_focus = str(previous.get("focus", ""))
    current_detail = str(previous.get("detail", ""))
    ui_detail.visible = false
    _save_breadcrumbs()
    _update_hud()


func _overview() -> void:
    _push_breadcrumb()
    rig.position = Vector3(0, 28, 0)
    rig.look_at(Vector3.ZERO, Vector3(0, 0, -1))
    current_detail = ""
    ui_detail.visible = false
    _save_breadcrumbs()
    _update_hud()


func _toggle_sonar() -> void:
    sonar_active = not sonar_active
    for line in visual_links:
        line.visible = sonar_active
    _update_hud()


func _update_hud() -> void:
    if ui_status == null:
        return
    var control := "SWIMMING" if controller_armed else "STANDBY"
    ui_status.text = "ECHOFOLD OCEAN  ·  READ ONLY  ·  Controller: %s  ·  Return path: %d\nLeft stick/WASD swim · Right stick/arrows look · Triggers/QE depth · Bumpers/ZC roll · Start/Tab arm" % [control, breadcrumbs.size()]
    var target := "No object at reticle"
    if objects.has(selected_id):
        target = str(objects[selected_id].get("name", objects[selected_id].get("title", "IXO node")))
    ui_target.text = "%s  ·  A/F enter  ·  B/Backspace return  ·  X sonar (%s)  ·  Y/G overview\nReal IXO data via verified read-only projection · No external program launched" % [target, "ON" if sonar_active else "OFF"]


func _save_breadcrumbs() -> void:
    if snapshot.is_empty():
        return
    var file := FileAccess.open(RESUME, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify({"state_id": snapshot["state_id"], "pose": _save_pose(),
            "focus": current_focus, "stack": breadcrumbs}))


func _restore_breadcrumbs() -> void:
    if not FileAccess.file_exists(RESUME):
        return
    var file := FileAccess.open(RESUME, FileAccess.READ)
    if file == null:
        return
    var restored = JSON.parse_string(file.get_as_text())
    if typeof(restored) != TYPE_DICTIONARY or restored.get("state_id", "") != snapshot.get("state_id", ""):
        return
    if typeof(restored.get("stack")) == TYPE_ARRAY:
        breadcrumbs.assign(restored["stack"])
    current_focus = str(restored.get("focus", ""))
    _restore_pose(restored.get("pose", {}))


func _notification(what: int) -> void:
    if what == NOTIFICATION_WM_CLOSE_REQUEST and not snapshot.is_empty():
        _save_breadcrumbs()

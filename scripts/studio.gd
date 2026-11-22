extends Control

const BrewEngineScript = preload("res://scripts/mod_engine.gd")
const FractureLabScript = preload("res://scripts/fracture_lab.gd")

## The editor stays focused: one source, one typed graph, one evidence rail.
## The graph is an inspectable projection in G0.1; effect editing uses the inspector.

const BG := Color("0b0c0e")
const PANEL := Color("121416")
const PANEL_ALT := Color("191b1e")
const INK := Color("e0e3e3")
const MUTED := Color("9da6a7")
const BLUE := Color("618bff")
const GREEN := Color("8fcb64")
const RED := Color("e66365")

var engine := BrewEngineScript.new()
var status_label: Label
var source_editor: CodeEdit
var preview_editor: TextEdit
var event_editor: TextEdit
var graph: GraphEdit
var effect_node: GraphNode
var effect_node_label: Label
var effect_select: OptionButton
var duration_spin: SpinBox
var source_path_label: Label
var before_door: ColorRect
var after_door: ColorRect
var before_state: Label
var after_state: Label
var open_dialog: FileDialog
var export_dialog: FileDialog
var view_stack: TabContainer
var fracture_lab


func _ready() -> void:
	_build_interface()
	_load_sample()
	call_deferred("_reset_graph_view")


func _build_interface() -> void:
	var backdrop := ColorRect.new()
	backdrop.color = BG
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(backdrop)

	var root := VBoxContainer.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.offset_left = 16
	root.offset_top = 12
	root.offset_right = -16
	root.offset_bottom = -12
	root.add_theme_constant_override("separation", 6)
	add_child(root)

	var header := HBoxContainer.new()
	header.custom_minimum_size.y = 56
	root.add_child(header)
	var brand := _label("DEEPBREW / EDIT", 27, INK)
	brand.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(brand)
	header.add_child(_label("NATIVE  •  MODDING EDITOR  /  G0.3.1", 13, MUTED))
	header.add_child(_button("[ IMPORT ]", func() -> void: open_dialog.popup_centered_ratio(0.65), BLUE))
	header.add_child(_button("[ SAMPLE ]", _load_sample, INK))

	var separator := HSeparator.new()
	root.add_child(separator)
	var body := HBoxContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 7)
	root.add_child(body)

	var left := _column_panel(230)
	body.add_child(left)
	left.add_child(_label("PROJECT / SOURCE", 16, INK))
	left.add_child(_label("ROOT\n  ├─ TARGET\n  │    └─ behavior.brew.json\n  ├─ PREVIEW\n  ├─ SANDBOX\n  ├─ FRACTURE / COLOCRYPT\n  └─ EVIDENCE", 15, MUTED))
	left.add_child(HSeparator.new())
	left.add_child(_label("TARGET IDENTITY", 14, INK))
	source_path_label = _label("No source loaded", 13, MUTED)
	source_path_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	left.add_child(source_path_label)
	left.add_child(_label("ADAPTER", 14, INK))
	left.add_child(_label("BEHAVIOR / JSON v1", 13, GREEN))
	left.add_child(_label("Unknown formats remain inspect-only.", 12, MUTED))
	left.add_spacer(false)
	left.add_child(_label("EXPLICIT SAFETY", 14, INK))
	left.add_child(_label("Imported originals are read-only.\nWork is isolated under app data.\nNo external executables are run.", 12, MUTED))

	var center := VBoxContainer.new()
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.add_theme_constant_override("separation", 7)
	body.add_child(center)

	var graph_panel := _column_panel(0)
	graph_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.add_child(graph_panel)
	graph_panel.add_child(_label("BEHAVIOR / FUNCTIONAL STATE PROJECTION", 14, INK))
	graph = GraphEdit.new()
	graph.name = "BehaviorGraph"
	graph.custom_minimum_size = Vector2(600, 265)
	graph.size_flags_vertical = Control.SIZE_EXPAND_FILL
	graph.show_grid = true
	graph.snapping_enabled = false
	graph.right_disconnects = false
	graph.show_menu = false
	graph.show_zoom_buttons = false
	graph.show_minimap_button = false
	graph.minimap_enabled = false
	graph.show_arrange_button = false
	graph.panning_scheme = GraphEdit.SCROLL_ZOOMS
	graph_panel.add_child(graph)
	_make_graph()

	view_stack = TabContainer.new()
	view_stack.custom_minimum_size = Vector2(600, 335)
	view_stack.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.add_child(view_stack)
	source_editor = CodeEdit.new()
	source_editor.name = "SOURCE"
	source_editor.editable = false
	source_editor.gutters_draw_line_numbers = true
	source_editor.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	view_stack.add_child(source_editor)
	preview_editor = TextEdit.new()
	preview_editor.name = "DIFF / PREVIEW"
	preview_editor.editable = false
	preview_editor.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	view_stack.add_child(preview_editor)
	var sandbox := VBoxContainer.new()
	sandbox.name = "VISUAL SANDBOX"
	view_stack.add_child(sandbox)
	sandbox.add_child(_label("LOCAL MODEL SIMULATION  /  NOT AN EXTERNAL GAME RUNTIME", 13, MUTED))
	var comparison := HBoxContainer.new()
	comparison.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sandbox.add_child(comparison)
	var before := _sandbox_card("BEFORE", comparison)
	var after := _sandbox_card("AFTER", comparison)
	before_door = before[0]
	before_state = before[1]
	after_door = after[0]
	after_state = after[1]
	fracture_lab = FractureLabScript.new()
	view_stack.add_child(fracture_lab)
	fracture_lab.proposal_requested.connect(_fracture_proposal)

	var right := _column_panel(282)
	body.add_child(right)
	right.add_child(_label("INSPECTOR / MODIFY", 16, INK))
	right.add_child(HSeparator.new())
	right.add_child(_label("TRIGGER", 12, MUTED))
	right.add_child(_label("ON ENTER  [SUPPORTED]", 14, INK))
	right.add_child(_label("EFFECT", 12, MUTED))
	effect_select = OptionButton.new()
	for name in BrewEngineScript.ALLOWED_EFFECTS:
		effect_select.add_item(name)
	right.add_child(effect_select)
	right.add_child(_label("DURATION / ms", 12, MUTED))
	duration_spin = SpinBox.new()
	duration_spin.min_value = 0
	duration_spin.max_value = 60000
	duration_spin.step = 100
	duration_spin.value = 1000
	right.add_child(duration_spin)
	right.add_child(HSeparator.new())
	right.add_child(_button("[ 1  PREVIEW CHANGE ]", _preview, BLUE))
	right.add_child(_button("[ 2  APPLY TO COPY ]", _apply, INK))
	right.add_child(_button("[ 3  TEST IN SANDBOX ]", _test, GREEN))
	right.add_child(_button("[ EXPORT MOD ]", func() -> void: export_dialog.popup_centered_ratio(0.65), INK))
	right.add_child(_button("[ ROLLBACK ]", _rollback, RED))
	right.add_child(HSeparator.new())
	right.add_child(_label("EVIDENCE / RECEIPTS", 14, INK))
	event_editor = TextEdit.new()
	event_editor.editable = false
	event_editor.size_flags_vertical = Control.SIZE_EXPAND_FILL
	event_editor.custom_minimum_size.y = 170
	right.add_child(event_editor)

	var footer := HBoxContainer.new()
	footer.custom_minimum_size.y = 33
	root.add_child(footer)
	status_label = _label("STATUS / READY", 13, MUTED)
	status_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(status_label)
	footer.add_child(_label("[ FOCUS ]    [ INSPECT ]    [ TEST ]    [ RETURN ]", 12, MUTED))

	open_dialog = FileDialog.new()
	open_dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	open_dialog.access = FileDialog.ACCESS_FILESYSTEM
	open_dialog.add_filter("*.brew.json", "DEEPBREW behavior target")
	open_dialog.file_selected.connect(_import_file)
	add_child(open_dialog)
	export_dialog = FileDialog.new()
	export_dialog.file_mode = FileDialog.FILE_MODE_SAVE_FILE
	export_dialog.access = FileDialog.ACCESS_FILESYSTEM
	export_dialog.add_filter("*.brew.json", "DEEPBREW exported mod")
	export_dialog.file_selected.connect(_export)
	add_child(export_dialog)


func _column_panel(min_width: int) -> VBoxContainer:
	var box := VBoxContainer.new()
	box.custom_minimum_size.x = min_width
	box.add_theme_constant_override("separation", 11)
	var style := StyleBoxFlat.new()
	style.bg_color = PANEL
	style.border_color = Color("444a4e")
	style.set_border_width_all(1)
	style.set_content_margin_all(12)
	box.add_theme_stylebox_override("panel", style)
	# Containers don't draw a panel style, so use a non-clicking backdrop.
	var back := ColorRect.new()
	back.color = PANEL
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	back.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	box.add_child(back)
	box.move_child(back, 0)
	return box


func _label(value: String, size: int, color: Color) -> Label:
	var lbl := Label.new()
	lbl.text = value
	lbl.add_theme_font_size_override("font_size", size)
	lbl.add_theme_color_override("font_color", color)
	return lbl


func _button(value: String, action: Callable, ink_color: Color) -> Button:
	var btn := Button.new()
	btn.text = value
	btn.custom_minimum_size.y = 40
	btn.add_theme_color_override("font_color", ink_color)
	btn.pressed.connect(action)
	return btn


func _make_graph() -> void:
	var trigger := _graph_node("trigger", "TRIGGER", "ON ENTER\nsource: sandbox", Vector2(45, 70), false, true)
	effect_node = _graph_node("effect", "TRANSFORMATION", "EFFECT: CLOSED\nduration: 1000 ms", Vector2(320, 70), true, true)
	effect_node.selected = true
	effect_node_label = effect_node.get_child(0) as Label
	_graph_node("evidence", "WITNESS", "EVENT → RECEIPT\nno runtime claims", Vector2(625, 70), true, false)
	graph.connect_node(trigger.name, 0, effect_node.name, 0)
	graph.connect_node(effect_node.name, 0, "evidence", 0)
	graph.scroll_offset = Vector2.ZERO


func _reset_graph_view() -> void:
	# GraphEdit may initialize its scroll range before the layout is measured.
	await get_tree().process_frame
	graph.scroll_offset = Vector2(0, 20)


func _graph_node(id: String, title: String, contents: String, offset: Vector2, left: bool, right: bool) -> GraphNode:
	var node := GraphNode.new()
	node.name = id
	node.title = title
	node.position_offset = offset
	node.custom_minimum_size = Vector2(205, 94)
	var child := _label(contents, 16, INK)
	node.add_child(child)
	node.set_slot(0, left, 0, GREEN, right, 0, GREEN)
	graph.add_child(node)
	return node


func _sandbox_card(title: String, parent: HBoxContainer) -> Array:
	var column := VBoxContainer.new()
	column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(column)
	column.add_child(_label(title, 14, INK))
	var panel := PanelContainer.new()
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(panel)
	var scene := Control.new()
	scene.custom_minimum_size = Vector2(200, 140)
	panel.add_child(scene)
	var ground := ColorRect.new()
	ground.color = Color("313638")
	ground.anchor_top = 0.78
	ground.anchor_right = 1.0
	ground.anchor_bottom = 0.85
	scene.add_child(ground)
	var zone := ColorRect.new()
	zone.color = Color("243e2f")
	zone.anchor_left = 0.17
	zone.anchor_top = 0.73
	zone.anchor_right = 0.84
	zone.anchor_bottom = 0.79
	scene.add_child(zone)
	var door := ColorRect.new()
	door.color = Color("60696c")
	door.anchor_left = 0.37
	door.anchor_top = 0.20
	door.anchor_right = 0.63
	door.anchor_bottom = 0.76
	scene.add_child(door)
	var state := _label("STATE: CLOSED", 13, MUTED)
	column.add_child(state)
	return [door, state]


func _load_sample() -> void:
	_import_file("res://examples/door_trigger.brew.json")


func _import_file(path: String) -> void:
	var result := engine.import_target(path)
	if not result.ok:
		_set_status("UNSUPPORTED / " + str(result.get("reason", "Unknown error")), RED)
		return
	source_path_label.text = str(engine.baseline.get("name", "Unnamed")) + "\n" + path.get_file() + "\nSHA256: " + engine.source_hash.substr(0, 18) + "…"
	_select_effect(engine.working["behavior"]["effect"])
	duration_spin.value = engine.working["behavior"]["duration_ms"]
	source_editor.text = engine.source_bytes.get_string_from_utf8()
	preview_editor.text = "No staged changes. Choose an effect, then PREVIEW."
	_sync_graph()
	_show_states("closed", "closed")
	_show_events()
	_set_status("IMPORTED / original preserved / " + path.get_file(), GREEN)


func _select_effect(effect: String) -> void:
	for i in effect_select.item_count:
		if effect_select.get_item_text(i) == effect:
			effect_select.select(i)


func _sync_graph() -> void:
	var behavior: Dictionary = engine.working.get("behavior", {})
	if behavior.is_empty():
		return
	effect_node_label.text = "EFFECT: " + str(behavior["effect"]).to_upper() + "\nduration: " + str(behavior["duration_ms"]) + " ms"


func _preview() -> void:
	var result := engine.preview_change(effect_select.get_item_text(effect_select.selected), int(duration_spin.value))
	if not result.ok:
		_set_status("PREVIEW REFUSED / " + str(result.reason), RED)
		return
	var changed: Array = result.changes
	preview_editor.text = "STAGED / NOT APPLIED\n" + "\n".join(changed) + "\n\n── BEFORE ──\n" + result.before + "\n\n── AFTER ──\n" + result.after
	view_stack.current_tab = 1
	_show_events()
	_set_status("PREVIEW / %d changed fields / no source writes" % changed.size(), BLUE)


func _fracture_proposal(proposal: Dictionary) -> void:
	# The Lab is an observer. Nothing is ever auto-applied or exported.
	# Cross-check the UI's proposal against the pinned read-only fixture.
	if not fracture_lab.probe.verified or proposal != fracture_lab.probe.propose_mutation():
		_set_status("FRACTURE REFUSED / proposal or Print mismatched", RED)
		return
	if engine.source_path == "":
		_set_status("FRACTURE REFUSED / import a supported mod target first", RED)
		return
	_select_effect(str(proposal["effect"]))
	duration_spin.value = int(proposal["duration_ms"])
	_preview()
	if engine.last_preview.get("is_change", false):
		engine._record("fracture_proposal", {
			"print_sha256": proposal["print_sha256"],
			"splice_sha256": proposal["source_splice_sha256"],
			"address": proposal["source_address"],
			"rule": proposal["rule"],
			"effect": proposal["effect"],
			"duration_ms": proposal["duration_ms"],
			"stage_only": true,
		})
		_show_events()
		_set_status("FRACTURE STAGED / diff visible / APPLY requires your click", BLUE)


func _apply() -> void:
	var result := engine.apply_preview()
	if not result.ok:
		_set_status("APPLY REFUSED / " + str(result.reason), RED)
		return
	source_editor.text = JSON.stringify(engine.working, "  ")
	_sync_graph()
	_show_events()
	_set_status("WORKING COPY UPDATED / " + str(result.working_hash).substr(0, 16), GREEN)


func _test() -> void:
	var result := engine.test_simulation()
	if not result.ok:
		_set_status("TEST REFUSED / " + str(result.get("reason", "Check failure")), RED)
		return
	_show_states("closed", str(result.observed))
	view_stack.current_tab = 2
	_show_events()
	_set_status("MODEL SIMULATION PASS / external runtime NOT tested", GREEN)


func _rollback() -> void:
	var result := engine.rollback_to_import()
	if not result.ok:
		_set_status("ROLLBACK FAILED / " + str(result.get("reason", "Verification failed")), RED)
		return
	source_editor.text = engine.source_bytes.get_string_from_utf8()
	preview_editor.text = "Restored imported baseline in working copy."
	_select_effect(engine.working["behavior"]["effect"])
	duration_spin.value = engine.working["behavior"]["duration_ms"]
	_sync_graph()
	_show_states("closed", "closed")
	_show_events()
	_set_status("ROLLBACK VERIFIED / working hash = original hash", GREEN)


func _export(path: String) -> void:
	var result := engine.export_mod(path)
	if result.ok:
		_set_status("MOD EXPORTED / " + str(result.hash).substr(0, 16), GREEN)
	else:
		_set_status("EXPORT REFUSED / " + str(result.reason), RED)
	_show_events()


func _show_states(before: String, after: String) -> void:
	before_state.text = "STATE: " + before.to_upper()
	after_state.text = "STATE: " + after.to_upper()
	before_door.color = Color("60696c")
	match after:
		"open":
			after_door.color = BLUE
		"highlight":
			after_door.color = GREEN
		_:
			after_door.color = Color("60696c")


func _show_events() -> void:
	var output := "LOCAL EVIDENCE LOG\n"
	for item in engine.evidence():
		output += str(item["time"]) + "  " + str(item["action"]).to_upper() + "\n"
	event_editor.text = output


func _set_status(value: String, color: Color) -> void:
	status_label.text = "STATUS / " + value
	status_label.add_theme_color_override("font_color", color)

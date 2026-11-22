class_name DeepbrewFractureLab
extends VBoxContainer

signal proposal_requested(proposal: Dictionary)

const ProbeScript = preload("res://scripts/fracture_probe.gd")
const MapScript = preload("res://scripts/fracture_map.gd")
const VesselScript = preload("res://scripts/vessel_view.gd")
const INK := Color("e0e3e3")
const MUTED := Color("9da6a7")
const GREEN := Color("a3ff12")
const BLUE := Color("618bff")
const CRIMSON := Color("ff1744")

var probe := ProbeScript.new()
var map
var vessel_view
var metrics_label: Label
var result_label: Label
var colour_legend: Label
var print_label: Label
var gate_buttons: Array[Button] = []
var slot_buttons: Array[Button] = []
var player: AudioStreamPlayer
var load_result: Dictionary = {}


func _ready() -> void:
	name = "FRACTURE / COLOCRYPT"
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_theme_constant_override("separation", 6)
	load_result = probe.load_bundle()
	_build()
	if load_result.ok:
		var mesh_result: Dictionary = vessel_view.load_ply(probe.base_path.path_join("COLOCRYPT_VESSEL.ply"))
		if not mesh_result.ok:
			load_result = mesh_result
			probe.verified = false
		else:
			map.set_data(probe.print_data["gates"])
	if load_result.ok:
		_update_selection()
	else:
		result_label.text = "FRACTURE DISABLED / " + str(load_result.get("reason", "Unknown fixture failure"))
		result_label.add_theme_color_override("font_color", CRIMSON)
		print_label.text = "UNVERIFIED BUNDLE / NO PROPOSALS"


func _build() -> void:
	var title := _label("FRACTURE LAB   /   COLOCRYPT × DEEPBREW", 18, INK)
	add_child(title)
	print_label = _label("PINNED PRINT  /  VERIFYING…", 11, MUTED)
	add_child(print_label)

	var bar := HBoxContainer.new()
	bar.add_theme_constant_override("separation", 3)
	add_child(bar)
	for i in range(10):
		var button := Button.new()
		button.text = "%02d" % i
		button.custom_minimum_size = Vector2(36, 26)
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.pressed.connect(_select_gate.bind(i))
		gate_buttons.append(button)
		bar.add_child(button)

	var content := HBoxContainer.new()
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 9)
	add_child(content)
	var left := VBoxContainer.new()
	left.custom_minimum_size.x = 410
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation", 8)
	content.add_child(left)
	left.add_child(_label("PARENT TIMELINE →     /     CHILD LANGUAGE ↑", 12, MUTED))
	map = MapScript.new()
	map.cell_selected.connect(select_address)
	map.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(map)

	var slots := HBoxContainer.new()
	slots.add_theme_constant_override("separation", 2)
	left.add_child(slots)
	for i in range(10):
		var button := Button.new()
		button.text = "%d" % i
		button.custom_minimum_size = Vector2(29, 26)
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.pressed.connect(_select_slot.bind(i))
		slot_buttons.append(button)
		slots.add_child(button)
	colour_legend = _label("AUTO-ASSIGNED CHROMATIC ADDRESS", 12, MUTED)
	left.add_child(colour_legend)
	metrics_label = _label("Awaiting verified sound-bearing measurements…", 12, INK)
	metrics_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	left.add_child(metrics_label)
	var controls := HBoxContainer.new()
	controls.add_theme_constant_override("separation", 5)
	left.add_child(controls)
	controls.add_child(_button("[ CONTACT ]", _contact, BLUE))
	controls.add_child(_button("[ AUDITION ]", _audition, INK))
	controls.add_child(_button("[ PROPOSE → DIFF ]", _propose, GREEN))
	result_label = _label("READ-ONLY UNTIL EXPLICIT STAGE / APPLY", 12, MUTED)
	result_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	left.add_child(result_label)

	var right := VBoxContainer.new()
	right.custom_minimum_size.x = 360
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(right)
	right.add_child(_label("PRINT → 3D VESSEL   /   VERIFIED PLY", 13, INK))
	vessel_view = VesselScript.new()
	right.add_child(vessel_view)
	right.add_child(_label("DRAG TO ORBIT   •   SCROLL TO ZOOM   •   102V / 200F", 11, MUTED))
	right.add_child(_label("OBSERVE → PROBE → PREVIEW → APPLY COPY → TEST → ROLLBACK", 11, GREEN))
	player = AudioStreamPlayer.new()
	add_child(player)


func _label(value: String, font_size: int, tone: Color) -> Label:
	var label := Label.new()
	label.text = value
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", tone)
	return label


func _button(value: String, on_press: Callable, tone: Color) -> Button:
	var button := Button.new()
	button.text = value
	button.custom_minimum_size.y = 32
	button.add_theme_color_override("font_color", tone)
	button.pressed.connect(on_press)
	return button


func _select_gate(index: int) -> void:
	select_address(index, probe.selected_slot)


func _select_slot(index: int) -> void:
	select_address(probe.selected_gate, index)


func select_address(gate: int, slot: int) -> Dictionary:
	var result := probe.select(gate, slot)
	if result.ok:
		_update_selection()
	return result


func _update_selection() -> void:
	var splice := probe.current_splice()
	var gate := probe.current_gate()
	map.set_active(probe.selected_gate, probe.selected_slot)
	print_label.text = "SOURCE-LOCKED PRINT / " + str(probe.PRINT_FINGERPRINT).substr(0, 19) + "…   |   10 × 10  /  1,240 BEARINGS"
	for i in range(10):
		var colour := Color.html(str(probe.print_data["gates"][i]["splices"][0]["status_colour"]))
		gate_buttons[i].add_theme_color_override("font_color", colour)
		gate_buttons[i].button_pressed = i == probe.selected_gate
	for i in range(10):
		var rgb: Array = gate["splices"][i]["display_rgb"]
		var colour := Color(float(rgb[0])/255.0, float(rgb[1])/255.0, float(rgb[2])/255.0)
		slot_buttons[i].add_theme_color_override("font_color", colour)
		slot_buttons[i].button_pressed = i == probe.selected_slot
	colour_legend.text = "%s   •   %s   •   %s" % [str(splice["language"]), str(splice["status_kind"]).to_upper(), str(splice["phase"])]
	metrics_label.text = "%s / %d sound bearings   |   %.1f Hz   |   %.1f PCM\nBAR WINDOW %s → %s (projection only)   |   OP %s" % [
		str(splice["address"]), int(splice["bearing_count"]), float(splice["mean_frequency_hz"]),
		float(splice["mean_strength_pcm"]), str(splice["bar_range_projection"][0]),
		str(splice["bar_range_projection"][1]), str(splice["language_opcode"])]
	result_label.text = "OBSERVING / no target file modified. CONTACT inspects; PROPOSE stages an experimental diff."
	result_label.add_theme_color_override("font_color", MUTED)


func _contact() -> Dictionary:
	if not probe.verified:
		return {"ok": false, "reason": "Fixture not verified."}
	var splice := probe.current_splice()
	var result := {"ok": true, "address": splice["address"], "bearing_digest": splice["bearing_digest"],
		"opcode": splice["language_opcode"], "result": splice["opcode_result"], "splice_sha256": splice["splice_sha256"]}
	result_label.text = "CONTACT / %s = %s\nSPLICE %s…" % [str(result.opcode), str(result.result), str(result.splice_sha256).substr(0, 18)]
	result_label.add_theme_color_override("font_color", BLUE)
	return result


func _audition() -> Dictionary:
	if not probe.verified:
		return {"ok": false, "reason": "Fixture not verified."}
	var bytes := FileAccess.get_file_as_bytes(probe.sound_file())
	if bytes.is_empty():
		return {"ok": false, "reason": "Verified MP3 could not be read."}
	var music := AudioStreamMP3.new()
	music.data = bytes
	player.stop()
	player.stream = music
	player.play()
	result_label.text = "AUDITION / source MP3 %02d. Audio playback is not a new decoding proof." % (probe.selected_gate + 1)
	return {"ok": true, "mp3_bytes": bytes.size()}


func _propose() -> Dictionary:
	var suggestion := probe.propose_mutation()
	if not suggestion.ok:
		return suggestion
	proposal_requested.emit(suggestion)
	return suggestion

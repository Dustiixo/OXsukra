extends SceneTree

const ProbeScript = preload("res://scripts/fracture_probe.gd")

var passed := 0
var failed := 0


func _initialize() -> void:
	call_deferred("run_checks")


func run_checks() -> void:
	var scene: Control = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	await process_frame
	var lab = scene.get("fracture_lab")
	var engine = scene.get("engine")
	var source_path := "res://examples/door_trigger.brew.json"
	var baseline_sha := FileAccess.get_sha256(source_path)
	check(lab != null, "fracture lab inhabits the existing native Studio tab")
	check(lab.load_result.get("ok", false), "pinned Print + PLY + proof + ten MP3s verified")
	check(lab.probe.verified, "lab refuses to operate without verified fixture")
	check(lab.probe.print_data["gates"].size() == 10, "ten primary gates retained")
	check(lab.probe.print_data["splices"] == 100, "hundred nested splices retained")
	check(lab.probe.print_data["measured_points_covered"] == 1240, "1240 source bearings covered")
	check(lab.probe.print_data["color_wheel_address_space"] == 360, "full hue namespace registry retained")
	check(lab.vessel_view.triangles_loaded == 200, "actual 200-face native Godot mesh is loaded")
	check(lab.vessel_view.vertex_count_loaded == 102, "actual 102 PLY vertices were parsed")
	check(lab.vessel_view.instance.mesh != null, "native 3D mesh exists, not a bitmap mockup")
	check(lab.map.gates.size() == 10, "hundred-cell fracture map is populated from Print")
	check(lab.gate_buttons.size() == 10 and lab.slot_buttons.size() == 10, "native selector exposes ten-by-ten addressing")
	var heal = lab.probe.print_data["gates"][8]["splices"][0]
	var scar = lab.probe.print_data["gates"][9]["splices"][0]
	check(heal["status_kind"] == "heal" and heal["status_colour"] == "#A3FF12", "green Heal status is source-assigned")
	check(scar["status_kind"] == "scar" and scar["status_colour"] == "#A020F0", "purple Scar status is source-assigned")
	check(lab.select_address(9, 7).get("ok", false), "native UI selects a nested colour address")
	check(lab.probe.current_splice()["address"] == "G09/H324/S07", "gate / hue / sublanguage address stays exact")
	check(lab.map.active_gate == 9 and lab.map.active_slot == 7, "fracture map follows selection")
	var map_click := InputEventMouseButton.new()
	map_click.button_index = MOUSE_BUTTON_LEFT
	map_click.pressed = true
	map_click.position = lab.map._cell_rect(3, 4).get_center()
	lab.map._gui_input(map_click)
	check(lab.probe.selected_gate == 3 and lab.probe.selected_slot == 4, "clicking an actual map cell selects the measured splice")
	lab.select_address(9, 7)
	var rotation_before: float = lab.vessel_view.body.rotation.y
	var orbit_press := InputEventMouseButton.new()
	orbit_press.button_index = MOUSE_BUTTON_LEFT
	orbit_press.pressed = true
	lab.vessel_view._gui_input(orbit_press)
	var orbit_move := InputEventMouseMotion.new()
	orbit_move.relative = Vector2(60, 0)
	lab.vessel_view._gui_input(orbit_move)
	check(lab.vessel_view.body.rotation.y != rotation_before, "3D Vessel responds to an actual mouse orbit event")
	var zoom_before: float = lab.vessel_view.camera.position.length()
	var wheel := InputEventMouseButton.new()
	wheel.button_index = MOUSE_BUTTON_WHEEL_UP
	wheel.pressed = true
	lab.vessel_view._gui_input(wheel)
	check(lab.vessel_view.camera.position.length() < zoom_before, "3D Vessel responds to wheel zoom")
	check(not lab.select_address(10, 1).get("ok", true), "out-of-bounds gates refused")
	check(not lab.select_address(0, 10).get("ok", true), "out-of-bounds sublanguages refused")
	check(FileAccess.get_sha256(source_path) == baseline_sha and not engine.applied, "inspection never changes imported mod")
	var contact: Dictionary = lab.call("_contact")
	check(contact.get("ok", false) and contact.has("splice_sha256"), "CONTACT reveals measured evidence and splice commitment")
	check(not lab.probe.propose_mutation().get("authority", "").is_empty(), "mapping explicitly disclaims authority")
	var playback: Dictionary = lab.call("_audition")
	check(playback.get("ok", false) and playback.get("mp3_bytes", 0) > 0, "selected source gate MP3 can be auditioned natively")
	lab.select_address(0, 0)
	var proposal: Dictionary = lab.probe.propose_mutation()
	check(proposal.get("ok", false) and proposal.get("effect", "") == "open", "measured sample produces a deterministic valid proposal")
	check(proposal["duration_ms"] <= 60000 and proposal["duration_ms"] >= 250, "suggested duration obeys mod adapter limits")
	check(engine.last_preview.is_empty(), "proposal has no side effects before explicit stage")
	lab.call("_propose")
	check(engine.last_preview.get("is_change", false), "explicit stage runs original mod-engine preview")
	check(not engine.applied and not FileAccess.file_exists(engine.working_path), "staging produces a diff, no executable or mod file")
	check(scene.get("view_stack").current_tab == 1, "Studio presents exact proposed change in existing DIFF tab")
	var provenance := false
	for event in engine.evidence():
		if event["action"] == "fracture_proposal" and event["data"].get("splice_sha256") == proposal["source_splice_sha256"]:
			provenance = true
	check(provenance, "proposal provenance binds source Print to existing evidence rail")
	scene.call("_apply")
	check(engine.applied and FileAccess.file_exists(engine.working_path), "user approval path applies only to isolated working copy")
	scene.call("_test")
	check(scene.get("status_label").text.contains("MODEL SIMULATION PASS"), "existing sandbox test works after fracture-derived edit")
	scene.call("_rollback")
	check(FileAccess.get_sha256(engine.working_path) == baseline_sha, "existing rollback restores exact imported bytes")
	check(FileAccess.get_sha256(source_path) == baseline_sha, "original mod target remains untouched throughout")
	var rejected: Dictionary = scene.get("fracture_lab").probe.select(-1, 0)
	check(not rejected.get("ok", true), "negative addressing is refused")
	var altered := ProbeScript.new()
	var temp := ProjectSettings.globalize_path("user://deepbrew_fracture_negative_%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(temp)
	for filename in ["COLOCRYPT_PRINT.json", "COLOCRYPT_VESSEL.ply", "VESSEL_PROOF.json"]:
		var bytes := FileAccess.get_file_as_bytes(ProbeScript.BUNDLE.path_join(filename))
		var writer := FileAccess.open(temp.path_join(filename), FileAccess.WRITE)
		writer.store_buffer(bytes)
		writer.close()
	for i in range(10):
		var filename := "packet_%02d.mp3" % (i + 1)
		var writer := FileAccess.open(temp.path_join(filename), FileAccess.WRITE)
		writer.store_buffer(FileAccess.get_file_as_bytes(ProbeScript.BUNDLE.path_join(filename)))
		writer.close()
	check(altered.load_bundle(temp).get("ok", false), "complete independent fixture copy verifies")
	var corrupt := FileAccess.open(temp.path_join("COLOCRYPT_PRINT.json"), FileAccess.READ_WRITE)
	corrupt.seek(100)
	corrupt.store_8(0x00)
	corrupt.close()
	check(not altered.load_bundle(temp).get("ok", true), "corrupted Print fails closed")
	check(not altered.verified, "a failed read invalidates previous verification state")
	check(not altered.propose_mutation().get("ok", true), "unverified bundle cannot propose changes")
	var new_print := FileAccess.open(temp.path_join("COLOCRYPT_PRINT.json"), FileAccess.WRITE)
	new_print.store_buffer(FileAccess.get_file_as_bytes(ProbeScript.BUNDLE.path_join("COLOCRYPT_PRINT.json")))
	new_print.close()
	var tampered_mp3 := FileAccess.open(temp.path_join("packet_01.mp3"), FileAccess.READ_WRITE)
	tampered_mp3.seek(16)
	tampered_mp3.store_8(0xFF)
	tampered_mp3.close()
	check(not altered.load_bundle(temp).get("ok", true), "changed original MP3 fails closed")
	var original_audio := FileAccess.open(temp.path_join("packet_01.mp3"), FileAccess.WRITE)
	original_audio.store_buffer(FileAccess.get_file_as_bytes(ProbeScript.BUNDLE.path_join("packet_01.mp3")))
	original_audio.close()
	var altered_ply := FileAccess.open(temp.path_join("COLOCRYPT_VESSEL.ply"), FileAccess.READ_WRITE)
	altered_ply.seek(123)
	altered_ply.store_8(0x00)
	altered_ply.close()
	check(not altered.load_bundle(temp).get("ok", true), "tampered 3D Vessel mesh fails closed")
	var changed_proposal := proposal.duplicate(true)
	changed_proposal["duration_ms"] = 60000
	scene.call("_fracture_proposal", changed_proposal)
	check(scene.get("status_label").text.contains("FRACTURE REFUSED"), "manipulated UI proposal rejected at Studio boundary")
	check(FileAccess.get_sha256(source_path) == baseline_sha, "source remains intact after adversarial checks")
	print("DEEPBREW FRACTURE G0.2 RESULT: %d passed, %d failed" % [passed, failed])
	lab.player.stop()
	lab.player.stream = null
	scene.queue_free()
	await process_frame
	await process_frame
	await create_timer(0.15).timeout  # let the MP3 decoder/audio thread release playback refs
	quit(1 if failed else 0)


func check(condition: bool, description: String) -> void:
	if condition:
		passed += 1
		print("PASS  ", description)
	else:
		failed += 1
		push_error("FAIL  " + description)

extends SceneTree

const BrewEngineScript = preload("res://scripts/mod_engine.gd")

var passed := 0
var failed := 0


func _initialize() -> void:
	check_hostile()


func check_hostile() -> void:
	var sample := "res://examples/door_trigger.brew.json"
	var original_sha := FileAccess.get_sha256(sample)
	var engine := BrewEngineScript.new()
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(sample))
	var temp := ProjectSettings.globalize_path("user://deepbrew_g0_3_hostile_%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(temp)

	check(engine.inspect(sample).get("ok", false), "real source schema is still accepted")
	var malicious := data.duplicate(true)
	malicious["shell_command"] = "untrusted"
	var foreign := temp.path_join("unknown_root.brew.json")
	write_json(foreign, malicious)
	check(not engine.inspect(foreign).get("ok", true), "unknown top-level execution channel rejected")
	check(not engine.import_target(foreign).get("ok", true), "unknown root field cannot be imported")

	malicious = data.duplicate(true)
	malicious["behavior"]["untrusted_opcode"] = "launch_process"
	foreign = temp.path_join("unknown_op.brew.json")
	write_json(foreign, malicious)
	check(not engine.inspect(foreign).get("ok", true), "unknown nested instruction rejected")
	check(not engine.import_target(foreign).get("ok", true), "nested instruction cannot be imported")

	malicious = data.duplicate(true)
	malicious["behavior"]["duration_ms"] = true
	foreign = temp.path_join("boolean_duration.brew.json")
	write_json(foreign, malicious)
	check(not engine.inspect(foreign).get("ok", true), "boolean duration is invalid")

	malicious = data.duplicate(true)
	malicious["behavior"]["trigger"] = "on_script"
	foreign = temp.path_join("bad_trigger.brew.json")
	write_json(foreign, malicious)
	check(not engine.inspect(foreign).get("ok", true), "unknown trigger rejected")

	foreign = temp.path_join("excessive.brew.json")
	var big_file := FileAccess.open(foreign, FileAccess.WRITE)
	big_file.store_buffer(PackedByteArray().duplicate())
	big_file.store_string("x".repeat(262145))
	big_file.close()
	check(not engine.inspect(foreign).get("ok", true), "oversized input rejected before JSON parsing")

	var controlled := temp.path_join("controlled.brew.json")
	var controlled_writer := FileAccess.open(controlled, FileAccess.WRITE)
	controlled_writer.store_buffer(FileAccess.get_file_as_bytes(sample))
	controlled_writer.close()
	check(engine.import_target(controlled).get("ok", false), "valid isolated target imported")
	check(engine.preview_change("open", 1400).get("is_change", false), "valid mutation still stages")
	check(engine.apply_preview().get("ok", false), "staged mutation updates only isolated working revision")
	var source_hash := FileAccess.get_sha256(controlled)
	var export_out := temp.path_join("should_refuse.brew.json")
	malicious = data.duplicate(true)
	malicious["notes"] = "changed externally after import"
	write_json(controlled, malicious)
	check(FileAccess.get_sha256(controlled) != source_hash, "forged external change is actually different")
	check(not engine.export_mod(export_out).get("ok", true), "changed original blocks export even after preview/apply")
	check(not FileAccess.file_exists(export_out), "denied export does not materialize a file")
	check(not engine.apply_preview().get("ok", true), "no pending preview can bypass source guard")
	check(engine.rollback_to_import().get("ok", false), "working revision can recover after source mismatch")
	check(FileAccess.get_sha256(sample) == original_sha, "bundled source unchanged through hostile suite")
	print("DEEPBREW G0.3 HOSTILE: %d passed, %d failed" % [passed, failed])
	quit(1 if failed else 0)


func write_json(path: String, value: Dictionary) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(value))
	file.close()


func check(ok: bool, description: String) -> void:
	if ok:
		passed += 1
		print("PASS  ", description)
	else:
		failed += 1
		push_error("FAIL  " + description)

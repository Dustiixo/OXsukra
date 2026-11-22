extends SceneTree

## Export and simulation must use the exact revision DeepBrew approved.
## A local edit to a working file is not an authorized edit in the Studio UI.

const BrewEngineScript = preload("res://scripts/mod_engine.gd")

var passed := 0
var failed := 0


func _initialize() -> void:
	_run()


func _run() -> void:
	var sample := "res://examples/door_trigger.brew.json"
	var source_sha := FileAccess.get_sha256(sample)
	var engine := BrewEngineScript.new()
	var source_dir := ProjectSettings.globalize_path("user://deepbrew_g0_3_1_hardening_%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(source_dir)
	var source := source_dir.path_join("source.brew.json")
	_write(source, FileAccess.get_file_as_bytes(sample))
	_check(engine.import_target(source).get("ok", false), "isolated fixture imported")
	_check(engine.preview_change("open", 1500).get("is_change", false), "open revision previewed")
	_check(engine.apply_preview().get("ok", false), "open revision applied")
	var revision := engine.working_path
	var approved := FileAccess.get_file_as_bytes(revision)
	_check(engine.test_simulation().get("ok", false), "untampered revision passes model test")
	var first := source_dir.path_join("clean_export.brew.json")
	_check(engine.export_mod(first).get("ok", false), "untampered revision exports")
	_check(FileAccess.get_sha256(first) == FileAccess.get_sha256(revision), "clean export bytes match revision")

	var edited: Dictionary = JSON.parse_string(approved.get_string_from_utf8())
	edited["behavior"]["effect"] = "highlight"
	edited["behavior"]["duration_ms"] = 777
	_write(revision, (JSON.stringify(edited) + "\n").to_utf8_buffer())
	var second := source_dir.path_join("tampered_valid.brew.json")
	_check(not engine.test_simulation().get("ok", true), "valid but unapproved working revision fails model")
	_check(not engine.export_mod(second).get("ok", true), "valid but unapproved working revision cannot export")
	_check(not FileAccess.file_exists(second), "failed export leaves no destination")

	edited = JSON.parse_string(approved.get_string_from_utf8())
	edited["behavior"]["execute"] = "untrusted_instruction"
	_write(revision, (JSON.stringify(edited) + "\n").to_utf8_buffer())
	var third := source_dir.path_join("tampered_unknown.brew.json")
	_check(not engine.test_simulation().get("ok", true), "unknown opcode in working revision rejected")
	_check(not engine.export_mod(third).get("ok", true), "unknown opcode in working revision cannot export")
	_check(not FileAccess.file_exists(third), "unknown opcode never materializes an export")

	_write(revision, "not even json".to_utf8_buffer())
	var fourth := source_dir.path_join("tampered_invalid.brew.json")
	_check(not engine.test_simulation().get("ok", true), "invalid JSON in working revision rejected")
	_check(not engine.export_mod(fourth).get("ok", true), "invalid JSON in working revision cannot export")
	_check(not FileAccess.file_exists(fourth), "invalid JSON never materializes an export")

	_write(revision, approved)
	_check(engine.test_simulation().get("ok", false), "original approved bytes restore model validity")
	var fifth := source_dir.path_join("restored.brew.json")
	_check(engine.export_mod(fifth).get("ok", false), "restored approved bytes can export")
	_check(FileAccess.get_sha256(fifth) == FileAccess.get_sha256(first), "restored export deterministic")
	_check(engine.rollback_to_import().get("ok", false), "rollback after tampering succeeds")
	_check(FileAccess.get_sha256(engine.working_path) == FileAccess.get_sha256(source), "rollback bytes match original fixture")
	_check(FileAccess.get_sha256(sample) == source_sha, "bundled source unchanged")
	print("DEEPBREW G0.3.1 HARDENING: %d passed, %d failed" % [passed, failed])
	quit(1 if failed else 0)


func _write(path: String, data: PackedByteArray) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_buffer(data)
	file.close()


func _check(ok: bool, description: String) -> void:
	if ok:
		passed += 1
		print("PASS  ", description)
	else:
		failed += 1
		push_error("FAIL  " + description)

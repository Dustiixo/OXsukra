extends SceneTree

## Deterministic bounded hammer test; never touches a live game or source file.
## Usage: godot --headless --path . --script tests/test_bounded_stress_g0_3_1.gd -- 512

const BrewEngineScript = preload("res://scripts/mod_engine.gd")
const MAX_CYCLES := 2048

var passed := 0
var failed := 0


func _initialize() -> void:
	_run()


func _run() -> void:
	var cycles := 512
	var args := OS.get_cmdline_user_args()
	if args.size() > 0 and args[0].is_valid_int():
		cycles = clampi(int(args[0]), 1, MAX_CYCLES)
	var sample := "res://examples/door_trigger.brew.json"
	var sample_sha := FileAccess.get_sha256(sample)
	var temp := ProjectSettings.globalize_path("user://deepbrew_g0_3_1_stress_%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(temp)
	var source := temp.path_join("untouched_source.brew.json")
	_write(source, FileAccess.get_file_as_bytes(sample))
	var source_sha := FileAccess.get_sha256(source)
	var engine := BrewEngineScript.new()
	_check(engine.import_target(source).get("ok", false), "isolated source imported")
	var effects := ["open", "highlight", "closed"]
	var completed := 0
	var tamper_attempts := 0
	for i in range(cycles):
		var effect: String = effects[i % effects.size()]
		var duration := 250 + (i * 97) % 59500
		if not _check(engine.preview_change(effect, duration).get("is_change", false), "round %d preview" % i):
			break
		if not _check(engine.apply_preview().get("ok", false), "round %d applied" % i):
			break
		var approved := FileAccess.get_file_as_bytes(engine.working_path)
		var destination := temp.path_join("export_%04d.brew.json" % i)
		if i % 4 == 0:
			tamper_attempts += 1
			var changed: Dictionary = JSON.parse_string(approved.get_string_from_utf8())
			changed["notes"] = "unauthorized working-copy mutation %d" % i
			_write(engine.working_path, (JSON.stringify(changed) + "\n").to_utf8_buffer())
			_check(not engine.test_simulation().get("ok", true), "round %d model rejects mutation" % i)
			_check(not engine.export_mod(destination).get("ok", true), "round %d export rejects mutation" % i)
			_check(not FileAccess.file_exists(destination), "round %d no unapproved export" % i)
			_write(engine.working_path, approved)
		if not _check(engine.test_simulation().get("ok", false), "round %d approved simulation" % i):
			break
		if not _check(engine.export_mod(destination).get("ok", false), "round %d approved export" % i):
			break
		_check(FileAccess.get_sha256(destination) == FileAccess.get_sha256(engine.working_path), "round %d export hash" % i)
		_check(FileAccess.get_sha256(source) == source_sha, "round %d source intact" % i)
		completed += 1
		if i % 16 == 15:
			_check(engine.rollback_to_import().get("ok", false), "round %d rollback" % i)
			_check(FileAccess.get_sha256(engine.working_path) == source_sha, "round %d rollback hash" % i)
	_check(FileAccess.get_sha256(sample) == sample_sha, "bundled fixture still exact")
	_check(completed == cycles, "completed all %d native revision cycles" % cycles)
	print("DEEPBREW NATIVE BOUNDED STRESS: %d/%d cycles, %d tamper attempts, %d passed, %d failed" % [completed, cycles, tamper_attempts, passed, failed])
	quit(1 if failed else 0)


func _write(path: String, data: PackedByteArray) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_buffer(data)
	file.close()


func _check(ok: bool, description: String) -> bool:
	if ok:
		passed += 1
		return true
	failed += 1
	push_error("FAIL  " + description)
	return false

class_name DeepbrewEngine
extends RefCounted

## A single real, deliberately constrained editing adapter.
## It never writes to the imported target. Executable input is never run.

const SCHEMA := "deepbrew.behavior.v1"
const ALLOWED_EFFECTS := ["closed", "open", "highlight"]
const ALLOWED_TRIGGERS := ["on_enter"]
const ALLOWED_ROOT_FIELDS := ["schema", "name", "target", "behavior", "notes"]
const ALLOWED_BEHAVIOR_FIELDS := ["trigger", "effect", "duration_ms"]
const MAX_SOURCE_BYTES := 262144

var source_path := ""
var source_hash := ""
var source_bytes := PackedByteArray()
var baseline: Dictionary = {}
var working: Dictionary = {}
var proposed: Dictionary = {}
var working_path := ""
var approved_working_hash := ""
var evidence_path := ""
var events: Array[Dictionary] = []
var applied := false
var last_preview: Dictionary = {}
var revision := 0


func inspect(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {"ok": false, "state": "missing", "reason": "Target file does not exist."}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {"ok": false, "state": "unreadable", "reason": "Cannot read target file."}
	if file.get_length() > MAX_SOURCE_BYTES:
		return {"ok": false, "state": "unsupported", "reason": "Source exceeds the 256 KiB adapter limit."}
	var bytes := file.get_buffer(file.get_length())
	file.close()
	var parser := JSON.new()
	if parser.parse(bytes.get_string_from_utf8()) != OK or typeof(parser.data) != TYPE_DICTIONARY:
		return {"ok": false, "state": "unknown", "reason": "This adapter requires a JSON object."}
	var value: Dictionary = parser.data
	if value.get("schema", "") != SCHEMA:
		return {"ok": false, "state": "unknown", "reason": "Unrecognized schema. The source is inspectable, but not editable by G0.1."}
	var problem := _validate(value)
	if problem != "":
		return {"ok": false, "state": "invalid", "reason": problem}
	return {"ok": true, "state": "supported", "name": value.get("name", "Untitled"), "target": value.get("target", ""), "source_hash": _hash(bytes), "bytes": bytes.size(), "behavior": value["behavior"].duplicate(true)}


func import_target(path: String) -> Dictionary:
	var probe := inspect(path)
	if not probe.ok:
		return probe
	var source_file := FileAccess.open(path, FileAccess.READ)
	var bytes := source_file.get_buffer(source_file.get_length())
	source_file.close()
	# The source is opened twice: once by inspect(), then here. Invalidate
	# any change in between instead of importing an unchecked second read.
	if _hash(bytes) != probe["source_hash"]:
		return {"ok": false, "state": "changed_during_import", "reason": "Source changed between discovery and import. Retry."}
	var parsed: Dictionary = JSON.parse_string(bytes.get_string_from_utf8())
	var directory := ProjectSettings.globalize_path("user://deepbrew_g0_1")
	var unique_id := _hash(bytes).substr(0, 10) + "_" + str(Time.get_ticks_usec())
	var run_dir := directory.path_join(unique_id)
	var error := DirAccess.make_dir_recursive_absolute(run_dir)
	if error != OK:
		return {"ok": false, "reason": "Cannot create private working directory: " + str(error)}
	source_path = path
	source_bytes = bytes
	source_hash = _hash(bytes)
	baseline = parsed.duplicate(true)
	working = baseline.duplicate(true)
	proposed = {}
	working_path = run_dir.path_join("revision_000.brew.json")
	approved_working_hash = ""
	evidence_path = run_dir.path_join("evidence.jsonl")
	events.clear()
	applied = false
	last_preview = {}
	revision = 0
	_record("import", {"source_hash": source_hash, "source": path, "target": baseline.get("target", "")})
	return {"ok": true, "state": "supported", "working_dir": run_dir, "source_hash": source_hash}


func preview_change(effect: String, duration_ms: int) -> Dictionary:
	if source_path == "":
		return {"ok": false, "reason": "Import a supported target first."}
	if not ALLOWED_EFFECTS.has(effect):
		return {"ok": false, "reason": "Unsupported effect."}
	if duration_ms < 0 or duration_ms > 60000:
		return {"ok": false, "reason": "Duration must be 0–60000 ms."}
	proposed = working.duplicate(true)
	var behavior: Dictionary = proposed["behavior"]
	var before: Dictionary = working["behavior"]
	behavior["effect"] = effect
	behavior["duration_ms"] = duration_ms
	var changes: Array[String] = []
	if before["effect"] != effect:
		changes.append("behavior.effect: %s → %s" % [before["effect"], effect])
	if before["duration_ms"] != duration_ms:
		changes.append("behavior.duration_ms: %d → %d" % [before["duration_ms"], duration_ms])
	last_preview = {"ok": true, "changes": changes, "before": JSON.stringify(working, "  "), "after": JSON.stringify(proposed, "  "), "is_change": changes.size() > 0}
	_record("preview", {"changes": changes, "applied": false})
	return last_preview


func apply_preview() -> Dictionary:
	if last_preview.is_empty() or not last_preview.get("is_change", false):
		return {"ok": false, "reason": "Preview a genuine change first."}
	if _source_changed():
		return {"ok": false, "reason": "Imported source changed externally. Reimport before applying."}
	var data := (JSON.stringify(proposed, "  ") + "\n").to_utf8_buffer()
	var next_path := _next_revision_path()
	var result := _write_atomically(next_path, data)
	if not result.ok:
		return result
	working_path = next_path
	working = proposed.duplicate(true)
	proposed = {}
	applied = true
	last_preview = {}
	var digest := _hash(data)
	approved_working_hash = digest
	_record("apply", {"working_hash": digest, "original_unchanged": true, "path": working_path})
	return {"ok": true, "working_path": working_path, "working_hash": digest}


func test_simulation() -> Dictionary:
	if not applied or not FileAccess.file_exists(working_path):
		return {"ok": false, "reason": "Apply a modification to the working copy first."}
	var bytes := FileAccess.get_file_as_bytes(working_path)
	if approved_working_hash == "" or _hash(bytes) != approved_working_hash:
		return {"ok": false, "reason": "Working revision changed outside the approved Studio edit; reapply from a trusted source."}
	var parsed = JSON.parse_string(bytes.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY or _validate(parsed) != "":
		return {"ok": false, "reason": "Working copy failed schema validation."}
	var config: Dictionary = parsed
	var behavior: Dictionary = config["behavior"]
	var observed := "closed"
	if behavior["trigger"] == "on_enter":
		observed = behavior["effect"]
	var source_intact := not _source_changed()
	var matches_configuration: bool = observed == working["behavior"]["effect"]
	var same_behavior: bool = behavior.get("trigger", "") == working["behavior"]["trigger"] and behavior.get("effect", "") == working["behavior"]["effect"] and int(behavior.get("duration_ms", -1)) == int(working["behavior"]["duration_ms"])
	var passed: bool = source_intact and matches_configuration and same_behavior
	var outcome := {"ok": passed, "kind": "model_simulation", "observed": observed, "expected": working["behavior"]["effect"], "working_hash": _hash(bytes), "source_unchanged": source_intact, "contract_verified": matches_configuration, "real_external_runtime_tested": false}
	_record("simulation", outcome)
	return outcome


func rollback_to_import() -> Dictionary:
	if source_path == "":
		return {"ok": false, "reason": "No target imported."}
	var next_path := _next_revision_path()
	var result := _write_atomically(next_path, source_bytes)
	if not result.ok:
		return result
	working_path = next_path
	approved_working_hash = ""
	working = baseline.duplicate(true)
	proposed = {}
	last_preview = {}
	applied = false
	var correct := FileAccess.get_sha256(working_path) == source_hash
	_record("rollback", {"ok": correct, "restored_hash": FileAccess.get_sha256(working_path), "matches_import": correct})
	return {"ok": correct, "restored_hash": FileAccess.get_sha256(working_path)}


func export_mod(destination: String) -> Dictionary:
	if not applied or not FileAccess.file_exists(working_path):
		return {"ok": false, "reason": "No applied modification to export."}
	if _source_changed():
		return {"ok": false, "reason": "Imported original changed externally; export refused."}
	if FileAccess.file_exists(destination):
		return {"ok": false, "reason": "Export refuses to overwrite an existing file."}
	if not destination.ends_with(".brew.json"):
		return {"ok": false, "reason": "Choose a .brew.json export filename."}
	var bytes := FileAccess.get_file_as_bytes(working_path)
	# An isolated working file is still on disk: reject edits made outside the
	# reviewed preview/apply path, even if the substituted JSON is well formed.
	if approved_working_hash == "" or _hash(bytes) != approved_working_hash:
		return {"ok": false, "reason": "Working revision changed outside the approved Studio edit; export refused."}
	var writer := FileAccess.open(destination, FileAccess.WRITE)
	if writer == null:
		return {"ok": false, "reason": "Cannot write export destination."}
	writer.store_buffer(bytes)
	writer.close()
	var correct := FileAccess.get_sha256(destination) == _hash(bytes)
	_record("export", {"destination": destination, "verified": correct, "hash": _hash(bytes)})
	return {"ok": correct, "destination": destination, "hash": _hash(bytes)}


func evidence() -> Array[Dictionary]:
	return events.duplicate(true)


func _validate(data: Dictionary) -> String:
	for key in data.keys():
		if key not in ALLOWED_ROOT_FIELDS:
			return "Unknown root field refused: " + str(key)
	if typeof(data.get("behavior")) != TYPE_DICTIONARY:
		return "Missing behavior object."
	var behavior: Dictionary = data["behavior"]
	for key in behavior.keys():
		if key not in ALLOWED_BEHAVIOR_FIELDS:
			return "Unknown behavior instruction refused: " + str(key)
	if not ALLOWED_TRIGGERS.has(behavior.get("trigger", "")):
		return "Unsupported trigger."
	if not ALLOWED_EFFECTS.has(behavior.get("effect", "")):
		return "Unsupported effect."
	if typeof(behavior.get("duration_ms")) != TYPE_FLOAT and typeof(behavior.get("duration_ms")) != TYPE_INT:
		return "Duration must be a number."
	var duration: float = behavior["duration_ms"]
	if duration != round(duration) or duration < 0 or duration > 60000:
		return "Duration must be an integer in 0–60000 ms."
	return ""


func _source_changed() -> bool:
	return not FileAccess.file_exists(source_path) or FileAccess.get_sha256(source_path) != source_hash


func _write_atomically(path: String, bytes: PackedByteArray) -> Dictionary:
	if FileAccess.file_exists(path):
		return {"ok": false, "reason": "Revision already exists; refusing overwrite."}
	var temporary := path + ".tmp"
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		return {"ok": false, "reason": "Cannot write temporary file."}
	file.store_buffer(bytes)
	file.close()
	if FileAccess.get_sha256(temporary) != _hash(bytes):
		return {"ok": false, "reason": "Temporary file verification failed."}
	var error := DirAccess.rename_absolute(temporary, path)
	if error != OK:
		return {"ok": false, "reason": "Cannot promote verified working file: " + str(error)}
	return {"ok": true}


func _record(action: String, values: Dictionary) -> void:
	var event := {"time": Time.get_datetime_string_from_system(true, true), "action": action, "data": values}
	events.append(event)
	if evidence_path != "":
		var file: FileAccess
		if FileAccess.file_exists(evidence_path):
			file = FileAccess.open(evidence_path, FileAccess.READ_WRITE)
			if file != null:
				file.seek_end()
		else:
			file = FileAccess.open(evidence_path, FileAccess.WRITE)
		if file != null:
			file.store_line(JSON.stringify({"schema": "deepbrew.event.v1", "source_hash": source_hash, "event": event}))
			file.close()


func _next_revision_path() -> String:
	revision += 1
	return working_path.get_base_dir().path_join("revision_%03d.brew.json" % revision)


func _hash(bytes: PackedByteArray) -> String:
	var hasher := HashingContext.new()
	hasher.start(HashingContext.HASH_SHA256)
	hasher.update(bytes)
	return hasher.finish().hex_encode()

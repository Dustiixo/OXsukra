extends SceneTree

const BrewEngineScript = preload("res://scripts/mod_engine.gd")

var passed := 0
var failed := 0


func _initialize() -> void:
	var engine := BrewEngineScript.new()
	var fixture := "res://examples/door_trigger.brew.json"
	var source_hash := FileAccess.get_sha256(fixture)
	var inspection := engine.inspect(fixture)
	check(inspection.get("ok", false), "supported adapter discovered")
	check(inspection.get("source_hash", "") == source_hash, "discovery fingerprint matches source")

	var imported := engine.import_target(fixture)
	check(imported.get("ok", false), "project imported into private workspace")
	check(engine.working_path != fixture, "working copy isolated from original")

	var staged := engine.preview_change("open", 1500)
	check(staged.get("ok", false) and staged.get("is_change", false), "real change previewed")
	check(staged.get("changes", []).size() == 2, "two changed fields identified")
	check(not FileAccess.file_exists(engine.working_path), "preview performed no file write")

	var applied := engine.apply_preview()
	check(applied.get("ok", false), "working copy written")
	check(FileAccess.get_sha256(fixture) == source_hash, "original source bytes unchanged")
	check(FileAccess.file_exists(engine.working_path), "working file exists")
	check(FileAccess.get_sha256(engine.working_path) != source_hash, "working copy differs from source")

	var test := engine.test_simulation()
	check(test.get("ok", false), "model simulation passes")
	check(test.get("observed", "") == "open", "model detects modified open effect")
	check(not test.get("real_external_runtime_tested", true), "test truthfully labels simulation")

	var export_path: String = str(imported.get("working_dir", "")).path_join("deliverable.brew.json")
	var exported := engine.export_mod(export_path)
	check(exported.get("ok", false), "mod exported")
	check(FileAccess.get_sha256(export_path) == FileAccess.get_sha256(engine.working_path), "export hash matches working copy")
	check(not engine.export_mod(export_path).get("ok", true), "export will not overwrite an existing file")

	var rolled := engine.rollback_to_import()
	check(rolled.get("ok", false), "rollback executed")
	check(FileAccess.get_sha256(engine.working_path) == source_hash, "working bytes restored to original")
	check(FileAccess.get_sha256(fixture) == source_hash, "original still unchanged after rollback")
	check(FileAccess.file_exists(engine.evidence_path), "evidence file persists")
	check(engine.evidence().size() >= 6, "provenance events recorded")
	var ledger := FileAccess.get_file_as_string(engine.evidence_path).strip_edges().split("\n")
	check(ledger.size() == engine.evidence().size(), "all evidence records persist append-only")

	check(not engine.preview_change("arbitrary-script", 1000).get("ok", true), "unsupported effects rejected")
	check(not engine.preview_change("open", 100000).get("ok", true), "out of bounds duration rejected")
	check(not engine.inspect("res://project.godot").get("ok", true), "unknown input stays inspect-only")

	print("DEEPBREW TEST RESULT: %d passed, %d failed" % [passed, failed])
	quit(1 if failed else 0)


func check(condition: bool, description: String) -> void:
	if condition:
		passed += 1
		print("PASS  ", description)
	else:
		failed += 1
		push_error("FAIL  " + description)

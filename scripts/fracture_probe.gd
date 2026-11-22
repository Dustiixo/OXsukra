class_name DeepbrewFractureProbe
extends RefCounted

## G0.2 read-only adapter over the independently verified COLOCRYPT v0.4
## fixture. This is an evidence visualizer and mutation *proposal* tool,
## not a new mod format, an executable music language, or an authority broker.

const BUNDLE := "res://assets/colocrypt"
const PRINT_SCHEMA := "ixo.rcll.colocrypt.print.v0.4"
const PRINT_FINGERPRINT := "c20cb09f1fdecafab8bad803aa7b7582b5ba28ee19789013b6a20296bf48421b"
const PRINT_RAW_SHA256 := "cb6ff325828cf4150d4a6026477c6114faa8352118bf89acd0f9b09492703425"
const PLY_SHA256 := "30cb3fe9d1334adab598734b163d4efba7e5337e363772acb5d9624aeb11c214"
const PROOF_RAW_SHA256 := "c7dd436f3e4fe6ab16c351631292bc2d171928011cedd3d0c987a4fb65f8c1a8"
const EFFECTS := ["open", "highlight", "closed"]

var print_data: Dictionary = {}
var base_path := ""
var selected_gate := 0
var selected_slot := 0
var verified := false


func load_bundle(path: String = BUNDLE) -> Dictionary:
	verified = false
	print_data = {}
	base_path = ""
	var targets := {
		"COLOCRYPT_PRINT.json": PRINT_RAW_SHA256,
		"COLOCRYPT_VESSEL.ply": PLY_SHA256,
		"VESSEL_PROOF.json": PROOF_RAW_SHA256,
	}
	for filename in targets:
		var full: String = path.path_join(filename)
		if not FileAccess.file_exists(full) or FileAccess.get_sha256(full) != targets[filename]:
			return {"ok": false, "reason": "Pinned fixture missing or changed: " + filename}
	var value = JSON.parse_string(FileAccess.get_file_as_string(path.path_join("COLOCRYPT_PRINT.json")))
	var proof = JSON.parse_string(FileAccess.get_file_as_string(path.path_join("VESSEL_PROOF.json")))
	if typeof(value) != TYPE_DICTIONARY or typeof(proof) != TYPE_DICTIONARY:
		return {"ok": false, "reason": "Invalid COLOCRYPT data encoding."}
	if value.get("schema") != PRINT_SCHEMA or value.get("fingerprint_sha256") != PRINT_FINGERPRINT:
		return {"ok": false, "reason": "Unsupported or mismatched Print."}
	if proof.get("print_sha256") != PRINT_FINGERPRINT or proof.get("ply_sha256") != PLY_SHA256:
		return {"ok": false, "reason": "Vessel proof is not paired with Print."}
	if not proof.get("closed_manifold_by_edge_incidence", false) or int(proof.get("triangles", 0)) != 200:
		return {"ok": false, "reason": "Vessel topology proof not accepted."}
	if int(value.get("splices", 0)) != 100 or int(value.get("measured_points_covered", 0)) != 1240:
		return {"ok": false, "reason": "Unexpected lattice dimensions."}
	var gates = value.get("gates", [])
	if typeof(gates) != TYPE_ARRAY or gates.size() != 10:
		return {"ok": false, "reason": "Expected ten primary gates."}
	var measured := 0
	for i in range(10):
		var gate = gates[i]
		if typeof(gate) != TYPE_DICTIONARY or gate.get("gate") != i:
			return {"ok": false, "reason": "Gate addressing mismatch."}
		var slices = gate.get("splices", [])
		if typeof(slices) != TYPE_ARRAY or slices.size() != 10:
			return {"ok": false, "reason": "Expected ten slots per gate."}
		var packet_path: String = path.path_join("packet_%02d.mp3" % (i + 1))
		if not FileAccess.file_exists(packet_path) or FileAccess.get_sha256(packet_path) != gate.get("source_mp3_sha256", ""):
			return {"ok": false, "reason": "Source audio failed hash check at gate %d." % i}
		for j in range(10):
			var splice = slices[j]
			if typeof(splice) != TYPE_DICTIONARY or splice.get("gate") != i or splice.get("slot") != j:
				return {"ok": false, "reason": "Fracture splice addressing mismatch."}
			if typeof(splice.get("display_rgb")) != TYPE_ARRAY or splice["display_rgb"].size() != 3:
				return {"ok": false, "reason": "Splice colour is invalid."}
			if not (float(splice.get("mean_frequency_hz", 0)) > 0.0 and float(splice.get("mean_strength_pcm", 0)) > 0.0):
				return {"ok": false, "reason": "Sound measurements must be positive."}
			measured += int(splice.get("bearing_count", 0))
	if measured != 1240:
		return {"ok": false, "reason": "Bearing coverage does not match the Print."}
	print_data = value
	base_path = path
	selected_gate = 0
	selected_slot = 0
	verified = true
	return {"ok": true, "fingerprint_sha256": PRINT_FINGERPRINT,
		"gates": 10, "splices": 100, "bearings": measured,
		"claim": "Pinned fixture verified, not a newly re-decoded MP3 proof."}


func select(gate: int, slot: int) -> Dictionary:
	if not verified:
		return {"ok": false, "reason": "Load and verify COLOCRYPT evidence first."}
	if gate < 0 or gate > 9 or slot < 0 or slot > 9:
		return {"ok": false, "reason": "Gate and slot must be within the 10 × 10 lattice."}
	selected_gate = gate
	selected_slot = slot
	return {"ok": true, "splice": current_splice().duplicate(true)}


func current_splice() -> Dictionary:
	if not verified:
		return {}
	return print_data["gates"][selected_gate]["splices"][selected_slot]


func current_gate() -> Dictionary:
	if not verified:
		return {}
	return print_data["gates"][selected_gate]


func sound_file() -> String:
	if not verified:
		return ""
	return base_path.path_join("packet_%02d.mp3" % (selected_gate + 1))


func propose_mutation() -> Dictionary:
	if not verified:
		return {"ok": false, "reason": "No verified fixture."}
	var splice := current_splice()
	var hz := float(splice["mean_frequency_hz"])
	var power := float(splice["mean_strength_pcm"])
	var effect: String = EFFECTS[int(floor(hz / 600.0)) % EFFECTS.size()]
	var milliseconds := clampi(int(round(power / 40.0)) * 50, 250, 60000)
	return {
		"ok": true, "effect": effect, "duration_ms": milliseconds,
		"source_address": splice["address"], "source_splice_sha256": splice["splice_sha256"],
		"print_sha256": PRINT_FINGERPRINT,
		"rule": "Experimental mapping: effect = [open, highlight, closed][floor(Hz/600) mod 3]; duration = clamp(round(PCM/40)*50, 250, 60000).",
		"authority": "NONE; proposal requires user preview/apply and a supported mod adapter.",
	}

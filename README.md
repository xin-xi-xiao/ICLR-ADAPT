# Analog layout dataset

**40 circuits · 3 PDKs · 3,760 complete-geometry observations.** Start with [`index.csv`](index.csv). Failed, timed-out and incomplete observations are excluded. `L ⊆ C ⊆ G`: 3,760 G / 2,364 C / 1,469 L. These labels describe the recorded ALIGN checks, not foundry signoff or electrical validation.

| File | Contents |
|---|---|
| `index.csv` | The single sample index: circuit/PDK, sampling identity, 35D actions and masks, G/C/L, connectivity/DRC, four metrics, runtime, archive/member paths and hashes |
| `data/<pair_id>.tar.gz` | `pair.json`; deduplicated adapted circuit inputs; `samples/<sample_id>/sample.json` and one `layout.gds` per observation |
| `common/<PDK>.tar.gz` | Shared model declarations and primitive generators; sample-specific `layers.json` is in `sample.json` |
| `formal35.json` | Fixed coordinate order, candidate lists, groups and reference values |
| `common/align_scripts.tar.gz` | Historical phase drivers, Formal35 binding/decoder and metric code, with source/export hashes |
| `manifest.json` | Release file hashes, sampling/quality metadata and source attribution |

The 14nm and 65nm domains are mock PDKs; SKY130 is a fixed ALIGN plugin snapshot. Circuit names and upstream notices identify circuit provenance, not dataset authors. Upstream licenses are retained in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Adapted circuit inputs are included for all 40 circuits and all 120 pairs. AnalogToBi netlists are included with redistribution permission confirmed by the contributor; this does not imply a general upstream dataset license.

**Sampling.** Each original pair requested 64 slots: a shared scrambled-Sobol block of 32 plus a lineage-specific block of 32. These are not the first 64 points of one Sobol sequence. Global sampling seed is 20260919; ALIGN seed is 1. Coordinate `j` selects `D_j[floor(u_j*len(D_j))]`. `requested35` is the discrete request; `executed35` holds reference on structurally inactive coordinates. JSON `null` in masks means unknown, not false. After G filtering, pairs retain different subsets (2–64 rows); match by original block/slot identifiers, not CSV row position.

**Metrics.** All four are minimized: `Aeval` is evaluation-bounding-box area (µm²); `Leq_signal` and `Leq_power` are per-layer union metal area divided by frozen reference width, summed over signal or power/ground geometry (µm-equivalent); `Ncut_intermetal` counts deduplicated intermetal cuts, excluding contacts/V0. These are not delay, power consumption, centerline wire length or electrical performance. `C` requires G and zero OPEN/SHORT/checker-unknown; `L` additionally requires zero DRC. G-only is not connectivity-qualified.

3,688 observations use a 1,200-second placement limit; 72 use a selective 3,600-second rescue limit. Rescue keeps the same logical slot. This success-conditioned dataset cannot estimate unconditional failure probability or complete campaign cost; selected-attempt runtime excludes prior failures. No failure records are included. Distinct logical slots do not necessarily imply distinct effective native configurations; no independent-observation claim is made for duplicate actions. Post-run masks, bindings, geometry and quality are not free pre-run prediction features. Split by circuit lineage and PDK as appropriate; no default train/test split is imposed.

```bash
python dataset.py summary
python dataset.py verify
python dataset.py extract --sample-id f31e78ad0bb46333__14nm__d2_001 --output /tmp/layout_example_NEW
python align_recipe.py --sample-id f31e78ad0bb46333__14nm__d2_001
```

Extraction needs only Python's standard library and refuses to overwrite its output directory. Archives contain ordinary files, no external symlinks. The GDS library name and timestamps are normalized; all other GDS records, including geometry, cell names and connectivity references, are unchanged. Original and exported hashes are retained in the sample record.

**Replay scope.** `align_recipe.py` displays the recorded five phases and native environment; it does not execute ALIGN. Complete replay requires interleaved Formal35 binding and the matching native binary (hash in `sample.json`), not an arbitrary stock ALIGN install. Historical scripts are provided for inspection; the matching native binary/build environment and a validated fresh-host full-flow launcher are **not bundled**. The compact archive omits intermediate layouts, verbose logs and expanded net-aware geometry. A GDS alone does not reconstruct signal/power ownership or all metric/checker provenance. Labels are preserved from the verified original observations, not recomputed from exported GDS.

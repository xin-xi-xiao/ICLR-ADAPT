# Rebuttal: physical verification and circuit-response evidence

This folder contains the **155 files extracted from `Anonymous_Evidence_Reviewed.zip`**, with their original relative paths and bytes preserved. The original ZIP is not duplicated here. Start with [FILE_INDEX.csv](FILE_INDEX.csv) for each file's design, evidence population and role.

| Location | Contents |
|---|---|
| [Evidence/DRC/](Evidence/DRC/) | ALIGN records for two historical examples; seven Calibre research-deck summaries and logs; geometry/reference scope |
| [Evidence/LVS/](Evidence/LVS/) | Five device-level LVS reports and logs against declared generator-effective references |
| [Evidence/Simulation/](Evidence/Simulation/) | Five-design unit/RC/RCC traces, scalar metrics, comparison tables and figures; REF local-loop stability; earlier PT sizing control |
| [Simulation definitions](Evidence/Simulation/Definitions/) | Device models, operating conditions, stimuli, loads, measurement windows and research RC coefficients |
| [Numerical recheck](Evidence/Simulation/Numerical_recheck/) | Archived recalculations and consistency summaries |

## Which implementations are compared?

The archive distinguishes **two historical ADAPT geometries** (CT-CMP and PT-CMP, under `DRC/<design>/ALIGN/`) from **five subsequent implementations** (CLK-CMP, CT-CMP, DC-Switch, PT-CMP and REF-BUF, under the other DRC, LVS and simulation directories). Sharing a design name does not make these the same layout. The association is recorded in [verification_scope.json](Evidence/DRC/verification_scope.json).

The follow-up implementations include generator/implementation repairs. CT uses VBN/VBP of 0.25/0.55 V, REF uses 20 µA, and PT includes two sensing-inverter sizing changes. They are distinguished from the original optimization outputs and source sizing. This archive is the inspectable physical-results attachment; the later matched baseline study and separate PDK-encoding/BO experiments are outside its scope.

## Recorded checks and measurement scope

- **DRC:** seven Calibre summaries report 49 executed research checks and zero generated results. This is a mock14 research rule deck, not a full foundry signoff deck.
- **LVS:** five reports are CORRECT against independently constructed generator-effective references, including named ports and zero-tolerance geometric L/W comparisons. Parallel/split-device reduction and matching notices remain visible. This establishes correspondence to the declared implementation reference; direct equivalence to the unexpanded original parameterized source is not established.
- **Simulation:** the primary comparisons contain 15 transient runs (five designs × unit/RC/RCC) and two REF local-STB runs. An additional earlier PT sizing-control run supplies the fourth PT curve. All 18 included Spectre logs record zero errors.
- **Models and conditions:** PTM-MG 14nm predictive devices, 0.8 V and 27°C; ideal-interconnect unit-device controls, distributed research RC, and a restricted nominal coupling approximation. These are research models rather than calibrated foundry PEX. Within each primary design comparison, device definitions, bias, stimulus and load are fixed.

The numerical files preserve both favorable and unfavorable changes. CT's output criteria use stated time-window means; crossing lags are signed event differences. REF settling uses a 1% band of the actual output step, and local STB measures VFB1 with VFB2 closed. DC-Switch is an externally supplied switching core. Simulation completion and the recorded probes do not assert complete application specifications. Exact definitions and coefficients are included alongside the data.

## Recalculate the measurements

Use Python 3 and NumPy. From this folder:

```sh
python verify_simulation.py . --output /tmp/rebuttal-verification-new
```

Choose a new output directory. The verifier reads the evidence without changing it and also accepts the original ZIP as input. It recalculates **84 primary scalar metrics, 56 pre/post changes, 108 recorded probes, eight local STB summary values and four earlier-control metrics**, and checks the included simulation completion records. The directory-reading adapter preserves the original numerical calculations.

This is a numerical consistency check, not a new EDA run. It needs no simulator, EDA license or private project code. No standalone GDS, circuit netlist or model-card input package is included in this physical-results attachment, so it does not independently reproduce DRC/LVS or rerun the circuit simulations.

The reports are anonymized derivatives of recorded native output; tables, figures and condition summaries are derived postprocessing. The extracted evidence retains its warnings, test conditions and reference distinctions. The source archive's SHA256 is `19ed35427a3a7059c2c5cb73774198fa813be72e0482a6a804bb48d15082e21f`.

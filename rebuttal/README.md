# Rebuttal Evidence

**155 evidence files.** [FILE_INDEX.csv](FILE_INDEX.csv) lists each file's design, contents and implementation.

| Folder | Contents |
|---|---|
| [DRC](Evidence/DRC/) | ALIGN reports and seven Calibre summaries covering 49 research rules |
| [LVS](Evidence/LVS/) | Five device-level comparisons against generator-effective references |
| [Simulation](Evidence/Simulation/) | Waveforms, metrics and figures for CLK-CMP, CT-CMP, DC-Switch, PT-CMP and REF-BUF |
| [Definitions](Evidence/Simulation/Definitions/) | Models, operating conditions, measurement definitions and RC coefficients |
| [Numerical recheck](Evidence/Simulation/Numerical_recheck/) | Recomputed metrics and consistency summaries |

The two historical CT/PT layouts in `DRC/<design>/ALIGN/` are separate from the five follow-up implementations used for LVS and simulation. The follow-ups include generator/implementation repairs; their references and changes are recorded in [verification_scope.json](Evidence/DRC/verification_scope.json).

Simulations use PTM-MG 14nm predictive devices at 0.8 V and 27°C, comparing ideal interconnect, research RC and nominal coupling (RCC). The package includes 15 primary transient runs, two REF local-STB runs and one earlier PT sizing control.

## Verify the numerical results

Requires Python 3 and NumPy. Run from this folder with a new output directory:

```sh
python verify_simulation.py . --output verification
```

The script recomputes 84 primary metrics, 56 pre/post changes, 108 probes, eight STB values and four earlier-control metrics from the supplied traces.

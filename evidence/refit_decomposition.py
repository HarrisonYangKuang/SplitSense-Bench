"""Descriptive decomposition of frozen v38 results; no fitting or gate revision."""
import hashlib
import json
import math
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent

def ranks(values):
    return [1 + sum(y < x for y in values) + (sum(y == x for y in values)-1)/2 for x in values]

def rho(left, right):
    a, b = ranks(left), ranks(right)
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    den = math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
    if den == 0:
        raise ValueError("Undefined rank correlation")
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/den

def main():
    raw = (ROOT / "appliances_v38_results.json").read_bytes()
    data = json.loads(raw)
    rows = []
    assert [r["episode"] for r in data["reports"]] == list(range(5))
    for r in data["reports"]:
        names = list(r["future_mse"])
        assert len(names) == 7
        common, retained, rank_common, rank_retained = {}, {}, {}, {}
        for split in ("random", "forward"):
            choice = r["choices"][split]
            assert choice == min(names, key=lambda n:r["validation_mse"][split][n])
            common[split] = r["future_mse"][choice]
            retained[split] = r["retained_mse"][split][choice]
            assert math.isclose(retained[split], r["retained_selected_mse"][split], rel_tol=1e-12)
            val = [r["validation_mse"][split][n] for n in names]
            rank_common[split] = rho(val, [r["future_mse"][n] for n in names])
            rank_retained[split] = rho(val, [r["retained_mse"][split][n] for n in names])
        variance = r["variance"]
        assert variance > 0
        e_common = (common["random"] - common["forward"])/variance
        e_retained = (retained["random"] - retained["forward"])/variance
        gains = {s:(retained[s]-common[s])/variance for s in common}
        d_common = rank_common["forward"]-rank_common["random"]
        assert math.isclose(e_common, r["E"], abs_tol=1e-12)
        assert math.isclose(d_common, r["D"], abs_tol=1e-12)
        assert math.isclose(e_retained-e_common, gains["random"]-gains["forward"], abs_tol=1e-12)
        rows.append(dict(episode=r["episode"], choices=r["choices"],
            common_selected_mse=common, retained_selected_mse=retained,
            E_common=e_common, E_retained=e_retained,
            normalized_refit_gain=gains, rho_common=rank_common,
            rho_retained=rank_retained, D_common=d_common,
            D_retained=rank_retained["forward"]-rank_retained["random"]))
    summary = {}
    for key in ("E_common", "E_retained", "D_common", "D_retained"):
        values = [r[key] for r in rows]
        summary[key] = dict(median=median(values), minimum=min(values), maximum=max(values), positive=sum(v>0 for v in values))
    print(json.dumps(dict(source_sha256=hashlib.sha256(raw).hexdigest(),
        scope="Five ordered episodes from one house; descriptive, not independent population replicates",
        primary_gate_unchanged=data["screen_pass"], rows=rows, summary=summary), indent=2, allow_nan=False))

if __name__ == "__main__":
    main()

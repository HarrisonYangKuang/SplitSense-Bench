"""Synthetic mechanism diagnostic, not real-world benchmark admission.

Only standard-library small fixtures may execute locally. Full generation/fits
belong in the private CPU worker. Time is an observed index, not a secret regime.
"""
import hashlib
import random

SEEDS = tuple(range(201, 206))
CASES = ('stationary', 'decrease', 'increase', 'return')
IDS = ('mean', 'ridge_all', 'ridge_recent', 'ridge_interaction',
       'hist_boost', 'extra_trees')

def slope(case, t):
    if case not in CASES:
        raise ValueError('unknown_case')
    if t < 60 or case == 'stationary' or (case == 'return' and t >= 100):
        return 1.0
    return 2.0 if case == 'increase' else 0.0

def rows(seed, case, times, per_time=16):
    """Keyed RNG prevents request order or partitioning from changing labels.

    All scenarios share x/noise within a seed for paired mechanism comparisons.
    x and y are dimensionless. Noise standard deviation is one.
    """
    answer = []
    for t in times:
        rng = random.Random(int.from_bytes(hashlib.sha256(
            f'v26:{seed}:{t}'.encode()).digest(), 'big'))
        for j in range(per_time):
            x, noise = rng.gauss(0, 1), rng.gauss(0, 1)
            answer.append((t, j, x, slope(case, t) * x + noise))
    return answer

def partition(seed):
    valid = sorted(range(100), key=lambda t: hashlib.sha256(
        f'v26:split:{seed}:{t}'.encode()).digest())[:20]
    return {'random_fit': [t for t in range(100) if t not in valid],
            'random_valid': sorted(valid), 'time_fit': list(range(80)),
            'time_valid': list(range(80, 100)), 'final': list(range(100)),
            'future': list(range(100, 120))}

def fit_rows(name, records):
    if name not in IDS:
        raise ValueError('unknown_model')
    if name == 'ridge_recent':
        recent = set(sorted({r[0] for r in records})[-20:])
        return [r for r in records if r[0] in recent]
    return records

def features(name, records):
    if name in ('mean', 'ridge_all', 'ridge_recent'):
        return [[r[2]] for r in records]
    if name == 'ridge_interaction':
        return [[r[2], r[0] / 100., r[2] * r[0] / 100.] for r in records]
    if name in ('hist_boost', 'extra_trees'):
        return [[r[2], r[0] / 100.] for r in records]
    raise ValueError('unknown_model')

def estimator(name):
    from sklearn.dummy import DummyRegressor
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import HistGradientBoostingRegressor, ExtraTreesRegressor
    if name == 'mean':
        return DummyRegressor(strategy='mean')
    if name.startswith('ridge_'):
        return Ridge(alpha=1., fit_intercept=True, solver='svd')
    if name == 'hist_boost':
        return HistGradientBoostingRegressor(max_iter=300, learning_rate=.05,
            max_leaf_nodes=15, min_samples_leaf=20, l2_regularization=1.,
            categorical_features=None, early_stopping=False, random_state=101)
    if name == 'extra_trees':
        return ExtraTreesRegressor(n_estimators=300, min_samples_leaf=5,
                                  n_jobs=2, random_state=101)
    raise ValueError('unknown_model')

# Concatenated after design.py; executed only on private Kaggle CPU.
import gzip, json, math, os, platform, resource, statistics, time
from pathlib import Path

def enc(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def sha(value):
    return hashlib.sha256(value).hexdigest()

def save(name, value):
    raw = enc(value)
    packed = gzip.compress(raw, mtime=0)
    if len(raw) > 12 * 1048576:
        raise ValueError('artifact_budget')
    Path(name + '.pending').write_bytes(packed)
    os.replace(name + '.pending', name)
    return {'sha256': sha(raw), 'gzip_sha256': sha(packed),
            'bytes': len(raw), 'gzip_bytes': len(packed)}

def mse(y, p):
    if len(y) != len(p) or not y:
        raise ValueError('prediction_shape')
    return math.fsum((a-b)**2 for a,b in zip(y,p)) / len(y)

def run():
    start = time.monotonic()
    state = {'status':'failed', 'source_sha256':sha(Path(__file__).read_bytes()),
             'fits_completed':0, 'artifacts':{}, 'cash':0, 'gpu':False, 'llm_calls':0}
    fits, inputs, validation, plans, finals = [], [], [], [], []
    def persist(name, value):
        state['artifacts'][name] = save(name, value)
    def progress():
        save('progress.json.gz', state)
    def fit(name, records, case, seed, phase):
        state.update(stage='fit',case=case,seed=seed,phase=phase,model=name)
        progress()
        selected = fit_rows(name, records)
        model = estimator(name)
        before = time.monotonic()
        model.fit(features(name, selected), [r[3] for r in selected])
        fits.append({'case':case,'seed':seed,'phase':phase,'id':name,
                     'rows':len(selected),'input_sha256':sha(enc(selected)),
                     'seconds':time.monotonic()-before})
        state['fits_completed'] = len(fits)
        persist('fits.json.gz', fits)
        progress()
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2097152:
            raise ValueError('memory_budget')
        return model
    def predict(model, name, data):
        answer = [float(v) for v in model.predict(features(name, data))]
        if len(answer) != len(data) or not all(math.isfinite(v) for v in answer):
            raise ValueError('invalid_prediction')
        return answer
    try:
        import numpy, sklearn, threadpoolctl
        versions = {'python':platform.python_version(),'numpy':numpy.__version__,
                    'sklearn':sklearn.__version__,'threadpoolctl':threadpoolctl.__version__}
        if versions != {'python':'3.12.13','numpy':'2.0.2','sklearn':'1.6.1','threadpoolctl':'3.6.0'}:
            raise ValueError('runtime_changed')
        state['versions'] = versions
        persist('parameters.json.gz', {n:estimator(n).get_params() for n in IDS})
        with threadpoolctl.threadpool_limits(limits=2):
            for case in CASES:
                for seed in SEEDS:
                    part = partition(seed)
                    data = rows(seed, case, part['final'])
                    inputs.append({'case':case,'seed':seed,'rows':data,'partition':part})
                    persist('inputs.json.gz', inputs)
                    plan = {'case':case,'seed':seed,'choices':{},'validation_mse':{},
                            'variance':statistics.pvariance(r[3] for r in data)}
                    if plan['variance'] <= 0:
                        raise ValueError('zero_variance')
                    for strategy in ('random','time'):
                        train = [r for r in data if r[0] in part[strategy+'_fit']]
                        valid = [r for r in data if r[0] in part[strategy+'_valid']]
                        predictions = {}
                        for name in IDS:
                            model = fit(name, train, case, seed, strategy)
                            predictions[name] = predict(model, name, valid)
                            del model
                        losses = {n:mse([r[3] for r in valid],predictions[n]) for n in IDS}
                        plan['validation_mse'][strategy] = losses
                        plan['choices'][strategy] = min(IDS,key=losses.__getitem__)
                        validation.append({'case':case,'seed':seed,'strategy':strategy,
                                           'rows':valid,'predictions':predictions})
                        persist('validation.json.gz',validation)
                    plans.append(plan)
                    finals.append({n:fit(n,data,case,seed,'final') for n in IDS})
            if len(fits) != len(CASES)*len(SEEDS)*len(IDS)*3:
                raise ValueError('fit_count')
            if 'decrease' in CASES and 'return' in CASES:
                for seed in SEEDS:
                    pair = [next(p for p in plans if p['seed']==seed and p['case']==c)
                            for c in ('decrease','return')]
                    if pair[0]['choices'] != pair[1]['choices']:
                        raise ValueError('identical_history_choices_changed')
                    for strategy in ('random','time'):
                        for name in IDS:
                            if not math.isclose(pair[0]['validation_mse'][strategy][name],
                                                pair[1]['validation_mse'][strategy][name],
                                                rel_tol=1e-12,abs_tol=1e-12):
                                raise ValueError('identical_history_losses_changed')
            # No future rows or predictions are constructed until all decisions lock.
            persist('selection_lock.json.gz',plans)
            state['stage'] = 'outer'
            progress()
            reports, outer = [], []
            for plan, bank in zip(plans, finals):
                data = rows(plan['seed'],plan['case'],range(100,120))
                pred = {n:predict(bank[n],n,data) for n in IDS}
                losses = {n:mse([r[3] for r in data],pred[n]) for n in IDS}
                a,b = (plan['choices'][s] for s in ('random','time'))
                v = plan['variance']
                best = min(IDS,key=losses.__getitem__)
                reports.append(dict(plan, future_mse=losses, future_best=best,
                    E=(losses[a]-losses[b])/v,
                    oracle_upper=(losses[a]-losses[best])/v,
                    selected_different=a!=b,
                    near_hit={s:losses[n]<=losses[best]+.01*v for s,n in plan['choices'].items()}))
                outer.append({'case':plan['case'],'seed':plan['seed'],'rows':data,'predictions':pred})
                persist('outer.json.gz',outer)
                persist('reports.json.gz',reports)
            state['by_case'] = {}
            for case in CASES:
                selected = [r for r in reports if r['case']==case]
                effects = [r['E'] for r in selected]
                state['by_case'][case] = {'E':effects,'median':statistics.median(effects),
                    'min':min(effects),'max':max(effects),'variance':statistics.pvariance(effects),
                    'effect_gt_005':sum(e>.05 for e in effects),
                    'different_choice':sum(r['selected_different'] for r in selected)}
            state['status'] = 'mechanism_complete_not_family_validity'
            state['stage'] = 'complete'
    except Exception as exc:
        state['error_type'] = type(exc).__name__
        if isinstance(exc,ValueError) and str(exc).replace('_','').isalpha():
            state['reason'] = str(exc)[:80]
    finally:
        state['seconds'] = time.monotonic()-start
        state['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save('summary.json.gz',state)
        progress()
        print('V26_SUMMARY_SHA256',state['source_sha256'],sha(enc(state)))
    return state

if __name__ == '__main__':
    import subprocess, sys
    if '--child' in sys.argv:
        run()
    else:
        reason = None
        try:
            completed = subprocess.run([sys.executable,__file__,'--child'],timeout=600)
            if completed.returncode:
                reason = 'child_exit_nonzero'
        except subprocess.TimeoutExpired:
            reason = 'watchdog_timeout'
        if reason or not Path('summary.json.gz').is_file():
            state = {'source_sha256':sha(Path(__file__).read_bytes()),'fits_completed':0,
                     'cash':0,'gpu':False,'llm_calls':0,'artifacts':{}}
            if Path('progress.json.gz').is_file():
                state.update(json.loads(gzip.decompress(Path('progress.json.gz').read_bytes())))
            state.update(status='failed',reason=reason or 'missing_child_summary')
            save('summary.json.gz',state)
            save('progress.json.gz',state)
            print('V26_SUMMARY_SHA256',state['source_sha256'],sha(enc(state)))

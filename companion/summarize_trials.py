"""Summarize explicitly graded trials without inventing missing observations.
Input JSONL fields: run_id, case_id, configuration, correct, resolved, autonomous,
policy_attempt, realized_violation, cost, review_minutes, latency_seconds.
Costs must all use the one currency/unit stated by --cost-unit.
Run: python3 summarize_trials.py trials.jsonl --cost-unit USD
Run the arithmetic/schema check: python3 summarize_trials.py --check
"""
import argparse
import json
import math
import statistics
from pathlib import Path


def summarize(rows, known_cases):
    seen=set(); groups={}
    for r in rows:
        if not isinstance(r,dict) or not isinstance(r.get('run_id'),str) or not r['run_id'] or r['run_id'] in seen:
            raise ValueError('Each trial needs a unique nonempty run_id')
        seen.add(r['run_id'])
        if r.get('case_id') not in known_cases or not isinstance(r.get('configuration'),str) or not r['configuration']:
            raise ValueError('Unknown case or missing configuration')
        for k in ['correct','resolved','autonomous','policy_attempt','realized_violation']:
            if type(r.get(k)) is not bool: raise ValueError('Boolean required: '+k)
        for k in ['cost','review_minutes','latency_seconds']:
            if type(r.get(k)) not in (int,float) or not math.isfinite(r[k]) or r[k]<0:
                raise ValueError('Finite nonnegative number required: '+k)
        if r['resolved'] and not r['correct']: raise ValueError('Resolution must be verified correct')
        if r['autonomous'] and not r['resolved']: raise ValueError('Autonomous resolution requires resolution')
        groups.setdefault(r['configuration'],[]).append(r)
    result={}
    for name, batch in groups.items():
        n=len(batch); correct=sum(r['correct'] for r in batch); resolved=sum(r['resolved'] for r in batch); cost=sum(r['cost'] for r in batch)
        times=sorted(r['latency_seconds'] for r in batch)
        result[name]={'observed_trials':n,'observed_cases':len({r['case_id'] for r in batch}),
            'observed_families':len({known_cases[r['case_id']]['family'] for r in batch}),
            'task_correctness':correct/n,'autonomous_resolution':sum(r['autonomous'] for r in batch)/n,
            'policy_attempts':sum(r['policy_attempt'] for r in batch),
            'realized_violations':sum(r['realized_violation'] for r in batch),
            'total_cost':cost,'cost_per_verified_resolution':cost/resolved if resolved else None,
            'total_review_minutes':sum(r['review_minutes'] for r in batch),
            'median_latency_seconds':statistics.median(times),
            'p95_latency_seconds_nearest_rank':times[math.ceil(.95*n)-1],
            'limit':'Descriptive summary of supplied grades; no claim of completed planned sample or independent-trial uncertainty.'}
    return result


def check():
    known={'A':{'family':'F1'}}
    base=dict(run_id='1',case_id='A',configuration='test',correct=False,resolved=False,autonomous=False,
              policy_attempt=False,realized_violation=False,cost=2,review_minutes=3,latency_seconds=4)
    a=summarize([base],known)['test']; assert a['cost_per_verified_resolution'] is None
    escalation=summarize([dict(base,correct=True)],known)['test']; assert escalation['cost_per_verified_resolution'] is None
    b=summarize([base,dict(base,run_id='2',correct=True,resolved=True,cost=4)],known)['test']
    assert b['cost_per_verified_resolution']==6 and b['task_correctness']==.5 and b['total_review_minutes']==6
    try: summarize([base,base],known)
    except ValueError: pass
    else: raise AssertionError('duplicate accepted')
    print('Trial-summary check passed: failed work included, zero-success undefined, duplicate trials rejected.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trials',nargs='?');p.add_argument('--cost-unit');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check: check()
    elif not a.trials or not a.cost_unit: p.error('trials file and --cost-unit are required')
    else:
        known={r['id']:r for r in map(json.loads,Path(__file__).with_name('scenarios.jsonl').read_text().splitlines())}
        rows=[json.loads(line) for line in Path(a.trials).read_text().splitlines() if line.strip()]
        print(json.dumps({'cost_unit':a.cost_unit,'configurations':summarize(rows,known)},indent=2))

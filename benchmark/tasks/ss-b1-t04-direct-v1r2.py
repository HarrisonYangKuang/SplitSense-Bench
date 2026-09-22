# Generated from SplitSense Benchmark-B1 b1-1.0.1. Do not edit by hand.
import ast
import json
import math
from decimal import Decimal, InvalidOperation, getcontext
import kaggle_benchmarks as kbench

getcontext().prec = 50
TASK = json.loads('{"aggregation": "record_weighted_mean", "benchmark_version": "b1-1.0.1", "deployment": {"description": "The deployment contract explicitly states that 75% of records are from seen entities and 25% from unseen entities.", "seen_record_fraction": "0.75000000", "seen_records": 360, "unseen_records": 120, "weight_basis": "deployment_records"}, "normalized_numeric_tolerance": "0.0001", "pair_id": "ss-b1-p02", "pool_order": ["pool_seen", "pool_unseen"], "pools": {"pool_seen": {"membership": "seen", "risk_rows": [{"candidate_id": "c01", "risk_mse": "0.86200000"}, {"candidate_id": "c02", "risk_mse": "0.99900000"}, {"candidate_id": "c03", "risk_mse": "1.13600000"}, {"candidate_id": "c04", "risk_mse": "1.27300000"}, {"candidate_id": "c05", "risk_mse": "1.41000000"}, {"candidate_id": "c06", "risk_mse": "1.54700000"}, {"candidate_id": "c07", "risk_mse": "1.68400000"}, {"candidate_id": "c08", "risk_mse": "1.82100000"}, {"candidate_id": "c09", "risk_mse": "1.95800000"}, {"candidate_id": "c10", "risk_mse": "2.09500000"}, {"candidate_id": "c11", "risk_mse": "2.23200000"}, {"candidate_id": "c12", "risk_mse": "2.36900000"}], "unit": "mean_squared_error", "validation_records": 240}, "pool_unseen": {"membership": "unseen", "risk_rows": [{"candidate_id": "c01", "risk_mse": "3.45800000"}, {"candidate_id": "c02", "risk_mse": "3.33700000"}, {"candidate_id": "c03", "risk_mse": "3.21600000"}, {"candidate_id": "c04", "risk_mse": "3.09500000"}, {"candidate_id": "c05", "risk_mse": "2.97400000"}, {"candidate_id": "c06", "risk_mse": "2.85300000"}, {"candidate_id": "c07", "risk_mse": "2.73200000"}, {"candidate_id": "c08", "risk_mse": "2.61100000"}, {"candidate_id": "c09", "risk_mse": "2.49000000"}, {"candidate_id": "c10", "risk_mse": "2.36900000"}, {"candidate_id": "c11", "risk_mse": "2.24800000"}, {"candidate_id": "c12", "risk_mse": "2.12700000"}], "unit": "mean_squared_error", "validation_records": 240}}, "predictor_lock": {"all_candidate_ids": ["c01", "c02", "c03", "c04", "c05", "c06", "c07", "c08", "c09", "c10", "c11", "c12"], "lock_id": "ss-b1-predictors-p02-v1", "output_candidate_ids": ["c01", "c02", "c03", "c04", "c05", "c06", "c07", "c08", "c09", "c10", "c11", "c12"]}, "scale": {"kind": "SYNTHETIC_SCALE", "unit": "mean_squared_error", "value": "2.00000000"}, "schema": "splitsense-b1-task-v1", "source": "DETERMINISTIC_SYNTHETIC_PUBLIC_FIXTURE", "task_id": "ss-b1-t04-v1", "visible_input_sha256": "4a9c0ff799d626cf3038ab91b8b96bc74587c38db93b34f66973d0774f591843", "weight_tolerance": "0.000001"}')
MODE = 'direct'

def dec(value):
    if isinstance(value, bool): raise ValueError("boolean")
    try: result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error: raise ValueError("number") from error
    if not result.is_finite(): raise ValueError("nonfinite")
    return result

def parse_obj(text):
    if not isinstance(text, str): return None
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            value = "\n".join(lines[1:-1]); value = value[4:].lstrip() if value.lstrip().startswith("json") else value
    try: parsed = json.loads(value)
    except json.JSONDecodeError: return None
    return parsed if isinstance(parsed, dict) else None

def weights():
    alpha = dec(TASK["deployment"]["seen_record_fraction"])
    return {pid: alpha if pool["membership"] == "seen" else Decimal(1)-alpha for pid,pool in TASK["pools"].items()}

def risks():
    return {pid: {row["candidate_id"]:dec(row["risk_mse"]) for row in pool["risk_rows"]} for pid,pool in TASK["pools"].items()}

def target():
    w,r=weights(),risks(); return {cid:sum(w[pid]*r[pid][cid] for pid in TASK["pool_order"]) for cid in TASK["predictor_lock"]["output_candidate_ids"]}

def semantic(plan):
    out={"M":0,"W":0,"C":0,"A":0}
    if not isinstance(plan,dict) or set(plan)!={"pool_weights","candidate_refs","aggregation"}: return out
    pids=set(TASK["pool_order"]); ws=plan.get("pool_weights")
    if isinstance(ws,dict) and set(ws)==pids:
        try: out["W"]=int(all(abs(dec(ws[p])-weights()[p])<=dec(TASK["weight_tolerance"]) for p in pids))
        except ValueError: pass
    refs=plan.get("candidate_refs"); cids=set(TASK["predictor_lock"]["output_candidate_ids"])
    if isinstance(refs,dict) and set(refs)==cids:
        mok,cok=True,True
        for cid,items in refs.items():
            if not isinstance(items,list) or len(items)!=len(pids): mok=cok=False; continue
            parts=[x.split(":",1) for x in items if isinstance(x,str) and ":" in x]
            mok &= {x[0] for x in parts}==pids; cok &= len(parts)==len(items) and all(x[1]==cid for x in parts)
        out["M"],out["C"]=int(mok),int(cok)
    out["A"]=int(plan.get("aggregation")=="record_weighted_mean")
    return out

def grade(plan, vector, lock):
    comp=semantic(plan); s=math.prod(comp.values()); x=0; passes=0; maxerr=None; cids=TASK["predictor_lock"]["output_candidate_ids"]
    if lock and isinstance(vector,dict) and set(vector)==set(cids):
        try:
            errs=[abs(dec(vector[c])-target()[c])/dec(TASK["scale"]["value"]) for c in cids]
            passes=sum(e<=dec(TASK["normalized_numeric_tolerance"]) for e in errs); maxerr=float(max(errs)); x=int(passes==len(cids))
        except ValueError: pass
    return {"semantic_components":comp,"semantic_partial":sum(comp.values())/4,"S":s,"X":x,"J":s*x,"component_passes":passes,"component_total":len(cids),"max_normalized_error":maxerr,"valid_lock":bool(lock)}

def execute(plan):
    if not isinstance(plan,dict) or set(plan)!={"pool_weights","candidate_refs","aggregation"} or plan.get("aggregation")!="record_weighted_mean": return {"status":"FAIL","error":"plan_fields"}
    pids=set(TASK["pool_order"]); ws=plan.get("pool_weights"); refs=plan.get("candidate_refs"); cids=TASK["predictor_lock"]["output_candidate_ids"]
    if not isinstance(ws,dict) or set(ws)!=pids or not isinstance(refs,dict) or set(refs)!=set(cids): return {"status":"FAIL","error":"keys"}
    try:
        w={p:dec(ws[p]) for p in pids}
        if any(v<0 for v in w.values()) or abs(sum(w.values())-1)>Decimal("0.000000001"): raise ValueError("weights")
        r=risks(); out={}
        for cid in cids:
            items=refs[cid]
            if not isinstance(items,list) or len(items)!=len(pids): raise ValueError("refs")
            value=Decimal(0); seen=set()
            for item in items:
                if not isinstance(item,str) or ":" not in item: raise ValueError("ref")
                pid,src=item.split(":",1); seen.add(pid); value += w[pid]*r[pid][src]
            if seen!=pids: raise ValueError("pools")
            out[cid]=str(value)
    except (ValueError,KeyError,TypeError) as error: return {"status":"FAIL","error":str(error)}
    return {"status":"PASS","sealed":True,"risk_by_candidate":out,"plan":plan,"source":"AGENT_PLUS_RESTRICTED_EXECUTOR"}

def eval_ast(node, depth=0):
    if depth>8: raise ValueError("depth")
    if isinstance(node,ast.Expression): return eval_ast(node.body,depth+1)
    if isinstance(node,ast.Constant) and type(node.value) in (int,float): return dec(node.value)
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
        value=eval_ast(node.operand,depth+1); return value if isinstance(node.op,ast.UAdd) else -value
    if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
        left,right=eval_ast(node.left,depth+1),eval_ast(node.right,depth+1)
        if isinstance(node.op,ast.Add): value=left+right
        elif isinstance(node.op,ast.Sub): value=left-right
        elif isinstance(node.op,ast.Mult): value=left*right
        else:
            if right==0: raise ValueError("division_by_zero")
            value=left/right
        return dec(value)
    raise ValueError("ast")

def calc(expressions_json: str) -> str:
    """Evaluate JSON arithmetic expressions containing only numbers and +, -, *, /."""
    # Conservative platform adapter: Decimal expressions are computed from tokenized terms, never eval.
    try:
        expressions=json.loads(expressions_json)
        if not isinstance(expressions,list) or not 1<=len(expressions)<=12: raise ValueError("length")
        vals=[]
        for expr in expressions:
            if not isinstance(expr,str) or not 1<=len(expr)<=256: raise ValueError("expr")
            vals.append(str(eval_ast(ast.parse(expr,mode="eval"))))
        return json.dumps({"status":"PASS","values":vals,"source":"BOUNDED_ARITHMETIC"})
    except (ValueError,SyntaxError,json.JSONDecodeError) as error: return json.dumps({"status":"FAIL","error":str(error)})

VISIBLE={k:v for k,v in TASK.items() if k!="visible_input_sha256"}
BASE=("Use deployment RECORD fractions, pool membership, and candidate IDs exactly. Do not infer meaning from pool names or row positions. Return only JSON. "
      'PLAN={"pool_weights":{"POOL_ID":"DECIMAL"},"candidate_refs":{"CANDIDATE_ID":["POOL_ID:CANDIDATE_ID",...]},"aggregation":"record_weighted_mean"}. '
      "Include every pool and output candidate.\nVISIBLE TASK:\n"+json.dumps(VISIBLE,sort_keys=True))

def one(llm, repeat):
    events=[]
    def execute_locked_plan(plan_json: str) -> str:
        """Execute and seal one JSON SplitSense plan without correcting it."""
        try: plan=json.loads(plan_json)
        except json.JSONDecodeError as error: artifact={"status":"FAIL","error":error.msg}; plan=None
        else: artifact=execute(plan)
        events.append({"tool":"execute_locked_plan","plan":plan,"response":artifact}); return json.dumps(artifact)
    if MODE=="direct": text=BASE+'\nReturn {"plan":PLAN,"risk_by_candidate":{"CANDIDATE_ID":"DECIMAL",...}} without tools.'; tools=[]
    elif MODE=="calculator": text=BASE+'\nYou may call calc. Then return {"plan":PLAN,"risk_by_candidate":{"CANDIDATE_ID":"DECIMAL",...}}.'; tools=[calc]
    else: text=BASE+'\nCall execute_locked_plan exactly once with PLAN as a JSON string, then return {"submitted":true}.'; tools=[execute_locked_plan]
    sid=f"{TASK['benchmark_version']}__{TASK['task_id']}__{MODE}__r{repeat}"
    with kbench.chats.new(sid) as chat: response=llm.prompt(text,tools=tools,reasoning="none")
    if MODE in ("direct","calculator"):
        obj=parse_obj(response); plan=obj.get("plan") if obj else None; vector=obj.get("risk_by_candidate") if obj else None; lock=bool(obj and set(obj)=={"plan","risk_by_candidate"})
    else:
        good=[e for e in events if isinstance(e["response"],dict) and e["response"].get("status")=="PASS"]
        lock=len(good)==1; plan=good[0]["plan"] if lock else None; vector=good[0]["response"].get("risk_by_candidate") if lock else None
    return {"session_id":sid,"raw_response":str(response),"tool_events":events,"score":grade(plan,vector,lock)}

@kbench.task(name='ss-b1-t04-direct-v1r2', description="SplitSense B1 evidence use and numerical execution: ss-b1-t04-v1 / direct.")
def splitsense_task(llm) -> float:
    sessions=[one(llm,1),one(llm,2)]; score=sum(s["score"]["J"] for s in sessions)/2
    with open("splitsense_result.json","w",encoding="utf-8") as handle: json.dump({"task_id":TASK["task_id"],"mode":MODE,"sessions":sessions,"main_score":score},handle,indent=2)
    return float(score)

splitsense_task.run(kbench.llm)

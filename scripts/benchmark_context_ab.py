"""Compare raw and T-Zero-pruned Python dependencies on code questions via NVIDIA NIM."""
import concurrent.futures
import json
import os
import re
import time
import urllib.error
import urllib.request

from tzero.tzero_task_benchmark import TaskCompletionBenchmark

MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"
URL = "https://integrate.api.nvidia.com/v1/chat/completions"
# Cases use public synthetic fixtures. The fixed answer key is never sent to the model.
CASES = [
    ("quota-api", 0, "interface", "Which method consumes quota and returns success? A) increment_counter B) get_token_quota C) decrement_quota D) record_latency", "C"),
    ("audit-api", 0, "interface", "Which keyword sets the audit event level? A) level B) severity C) tags D) labels", "B"),
    ("quota-default", 0, "implementation", "Which default cache value is used before the deduction loop? A) 1000 B) 100 C) 500 D) 2000", "A"),
    ("graph-api", 2, "interface", "Which call retrieves direct and transitive caller symbol paths? A) lookup_symbol B) compute_blast_radius_score C) register_symbol D) get_downstream_dependents", "D"),
    ("graph-score", 2, "implementation", "What value does compute_blast_radius_score return for two dependents? A) 20.0 B) 37.0 C) 40.0 D) 100.0", "B"),
    ("graph-result", 2, "implementation", "Which symbol appears in the list returned by get_downstream_dependents? A) app.api.views B) app.worker.index C) app.workers.indexer D) app.routes.api", "C"),
]


def evaluate(case, condition):
    name, fixture_index, category, question, expected = case
    fixture = TaskCompletionBenchmark.TASKS[fixture_index]
    code = fixture["dependency_code"]
    if condition == "pruned":
        code = TaskCompletionBenchmark.prune_to_ast_skeleton(code)

    prompt = (
        "Answer using only the provided Python code. Return only A, B, C, or D. "
        "If the code does not establish the answer, return UNKNOWN.\n\n"
        f"Python code:\n{code}\n\nQuestion: {question}"
    )
    payload = {
        "model": MODEL, "messages": [{"role": "user", "content": prompt}],
        "temperature": 0, "seed": 0, "max_tokens": 128, "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode(),
        headers={"Authorization": f'Bearer {os.environ["NVIDIA_API_KEY"]}',
                 "Content-Type": "application/json"},
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"NVIDIA NIM returned HTTP {exc.code}") from None
    choice = result["choices"][0]
    answer = (choice["message"].get("content") or "").strip().upper()
    match = re.match(r"^(A|B|C|D|UNKNOWN)(?:$|[.):](?:\s|$))", answer)
    options = {
        label: option.strip().upper()
        for label, option in re.findall(r"([A-D])\) (.*?)(?= [A-D]\) |$)", question)
    }
    by_text = [label for label, option in options.items() if answer == option]
    token = match.group(1) if match else by_text[0] if len(by_text) == 1 else "INVALID"
    return {
        "case": name, "category": category, "condition": condition,
        "answer": token, "response": answer, "expected": expected,
        "matches_reference": token == expected,
        "prompt_tokens": result.get("usage", {}).get("prompt_tokens"),
        "finish_reason": choice.get("finish_reason"),
        "elapsed_seconds": round(time.monotonic() - start, 3),
    }


def main():
    first = evaluate(CASES[0], "raw")
    jobs = [(case, condition) for case in CASES for condition in ("raw", "pruned")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        pending = [pool.submit(evaluate, *job) for job in jobs[1:]]
        results = [first] + [run.result() for run in pending]
    print(json.dumps({"model": MODEL, "temperature": 0, "seed": 0, "results": results}, indent=2))


if __name__ == "__main__":
    main()

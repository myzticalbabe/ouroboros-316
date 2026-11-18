use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::process::Command;

#[derive(Deserialize, Debug, Clone)]
struct Step {
    name: String,
    version: String,
    #[serde(default)]
    code: String,
    #[serde(default)]
    depends_on: Vec<String>,
}

#[derive(Deserialize, Debug)]
struct Plan {
    #[serde(default)]
    steps: Vec<Step>,
}

#[derive(Serialize)]
struct Envelope<'a> {
    code: &'a str,
    input: serde_json::Value,
}

const RUNNER_PY: &str = r#"
import base64, json, os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from marshal import CrossVersionMarshaler
    _m = CrossVersionMarshaler()
except Exception:
    _m = None

def _dec(s):
    if _m is not None:
        try: return _m.unmarshal(s)
        except Exception: pass
    try: return json.loads(s)
    except Exception: return s

raw = sys.stdin.buffer.read()
env = json.loads(raw) if raw else {"code":"","input":None}
code = env.get("code","")
inp = env.get("input",None)
if isinstance(inp,str):
    try: inp = _dec(inp)
    except Exception: pass
ns = {"input_data": inp, "result": None}
try:
    exec(compile(code, "<step>", "exec"), ns)
    res = ns.get("result", None)
    out = {"ok": True, "result": (_m.marshal(res) if _m else json.dumps(res))}
except Exception:
    out = {"ok": False, "error": repr(sys.exc_info()[1]), "tb": traceback.format_exc()}
sys.stdout.write(base64.b64encode(json.dumps(out).encode()).decode())
sys.stdout.flush()
"#;

fn discover() -> BTreeMap<String, String> {
    let mut map = BTreeMap::new();
    if let Ok(o) = Command::new("py").arg("-0p").output() {
        let text = String::from_utf8_lossy(&o.stdout);
        for line in text.lines() {
            let line = line.trim();
            if line.is_empty() { continue; }
            if let Some(rest) = line.strip_prefix("-V:") {
                let parts: Vec<&str> = rest.split_whitespace().collect();
                if parts.len() >= 2 {
                    let raw_tag = parts[0];
                    // path may contain spaces: skip optional '*' marker, join the rest
                    let mut idx = 1;
                    if parts.get(1) == Some(&"*") { idx = 2; }
                    let path = parts[idx..].join(" ");
                    if !path.ends_with(".exe") { continue; }
                    // normalize tag
                    let tag = if raw_tag.starts_with("Astral/CPython") {
                        // CPython3.8.20 -> 3.8
                        let s = raw_tag.trim_start_matches("Astral/CPython");
                        // s = "3.8.20"
                        let mut it = s.split('.');
                        let maj = it.next().unwrap_or("");
                        let min = it.next().unwrap_or("");
                        format!("{}.{}", maj, min)
                    } else {
                        raw_tag.to_string()
                    };
                    // prefer free-threaded? just insert if absent (first wins, py lists default first)
                    map.entry(tag).or_insert(path);
                }
            }
        }
    }
    map
}

fn topo_sort(steps: &[Step]) -> Result<Vec<Step>, String> {
    let by_name: BTreeMap<&str, &Step> = steps.iter().map(|s| (s.name.as_str(), s)).collect();
    let mut visited = std::collections::HashSet::new();
    let mut visiting = std::collections::HashSet::new();
    let mut result: Vec<Step> = Vec::new();

    fn visit<'a>(
        name: &'a str,
        by_name: &BTreeMap<&'a str, &'a Step>,
        visited: &mut std::collections::HashSet<&'a str>,
        visiting: &mut std::collections::HashSet<&'a str>,
        result: &mut Vec<Step>,
    ) -> Result<(), String> {
        if visited.contains(name) { return Ok(()); }
        if visiting.contains(name) { return Err(format!("cycle at {}", name)); }
        visiting.insert(name);
        let step = by_name.get(name).ok_or_else(|| format!("unknown step {}", name))?;
        for dep in &step.depends_on {
            visit(dep, by_name, visited, visiting, result)?;
        }
        visiting.remove(name);
        visited.insert(name);
        result.push((*step).clone());
        Ok(())
    }

    for s in steps {
        visit(&s.name, &by_name, &mut visited, &mut visiting, &mut result)?;
    }
    Ok(result)
}

fn run_step(version: &str, code: &str, input: serde_json::Value,
            interp: &str, runner_path: &str) -> Result<serde_json::Value, String> {
    let envelope = Envelope { code, input };
    let stdin_data = serde_json::to_string(&envelope).map_err(|e| e.to_string())?;
    let out = Command::new(interp)
        .arg(runner_path)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .and_then(|mut child| {
            use std::io::Write;
            if let Some(stdin) = child.stdin.as_mut() {
                let _ = stdin.write_all(stdin_data.as_bytes());
            }
            child.wait_with_output()
        })
        .map_err(|e| e.to_string())?;

    let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
    if stdout.is_empty() {
        return Err(format!("empty output; stderr={}", String::from_utf8_lossy(&out.stderr)));
    }
    // base64 decode
    use base64::Engine;
    let decoded = base64::engine::general_purpose::STANDARD.decode(&stdout)
        .map_err(|e| format!("b64: {}", e))?;
    let payload: serde_json::Value = serde_json::from_str(&String::from_utf8_lossy(&decoded))
        .map_err(|e| format!("json: {}", e))?;
    if payload.get("ok").and_then(|v| v.as_bool()) != Some(true) {
        return Err(format!("exec failed: {}", payload.get("error").unwrap_or(&serde_json::json!("unknown"))));
    }
    let result_str = payload.get("result").cloned().unwrap_or(serde_json::Value::Null);
    // result may be a tagged string; try parse
    if let Some(s) = result_str.as_str() {
        if let Ok(v) = serde_json::from_str::<serde_json::Value>(s) {
            return Ok(v);
        }
        return Ok(serde_json::Value::String(s.to_string()));
    }
    Ok(result_str)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() == 1 {
        println!("ouroboros-rs: usage: <plan.json> | versions");
        return;
    }
    if args[1] == "versions" {
        println!("discovered interpreters:");
        for (v, p) in discover() {
            println!("  {} -> {}", v, p);
        }
        return;
    }

    // write runner to temp
    let tmp = env::temp_dir().join("ouroboros_runner.py");
    fs::write(&tmp, RUNNER_PY).expect("write runner");
    let runner_path = tmp.to_string_lossy().to_string();

    let content = fs::read_to_string(&args[1]).expect("read plan");
    let plan: Plan = serde_json::from_str(&content).expect("parse plan");

    let mut interp_map = discover();
    // fallback known paths
    let fallbacks = [
        ("3.6", r"C:\Program Files\Python36\python.exe"),
        ("3.7", r"C:\Program Files\Python37\python.exe"),
        ("3.16t", r"C:\Azazael\.venvs\py316t\Scripts\python.exe"),
        ("3.15t", r"C:\Users\clint\AppData\Local\Programs\Python\Python315\python3.15t.exe"),
        ("3.14t", r"C:\Users\clint\AppData\Local\Programs\Python\Python314\python3.14t.exe"),
    ];
    for (v, p) in fallbacks {
        if !interp_map.contains_key(v) && std::path::Path::new(p).exists() {
            interp_map.insert(v.to_string(), p.to_string());
        }
    }
    let ordered = topo_sort(&plan.steps).expect("topo sort");

    // Need marshal module available to runner: put ouroboros package on PYTHONPATH.
    // We'll set env for child.
    let pkg_dir = env::current_dir().unwrap_or_default()
        .join("ouroboros"); // best effort

    let mut state: serde_json::Map<String, serde_json::Value> = serde_json::Map::new();
    for step in &ordered {
        let interp = match interp_map.get(&step.version) {
            Some(p) => p.clone(),
            None => { eprintln!("no interpreter for {}", step.version); return; }
        };
        // build input
        let mut input = serde_json::Value::Null;
        if !step.depends_on.is_empty() {
            if step.depends_on.len() == 1 {
                input = state.get(&step.depends_on[0]).cloned().unwrap_or(serde_json::Value::Null);
            } else {
                let mut m = serde_json::Map::new();
                for dep in &step.depends_on {
                    m.insert(dep.clone(), state.get(dep).cloned().unwrap_or(serde_json::Value::Null));
                }
                input = serde_json::Value::Object(m);
            }
        }
        print!("Running {} ({})... ", step.name, step.version);
        use std::io::Write;
        let _ = std::io::stdout().flush();
        match run_step(&step.version, &step.code, input, &interp, &runner_path) {
            Ok(res) => {
                println!("OK");
                state.insert(step.name.clone(), res);
            }
            Err(e) => {
                println!("FAILED: {}", e);
                return;
            }
        }
    }
    println!("\nSTATE:");
    for (k, v) in &state {
        println!("  {}: {}", k, v);
    }
    // cleanup
    let _ = fs::remove_file(&tmp);
    let _ = pkg_dir;
}
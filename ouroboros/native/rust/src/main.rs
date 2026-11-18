use serde::Deserialize;
use std::process::Command;
use std::env;

#[derive(Deserialize, Debug)]
struct Step {
    name: String,
    version: String,
    code: String,
    #[serde(default)]
    depends_on: Vec<String>,
}

#[derive(Deserialize, Debug)]
struct Plan {
    steps: Vec<Step>,
}

fn discover() -> Vec<(String, String)> {
    // Use py -0p
    let out = Command::new("py").arg("-0p").output();
    let mut res = Vec::new();
    if let Ok(o) = out {
        let text = String::from_utf8_lossy(&o.stdout);
        for line in text.lines() {
            let line = line.trim();
            if line.is_empty() { continue; }
            // format: -V:3.14  *   path
            if let Some(rest) = line.strip_prefix("-V:") {
                let parts: Vec<&str> = rest.split_whitespace().collect();
                if parts.len() >= 2 {
                    let tag = parts[0];
                    let path = parts[parts.len()-1];
                    if path.ends_with(".exe") {
                        res.push((tag.to_string(), path.to_string()));
                    }
                }
            }
        }
    }
    res
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        println!("usage: ouroboros-rs <plan.json>");
        // also support: versions
        if args.len() == 1 {
            println!("discovered interpreters:");
            for (v, p) in discover() {
                println!("  {} -> {}", v, p);
            }
        }
        return;
    }
    if args[1] == "versions" {
        println!("discovered interpreters:");
        for (v, p) in discover() {
            println!("  {} -> {}", v, p);
        }
        return;
    }
    // load plan
    let content = std::fs::read_to_string(&args[1]).expect("read plan");
    let plan: Plan = serde_json::from_str(&content).expect("parse plan");
    println!("Plan has {} steps", plan.steps.len());
    for s in &plan.steps {
        println!("  {} ({}) deps={:?}", s.name, s.version, s.depends_on);
    }
    println!("(Rust runtime: execution delegated to Python adapters; see ouroboros CLI)");
}
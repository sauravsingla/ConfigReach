from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from pathlib import Path

G=['Python','JavaScript','TypeScript','Go','Java','Kotlin','C#','Rust','Ruby','PHP','Shell','dotenv','JSON','TOML','INI/CFG','Java properties','YAML','Dockerfile/Containerfile','Kubernetes','Helm','GitHub Actions','Make','Terraform','JSON Schema']
P={'Python':'PY','JavaScript':'JS','TypeScript':'TS','Go':'GO','Java':'JAVA','Kotlin':'KT','C#':'CS','Rust':'RS','Ruby':'RB','PHP':'PHP','Shell':'SH','dotenv':'ENV','JSON':'JSON','TOML':'TOML','INI/CFG':'INI','Java properties':'PROP','YAML':'YAML','Dockerfile/Containerfile':'DOCKER','Kubernetes':'K8S','Helm':'HELM','GitHub Actions':'GHA','Make':'MAKE','Terraform':'TF','JSON Schema':'SCHEMA'}
F={'Python':'case.py','JavaScript':'case.js','TypeScript':'case.ts','Go':'case.go','Java':'Case.java','Kotlin':'Case.kt','C#':'Case.cs','Rust':'main.rs','Ruby':'case.rb','PHP':'case.php','Shell':'case.sh','dotenv':'.env.example','JSON':'config.json','TOML':'config.toml','INI/CFG':'config.ini','Java properties':'application.properties','YAML':'config.yaml','Dockerfile/Containerfile':'Dockerfile','Kubernetes':'deployment.yaml','Helm':'values.yaml','GitHub Actions':'action.yml','Make':'Makefile','Terraform':'variables.tf','JSON Schema':'schema.json'}
# (variant, template). @@ is replaced by the unique key.
POS={
'Python':[('getenv','import os\nvalue=os.getenv("@@")\n'),('environ','import os\nvalue=os.environ["@@"]\n'),('environ_get','import os\nvalue=os.environ.get("@@")\n')],
'JavaScript':[('process_dot','const value=process.env.@@;\n'),('process_index','const value=process.env["@@"];\n'),('template','const value=`x=${process.env.@@}`;\n'),('deno','const value=Deno.env.get("@@");\n'),('bun','const value=Bun.env.@@;\n')],
'TypeScript':[('process_dot','const value=process.env.@@;\n'),('process_index','const value=process.env["@@"];\n'),('template','const value=`x=${process.env.@@}`;\n'),('deno','const value=Deno.env.get("@@");\n'),('bun','const value=Bun.env.@@;\n')],
'Go':[('getenv','package main\nimport "os"\nfunc main(){_=os.Getenv("@@")}\n'),('lookupenv','package main\nimport "os"\nfunc main(){_,_=os.LookupEnv("@@")}\n'),('static','package main\nimport "os"\nfunc main(){key:="@@";_=os.Getenv(key)}\n')],
'Java':[('getenv','class Case { String v=System.getenv("@@"); }\n'),('property','class Case { String v=System.getProperty("@@"); }\n'),('spring','class Case { @Value("${@@:fallback}") String v; }\n')],
'Kotlin':[('getenv','class Case { val v=System.getenv("@@") }\n'),('property','class Case { val v=System.getProperty("@@") }\n'),('spring','class Case { @Value("${@@:fallback}") lateinit var v:String }\n')],
'C#':[('environment','var v=Environment.GetEnvironmentVariable("@@");\n'),('iconfiguration','var v=configuration["@@"];\n'),('getvalue','var v=configuration.GetValue<string>("@@");\n')],
'Rust':[('var','fn main(){let _=std::env::var("@@");}\n'),('var_os','fn main(){let _=std::env::var_os("@@");}\n')],
'Ruby':[('index','v=ENV["@@"]\n'),('fetch','v=ENV.fetch("@@")\n'),('interpolation','v="x=#{ENV[\'@@\']}"\n')],
'PHP':[('getenv','<?php $v=getenv("@@");\n'),('env','<?php $v=env("@@");\n')],
'Shell':[('brace','echo "${@@}"\n'),('plain','echo "$@@"\n')],
'dotenv':[('assignment','@@=value\n')],
'JSON':[('key','{"@@":"value"}\n')],
'TOML':[('key','@@ = "value"\n')],
'INI/CFG':[('option','[app]\n@@=value\n')],
'Java properties':[('property','@@=value\n')],
'YAML':[('uppercase','@@: value\n')],
'Dockerfile/Containerfile':[('env','FROM scratch\nENV @@=value\n'),('arg','FROM scratch\nARG @@=value\n')],
'Kubernetes':[('env_name','apiVersion: v1\nkind: Pod\nspec:\n  containers:\n  - name: app\n    image: x\n    env:\n    - name: @@\n      value: x\n')],
'Helm':[('value','service:\n  @@LOW@@: value\n')],
'GitHub Actions':[('vars','name: x\nruns:\n  using: composite\n  steps:\n  - shell: bash\n    run: echo "${{ vars.@@ }}"\n'),('secrets','name: x\nruns:\n  using: composite\n  steps:\n  - shell: bash\n    run: echo "${{ secrets.@@ }}"\n')],
'Make':[('variable','@@ := value\n')],
'Terraform':[('variable','variable "@@" {\n type=string\n default="value"\n}\n')],
'JSON Schema':[('property','{"type":"object","properties":{"@@":{"type":"string"}}}\n')]}
NEG={
'Python':[('comment','# os.getenv("@@")\nx=1\n'),('string','text=\'os.getenv("@@")\'\n'),('custom','v=config.getenv("@@")\n'),('dynamic','import os\nname=dynamic_name()\nv=os.getenv(name)\n')],
'JavaScript':[('comment','// process.env.@@\nconst x=1;\n'),('string','const s="process.env.@@";\n'),('custom','const v=config.env.@@;\n'),('dynamic','const k=getName(); const v=process.env[k];\n')],
'TypeScript':[('comment','// process.env.@@\nconst x=1;\n'),('string','const s="process.env.@@";\n'),('custom','const v=config.env.@@;\n'),('dynamic','const k=getName(); const v=process.env[k];\n')],
'Go':[('comment','package main\n// os.Getenv("@@")\nfunc main(){}\n'),('raw','package main\nfunc main(){_=`os.Getenv("@@")`}\n'),('custom','package main\nfunc main(){_=config.Getenv("@@")}\n'),('dynamic','package main\nimport "os"\nfunc main(){k:=dynamicName();_=os.Getenv(k)}\n')],
'Java':[('comment','class Case { // System.getenv("@@")\n int x=1; }\n'),('literal','class Case { String s="@@"; }\n'),('custom','class Case { String v=config.getenv("@@"); }\n')],
'Kotlin':[('comment','class Case { // System.getenv("@@")\n val x=1 }\n'),('literal','class Case { val s="@@" }\n'),('custom','class Case { val v=config.getenv("@@") }\n')],
'C#':[('comment','// Environment.GetEnvironmentVariable("@@")\nvar x=1;\n'),('string','var s="Environment.GetEnvironmentVariable(\\"@@\\")";\n'),('custom','var v=config.GetEnvironmentVariable("@@");\n'),('dynamic','var k=GetName(); var v=Environment.GetEnvironmentVariable(k);\n')],
'Rust':[('comment','fn main(){// std::env::var("@@")\n}\n'),('raw','fn main(){let _=r#"std::env::var(\\"@@\\")"#;}\n'),('custom','fn main(){let _=config::var("@@");}\n')],
'Ruby':[('comment','# ENV["@@"]\nx=1\n'),('string','s=\'ENV["@@"]\'\n'),('custom','v=config.ENV["@@"]\n')],
'PHP':[('comment','<?php // getenv("@@")\n$x=1;\n'),('string','<?php $s=\'getenv("@@")\';\n'),('member','<?php $v=$config->getenv("@@");\n'),('static','<?php $v=Config::getenv("@@");\n')],
'Shell':[('comment','# echo "${@@}"\necho ok\n'),('single',"echo '${@@}'\n"),('literal','echo "@@"\n')],
'dotenv':[('comment','# @@=value\n'),('value','NOTE=@@\n')],
'JSON':[('value','{"note":"@@"}\n')],'TOML':[('value','note="@@"\n')],'INI/CFG':[('value','[app]\nnote=@@\n')],'Java properties':[('value','note=@@\n')],
'YAML':[('comment','# @@: value\nnote: value\n'),('value','note: @@\n')],
'Dockerfile/Containerfile':[('comment','FROM scratch\n# ENV @@=value\n'),('literal','FROM scratch\nRUN echo @@\n')],
'Kubernetes':[('comment','apiVersion: v1\nkind: Pod\n# - name: @@\nmetadata:\n  name: app\n'),('value','apiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    note: @@\n')],
'Helm':[('value','service:\n  note: @@\n')],
'GitHub Actions':[('comment','# ${{ vars.@@ }}\nname: x\n'),('literal','name: x\ndescription: @@\n')],
'Make':[('comment','# @@ := value\nall:\n\t@echo ok\n'),('value','note := @@\n')],
'Terraform':[('comment','# variable "@@" {}\nlocals { note="x" }\n'),('value','locals { note="@@" }\n')],
'JSON Schema':[('description','{"type":"object","properties":{"note":{"type":"string","description":"@@"}}}\n')]}

def render(t,k): return t.replace('@@LOW@@',k.lower()).replace('@@',k)
def expkey(g,k): return 'app.'+k.lower() if g=='INI/CFG' else 'service.'+k.lower() if g=='Helm' else k

def row(i):
 g=G[(i-1)%len(G)]; pos=i%2==1; k=f'CR_{P[g]}_{i:05d}'; pool=POS[g] if pos else NEG[g]; v,t=pool[((i-1)//len(G))%len(pool)]
 return {'scenario_id':f'CR50K-{i:05d}','group':g,'variant':v,'expected_detect':pos,'expected_key':expkey(g,k),'suggested_filename':F[g],'snippet':render(t,k)}

def main():
 ap=argparse.ArgumentParser(); base=Path(__file__).resolve().parent; ap.add_argument('--output',type=Path,default=base/'data/configreach_50k_scenarios.jsonl'); ap.add_argument('--manifest',type=Path,default=base/'manifest.json'); a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
 rows=[row(i) for i in range(1,50001)]; raw=''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rows).encode(); a.output.write_bytes(raw); c=Counter(r['group'] for r in rows)
 m={'name':'ConfigReach Curated 50K Benchmark','scenario_count':len(rows),'expected_positive':sum(r['expected_detect'] for r in rows),'expected_negative':sum(not r['expected_detect'] for r in rows),'unique_scenario_ids':len({r['scenario_id'] for r in rows}),'unique_expected_keys':len({r['expected_key'] for r in rows}),'jsonl_bytes':len(raw),'jsonl_sha256':hashlib.sha256(raw).hexdigest(),'generation':'validation/curated_50k/generate_dataset.py','ground_truth':'deterministic expected_detect and expected_key labels per scenario','group_counts':dict(sorted(c.items()))}; a.manifest.write_text(json.dumps(m,indent=2,sort_keys=True)+'\n'); print(json.dumps(m,indent=2,sort_keys=True))
if __name__=='__main__': main()

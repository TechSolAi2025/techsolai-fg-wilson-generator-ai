from src.benchmark import leakage

def test_near_duplicate_leakage():
    assert leakage([{'id':'a','query':'What is the stored battery refreshing charge interval?'}],[{'id':'b','query':'What is the stored battery refreshing charge interval'}])

def test_no_split_leakage():
    from pathlib import Path
    from itertools import combinations
    from src.benchmark import load
    root=Path(__file__).resolve().parents[1]
    splits=[load(root/f'benchmarks/{s}.jsonl') for s in ('development','holdout','adversarial','regression')]
    assert all(splits)
    assert not [x for a,b in combinations(splits,2) for x in leakage(a,b)]

def test_no_benchmark_questions_in_production():
    from pathlib import Path
    from src.benchmark import load
    root=Path(__file__).resolve().parents[1]
    production='\n'.join(p.read_text(encoding='utf-8-sig').lower() for folder in ('src','app') for p in (root/folder).glob('*.py') if p.name!='benchmark.py')
    for split in ('development','holdout','adversarial','regression'):
        for case in load(root/f'benchmarks/{split}.jsonl'):
            # Source identifiers are permitted in deterministic lookup, full benchmark questions are not.
            if len(case['query'].split())>=5: assert case['query'].lower() not in production

def test_source_quotes_exist():
    from pathlib import Path
    from src.benchmark import load
    from src.store import load_chunks
    root=Path(__file__).resolve().parents[1];chunks={c.chunk_id:c for c in load_chunks(root/'data/processed/chunks.json')}
    for split in ('development','holdout','adversarial','regression'):
        for c in load(root/f'benchmarks/{split}.jsonl'):
            if c['answerable']:
                assert c['expected_chunk_ids']
                for ident in c['expected_chunk_ids']:
                    assert ident in chunks
                assert any(c['expected_quote'].lower() in chunks[ident].text.lower() for ident in c['expected_chunk_ids'])

def test_secret_scan():
    from pathlib import Path
    import re
    root=Path(__file__).resolve().parents[1]
    patterns=[r'\bsk-[A-Za-z0-9_-]{24,}',r'\bghp_[A-Za-z0-9]{30,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'\bAKIA[0-9A-Z]{16}\b']
    findings=[]
    for folder in ('src','app','docs','exports','benchmarks','scripts','data/raw'):
        for p in (root/folder).rglob('*'):
            if p.suffix not in ('.py','.md','.json','.jsonl','.toml'):continue
            text=p.read_text(encoding='utf-8-sig')
            if any(re.search(pattern,text) for pattern in patterns):findings.append(str(p))
    assert not findings

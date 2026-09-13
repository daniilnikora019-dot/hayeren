# -*- coding: utf-8 -*-
"""Проверка ручного ядра: каждое слово должно быть засвидетельствовано.

Слова ядра я пишу сам, а значит могу ошибиться в букве. Поэтому каждое
сверяется с двумя независимыми источниками: статьёй Викисловаря и живым
корпусом текстов. Слово, которого нет нигде, — почти наверняка опечатка.
"""
import json, glob, os, sys, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = '/private/tmp/claude-501/-Users-daniilnikora/80cc56f5-30da-481e-a405-1437dcadb45d/scratchpad'
WIKT = f'{SCRATCH}/hy.jsonl'
FREQ = [f'{SCRATCH}/hye_wikipedia_2021_300K/hye_wikipedia_2021_300K-words.txt',
        f'{SCRATCH}/hye_newscrawl_2011_100K/hye_newscrawl_2011_100K-words.txt']

wikt = set()
for line in open(WIKT, encoding='utf-8'):
    w = json.loads(line).get('word')
    if w: wikt.add(w.strip().lower())

corpus = {}
for p in FREQ:
    if not os.path.exists(p): continue
    for line in open(p, encoding='utf-8'):
        q = line.rstrip('\n').split('\t')
        if len(q) >= 3:
            try: corpus[q[1].lower()] = corpus.get(q[1].lower(), 0) + int(q[2])
            except ValueError: pass

core = []
for f in sorted(glob.glob(os.path.join(BASE, 'data/parts/*.json'))):
    core += [(os.path.basename(f), *row) for row in json.load(open(f, encoding='utf-8'))]

nowhere, only_corpus, dupes = [], [], []
seen = {}
for src, cat, w, ru in core:
    key = w.strip().lower()
    if key in seen: dupes.append((w, seen[key], src))
    seen[key] = src
    parts = key.split()
    in_wikt = key in wikt or all(p in wikt for p in parts)
    in_corp = all(corpus.get(p, 0) >= 3 for p in parts)
    if not in_wikt and not in_corp: nowhere.append((src, w, ru))
    elif not in_wikt: only_corpus.append((w, ru, min(corpus.get(p, 0) for p in parts)))

print(f'записей в ядре: {len(core)}')
print(f'подтверждены словарём или корпусом: {len(core) - len(nowhere)}')
if dupes:
    print(f'\nПОВТОРЫ ({len(dupes)}):')
    for w, a, b in dupes: print(f'  {w:24} {a} и {b}')
if only_corpus:
    print(f'\nнет в Викисловаре, но есть в корпусе ({len(only_corpus)}) — это нормально:')
    for w, ru, n in only_corpus[:40]: print(f'  {w:24} {ru[:26]:28} встреч {n}')
if nowhere:
    print(f'\nНЕ НАЙДЕНЫ НИГДЕ ({len(nowhere)}) — проверить написание:')
    for src, w, ru in nowhere: print(f'  {src:16} {w:24} {ru}')
sys.exit(1 if nowhere or dupes else 0)

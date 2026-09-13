# -*- coding: utf-8 -*-
"""Озвучка армянских слов моделью Piper (hy_AM-gor).

У Microsoft армянского голоса нет вовсе — в 322 голосах на 142 локали его не
оказалось, — поэтому взята открытая нейросетевая модель Piper. Она работает
офлайн, файлы генерируются заранее и лежат рядом с приложением, так что
устройство приложения не отличается от грузинского и румынского.

  python3 tools/tts_generate.py            дозаписать недостающие
  python3 tools/tts_generate.py --all      перегенерировать всё
"""
import hashlib, json, os, subprocess, sys, wave

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.expanduser('~/Library/Application Support/hayeren/tools/hy_AM-gor-medium.onnx')
PIPER = os.path.expanduser('~/venvs/piper/bin/python')
OUT = os.path.join(BASE, 'audio/f')
INDEX = os.path.join(BASE, 'data/audio_index.json')


def key(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]


def main():
    if not os.path.exists(MODEL):
        sys.exit(f'нет модели {MODEL}')
    words = json.load(open(os.path.join(BASE, 'data/words-hy.json'), encoding='utf-8'))['words']
    alphabet = json.load(open(os.path.join(BASE, 'data/alphabet-hy.json'), encoding='utf-8'))
    texts = [w['ka'] for w in words] + [a[5] for a in alphabet if a[5]] + [a[2] for a in alphabet]
    texts = [t for t in dict.fromkeys(texts) if t.strip()]

    os.makedirs(OUT, exist_ok=True)
    idx = {} if '--all' in sys.argv else (
        json.load(open(INDEX, encoding='utf-8')) if os.path.exists(INDEX) else {})
    todo = [t for t in texts if key(t) not in idx or
            not os.path.exists(os.path.join(OUT, key(t) + '.mp3'))]
    print(f'слов всего: {len(texts)} · озвучить: {len(todo)}')
    if not todo:
        return

    script = os.path.join(BASE, 'tools/_piper_batch.py')
    with open(script, 'w', encoding='utf-8') as f:
        f.write(
            "import io,json,sys,wave,lameenc\n"
            "from piper import PiperVoice\n"
            "v=PiperVoice.load(sys.argv[1])\n"
            "def mp3(pcm,rate):\n"
            "    e=lameenc.Encoder(); e.set_bit_rate(48); e.set_in_sample_rate(rate)\n"
            "    e.set_channels(1); e.set_quality(2)\n"
            "    return e.encode(pcm)+e.flush()\n"
            "for n,(t,p) in enumerate(json.load(open(sys.argv[2],encoding='utf-8')),1):\n"
            "    buf=io.BytesIO()\n"
            "    with wave.open(buf,'wb') as o: v.synthesize_wav(t,o)\n"
            "    buf.seek(0); w=wave.open(buf)\n"
            "    open(p,'wb').write(mp3(w.readframes(w.getnframes()),w.getframerate()))\n"
            "    if n%200==0: print(f' {n}',flush=True)\n")
    jobs = [[t, os.path.join(OUT, key(t) + '.mp3')] for t in todo]
    jf = os.path.join(BASE, 'tools/_piper_jobs.json')
    json.dump(jobs, open(jf, 'w', encoding='utf-8'), ensure_ascii=False)
    subprocess.run([PIPER, script, MODEL, jf], check=True)
    os.remove(script); os.remove(jf)

    for t in texts:
        k = key(t)
        if os.path.exists(os.path.join(OUT, k + '.mp3')):
            idx[t] = k
    json.dump(idx, open(INDEX, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(f'в индексе: {len(idx)} · файлов: {len(os.listdir(OUT))} · всего {total // 1024 // 1024} МБ')


if __name__ == '__main__':
    main()

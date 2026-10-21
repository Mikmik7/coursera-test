# Generates soundtrack.wav: soft I-V-vi-IV pad + pluck arpeggio + click pops and reveal chimes.
import numpy as np, wave, re

SR, DUR = 44100, 82.0
n = int(SR * DUR); t = np.arange(n) / SR
out = np.zeros(n)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)

BEAT = 60 / 96
CHORDS = [[48, 55, 64, 67], [43, 55, 62, 71], [45, 57, 64, 72], [41, 57, 65, 69]]  # C G Am F
BAR = BEAT * 4

def add(sig, start):
    i = int(start * SR); j = min(n, i + len(sig))
    if i < n: out[i:j] += sig[:j - i]

# pad + bass
for c in range(int(DUR / (BAR * 2)) + 1):
    ch = CHORDS[c % 4]; st = c * BAR * 2; L = BAR * 2 + 0.4
    tt = np.arange(int(L * SR)) / SR
    env = np.minimum(1, tt / 0.8) * np.minimum(1, (L - tt) / 0.6)
    pad = sum(np.sin(2 * np.pi * hz(m + 12) * tt) + 0.5 * np.sin(2 * np.pi * hz(m + 12) * 1.003 * tt) for m in ch[1:])
    add(0.035 * pad * env, st)
    for b in range(4):
        bt = np.arange(int(BEAT * 1.9 * SR)) / SR
        add(0.12 * np.sin(2 * np.pi * hz(ch[0] - 12 + 12) * bt) * np.exp(-bt * 2.2) * np.minimum(1, bt / 0.01), st + b * BEAT * 2)

# pluck arpeggio (8ths)
step = BEAT / 2
for k in range(int(DUR / step)):
    ch = CHORDS[int(k * step / (BAR * 2)) % 4]
    pat = [1, 2, 3, 2, 1, 3, 2, 3]
    m = ch[pat[k % 8]] + 12
    pt = np.arange(int(0.9 * SR)) / SR
    f = hz(m)
    sig = (np.sin(2 * np.pi * f * pt) + 0.3 * np.sin(4 * np.pi * f * pt) + 0.1 * np.sin(6 * np.pi * f * pt))
    add(0.05 * sig * np.exp(-pt * 5) * np.minimum(1, pt / 0.004), k * step)

# soft shaker on offbeats
rng = np.random.default_rng(1)
for k in range(int(DUR / step)):
    if k % 2: 
        st_ = np.arange(int(0.06 * SR)) / SR
        nz = rng.standard_normal(len(st_)); nz = np.diff(np.concatenate([[0], nz]))
        add(0.012 * nz * np.exp(-st_ * 70), k * step)

# master fades + ducking under nothing; normalize music bed
fade = np.minimum(1, t / 1.5) * np.minimum(1, (DUR - t) / 3.0)
out *= fade
out = out / np.abs(out).max() * 0.32

# UI sounds, times read from scene.html so they stay in sync
html = open('scene.html', encoding='utf-8').read()
clicks = [float(x) for x in re.search(r'CLICKS = \[([^\]]+)\]', html).group(1).split(',')]
for c in clicks:
    pt = np.arange(int(0.08 * SR)) / SR
    f = 1100 * np.exp(-pt * 18)
    add(0.28 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-pt * 45), c)
for c in [7.2, 28.5, 60.6, 72.6, 76.4]:  # bubble, installed, page reveal, pink, end
    for i, m in enumerate([84, 88, 91]):
        pt = np.arange(int(1.2 * SR)) / SR
        add(0.09 * (np.sin(2 * np.pi * hz(m) * pt) + 0.2 * np.sin(2 * np.pi * hz(m) * 2.76 * pt)) * np.exp(-pt * 3.5), c + i * 0.07)

out = np.tanh(out * 1.2) / np.tanh(1.2) * 0.85
pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
st = np.repeat(pcm[:, None], 2, axis=1)
with wave.open('soundtrack.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print('ok', len(pcm) / SR)

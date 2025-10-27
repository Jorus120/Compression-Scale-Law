# Minimal CSL toy demo: same PSD + same marginal, different phases -> compressibility gap
# Shows surrogate-minus-real code length vs window size and the log–log slope b (alpha = 1 - b).
import numpy as np, gzip, io, lzma
import matplotlib.pyplot as plt

def from_mag_phase(mag, ph):
    N2 = len(mag)
    N = (N2 + 1) * 2
    z = mag * np.exp(1j * ph)
    spec = np.zeros(N, dtype=complex)
    spec[1:N2+1] = z
    spec[-N2:] = np.conj(z[::-1])
    x = np.fft.ifft(spec).real
    return x / (np.std(x) + 1e-12)

def rank_map_to(ref, target):
    # Map 'target' to share the empirical marginal of 'ref'
    order = np.argsort(np.argsort(target))
    ref_sorted = np.sort(ref)
    return ref_sorted[order]

def q8(x):
    # Monotone companding + 8-bit quantization (codec-agnostic enough)
    x = np.tanh(x)
    xn = (x - x.min()) / (x.max() - x.min() + 1e-12)
    return (xn * 255).astype(np.uint8)

def gz_len(arr):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=6) as f:
        f.write(arr.tobytes())
    return len(buf.getvalue())

def lz_len(arr):
    return len(lzma.compress(arr.tobytes(), preset=6))

def one_run(N=8192, spectrum_power=0.5, sizes=(128,256,512,1024,2048), seed=0, use_lzma=False):
    rng = np.random.default_rng(seed)
    freqs = np.arange(1, N//2)
    # |FFT| magnitudes fixed -> PSD ~ 1/f^(spectrum_power)
    magnitudes = 1.0 / np.power(freqs, spectrum_power/2)

    # Deterministic phase law (creates phase coupling/intermittency)
    phi_locked = np.mod(0.3*freqs + 0.02*freqs**2, 2*np.pi)
    # Random phases for surrogate; then rank-map to match marginals
    phi_rand = rng.uniform(0, 2*np.pi, size=freqs.shape)

    x_real = from_mag_phase(magnitudes, phi_locked)
    x_surr0 = from_mag_phase(magnitudes, phi_rand)
    x_surr = rank_map_to(x_real, x_surr0)  # match marginal distribution

    comp = lz_len if use_lzma else gz_len

    gaps = []
    for L in sizes:
        K = N // L
        reals = []; surrs = []
        for k in range(K):
            sl = slice(k*L, (k+1)*L)
            reals.append(comp(q8(x_real[sl])))
            surrs.append(comp(q8(x_surr[sl])))
        gap = float(np.mean(surrs) - np.mean(reals))  # >0 => real compresses better
        gaps.append(gap)

    L = np.array(sizes, float)
    g = np.array(gaps) + 1e-12  # avoid log(0)
    mask = g > 0
    b = float(np.polyfit(np.log(L[mask]), np.log(g[mask]), 1)[0])  # fit only where gap>0
    alpha = 1 - b
    return np.array(sizes), np.array(gaps), b, alpha

if __name__ == '__main__':
    sizes = [128,256,512,1024,2048]
    for codec in ('gzip','lzma'):
        use_lzma = (codec=='lzma')
        bs=[]; alphas=[]; sum_gaps=None
        for seed in range(10):
            L, gaps, b, a = one_run(sizes=sizes, seed=seed, use_lzma=use_lzma)
            bs.append(b); alphas.append(a)
            sum_gaps = gaps if sum_gaps is None else sum_gaps + gaps
        mean_gaps = sum_gaps/10
        mean_b = float(np.mean(bs)); mean_alpha = float(np.mean(alphas))

        # Log–log plot of mean gap vs window size
        import matplotlib.pyplot as plt
        mask = mean_gaps > 0
        plt.figure()
        plt.loglog(np.array(L)[mask], mean_gaps[mask], marker='o')
        plt.xlabel('Window size')
        plt.ylabel('Surrogate − Real code length (bytes)')
        plt.title(f'CSL demo ({codec}) — mean slope b≈{mean_b:.2f}, α≈{mean_alpha:.2f}')
        plt.savefig(f'csl_phase_demo_{codec}.png', bbox_inches='tight', dpi=160)
        plt.close()

        print(f'[{codec}] sizes={list(L)}, mean_gaps={list(np.round(mean_gaps,1))}, mean_b={mean_b:.2f}, mean_alpha={mean_alpha:.2f}')

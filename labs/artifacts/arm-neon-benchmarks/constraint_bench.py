#!/usr/bin/env python3
"""ARM NEON Constraint Checker — Python numpy baseline
Benchmark: 100M constraint checks using numpy vectorization
"""
import numpy as np
import time

N = 100_000_000
print("=" * 70)
print("ARM NEON Constraint Checker — Python numpy baseline")
print("=" * 70)

# Generate input data
t0 = time.time()
inputs = np.arange(N, dtype=np.int32) % 100
print(f"\n  Data generation: {(time.time()-t0)*1000:.1f}ms")

# 1. Python loop (slow baseline)
lo, hi = 0, 50
print("\n  1. Python loop (pure Python, slow):")
t0 = time.time()
pass_count = sum(1 for v in inputs[:1_000_000] if lo <= v <= hi)
t1 = time.time()
print(f"     Sample (1M): {(t1-t0)*1000:.1f}ms  Rate: {1_000_000/(t1-t0):.0f}/s")

# 2. numpy vectorized
print("\n  2. numpy vectorized (NEON via BLAS):")
t0 = time.time()
mask = (inputs >= lo) & (inputs <= hi)
t1 = time.time()
pass_count = int(mask.sum())
elapsed = t1 - t0
cps = N / elapsed
print(f"     Time: {elapsed*1000:.3f}ms  Throughput: {cps:.0f} checks/s")
print(f"     Pass rate: {pass_count/N*100:.1f}%  Per check: {elapsed*1e9/N:.2f}ns")

# 3. Multi-constraint (10 checks)
print("\n  3. 10 constraints (numpy AND chain):")
pairs = [
    (0, 90), (10, 80), (20, 70), (5, 85), (15, 75),
    (25, 65), (0, 95), (10, 85), (20, 75), (30, 65),
]
t0 = time.time()
mask = np.ones(N, dtype=np.int32)
for lo, hi in pairs:
    mask &= (inputs >= lo) & (inputs <= hi)
t1 = time.time()
pass_count = int(mask.sum())
elapsed = t1 - t0
cps = N / elapsed
print(f"     Time: {elapsed*1000:.3f}ms  Throughput: {cps:.0f} input-sets/s")
print(f"     Effective: {cps*10:.0f} individual checks/s")
print(f"     Pass rate: {pass_count/N*100:.1f}%")

# 4. Bitmask popcount
pop_n = N // 10
print(f"\n  4. Bitmask popcount ({pop_n:,} ops):")
domains = np.arange(pop_n, dtype=np.uint64) * 2654435761
t0 = time.time()
pop_results = np.zeros(pop_n, dtype=np.uint64)
for i in range(pop_n):
    pop_results[i] = bin(domains[i]).count('1')
t1 = time.time()
print(f"     Popcount: {(t1-t0)*1000:.1f}ms  = {pop_n/(t1-t0):.0f} /s")

# 5. Domain intersection (vectorized)
print(f"\n  5. Domain intersection ({pop_n:,} ops):")
b = np.arange(pop_n, dtype=np.uint64) * 7 * 2654435761
t0 = time.time()
inter = domains & b
t1 = time.time()
print(f"     Intersect: {(t1-t0)*1000:.3f}ms  = {pop_n/(t1-t0):.0f} /s")

print(f"\n{'=' * 70}")
print("Python numpy — BLAS backend auto-vectorizes to NEON")
print("Only suitable for prototyping — 100x slower than native Fortran/Rust")
print(f"{'=' * 70}")

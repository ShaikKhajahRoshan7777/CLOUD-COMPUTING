"""Task 3 - sizing specification evaluated step by step (decimal units: 1 TB = 1000 GB, 1 GB = 1000 MB)."""
import math

def size(imagery_gb_day=200.0, show=True):
    stations, per_min, rec_b, comp = 5000, 1, 400, 3
    repl, days, disks, disk_tb, usable, thr_mb, window_h = 3, 365, 12, 8, 0.70, 150, 2
    weather_raw = stations * per_min * 1440 * rec_b / 1e9          # GB/day
    raw_total = weather_raw + imagery_gb_day
    weather_stored = weather_raw / comp
    stored_total = weather_stored + imagery_gb_day
    year_repl_tb = stored_total * days * repl / 1000
    node_cap_tb = disks * disk_tb * usable
    n_storage = math.ceil(year_repl_tb / node_cap_tb)
    node_thr = disks * thr_mb                                      # MB/s per node (disks in parallel)
    node_scan_gb = node_thr * window_h * 3600 / 1000               # GB per node in window
    n_scan = math.ceil(stored_total / node_scan_gb)
    final = max(n_storage, n_scan)
    r = dict(weather_raw=weather_raw, raw_total=raw_total, weather_stored=weather_stored, stored_total=stored_total,
             year_repl_tb=year_repl_tb, node_cap_tb=node_cap_tb, n_storage=n_storage, node_thr=node_thr,
             node_scan_gb=node_scan_gb, n_scan=n_scan, final=final,
             governs="STORAGE" if n_storage >= n_scan else "SCAN WINDOW")
    if show:
        print(f" S1 weather readings/day     = {stations} x 1440 x {per_min} = {stations*1440:,}")
        print(f" S2 weather raw volume       = {stations*1440:,} x {rec_b} B = {weather_raw:.2f} GB/day")
        print(f" S3 imagery raw volume       = {imagery_gb_day:.2f} GB/day")
        print(f" S4 total raw volume         = {raw_total:.2f} GB/day")
        print(f" S5 weather stored (3:1)     = {weather_raw:.2f} / {comp} = {weather_stored:.2f} GB/day")
        print(f" S6 total stored per day     = {weather_stored:.2f} + {imagery_gb_day:.2f} = {stored_total:.2f} GB/day")
        print(f" S7 one-year replicated      = {stored_total:.2f} x {days} x {repl} = {year_repl_tb:.2f} TB")
        print(f" S8 usable capacity per node = {disks} x {disk_tb} x {usable} = {node_cap_tb:.1f} TB")
        print(f" S9 nodes for storage        = ceil({year_repl_tb:.2f} / {node_cap_tb:.1f}) = {n_storage}")
        print(f" S10 scan rate per node      = {disks} x {thr_mb} = {node_thr} MB/s -> {node_scan_gb/1000:.2f} TB in {window_h} h")
        print(f" S11 nodes for scan window   = ceil({stored_total:.2f} / {node_scan_gb:.0f}) = {n_scan}")
        print(f" S12 FINAL nodes             = max({n_storage}, {n_scan}) = {final}   governed by {r['governs']}")
    return r

if __name__ == "__main__":
    print("=" * 74); print(" TASK 3 : AGRICULTURE AND WEATHER PLATFORM - SIZING DESK-CHECK"); print("=" * 74)
    base = size()
    print(f" imagery share of daily storage = {200/base['stored_total']*100:.1f} %")
    print("\n" + "=" * 74); print(" WHAT-IF : imagery doubles to 400 GB/day"); print("=" * 74)
    d = size(400.0)
    print(f"\n Result: {base['final']} nodes -> {d['final']} nodes (storage still governs)")
    assert round(base['year_repl_tb'], 2) == 220.05 and base['final'] == 4

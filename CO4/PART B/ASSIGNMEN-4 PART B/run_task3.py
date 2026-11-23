"""TASK 3 - Security & privacy engineering under attack.   Run:  python run_task3.py"""
import os, sys, time, json, statistics, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from common.utils import *
from task3 import data, access, privacy, crypto

plt.rcParams["font.family"] = "Liberation Serif"
banner("TASK 3 - SECURITY AND PRIVACY ENGINEERING UNDER ATTACK")
env = env_info(); print("ENVIRONMENT:", json.dumps({k: env[k] for k in ("python", "cpu", "cpu_cores", "ram_gb", "cryptography")}))
ben = data.make_beneficiaries(5000); aux = data.make_auxiliary(ben, 0.60)
ben.to_csv(os.path.join(DATA, "beneficiaries.csv"), index=False); aux.to_csv(os.path.join(DATA, "auxiliary_public.csv"), index=False)
print("\nDATASETS (synthetic): beneficiaries=%d records, auxiliary=%d records (%.0f%% of the same people)" % (len(ben), len(aux), 100 * len(aux) / len(ben)))
print(ben.head(3).to_string(index=False)); out = {}

# ------------------------------------------------------------------ Stage A
print("\n" + "-" * 78 + "\nSTAGE A - ROLE-BASED ACCESS CONTROL + HASH-CHAINED AUDIT\n" + "-" * 78)
con = access.build_db(ben); audit = access.AuditLog()
for user, role in (("analyst_asha", "fraud_analyst"), ("researcher_ravi", "researcher")):
    cols, rows, entry = access.run_query(con, audit, user, role, access.ROLE_VIEWS[role])
    print("\n[%s as %s] SELECT * FROM %s LIMIT 3" % (user, role, access.ROLE_VIEWS[role]))
    print("  " + " | ".join(cols))
    for r in rows: print("  " + " | ".join(str(x) for x in r))
    print("  AUDIT -> seq=%d %s user=%s role=%s view=%s rows=%d decision=%s hash=%s..." % (entry["seq"], entry["time"], user, role, entry["relation"], entry["rows"], entry["decision"], entry["hash"][:16]))
try:
    access.run_query(con, audit, "researcher_ravi", "researcher", "beneficiaries")
except PermissionError as e:
    print("\n[researcher_ravi] SELECT * FROM beneficiaries  ->  PermissionError: %s" % e)
    print("  AUDIT -> seq=%d decision=%s hash=%s..." % (audit.entries[-1]["seq"], audit.entries[-1]["decision"], audit.entries[-1]["hash"][:16]))
ok, bad = audit.verify(); print("\nAudit chain verification (%d entries): %s" % (len(audit.entries), "VALID" if ok else "BROKEN at %s" % bad))
out["audit_entries"] = len(audit.entries)

# ------------------------------------------------------------------ Stage B
print("\n" + "-" * 78 + "\nSTAGE B - LINKAGE ATTACK ON THE ORIGINAL RELEASE RULE (drop Name and ID_Number)\n" + "-" * 78)
pred = privacy.predicted_reidentification(len(ben), len(data.PINS), 14610, 0.60)
pred["made_at"] = time.strftime("%Y-%m-%d %H:%M:%S"); save_json("task3_prediction.json", pred)
print("PREDICTION (recorded before the attack):")
print("  cells = 25 PINs x 14,610 days x 2 genders = %d ; P(unique) = exp(-(N-1)/cells) = %.4f" % (pred["cells"], pred["p_unique"]))
print("  expected unique records = %.0f ; expected re-identified (60%% in auxiliary) = %.0f" % (pred["unique_records"], pred["reidentified"]))
release = pd.read_sql("SELECT * FROM v_researcher", con)                 # exactly what the researcher view releases
uniq = int((release.groupby(privacy.QI)["Scheme"].transform("size") == 1).sum())
matches, res = privacy.linkage_attack(release, aux, truth_names=ben["Name"])
print("ATTACK RESULT:")
print("  released records unique on (PIN, DOB, Gender) : %d  (predicted %.0f)" % (uniq, pred["unique_records"]))
print("  records re-identified by joining the auxiliary: %d  (predicted %.0f, error %+.1f%%)" % (res["matched"], pred["reidentified"], 100 * (res["matched"] - pred["reidentified"]) / pred["reidentified"]))
print("  of which correct (verified with ground truth)  : %d  (precision %.1f%%)" % (res["correct"], 100 * res["correct"] / res["matched"]))
print("  EXAMPLE of exposed individuals (Name linked to Scheme and Amount):")
print(matches[["Name", "PIN_Code", "Date_of_Birth", "Gender", "Scheme", "Amount"]].head(4).to_string(index=False))
out["B"] = {"pred": pred, "unique": uniq, "reidentified": res["matched"], "correct": res["correct"]}

# ------------------------------------------------------------------ Stage C
print("\n" + "-" * 78 + "\nSTAGE C - GENERALISATION LATTICE, k-ANONYMITY AND UTILITY LOSS\n" + "-" * 78)
TARGET_K, MAX_SUPP = 5, 0.02
age_year = ben["Date_of_Birth"].str[:4].astype(int)
lattice = []
print("k (minimum class size) before suppression;  rows = PIN digits kept, columns = DOB generalisation")
print("%-10s" % "PIN\\DOB" + "".join("%-14s" % l for l in privacy.DOB_LEVELS))
for pdig in privacy.PIN_LEVELS:
    line = "%-10s" % ("%d digits" % pdig)
    for dl in range(6):
        g = privacy.generalise(release, pdig, dl); k, sizes = privacy.k_of(g)
        supp = float((sizes < TARGET_K).mean())
        lattice.append({"pin": pdig, "dob": dl, "k": k, "supp": supp, "loss": privacy.info_loss(pdig, dl)})
        line += "%-14s" % ("k=%d (%.1f%%)" % (k, 100 * supp) if supp else "k=%d" % k)
    print(line)
print("(percentage = records in classes smaller than %d that would have to be suppressed)" % TARGET_K)
cand = [r for r in lattice if r["supp"] <= MAX_SUPP]
best = min(cand, key=lambda r: r["loss"])
g_rel = privacy.generalise(release, best["pin"], best["dob"]); _, sizes = privacy.k_of(g_rel)
keep = sizes >= TARGET_K; g_kept = g_rel[keep]; k_ach, _ = privacy.k_of(g_kept)
g_aux = privacy.generalise(aux, best["pin"], best["dob"])
_, res_c = privacy.linkage_attack(g_kept, g_aux, truth_names=ben.loc[g_kept.index, "Name"])
print("\nCHOSEN NODE (minimum information loss with <= %.0f%% suppression): PIN %d digits, DOB = %s" % (100 * MAX_SUPP, best["pin"], privacy.DOB_LEVELS[best["dob"]]))
print("  k achieved                           : %d  (target %d)" % (k_ach, TARGET_K))
print("  records suppressed                   : %d of %d (%.2f%%)" % ((~keep).sum(), len(release), 100 * (~keep).mean()))
print("  records still re-identifiable        : %d  (before: %d)" % (res_c["matched"], res["matched"]))
# utility
pin_key = ben["PIN_Code"]; pin_gen = g_rel["PIN_Code"]
age_key = age_year; age_gen = g_rel["Date_of_Birth"]
m_pin = privacy.mape_group_means(ben.assign(Amount=ben["Amount"]), pin_key, pin_gen)
m_age = privacy.mape_group_means(ben, age_key, age_gen)
glob_before, glob_after = ben["Amount"].mean(), ben.loc[g_kept.index, "Amount"].mean()
scheme_b = ben.groupby("Scheme")["Amount"].mean(); scheme_a = ben.loc[g_kept.index].groupby("Scheme")["Amount"].mean()
print("UTILITY LOSS (aggregates the researcher could previously compute):")
print("  mean Amount per 6-digit PIN  -> only per-%s available : mean abs %% error = %.2f%%" % ("%d-digit prefix" % best["pin"], m_pin))
print("  mean Amount per birth year   -> only per-%s available : mean abs %% error = %.2f%%" % (privacy.DOB_LEVELS[best["dob"]], m_age))
print("  overall mean Amount           : %.2f -> %.2f (%+.2f%%)  [suppression effect]" % (glob_before, glob_after, 100 * (glob_after - glob_before) / glob_before))
print("  mean Amount per Scheme (max abs change): %.2f%%" % (100 * ((scheme_a - scheme_b).abs() / scheme_b).max()))
print("  information-loss index (0 = none, 1 = everything hidden): %.3f" % best["loss"])
out["C"] = {"lattice": lattice, "best": best, "k": k_ach, "suppressed": int((~keep).sum()), "reid_after": res_c["matched"], "mape_pin": m_pin, "mape_age": m_age,
            "glob_before": glob_before, "glob_after": glob_after}

# ------------------------------------------------------------------ Stage D
print("\n" + "-" * 78 + "\nSTAGE D - ENCRYPTION AT REST (AES-256-GCM), INTEGRITY (HMAC / SHA-256) AND TAMPER DETECTION\n" + "-" * 78)
enc_key, mac_key = crypto.new_keys(); aes = AESGCM(enc_key)
big = data.make_beneficiaries(100_000, seed=5)
p_plain, p_enc = os.path.join(DATA, "ben_plain_100k.csv"), os.path.join(DATA, "ben_encrypted_100k.csv")
big.to_csv(p_plain, index=False)
t0 = time.perf_counter(); prot = crypto.protect(big, enc_key, mac_key); t_encwrite = time.perf_counter() - t0
prot.to_csv(p_enc, index=False)
def pipe_plain():
    d = pd.read_csv(p_plain); return d.groupby("Scheme")["Amount"].mean()
def pipe_enc():
    d = pd.read_csv(p_enc); d["Amount"] = [float(crypto.decrypt_field(aes, t, r.encode())) for t, r in zip(d["Amount"], d["RecID"])]
    return d.groupby("Scheme")["Amount"].mean()
_, tp, mp, sp_ = repeat_timed(pipe_plain, 3); r_enc, te, me, se = repeat_timed(pipe_enc, 3)
same = np.allclose(pipe_plain().sort_index().values, r_enc.sort_index().values)
print("Pipeline = read file -> (decrypt Amount) -> mean Amount per Scheme, on %d records, 3 runs each:" % len(big))
print("  plaintext  : %.3f +/- %.3f s     file %.1f MB" % (mp, sp_, os.path.getsize(p_plain) / 1e6))
print("  encrypted  : %.3f +/- %.3f s     file %.1f MB   (ID_Number and Amount encrypted per field; + HMAC column)" % (me, se, os.path.getsize(p_enc) / 1e6))
print("  overhead   : %+.1f%% run time, %+.1f%% storage ; one-off protect-and-write cost %.2f s ; aggregate identical: %s" % (100 * (me - mp) / mp, 100 * (os.path.getsize(p_enc) / os.path.getsize(p_plain) - 1), t_encwrite, same))

small = crypto.protect(big.head(20_000), enc_key, mac_key); p_small = os.path.join(DATA, "ben_protected_20k.csv"); small.to_csv(p_small, index=False)
manifest = {"sha256": crypto.file_sha256(p_small), "records": len(small)}
print("\nINTEGRITY BASELINE: 20,000 protected records, file SHA-256 = %s..., record count = %d" % (manifest["sha256"][:24], manifest["records"]))
mac0, gcm0 = crypto.verify_table(small, enc_key, mac_key); print("  verification of untouched data: HMAC failures=%d, AES-GCM failures=%d" % (len(mac0), len(gcm0)))
def write_and_hash(df, name):
    p = os.path.join(DATA, name); df.to_csv(p, index=False); return crypto.file_sha256(p)
rows = []
def tamper(label, df):
    reread = pd.read_csv(io := p_small) if False else df
    bm, bg = crypto.verify_table(df, enc_key, mac_key)
    fh = write_and_hash(df, "tamper_tmp.csv") != manifest["sha256"]
    cnt = len(df) != manifest["records"]
    rows.append({"attack": label, "hmac": len(bm), "gcm": len(bg), "file_hash": fh, "count": cnt})
    print("  %-52s HMAC:%-5s AES-GCM:%-5s file-SHA256:%-8s count:%s" % (label, "FAIL" if bm else "ok", "FAIL" if bg else "ok", "CHANGED" if fh else "same", "CHANGED" if cnt else "same"))
print("TAMPER EXPERIMENTS (each starts from the untouched table):")
t = small.copy(); t.loc[1234, "Scheme"] = "Farm Subsidy"; tamper("T1 edit a plaintext field (Scheme) of record R0001234", t)
t = small.copy(); tok = t.loc[777, "Amount"]; t.loc[777, "Amount"] = tok[:-4] + ("AAAA" if tok[-4:] != "AAAA" else "BBBB"); tamper("T2 modify the ciphertext of Amount of record R0000777", t)
t = small.copy(); a, b = t.loc[10, "Amount"], t.loc[11, "Amount"]; t.loc[10, "Amount"], t.loc[11, "Amount"] = b, a; tamper("T3 swap encrypted Amounts of records R10 and R11", t)
t = small.drop(index=555).reset_index(drop=True); tamper("T4 DELETE one whole record (R0000555)", t)
a_copy = access.AuditLog(); a_copy.entries = [dict(e) for e in audit.entries]; a_copy.entries[1]["rows"] = 0
okc, badc = a_copy.verify(); print("  %-52s hash chain: %s (first bad entry seq=%s)" % ("T5 edit audit entry #1 (rows 3 -> 0)", "BROKEN" if not okc else "ok", badc))
out["D"] = {"plain_mean": mp, "plain_sd": sp_, "enc_mean": me, "enc_sd": se, "overhead_pct": 100 * (me - mp) / mp, "size_plain": os.path.getsize(p_plain), "size_enc": os.path.getsize(p_enc),
            "protect_s": t_encwrite, "tamper": rows, "audit_tamper_detected": not okc, "records_big": len(big)}
save_json("task3_results.json", out)

# ------------------------------------------------------------------ figures
fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.0))
K = np.array([[next(r["k"] for r in lattice if r["pin"] == p and r["dob"] == d) for d in range(6)] for p in privacy.PIN_LEVELS])
im = ax[0].imshow(np.log10(K), cmap="Blues", aspect="auto")
for i in range(K.shape[0]):
    for j in range(K.shape[1]): ax[0].text(j, i, K[i, j], ha="center", va="center", fontsize=8, color="white" if np.log10(K[i, j]) > 1.6 else "black")
ax[0].set_xticks(range(6)); ax[0].set_xticklabels(["exact", "month", "year", "5y", "10y", "20y"], fontsize=8); ax[0].set_yticks(range(5))
ax[0].set_yticklabels(["6 dig", "5 dig", "4 dig", "3 dig", "none"], fontsize=8); ax[0].set_title("(a) k-anonymity lattice (min class size)")
bi = [(privacy.PIN_LEVELS.index(best["pin"]), best["dob"])]; ax[0].add_patch(plt.Rectangle((bi[0][1] - .5, bi[0][0] - .5), 1, 1, fill=False, ec="red", lw=2))
ax[1].scatter([r["loss"] for r in lattice], [r["k"] for r in lattice], c=["#c55a11" if r["supp"] > MAX_SUPP else "#1f4e79" for r in lattice], s=22)
ax[1].scatter([best["loss"]], [best["k"]], marker="*", s=220, c="gold", ec="k", zorder=5); ax[1].set_yscale("log"); ax[1].axhline(TARGET_K, ls="--", c="grey", lw=1)
ax[1].set_xlabel("information-loss index"); ax[1].set_ylabel("k before suppression (log)"); ax[1].set_title("(b) Privacy vs utility trade-off")
ax[2].bar(["plaintext", "AES-GCM\n+ HMAC"], [mp, me], yerr=[sp_, se], color=["#548235", "#c55a11"], capsize=5); ax[2].set_ylabel("pipeline time (s), mean +/- SD, n=3"); ax[2].set_title("(c) Encryption overhead (100k records)")
for a in ax: a.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "fig_task3.png"), dpi=170); plt.close()
print("\nSaved results/task3_results.json and figures/fig_task3.png")

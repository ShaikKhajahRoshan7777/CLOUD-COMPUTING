"""Task 1 - checks the repaired specification: 6 stages, 6 fields each, a data-protection rule per stage, defence <= 100 words."""
from task1_spec_data import STAGES, FIELDS, DEFENCE

print("=" * 72)
print(" TASK 1 : SPECIFICATION COMPLETENESS CHECK  (HospitalAnalytics)")
print("=" * 72)
ok = True
for no, name, body in STAGES:
    missing = [f for f in FIELDS if not body.get(f, "").strip()]
    has_rule = body["SECURITY"].startswith("Data-protection rule:")
    status = "PASS" if not missing and has_rule else "FAIL"
    ok &= status == "PASS"
    print(f" Stage {no} {name:<28} fields={len(FIELDS)-len(missing)}/6  protection-rule={'yes' if has_rule else 'NO'}  [{status}]")
words = len(DEFENCE.split())
print("-" * 72)
print(f" Stages specified          : {len(STAGES)}")
print(f" Defence word count        : {words}  (limit 100)  [{'PASS' if words <= 100 else 'FAIL'}]")
print(f" Overall                   : {'ALL CHECKS PASSED' if ok and words <= 100 else 'CHECK FAILED'}")

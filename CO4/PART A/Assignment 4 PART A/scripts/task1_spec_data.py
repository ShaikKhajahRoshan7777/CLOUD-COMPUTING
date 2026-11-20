"""Task 1 - repaired HospitalAnalytics specification held as data (six stages x six fields)."""

FIELDS = ["INPUT", "PROCESS", "OUTPUT", "STORAGE", "LATENCY", "SECURITY"]

DEFENCE = (
    "The rewritten design is a specification because every stage states its input, a testable "
    "processing rule, output, storage zone, latency and security control in measurable terms. "
    "'Clean' becomes named checks with a defined fate for failing records, and 'everywhere' and "
    "'everyone' become zones and role tiers. Another engineer could build and test it without "
    "asking questions, and verified stage by stage, using any technology. No product, code or configuration appears, so it "
    "describes required behaviour, never an implementation choice."
)

STAGES = [
    ("1", "SECURE INTAKE", {
        "INPUT": "From 300 hospitals: EHR extracts (FHIR JSON) hourly, lab reports (CSV) nightly at 02:00, medical images (DICOM) nightly. Assumed volume: 6 x 10^6 records/day (about 12 GB) and about 3 TB of images/day.",
        "PROCESS": "Authenticate each hospital; accept a file only with a manifest (hospital ID, file count, SHA-256). Checksum mismatch: REJECT the file and request resend. Write one intake receipt per file.",
        "OUTPUT": "Verified files to the landing buffer; receipts to the audit log.",
        "STORAGE": "Encrypted landing buffer; deleted 7 days after Stage 2 acknowledges.",
        "LATENCY": "EHR within 1 h of sending; labs within 2 h of the nightly drop; images by 06:00.",
        "SECURITY": "Data-protection rule: data enters only over mutual TLS with write-only hospital credentials; AES-256 at rest; no hospital can read another hospital's files.",
    }),
    ("2", "VALIDATE AND QUARANTINE", {
        "INPUT": "Verified files from the landing buffer.",
        "PROCESS": "Per record check: required fields present (patient key, hospital ID, encounter date, ICD-10 code); code in the ICD-10 list; date not in future and not before birth; lab value within the physiological range; DEDUPLICATE on (hospital ID, patient key, encounter ID). Failing records go to QUARANTINE with a reason code, never deleted or silently corrected. If a hospital's daily reject rate exceeds 5%, hold its batch and alert its data steward.",
        "OUTPUT": "Valid records to the Raw Identified Zone; rejects to quarantine; daily quality report to the hospital.",
        "STORAGE": "Raw Identified Zone inside the state data centre (data residency), kept 7 years; quarantine kept 90 days.",
        "LATENCY": "Each batch validated within 30 min of arrival.",
        "SECURITY": "Data-protection rule: quarantine holds identifiers so it has the same access class as the raw zone; logs record rule and reason code, never patient values.",
    }),
    ("3", "DE-IDENTIFY AND SEPARATE", {
        "INPUT": "Valid records and images from the Raw Identified Zone.",
        "PROCESS": "Replace name, address, phone and national ID by a keyed pseudonym (HMAC-SHA-256, key in a key-management service, rotated yearly). Drop free-text notes. Generalise date of birth to a 5-year age band, PIN code to its first 3 digits, exact dates to month. Strip DICOM header identifiers. SUPPRESS any group (age band, region, diagnosis) with fewer than 10 patients.",
        "OUTPUT": "De-identified records and images to the Curated Zone. The pseudonym-to-identity mapping never leaves the Raw zone.",
        "STORAGE": "Curated Zone on separate storage from the raw zone, kept 10 years for long-term trends.",
        "LATENCY": "Records within 2 h of validation; images within 12 h.",
        "SECURITY": "Data-protection rule: the job may read raw and only write curated; the HMAC key is never stored beside the data; no person can open its intermediate files.",
    }),
    ("4", "ANALYSE DISEASE TRENDS", {
        "INPUT": "De-identified records from the Curated Zone (about 6 x 10^6 per day).",
        "PROCESS": "Compute weekly counts and rates per disease (ICD-10 3-character), district and age band. Flag a trend when the 4-week moving average exceeds the previous 12-week mean by more than 20%. Suppress any output cell below 10.",
        "OUTPUT": "Trend tables and trend alerts for the epidemiology team.",
        "STORAGE": "Results store, kept 10 years.",
        "LATENCY": "Daily provisional counts by 08:00; weekly job finished within 4 h.",
        "SECURITY": "Data-protection rule: analysts hold the role Epidemiologist on the Curated Zone only; results are screened for small cells before being written.",
    }),
    ("5", "CONTROLLED SHARING", {
        "INPUT": "Result tables from Stage 4.",
        "PROCESS": "Publish by tier. Tier 1 public: district-level aggregates, cells below 10 suppressed. Tier 2 approved researchers: de-identified records after a signed agreement and ethics approval. Tier 3 health officers: district and hospital level. Each release needs an approval ticket from the data steward.",
        "OUTPUT": "Dashboards and files to the named tier only.",
        "STORAGE": "Publication zone; each release copy and its ticket kept 5 years.",
        "LATENCY": "Tier 1 refreshed within 1 h of Stage 4; Tier 2 requests served in 5 working days.",
        "SECURITY": "Data-protection rule: identifiers are never published to any tier; role-based access with MFA; links expire in 30 days; download volume capped per user.",
    }),
    ("6", "AUDIT, FAILURE AND REPLAY", {
        "INPUT": "Audit events and job status from Stages 1 to 5.",
        "PROCESS": "Append one audit record (who, what, when, purpose) for every access, release and rule failure. Retry a failed batch 3 times at 15-minute intervals, then hold downstream stages and alert on-call. REPLAY from the Raw zone using the same record keys so a re-run never creates duplicates. Review access monthly.",
        "OUTPUT": "Audit reports and failure alerts to the security officer.",
        "STORAGE": "Write-once audit store on a system separate from the data clusters, kept 7 years.",
        "LATENCY": "Audit entry within 1 min; alert within 5 min of the third failure.",
        "SECURITY": "Data-protection rule: services can append but nobody, including data administrators, can edit or erase audit entries; auditors read only.",
    }),
]

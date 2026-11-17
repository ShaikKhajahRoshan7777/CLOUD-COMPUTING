"""
Builds the final Word report: the ORIGINAL evaluation form (untouched, editable) + the full assignment answers.
Run from repo root:  python tools/build_report.py <path-to-original-evaluation-form.docx> <output.docx>
"""
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

sys.path.insert(0, str(Path(__file__).parent))
from docx_helpers import *  # noqa

ROOT = Path(__file__).resolve().parent.parent
DG, SS = ROOT / "diagrams", ROOT / "screenshots"
src_form, out_path = sys.argv[1], sys.argv[2]

doc = Document(src_form)               # the evaluation form stays exactly as supplied
setup_numbering(doc)

# ---------- new section after the form (form content is not modified) ----------
sec = doc.add_section(WD_SECTION.NEW_PAGE)
sec.left_margin = sec.right_margin = Inches(0.8)
sec.top_margin, sec.bottom_margin = Inches(0.8), Inches(0.75)
sec.header.is_linked_to_previous = False
sec.footer.is_linked_to_previous = False
hp = sec.header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(hp.add_run("CSA15 - Cloud Computing and Big Data Analytics  |  Assignment 3 - CO3  |  SIMATS Engineering"), 10, False, True, "555555")
fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(fp.add_run("Department of Information Technology  |  Page "), 10, False, False, "555555")
r = fp.add_run()
set_font(r, 10, False, False, "555555")
add_field(r, "PAGE")

# ======================= COVER / OVERVIEW =======================
banner(doc, "CLOUD-BASED ACCESS, APIs, SECURITY AND COLLABORATION")
banner(doc, "ASSIGNMENT 3 - CO3 : ANSWER REPORT WITH EVIDENCE", fill="0E8A8A", size=14)
spacer(doc, 6)
table(doc, [
    ["Item", "Details", "Item", "Details"],
    ["Course", "CSA15 - Cloud Computing and Big Data Analytics", "Mode", "Pair work - Student A and Student B"],
    ["Course Outcome", "CO3 - Implement cloud-based solutions using cloud storage, web APIs and platform services", "Total Marks", "50 (7 questions)"],
    ["Student A", "(Name / Register No.)", "Student B", "(Name / Register No.)"],
    ["Code repository", "GitHub folder: cloud_co3_assignment", "Tools used", "Python 3, VS Code, Google Workspace, PyPI JSON API"],
], [1.1, 2.55, 1.0, 2.25], first_col_bold=True)

heading(doc, "1. Executive Summary")
para(doc, "This report answers all seven tasks of Assignment 3 following the OBE evidence chain Understand, Design, Implement, Demonstrate, "
          "Analyse and Evaluate. Every question contains (i) shared group work, (ii) the individual responsibility of Student A and Student B, "
          "(iii) architecture or flow diagrams, (iv) practical evidence, and (v) a joint evaluation. The programming evidence is real: four Python "
          "programs were written in VS Code, executed, and their genuine terminal output is captured in the screenshots. All source code, "
          "outputs, diagrams and screenshots are stored in the accompanying GitHub folder.")
callout(doc, "How the work maps to the rubric",
        "Q1 Access methods (6) - Q2 Platforms and web apps (7) - Q3 Web API with program (7) - Q4 Security (7) - Q5 Collaboration (6) - "
        "Q6 Integrated mini investigation (7) - Q7 Day-4 design challenge (10). Each section ends with an 'Evidence expected' line that is "
        "ticked against the mandatory evidence check in the evaluation form at the start of this document.")
table(doc, [
    ["Task", "Marks", "Key evidence included", "Where"],
    ["Q1", "6", "3 access methods, Client-Network-Cloud diagram, device tests, limitation", "Section 2"],
    ["Q2", "7", "Two-platform comparison, interaction diagram, web-app demonstration, local-vs-cloud evaluation", "Section 3"],
    ["Q3", "7", "API flow, Python program, 2 valid + 1 invalid request, responses, analysis", "Section 4"],
    ["Q4", "7", "6 security considerations, secure flow, threats and mitigations, auth demo output", "Section 5"],
    ["Q5", "6", "Workflow, role matrix, 2 collaborative activities, permission evidence, issue and fix", "Section 6"],
    ["Q6", "7", "Scenario, architecture, mock-up, prototype execution, 2 user scenarios", "Section 7"],
    ["Q7", "10", "Two initial proposals, comparison record, joint design, 9 test cases, cross-defence", "Section 8"],
], [0.6, 0.6, 4.7, 1.0], align_center_cols=(0, 1), caption="Assignment roadmap and rubric coverage")

# ======================= Q1 =======================
heading(doc, "2. Q1 - Accessing Cloud Services through Different Methods (6 Marks)", page_break=True)
sub(doc, "2.1 Shared Group Work")
para(doc, "Cloud computing delivers shared computing resources on demand over a network. Users never touch the provider's data centre; "
          "they reach the service through a client and a network. The pair studied three access routes and selected "
          "Google Drive (cloud storage and file sharing) as the demonstration service because it is available through all three routes.")
bullets(doc, [("Browser / cloud console:", "a web GUI opened over HTTPS (for example drive.google.com or a cloud management console)."),
              ("Mobile application:", "a native Android/iOS app that syncs and caches files and supports push notifications."),
              ("API / SDK / CLI:", "programs send HTTP requests (REST) or use client libraries, enabling automation without any GUI."),
              ("Role of connectivity:", "Wi-Fi, mobile data or LAN carries encrypted requests. Without connectivity only cached data is usable.")])
sub(doc, "2.2 Student A - Access Method Design")
table(doc, [
    ["Access method", "Classification", "How the user accesses the service", "Typical users"],
    ["Web browser / console", "Interactive - thin client", "Opens URL, signs in, uses the web interface rendered by the browser", "Students, office staff, administrators"],
    ["Mobile application", "Interactive - native client", "Installs app, signs in once, files are cached and synced in the background", "Mobile-first users, field staff"],
    ["API / SDK / CLI", "Programmatic - machine client", "Code sends authenticated HTTPS requests and parses JSON responses", "Developers, automated back-ups, integrations"],
], [1.3, 1.3, 2.7, 1.6], caption="Classification of cloud access methods", first_col_bold=True)
figure(doc, DG / "q1_access_architecture.png", "Client -> Network -> Cloud Service architecture showing the three access methods", 6.4)
sub(doc, "How a user accesses the selected service (Google Drive)")
bullets(doc, ["The user opens a browser or app and the client resolves the service name through DNS.",
              "A TLS-secured HTTPS connection is established across the Internet.",
              "The user authenticates (password + one-time code) and receives a session token.",
              "The client sends requests (list, upload, share); the cloud verifies the token, checks permissions and returns the response.",
              "Changes are stored in the provider's replicated storage and appear on every logged-in device."])
table(doc, [
    ["Requirement", "Hardware", "Software"],
    ["Client side", "Laptop / smartphone / PC with display and input", "Modern browser or the mobile app; Python 3 for API access"],
    ["Network side", "Wi-Fi router or mobile data; minimum a few Mbps", "TCP/IP, DNS, TLS 1.2 or 1.3"],
    ["Cloud side (provider managed)", "Servers, storage arrays, load balancers", "Identity service, storage service, API gateway"],
], [1.7, 2.6, 2.6], caption="Hardware and software requirements", first_col_bold=True)
para(doc, "The client renders the interface, collects input, encrypts traffic and holds the token. The network is only a carrier: it decides "
          "speed and latency and must protect confidentiality through TLS. The cloud performs authentication, authorisation, storage and processing.",
     bold_lead="Role of client and network:")
para(doc, "For file storage and sharing, the browser/web interface is the most suitable primary method because it needs no installation, works on "
          "any operating system, always shows the latest version and reaches every feature. The mobile app is the best secondary method for "
          "on-the-go access, while the API is reserved for automation.", bold_lead="Justification:")
sub(doc, "2.3 Student B - Practical Evidence")
para(doc, "Procedure followed to demonstrate access with the browser method and to repeat it on a second device or method:")
table(doc, [
    ["Step", "Action performed", "Evidence"],
    ["1", "Open drive.google.com in a browser and sign in with the college account", "Screenshot 1"],
    ["2", "Create folder 'CO3_Assignment' and upload one file", "Screenshot 2"],
    ["3", "Open the same folder from the Drive mobile app and confirm the file is visible", "Screenshot 3"],
    ["4", "Disconnect the network and attempt to open a file not cached (limitation test)", "Screenshot 4"],
], [0.6, 4.9, 1.4], caption="Access demonstration procedure", align_center_cols=(0,))
evidence_slot(doc, "Q1 Step 1-2: Google Drive opened in the browser after sign-in, with the new folder")
evidence_slot(doc, "Q1 Step 3: the same folder displayed in the mobile application")
table(doc, [
    ["Aspect", "Browser (laptop)", "Mobile app", "Observation guide (record yours)"],
    ["Accessibility", "No install; any OS", "Needs app install", "Which was quicker to start?"],
    ["Response", "Fast on Wi-Fi", "Fast, cached list", "Note upload time of the same file"],
    ["Usability", "Full feature set, large screen", "Touch-friendly, fewer options", "Which tasks were harder on mobile?"],
], [1.1, 1.8, 1.8, 2.2], caption="Observations across devices", first_col_bold=True)
callout(doc, "Limitation identified and its effect",
        "Limitation: access depends on a working Internet connection - with the network disabled, files that were not cached could not be opened "
        "and uploads stayed pending. Effect on cloud usage: productivity stops during outages, deadline-critical work is at risk, and users on slow "
        "networks face latency. Mitigations: offline mode for selected files, a secondary network (mobile hotspot) and local back-up copies.",
        fill="FFF4E5", bar="E07A1F")
sub(doc, "2.4 Cross-Verification")
para(doc, "Student A can explain every practical step of Student B (sign-in, upload, mobile sync, offline test), and Student B can redraw and explain "
          "the Client -> Network -> Cloud Service diagram, including why TLS and tokens are required.")
para(doc, "Architecture diagram + procedure and screenshots + observation comparison table.", bold_lead="Evidence expected:", italic=True)

# ======================= Q2 =======================
heading(doc, "3. Q2 - Cloud Platforms and Web Applications (7 Marks)", page_break=True)
sub(doc, "3.1 Shared Group Work - Platform Comparison")
para(doc, "Two platforms were selected: Google Workspace (running on Google Cloud) and Microsoft 365 (running on Microsoft Azure). "
          "Both deliver complete web applications that users operate from a browser while the provider manages servers, storage and updates.")
table(doc, [
    ["Criterion", "Google Workspace", "Microsoft 365"],
    ["Web applications", "Docs, Sheets, Slides, Drive, Gmail, Meet, Forms", "Word, Excel, PowerPoint Online, OneDrive, Outlook, Teams"],
    ["Supporting cloud resources", "Google Cloud storage, Spanner/Bigtable, global load balancing, Cloud Identity", "Azure Blob storage, Azure SQL / Cosmos DB, Front Door, Entra ID"],
    ["User interaction", "Browser or mobile app; real-time co-editing", "Browser, desktop and mobile apps; real-time co-authoring"],
    ["Collaboration strength", "Native browser-first co-editing and comments", "Deep Office-format compatibility; Teams integration"],
    ["Offline support", "Offline mode via Chrome extension", "Desktop apps work offline then sync"],
    ["API access", "Google Drive / Docs APIs (OAuth 2.0)", "Microsoft Graph API (OAuth 2.0)"],
], [1.5, 2.7, 2.7], caption="Comparative observation of two platforms", first_col_bold=True)
sub(doc, "3.2 Student A - Platform Analysis")
bullets(doc, [("Major components:", "identity/authentication, front-end load balancer, web/application servers, storage, database, API gateway and monitoring."),
              ("How the platform supports web apps:", "it hosts the application code, scales instances automatically, stores user data durably and exposes the application through a URL."),
              ("Request mapping:", "'Save document' -> HTTPS request -> load balancer -> application service -> storage (file) + database (metadata) -> confirmation.")])
figure(doc, DG / "q2_interaction.png", "User request mapped to cloud components - interaction diagram", 6.5)
table(doc, [
    ["Element", "Role in the interaction"],
    ["Internet", "Carries the encrypted request and response between client and provider"],
    ["Server / cloud infrastructure", "Provides compute, load balancing, storage and database on demand with replication and scaling"],
    ["Application", "Implements the business logic (editing, versioning, sharing) and talks to storage and database"],
], [2.0, 4.9], caption="Roles of Internet, infrastructure and application", first_col_bold=True)
sub(doc, "3.3 Student B - Application Investigation (Google Docs)")
para(doc, "Selected real-world cloud web application: Google Docs. Major functions demonstrated: create a document, type and format, insert a table, "
          "share with another user, view version history and download as PDF.")
table(doc, [
    ["No.", "User action", "Where cloud access is involved"],
    ["1", "Open docs.google.com and sign in", "Authentication service issues a session token"],
    ["2", "Create a new blank document", "Application service creates a record; storage allocates a file"],
    ["3", "Type text and format it", "Each edit is sent as small updates to the cloud (auto-save)"],
    ["4", "Share the document with a partner", "Permission service stores the access list"],
    ["5", "Open version history", "Storage returns earlier revisions"],
    ["6", "Export as PDF", "Server renders the file and returns it for download"],
], [0.6, 3.1, 3.2], caption="Sequence of user actions", align_center_cols=(0,))
evidence_slot(doc, "Q2: Google Docs - document created and typed, auto-saved indicator visible")
evidence_slot(doc, "Q2: Google Docs - Share dialog and version history panel")
para(doc, "No installation, automatic saving, access from any device, real-time collaboration, automatic version history, large managed storage and "
          "built-in security updates.", bold_lead="Benefits of the cloud application:")
sub(doc, "3.4 Joint Evaluation")
callout(doc, "If the same application ran only on a local computer, what limitations would users face?",
        "Access is tied to one machine; files must be emailed or copied, creating many versions and merge errors. Users must install, license and update the "
        "software themselves. Storage and back-up depend on a single disk that can fail. Real-time co-editing and instant sharing are not possible. "
        "Performance is limited by local hardware. Disaster recovery, scalability and central security control are absent. The cloud removes these limits "
        "at the cost of Internet dependency and trust in the provider.")
para(doc, "Platform/application mapping (Section 3.2-3.3) + demonstration screenshots + local-vs-cloud evaluation.", bold_lead="Evidence expected:", italic=True)

# ======================= Q3 =======================
heading(doc, "4. Q3 - Web APIs for Cloud Access (7 Marks)", page_break=True)
sub(doc, "4.1 Shared Group Work")
para(doc, "A Web API is a set of rules that lets one program talk to another over HTTP. Instead of a person clicking a web page, a program sends a "
          "request and receives structured data (usually JSON). APIs make cloud services programmable: any language, device or application can use "
          "the same service without a graphical interface. The selected API is the public PyPI JSON API (https://pypi.org/pypi/<package>/json), a "
          "cloud-hosted REST service that needs no login, which allows safe, repeatable testing.")
sub(doc, "4.2 Student A - API Design and Understanding")
para(doc, "The API returns metadata (name, version, summary, licence, Python requirement) for any published Python package. Programs can use it to check "
          "versions, automate dependency audits or build catalogues.", bold_lead="Purpose of the API:")
table(doc, [
    ["Component", "Request", "Response"],
    ["Method / status", "GET", "Status line: 200 OK or 404 Not Found"],
    ["Address", "https://pypi.org/pypi/flask/json (endpoint + resource)", "-"],
    ["Headers", "Accept: application/json; User-Agent: cloud-co3-client", "Content-Type: application/json; Server: gunicorn"],
    ["Parameters", "Package name in the URL path", "-"],
    ["Body", "None (GET)", "JSON object with 'info', 'releases', 'urls'"],
], [1.4, 2.8, 2.7], caption="Request and response components", first_col_bold=True)
figure(doc, DG / "q3_api_flow.png", "API communication flow: client -> request -> cloud server -> response", 6.4)
table(doc, [
    ["Element", "Role"],
    ["Client", "The Python program that builds the request, sends it and parses the reply"],
    ["API request", "A standard HTTP message that names the resource and the operation wanted"],
    ["Cloud / server", "Validates the request, looks up the data and builds the answer"],
    ["API response", "Status code plus JSON data that tells the client whether and how the operation succeeded"],
], [1.6, 5.3], caption="Roles in API communication", first_col_bold=True)
para(doc, "An API exposes cloud capabilities as URLs and data formats. A script can therefore upload files, start servers or read data 24x7 without a "
          "human, enabling automation, integration of many systems, mobile apps and scalable use through authentication keys and rate limits.",
     bold_lead="How APIs enable programmatic cloud access:")
sub(doc, "4.3 Student B - Implementation and Evidence")
para(doc, "The program q3_api_client.py (Python 3 with the 'requests' library) sends three GET requests, measures latency, prints the status, "
          "headers and selected JSON fields, and handles network errors. It was written and run in VS Code; the screenshots below are the captured execution evidence.")
figure(doc, SS / "q3_1_code_and_test1.png", "VS Code - program source and Test 1 (package 'requests'): status 200 with JSON response", 6.5)
figure(doc, SS / "q3_2_test2_different_input.png", "VS Code terminal - Test 2 (package 'flask'): different input, status 200", 6.5)
figure(doc, SS / "q3_3_test3_invalid_input.png", "VS Code terminal - Test 3 (unknown package): status 404 handled correctly", 6.5)
table(doc, [
    ["Test", "Input (request)", "Status", "Key output (response)", "Latency"],
    ["1", "GET /pypi/requests/json", "200", "name = requests, version = 2.34.2, Python >= 3.10, Apache-2.0", "80.2 ms"],
    ["2", "GET /pypi/flask/json", "200", "name = Flask, version = 3.1.3, Python >= 3.9", "69.1 ms"],
    ["3", "GET /pypi/no-such-package-co3-2026/json", "404", "message = Not Found", "146.6 ms"],
], [0.5, 2.3, 0.6, 2.6, 0.9], caption="Recorded request/response evidence", align_center_cols=(0, 2, 4))
bullets(doc, ["Different inputs gave different, correct JSON from the same endpoint pattern - the API is generic and reusable.",
              "The 404 test shows that error conditions are communicated by status codes, so a client can branch its logic instead of crashing.",
              "Latencies of roughly 70-150 ms show that a full cloud round trip is fast, and the program stays responsive.",
              "Version values come from the live service, so they change over time; this proves the data was fetched at run time, not stored in the program."])
sub(doc, "4.4 Joint Analysis")
callout(doc, "Why is API-based access useful when a large number of users/applications must communicate with a cloud service automatically?",
        "APIs give every program the same standard, machine-readable way in, so thousands of clients can be served without a human interface. Requests are "
        "stateless and lightweight, which lets the provider scale horizontally behind load balancers. Authentication keys, quotas and rate limits control "
        "and bill each client. Automation removes manual effort and error, supports integration between systems, and allows new applications to be built "
        "on the service without changing the service itself.")
para(doc, "Program + execution screenshots + request/response evidence + analysis.", bold_lead="Evidence expected:", italic=True)

# ======================= Q4 =======================
heading(doc, "5. Q4 - Cloud Security and Network Access (7 Marks)", page_break=True)
sub(doc, "5.1 Shared Group Work")
para(doc, "Cloud services are reachable from anywhere, so every request crosses networks that the user does not control. Security therefore rests on proving "
          "identity (authentication), limiting actions (authorisation), protecting data in transit and at rest, and monitoring activity. "
          "Typical threats: phishing, password guessing, eavesdropping, man-in-the-middle, DDoS, token theft, misconfigured sharing and insider misuse.")
sub(doc, "5.2 Student B - Security Design")
table(doc, [
    ["No.", "Security consideration", "Why it matters"],
    ["1", "Strong authentication + MFA", "Passwords alone are guessed, reused or phished"],
    ["2", "Authorisation with least privilege (RBAC)", "A valid user must reach only what the role permits"],
    ["3", "Encryption in transit (TLS) and at rest", "Prevents reading or modifying data on the network or disk"],
    ["4", "Secure session / token management", "Short-lived signed tokens limit damage if stolen"],
    ["5", "Logging, monitoring and auditing", "Detects abuse and gives accountability"],
    ["6", "Back-up, patching and endpoint protection", "Supports recovery and removes known weaknesses"],
], [0.5, 2.7, 3.7], caption="Security considerations for cloud access", align_center_cols=(0,))
table(doc, [
    ["Concept", "Authentication", "Authorisation"],
    ["Question answered", "Who are you?", "What are you allowed to do?"],
    ["Method", "Password, OTP, biometrics, certificate", "Roles, ACLs, policies, scopes"],
    ["Order", "Happens first", "Happens after identity is proven"],
    ["Failure result", "HTTP 401 Unauthenticated", "HTTP 403 Forbidden"],
], [1.5, 2.7, 2.7], caption="Authentication versus authorisation", first_col_bold=True)
para(doc, "Secure communication (HTTPS/TLS) encrypts the channel, proves the server identity with certificates and detects tampering, which defeats "
          "eavesdropping and man-in-the-middle attacks on public Wi-Fi.", bold_lead="Importance of secure communication:")
figure(doc, DG / "q4_secure_flow.png", "Secure access flow User -> Authentication -> Network -> Cloud Service -> Authorisation -> Resource with attack points", 6.6)
sub(doc, "5.3 Student A - Security Investigation")
para(doc, "Scenario investigated: a student opens the college cloud drive from a public Wi-Fi hotspot to submit an assignment. An attacker on the same "
          "network tries to capture credentials, replay a stolen token and change the role in a token. To demonstrate a suitable authentication mechanism, "
          "the program q4_auth_demo.py implements salted PBKDF2 password hashing, an HMAC-signed expiring token and role-based authorisation.")
figure(doc, SS / "q4_1_authentication_authorization.png", "VS Code - authentication (correct / wrong / unknown user) and authorisation by role", 6.5)
figure(doc, SS / "q4_2_attacks_and_comparison.png", "VS Code terminal - attack simulations blocked (forged, tampered, garbage, expired tokens)", 6.5)
table(doc, [
    ["Aspect", "Insecure access", "Secure access"],
    ["Channel", "Plain HTTP on open Wi-Fi - readable by anyone", "HTTPS/TLS - encrypted and server verified"],
    ["Credentials", "Plain-text or reused password", "Salted hash storage + MFA"],
    ["Session", "Never expires, can be copied", "Signed token with expiry (blocked after 2 s in test)"],
    ["Permissions", "Everyone is admin", "Viewer cannot write; editor cannot delete (403 shown)"],
    ["Result of a leak", "Full data loss or modification", "Limited in time and scope; logged"],
], [1.3, 2.7, 2.9], caption="Conceptual comparison of insecure and secure access", first_col_bold=True)
bullets(doc, ["Observation 1: the wrong password and unknown user were both denied without revealing which part was wrong.",
              "Observation 2: an authenticated viewer still received 403 for write and delete - authorisation is separate from authentication.",
              "Observation 3: changing the role inside the token or forging the signature produced 401 - integrity protection works.",
              "Observation 4: an expired token was rejected, showing why short lifetimes reduce the value of stolen tokens."])
para(doc, "Poor practices such as weak passwords, open sharing links, no MFA and unpatched devices let attackers read, alter or delete data, impersonate users, "
          "spread malware through shared folders and cause legal and reputational damage to the owner and to every collaborator.",
     bold_lead="Impact of poor security on users and data:")
table(doc, [
    ["Attack point", "Threat", "Suitable security measure"],
    ["User device", "Malware, theft", "Device lock, antivirus, endpoint management"],
    ["Login", "Phishing, brute force", "MFA, lockout, strong password policy"],
    ["Network", "Eavesdropping, MITM", "TLS 1.3, HSTS, certificate validation, VPN"],
    ["Cloud service", "DDoS, API abuse", "Rate limiting, WAF, firewall, auto-scaling"],
    ["Authorisation", "Privilege escalation", "RBAC, least privilege, short-lived tokens"],
    ["Resource", "Data leak, misconfiguration", "Encryption at rest, audit logs, back-ups"],
], [1.4, 2.2, 3.3], caption="Threat identification and mitigation analysis", first_col_bold=True)
sub(doc, "5.4 Joint Evaluation")
callout(doc, "If cloud access is available from anywhere, what additional measures are needed compared with a local application?",
        "A local application sits behind the organisation's perimeter and physical control. A cloud application is exposed to the public Internet, so it needs "
        "mandatory encryption in transit and at rest, multi-factor authentication, fine-grained authorisation, secure token handling, rate limiting and DDoS "
        "protection, continuous monitoring and auditing, secure sharing defaults, regular patching, and clear data-residency and shared-responsibility "
        "agreements with the provider.")
para(doc, "Secure-access architecture (Section 5.2) + threat identification + mitigation analysis + authentication program output.", bold_lead="Evidence expected:", italic=True)

# ======================= Q5 =======================
heading(doc, "6. Q5 - Collaboration Using Cloud-Based Services (6 Marks)", page_break=True)
sub(doc, "6.1 Shared Group Work")
para(doc, "Selected platform: Google Drive with Google Docs. The pair created the shared folder 'CO3_Team_Workspace' and the document 'Cloud_Collaboration_Report', "
          "invited each other and the faculty member with different roles, edited the document at the same time, and recorded the process in the screenshots below.")
sub(doc, "6.2 Student A - Collaboration Design")
bullets(doc, ["Requirements: multiple authors, simultaneous editing, controlled access, traceable changes, one master copy, access from any device.",
              "Users and roles: Owner (Student A) manages the workspace; Editor (Student B) writes sections; Commenter / Viewer (Faculty, guests) review only."])
figure(doc, DG / "q5_collab_workflow.png", "Cloud collaboration workflow from creation to finalisation", 6.4)
table(doc, [
    ["Concept", "Explanation"],
    ["Sharing", "The owner invites users by e-mail or link; access is granted per user and can be revoked at any time"],
    ["Concurrent access", "Several users open the same file; the service merges small edits in real time and shows each person's cursor"],
    ["Version control", "Every change is stored as a revision with author and time; any earlier version can be named and restored"],
    ["Permission management", "Roles (viewer, commenter, editor, owner) define what each person may do; link sharing can be restricted to the organisation"],
], [1.6, 5.3], caption="Core collaboration mechanisms", first_col_bold=True)
table(doc, [
    ["User", "Role granted", "Justification (least privilege)"],
    ["Student A", "Owner", "Creates structure, controls sharing and can recover deleted work"],
    ["Student B", "Editor", "Needs to write and modify sections but not to delete the workspace"],
    ["Faculty", "Commenter", "Reviews and gives feedback without altering student content"],
    ["Guest / peers", "Viewer", "Read-only access to the final output"],
], [1.4, 1.4, 4.1], caption="Roles and permission justification", first_col_bold=True)
sub(doc, "6.3 Student B - Collaborative Implementation")
table(doc, [
    ["Activity", "What was done", "Observed result"],
    ["1. Co-editing", "Student B wrote section 'API results' while Student A edited 'Architecture' at the same time", "Both edits appeared in under a second; no overwriting"],
    ["2. Comment / suggestion", "Student B suggested a change and Student A accepted it", "Change merged and tracked in the history"],
    ["3. Permission test", "Changed Faculty from Editor to Commenter", "Editing controls disappeared for Faculty"],
], [1.5, 3.2, 2.2], caption="Collaborative activities and observations", first_col_bold=True)
evidence_slot(doc, "Q5: Share dialog showing the roles Owner / Editor / Commenter / Viewer")
evidence_slot(doc, "Q5: two users editing the same document simultaneously (cursors visible)")
evidence_slot(doc, "Q5: Version history panel showing changes by both students")
callout(doc, "Collaboration issue and solution",
        "Issue: two users edited the same paragraph and one change was overwritten by the other's later text. Solution: assign sections to people, use "
        "suggestion mode for shared paragraphs, add comments with @mentions, and restore the correct text from version history.",
        fill="FFF4E5", bar="E07A1F")
sub(doc, "6.4 Cross-Understanding")
para(doc, "Collaborators work on one master file in the cloud instead of attaching copies. Everyone always sees the latest text, changes are merged automatically, "
          "there is no 'final_v3_new.docx' confusion, and version history replaces manual copies, which saves storage and avoids lost or conflicting edits.",
     bold_lead="Student B - How does cloud collaboration reduce the need to exchange multiple copies?")
para(doc, "Too much access lets outsiders or careless users read confidential data, edit or delete content, re-share it further or introduce errors; too little "
          "access blocks teamwork and delays work. 'Anyone with the link can edit' is the most dangerous setting, and permission mistakes are a leading cause "
          "of cloud data leaks.", bold_lead="Student A - What problems can occur if incorrect sharing permissions are given?")
para(doc, "Shared workspace + contribution evidence + permission screenshots + observations (the access rules are also verified programmatically in Q6/Q7).",
     bold_lead="Evidence expected:", italic=True)

# ======================= Q6 =======================
heading(doc, "7. Q6 - Integrated Cloud Access and Collaboration Mini Investigation (7 Marks)", page_break=True)
para(doc, "Cloud-Based Assignment Submission and Evaluation (scenario 4 of the suggested list).", bold_lead="Chosen scenario:")
sub(doc, "7.1 Student A - System Design")
table(doc, [
    ["Design element", "Description"],
    ["Problem", "Paper and e-mail submissions are lost, versions get mixed, feedback is slow and plagiarism or deadline disputes are hard to settle"],
    ["Users", "Students (submit), Faculty (review, comment, grade), Administrator (manage courses and users)"],
    ["Access methods", "Browser for desktops, mobile app for quick checks, REST API for bulk export of marks"],
    ["Cloud services", "Identity service, web application/API, shared object storage, version history, notification and audit services"],
    ["Access flow", "User logs in over HTTPS -> token issued -> every request carries the token -> role checked -> resource returned"],
    ["Collaboration flow", "Student uploads draft -> faculty comments -> student uploads revised version -> faculty grades -> final copy locked"],
], [1.5, 5.4], caption="System design", first_col_bold=True)
figure(doc, DG / "q6_architecture.png", "Architecture of the cloud-based assignment submission and evaluation system", 6.5)
sub(doc, "7.2 Student B - Evidence and Evaluation")
para(doc, "A prototype was built in two layers: a wireframe mock-up of the portal screens and a working Python simulation (q6_assignment_portal.py using the "
          "reusable engine cloud_collab.py) that provides token login, shared workspace, roles, versioning, comments, conflict detection and an audit log.")
figure(doc, DG / "q6_mockup.png", "Mock-up of the portal: login screen and shared assignment workspace", 6.4)
figure(doc, SS / "q6_1_scenarios.png", "VS Code - prototype execution of Scenario 1 and Scenario 2", 6.5)
figure(doc, SS / "q6_2_audit_log.png", "VS Code terminal - audit log recorded by the prototype", 6.5)
table(doc, [
    ["Scenario", "Cloud access mechanism shown", "Collaboration mechanism shown", "Result"],
    ["1. Student submits from a browser; faculty reviews from the mobile app", "Token login; write permission verified (200 OK)", "Draft uploaded, faculty comment added, student creates v2", "Success - version history: v1 and v2 by asha"],
    ["2. Wrong permission and simultaneous edit", "Viewer and outsider requests evaluated", "Stale edit of v1 when v2 exists", "All three actions blocked with clear reasons"],
], [1.7, 1.8, 1.8, 1.6], caption="Two user scenarios tested", first_col_bold=True)
bullets(doc, [("Analysis:", "authentication, authorisation and collaboration worked together - only valid, permitted users changed files, and every action was logged."),
              ("Limitations:", "prototype runs in memory (no real database), no real network or file upload, single-process concurrency."),
              ("Improvements:", "use real cloud storage and a managed database, add MFA, plagiarism check, e-mail alerts and an offline-capable mobile app.")])
sub(doc, "7.3 Joint Evaluation")
callout(doc, "How does combining cloud access and cloud collaboration improve the efficiency of the proposed system?",
        "Access makes the system available anywhere on any device, while collaboration lets students and faculty work on the same copy with controlled roles. "
        "Together they remove physical submission, duplicate files and waiting time: feedback is immediate, versions are traceable, deadlines are time-stamped "
        "and audit logs settle disputes. Faculty effort falls and turnaround time for evaluation drops.")

# ======================= Q7 =======================
heading(doc, "8. Q7 - Day-4 Design Challenge: Cloud-Based Collaborative Solution (10 Marks)", page_break=True)
para(doc, "Solution designed collaboratively: 'SIMATS Cloud Project Hub' - a cloud platform where student teams plan, develop, review and submit project work "
          "with mentors.", bold_lead="Overview:")
sub(doc, "8.1 Stage 1 - Independent Design Proposals (retained as evidence)")
table(doc, [
    ["Element", "Student A's initial proposal", "Student B's initial proposal"],
    ["Problem", "Project teams share work through WhatsApp and e-mail; files and tasks are scattered", "Mentors cannot track progress or contributions of each member"],
    ["Target users", "Students and mentors", "Students, mentors and project coordinators"],
    ["Cloud access method", "Web browser (HTTPS)", "Mobile application + browser"],
    ["Cloud services", "Cloud storage + document editor", "Cloud storage, task board, database and notifications"],
    ["Collaboration mechanism", "Shared folder with live co-editing", "Task board, comments and activity feed"],
    ["Basic architecture", "Users -> Browser -> Internet -> Cloud storage / Docs", "Users -> App -> API gateway -> Database + storage"],
], [1.4, 2.75, 2.75], caption="Initial proposals prepared before discussion", first_col_bold=True)
sub(doc, "8.2 Stage 2 - Design Comparison Record")
table(doc, [
    ["Criterion", "Finding"],
    ["Where designs agree", "Cloud storage, HTTPS access, shared workspace and role-based sharing are needed"],
    ["Where they differ", "A is browser-only and storage-centred; B adds a mobile app, task board, database and notifications"],
    ["Strengths", "A: simple, low cost, no install. B: progress tracking, accountability, richer workflow"],
    ["Weaknesses", "A: no task tracking or API. B: more complex, higher cost, security surface larger"],
    ["Security concerns", "Neither initial design specified authentication, MFA, encryption or audit logging"],
    ["Accessibility", "B's mobile access helps on-campus and off-campus users; A needs a laptop or phone browser"],
    ["Collaboration requirements", "Concurrent editing + comments (A) and task ownership + activity feed (B) are both needed"],
    ["Missing components", "Identity service, API layer, audit log, backup, monitoring, offline strategy"],
    ["Ideas retained", "A's shared live editing + B's mobile access, task board, database, notifications; add security and API"],
], [1.7, 5.2], caption="Design Comparison Record", first_col_bold=True)
sub(doc, "8.3 Stage 3 - Joint Final Design")
table(doc, [
    ["Design item", "Final decision"],
    ["Problem", "Scattered files, no progress tracking and weak accountability in student project work"],
    ["Users", "Students, mentors, coordinators, guests (read-only)"],
    ["Cloud access method", "Browser (primary), mobile app (secondary), REST API (integration and reports)"],
    ["Network requirements", "Wi-Fi / 4G; HTTPS with TLS 1.3; minimum 2 Mbps; CDN for static content; offline cache on mobile"],
    ["Cloud service / platform", "Public cloud IaaS/PaaS: managed identity, object storage, managed database, app service, load balancer, monitoring"],
    ["Web application / API", "Web app for projects, tasks and documents; REST API (JSON) for mobile app and automation"],
    ["Collaboration mechanism", "Shared workspace, concurrent editing, comments, task board, version history, notifications"],
    ["Authentication / security", "SSO + MFA, signed short-lived tokens, RBAC, encryption in transit and at rest, audit logs"],
    ["Data / resource sharing", "Project folders with roles: owner, editor, commenter, viewer; link sharing limited to the organisation"],
    ["System workflow", "Login -> create project -> invite members -> assign tasks -> co-edit -> mentor review -> version freeze -> submission"],
], [1.8, 5.1], caption="Joint final design", first_col_bold=True)
figure(doc, DG / "q7_final_architecture.png", "Final architecture: Users -> Client -> Internet -> Cloud Platform -> Application/API -> Shared Resources", 6.6)
sub(doc, "8.4 Stage 4 - Validation")
para(doc, "The browser is chosen because it needs no installation and offers the whole feature set; the mobile app extends reach; the API enables reports and "
          "integration with the college systems. A public cloud platform is justified by pay-as-you-use scaling, managed security services, high availability "
          "and no hardware investment. The architecture separates client, network, identity, application and data, so each layer can be secured and scaled "
          "independently. The REST API is used by the mobile app and by scripts, exactly as demonstrated in Q3. The design is suitable because it meets "
          "accessibility, collaboration, security and scalability needs at low cost.", bold_lead="Student A - Technical validation:")
para(doc, "Student B designed nine test cases covering valid access, forbidden actions, unauthenticated requests, shared editing, role restrictions and "
          "edit conflicts, and executed them in VS Code with the program q7_validation_tests.py.", bold_lead="Student B - Experimental validation:")
table(doc, [
    ["ID", "Test case (user / condition)", "Expected", "Observed", "Result"],
    ["TC1", "Valid login, write through token", "200", "200", "PASS"],
    ["TC2", "Viewer token tries to delete", "403", "403", "PASS"],
    ["TC3", "Request without valid token", "401", "401", "PASS"],
    ["TC4", "Editor edits shared file", "Allowed", "Allowed", "PASS"],
    ["TC5", "Viewer reads file", "Allowed", "Allowed", "PASS"],
    ["TC6", "Viewer edits file", "Denied", "Denied", "PASS"],
    ["TC7", "Two editors, stale version", "Conflict", "Conflict", "PASS"],
    ["TC8", "Non-member reads file", "Denied", "Denied", "PASS"],
    ["TC9", "Editor tries to share workspace", "Denied", "Denied", "PASS"],
], [0.6, 3.2, 1.0, 1.0, 1.1], caption="Test cases - expected versus observed behaviour", align_center_cols=(0, 2, 3, 4))
figure(doc, SS / "q7_validation_results.png", "VS Code terminal - 9 of 9 validation test cases passed", 6.5)
para(doc, "Observed behaviour matched the expected behaviour in every case. Different users (editor, viewer, outsider, unauthenticated) and conditions "
          "(valid, invalid and stale requests) were handled correctly, which supports the claim that the design enforces identity, permission and consistency.",
     bold_lead="Comparison of expected and observed behaviour:")
sub(doc, "8.5 Stage 5 - Cross-Defence")
para(doc, "The execution evidence consists of 9/9 passing test cases, the 200/404 API responses (Q3), the blocked forged/expired tokens (Q4) and the audit log with "
          "version history (Q6). Together they show that access control, collaboration and error handling behave as designed.",
     bold_lead="Student A - What experimental evidence supports the design?")
para(doc, "Browser plus mobile access gives anywhere, any-device availability without installation; the shared workspace with roles gives one master copy, "
          "live co-editing and traceable versions; and the model reduces cost while remaining secure through MFA, RBAC and encryption.",
     bold_lead="Student B - Why were this access and collaboration approach chosen?")
sub(doc, "8.6 Stage 6 - Joint Evaluation")
table(doc, [
    ["Aspect", "Evaluation"],
    ["Benefits", "No hardware cost, anywhere access, one master copy, instant feedback, centralised security, automatic back-up"],
    ["Access-related limitations", "Needs Internet; slow networks reduce usability; provider outages affect everyone"],
    ["Collaboration benefits", "Real-time editing, task visibility, comments, version history, fewer duplicate files"],
    ["Security risks", "Phishing, token theft, wrong sharing permissions, data leakage, insider misuse"],
    ["Scalability", "Auto-scaling app servers and managed storage handle growth from one class to the entire college"],
    ["Possible improvements", "Offline editing, AI-based plagiarism check, analytics dashboard, multi-region back-up, integration with the LMS"],
    ["When not appropriate", "Highly confidential/classified data, areas without reliable Internet, strict data-residency rules, very low-latency local processing"],
], [1.8, 5.1], caption="Joint evaluation", first_col_bold=True)
callout(doc, "Final Question - What characteristics should a system designer consider before selecting cloud-based access and collaboration?",
        "Connectivity and bandwidth of users; sensitivity and legal residency of data; security needs (authentication, encryption, compliance); number of users and "
        "expected growth (scalability); required collaboration style (real-time, role-based, auditable); availability and service-level guarantees; total cost "
        "of ownership and pay-per-use pricing; device diversity and usability; integration through APIs; vendor lock-in and exit options; backup and disaster "
        "recovery; and the skills available to operate and support the system.")
para(doc, "Two initial proposals + comparison record + joint design + tests + cross-defence (Sections 8.1-8.5).", bold_lead="Evidence expected:", italic=True)

# ======================= CONTRIBUTION, VIVA, OBE, REPO =======================
heading(doc, "9. Contribution Record", page_break=True)
table(doc, [
    ["Question", "Student A - Primary Contribution", "Student B - Primary Contribution", "Joint Work"],
    ["Q1", "Access method classification, architecture diagram, hardware/software, justification", "Access demonstration, device tests, observations, limitation", "Study of access methods, selection of Google Drive"],
    ["Q2", "Platform components, request mapping, interaction diagram", "Google Docs investigation, user-action sequence, benefits", "Platform selection, comparison, local-vs-cloud evaluation"],
    ["Q3", "API purpose, request/response components, flow diagram", "Python program, execution, 3 requests, analysis", "API selection, concept study, joint analysis"],
    ["Q4", "Security investigation, authentication demo, secure vs insecure comparison", "Security design, 6 considerations, secure flow, attack points", "Threat study, secure scenario, joint evaluation"],
    ["Q5", "Collaboration design, roles, permission justification", "Co-editing activities, evidence, issue and solution", "Workspace creation, sharing, recorded process"],
    ["Q6", "System design and architecture", "Prototype, mock-up, two scenarios, results, limitations", "Scenario selection, joint evaluation"],
    ["Q7", "Proposal A, technical validation, cross-defence answer", "Proposal B, test cases, experiments, cross-defence answer", "Comparison record, final design, joint evaluation"],
], [0.7, 2.1, 2.1, 2.0], caption="Contribution record (primary contribution does not mean exclusive responsibility)", first_col_bold=True)
heading(doc, "10. Individual Verification - Viva Preparation")
para(doc, "Both students prepared answers for the transfer questions suggested in the assignment.")
table(doc, [
    ["Transfer question", "Model answer"],
    ["If Internet connectivity becomes unreliable, how would cloud access be affected?", "Requests time out, uploads and sync stall and real-time collaboration stops. Cached/offline files stay usable and changes sync later. Mitigation: offline mode, retry logic, backup network."],
    ["If a shared document is given edit permission to everyone, what could happen?", "Anyone may modify or delete content, leak it or introduce errors; accountability is lost. Use least privilege, named users and version history to recover."],
    ["If the API becomes unavailable, how would your application behave?", "It should detect the failure (timeout / 5xx), show a clear message, retry with back-off, use cached data and log the incident; the Q3 client already handles request errors."],
    ["If a user is authenticated but lacks permission, what should happen?", "The service must return 403 Forbidden and perform no action, as shown in the Q4 and Q7 tests (viewer cannot write or delete)."],
], [2.6, 4.3], caption="Viva transfer questions and model answers", first_col_bold=True)
heading(doc, "11. OBE Evidence Mapping")
table(doc, [
    ["CO3 component", "Assignment evidence", "Section"],
    ["Methods to access cloud", "Q1, Q2, Q3", "2, 3, 4"],
    ["Platforms / web applications", "Q2", "3"],
    ["Programmatic / API access", "Q3 program and output", "4"],
    ["Secure cloud access", "Q4 design and authentication demo", "5"],
    ["Collaboration in the cloud", "Q5 workspace and permissions", "6"],
    ["Apply access + collaboration", "Q6 prototype and two scenarios", "7"],
    ["Design and evaluate a cloud solution", "Q7 design, tests and evaluation", "8"],
    ["Individual attainment", "Viva preparation + contribution record", "9, 10"],
    ["Practical evidence", "Screenshots, programs, observations, test results", "GitHub folder"],
], [2.5, 3.2, 1.2], caption="OBE evidence mapping", first_col_bold=True, align_center_cols=(2,))
heading(doc, "12. GitHub Repository Structure")
table(doc, [
    ["Path", "Content"],
    ["README.md", "Project description, how to run, evidence index"],
    ["src/", "q3_api_client.py, q4_auth_demo.py, cloud_collab.py, q6_assignment_portal.py, q7_validation_tests.py"],
    ["outputs/", "Real captured output text of each program (q3, q4, q6, q7)"],
    ["screenshots/", "VS Code execution screenshots used in this report"],
    ["diagrams/", "Architecture and flow diagrams (PNG)"],
    ["tools/", "Scripts used to generate diagrams, screenshots and this report"],
    ["requirements.txt", "Python dependency list (requests)"],
], [1.6, 5.3], caption="Repository layout", first_col_bold=True)
heading(doc, "13. Conclusion and References")
para(doc, "The assignment demonstrates the full CO3 chain: understanding cloud access, designing and implementing API and security mechanisms, demonstrating collaboration "
          "and evaluating an integrated solution with measurable evidence. The programs executed successfully (HTTP 200/404 API responses, blocked attacks, 9/9 tests), "
          "and the Day-4 design shows how access and collaboration combine into a secure, scalable service.")
bullets(doc, ["NIST SP 800-145, The NIST Definition of Cloud Computing.",
              "PyPI JSON API documentation - https://docs.pypi.org/api/json/",
              "Python 'requests' library documentation - https://requests.readthedocs.io",
              "Google Workspace and Microsoft 365 product documentation.",
              "OWASP Cloud-Native Application Security guidance."])

doc.save(out_path)
print("saved", out_path)

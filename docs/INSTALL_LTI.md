# Installing LMS Bridge in your LMS — click-by-click runbooks (LTI 1.3 / Advantage)

LMS Bridge is a standard **LTI 1.3 / LTI Advantage** tool. Register it once with your LMS and it
works inside any course: single sign-on, automatic rostering (NRPS), gradebook access (AGS), and
one-click placement (Deep Linking).

This guide has an exact runbook for **Canvas, Moodle, Brightspace (D2L), and Blackboard
(Anthology)**. Steps were verified against current vendor documentation (2025–2026); LMS admin UIs
change, so where a label may vary by release it's flagged. You need **LMS-admin access** for every
path below (LTI 1.3 cannot be installed by an instructor alone).

---

## 0. The four LMS Bridge URLs (the tool side)

From your running backend at `https://YOUR-HOST`, every LMS needs these. `GET
https://YOUR-HOST/api/v1/lti/config` returns them as JSON, and they're also shown in the admin
console under the **LMS (LTI)** tab.

| Role in the LMS form | LMS Bridge URL |
|----------------------|----------------|
| OpenID Connect **initiation / login** URL | `https://YOUR-HOST/api/v1/lti/login` |
| **Target Link URI** / Launch URL | `https://YOUR-HOST/api/v1/lti/launch` |
| **Redirect URI(s)** | `https://YOUR-HOST/api/v1/lti/launch` |
| Public **keyset (JWKS)** URL | `https://YOUR-HOST/api/v1/lti/jwks` |
| **Dynamic Registration** URL (Canvas/Moodle one-click) | `https://YOUR-HOST/api/v1/lti/register` |

Set `TOOL_BASE_URL` and `FRONTEND_BASE_URL` (backend env) to your real public hostnames first, or
launch redirects won't resolve. Everything must be served over **HTTPS**.

### Two ways to register
- **Dynamic Registration (one click)** — supported by **Canvas** and **Moodle**. You paste the
  Dynamic Registration URL above; the LMS and LMS Bridge exchange all config automatically.
- **Manual registration** — used by **Brightspace** and **Blackboard** (and works for any LMS). You
  enter the four URLs in the LMS, then record what the LMS gives back (issuer, client ID,
  deployment ID, and the LMS's auth/token/JWKS endpoints) in LMS Bridge's **LMS (LTI)** tab → **+
  Add LMS manually** (API equivalent: `POST /api/v1/lti/registrations`).

After any launch, LMS Bridge auto-provisions the user, course, and role on first use — no extra
password, no manual roster.

### Two ways to roll it out (admin's choice)
After the one-time admin registration, you decide how widely it's available — each LMS section below
spells out both under **"Admin's choice — who can use it":**
- **Account-wide:** make it available to every course so any instructor can use it (Canvas can even
  push it into every course's navigation automatically).
- **Opt-in per instructor / pilot:** enable it but limit scope (a developer-key Client ID handed to
  instructors, a course-category/org-unit restriction, etc.) so only chosen instructors add it to
  their own courses. Ideal for a single-instructor pilot.

In every LMS except Canvas's account-wide nav push, the instructor still does the final one-click
placement in their own course.

---

## 1. Canvas (Instructure)

Canvas supports both dynamic registration and manual key entry. Dynamic is fastest.

### Platform endpoints (Canvas Cloud / production)
These are the same for every `*.instructure.com` tenant (for **beta**/**test**, replace
`sso.canvaslms.com` with `sso.beta.canvaslms.com` / `sso.test.canvaslms.com`; self-hosted Canvas
uses its own host):

| LMS Bridge field | Value |
|------------------|-------|
| `issuer` | `https://canvas.instructure.com` |
| `auth_login_url` (OIDC auth redirect) | `https://sso.canvaslms.com/api/lti/authorize_redirect` |
| `auth_token_url` (OAuth2 token) | `https://sso.canvaslms.com/login/oauth2/token` |
| `key_set_url` (Canvas JWKS) | `https://sso.canvaslms.com/api/lti/security/jwks` |

### Option A — Dynamic Registration (recommended)
1. **Admin** → click your **account name** → **Developer Keys**.
2. Click **+ Developer Key** → **+ LTI Registration**.
3. In **Dynamic Registration URL**, paste `https://YOUR-HOST/api/v1/lti/register` → **Continue**.
4. The LMS Bridge registration screen opens; confirm → control returns to Canvas.
5. On the review screen, leave **Permissions** (scopes) and **Placements** enabled → **Enable &
   Close**.
6. Back on **Developer Keys**, set the key's **State** to **ON** and **copy the Client ID**. **This
   is the only required admin step** — turning the key ON makes the Client ID usable institution-wide.
   You now choose *who installs it where* (step 7).
7. **Get it into courses — two ways:**
   - **Account-wide (admin pushes to everyone):** **Admin** → **Settings** → **Apps** tab → **View
     App Configurations** → **+ App** → **Configuration Type: By Client ID** → paste the Client ID →
     **Submit** → **Install**. It now appears in every course. *(Newer "Canvas Apps" UI: **Admin →
     Apps → Manage → Install a New App → LTI 1.3 → Dynamic Registration**, then step through
     Permissions → Data sharing → Placements → Install.)*
   - **Per instructor (opt-in — like Moodle/Brightspace/Blackboard):** skip the account-wide install.
     Just hand instructors the **Client ID**; each one installs it in only their own course (see
     **Instructor self-install** below). This is the closest Canvas gets to instructor-only setup.

### Option B — Manual key entry
1. **Admin → Developer Keys → + Developer Key → + LTI Key**.
2. **Method: Manual Entry**. Fill: **Title**, **Description**, **Target Link URI** =
   `https://YOUR-HOST/api/v1/lti/launch`, **OpenID Connect Initiation Url** =
   `https://YOUR-HOST/api/v1/lti/login`, **JWK Method: Public JWK URL** =
   `https://YOUR-HOST/api/v1/lti/jwks`. Add **Redirect URIs** = the launch URL.
   *(Or choose **Enter URL** and paste `https://YOUR-HOST/api/v1/lti/config` — but that returns the
   LMS Bridge URL list, not a Canvas-shaped key, so Manual Entry is clearer here.)*
3. Under **LTI Advantage Services**, enable the toggles for **assignment/line-item data** (AGS) and
   **retrieve user data for the context** (NRPS). Under **Placements**, add **Course Navigation**
   (and, if you want content insertion, a placement with message type **LtiDeepLinkingRequest**).
4. **Save** → set **State ON** → copy **Client ID**, then install it via either route in Option A, step 7.
5. Record the Canvas endpoints above + the Client ID (and the Deployment ID from the app's
   **Settings → Deployment ID**) in LMS Bridge's **LMS (LTI)** tab.

### Instructor self-install (course level — no admin push needed)
Once the developer key is **ON** (the admin's one-time step above), an instructor can add LMS Bridge
to just their own course — the same opt-in flow as Moodle, Brightspace, and Blackboard:
1. **Course → Settings → Apps tab → + App → Configuration Type: By Client ID** → paste the **Client
   ID** your admin gave you → **Submit** → **Install**. *(Same install screen as the account-wide
   one, but scoped to your course only — no admin rights needed.)*
2. Surface it: **Course → Settings → Navigation** → drag **LMS Bridge** into the menu → **Save**; or
   **Course → Modules → + → External Tool → LMS Bridge → Add Item**.

*If your admin already installed it account-wide, skip step 1 — just do step 2.*

---

## 2. Moodle (4.x and 5.x)

The LTI 1.3 admin flow and labels are identical across Moodle 4.0–5.2.

### Option A — Dynamic Registration (recommended)
1. **Site administration → Plugins → Activity modules → External tool → Manage tools**.
2. In the **Tool URL** box, paste `https://YOUR-HOST/api/v1/lti/register`.
3. Click **Add LTI Advantage** (not "Add Legacy LTI").
4. The LMS Bridge registration panel opens and auto-exchanges configuration; it closes and the tool
   appears under **Pending**.
5. Review it, then **activate** the tool (move Pending → Active). Set it to **Show in activity
   chooser** so instructors can add it.

### Option B — Manual configuration
1. **Manage tools → configure a tool manually**.
2. Set: **Tool name**; **Tool URL** = `https://YOUR-HOST/api/v1/lti/launch`; **LTI version = LTI
   1.3**; **Public key type = Keyset URL**; **Public keyset** =
   `https://YOUR-HOST/api/v1/lti/jwks`; **Initiate login URL** =
   `https://YOUR-HOST/api/v1/lti/login`; **Redirection URI(s)** =
   `https://YOUR-HOST/api/v1/lti/launch`. Tick **Supports Deep Linking** (Content-Item).
3. **Services**: set **IMS LTI Assignment and Grade Services** to *grade sync and column
   management* (AGS), and **IMS LTI Names and Role Provisioning** to *retrieve members' information*
   (NRPS). **Privacy**: share name/email as your policy allows; **Accept grades from the tool** as
   needed. **Save changes**.
4. Open the tool's **Tool configuration details** (the list icon on the tool card) and copy Moodle's
   platform values into LMS Bridge's **LMS (LTI)** tab:

| Moodle "Tool configuration details" | LMS Bridge field |
|-------------------------------------|------------------|
| **Platform ID** | `issuer` |
| **Client ID** | `client_id` |
| **Deployment ID** | deployment id |
| **Authentication request URL** (`/mod/lti/auth.php`) | `auth_login_url` |
| **Access token URL** (`/mod/lti/token.php`) | `auth_token_url` |
| **Public keyset URL** (`/mod/lti/certs.php`) | `key_set_url` |

### Admin's choice — who can use it
Moodle external tools are always *added to a course by the instructor*; the admin controls who is
allowed to:
- **Available to everyone (recommended):** when activating the tool, set **Tool visibility = Show in
  activity chooser and as a preconfigured tool**. Every instructor can then self-add it (below).
- **Restricted pilot:** keep it off the chooser (or share the preconfigured tool with only chosen
  course categories) and let just the pilot instructors add it. 

There is no whole-site auto-placement in Moodle — even when it's available to all, each instructor
still adds the activity to their own course.

### Instructor places it in a course
- Course → **Edit mode** on → **Add an activity or resource** → pick **LMS Bridge** (or **External
  tool** → Preconfigured tool = LMS Bridge). If deep linking is on, click **Select content** to pick
  a specific activity → **Save and return to course**.

---

## 3. Brightspace (D2L)

Brightspace splits the work across two admin pages: **register** under *Manage Extensibility*, then
**deploy** under *External Learning Tools*. Requires the **Manage LTI Tools** permission.

### Step 1 — Register the tool
1. **Admin Tools (gear) → Manage Extensibility → LTI Advantage tab → Register Tool**.
2. **Dynamic (recommended):** choose **Dynamic**, paste `https://YOUR-HOST/api/v1/lti/register`,
   keep **Configure Deployment** on, click **Register** (it opens LMS Bridge in a new tab to confirm).
   Per spec the new registration is **disabled by default — enable it** afterward. *(Standard/manual
   alternative: enter **Name**, **Domain** = `YOUR-HOST`, **Redirect URLs** =
   `https://YOUR-HOST/api/v1/lti/launch`, **OpenID Connect Login URL** =
   `https://YOUR-HOST/api/v1/lti/login`, **Target Link URI** = the launch URL, **Keyset URL** =
   `https://YOUR-HOST/api/v1/lti/jwks`; enable **Assignment and Grade Services** + **Names and Role
   Provisioning Services**; recommended: enable substitution parameter `$Activity.id.history`.)*
3. Brightspace shows a config block. Copy these into LMS Bridge's **LMS (LTI)** tab:

| Brightspace label | LMS Bridge field |
|-------------------|------------------|
| **Issuer** (your tenant host, e.g. `https://<tenant>.brightspace.com`) | `issuer` |
| **Client Id** | `client_id` |
| **OpenId Connect Authentication Endpoint** | `auth_login_url` |
| **Brightspace OAuth2 Access Token URL** | `auth_token_url` |
| **Brightspace Keyset URL** | `key_set_url` |

### Step 2 — Create a Deployment (this is what shares it to courses)
1. **Admin Tools (gear) → External Learning Tools → LTI Advantage tab → New Deployment**.
2. **Tool** = the registration you just made. Add **Name**.
3. **Extensions**: tick **Assignment and Grade Services** and **Names and Role Provisioning
   Services**. **Security Settings**: enable the user fields to send (Name, Email, User ID) and **Org
   Unit Information**.
4. **Add Org Units** → select the org unit(s) (and descendants) the tool should be available in →
   **Create Deployment**.
5. Copy the returned **Deployment Id** (GUID) into the deployment field in LMS Bridge's **LMS (LTI)**
   tab.

### Step 3 — Create a Link (so it can be placed)
- On the deployment → **View Links → New Link** → **Name**, **URL** =
  `https://YOUR-HOST/api/v1/lti/launch`, **Type** = *Basic Launch* (or *Deep Linking Quicklink* for
  content selection) → **Save and Close**.

### Admin's choice — how wide to deploy
The **Org Units** you attach in Step 2 set the scope:
- **Whole organization (account-wide):** add the top-level org unit **+ descendants** → every course
  can use it and any instructor self-places the link (below).
- **Specific departments/courses (opt-in pilot):** add only those org units → only those courses see
  it.

Either way the instructor places the link in their own course — Brightspace has no force-into-every-
course option.

### Instructor places it in a course
- **Content → Add Existing → External Learning Tools** → select the LMS Bridge link; or via **Insert
  Stuff** / a **Quicklink** in the editor. Deep-Linking links open the tool's content picker.

---

## 4. Blackboard Learn (Anthology)

Blackboard uses a **two-actor** model. The **tool owner registers once** in the Anthology Developer
Portal to get a Client ID; **each institution's admin** then deploys that Client ID. Blackboard does
**not** use OIDC dynamic registration, so the LMS Bridge `/register` URL is not used here.

### Step 1 — Tool owner: register in the Developer Portal (one time, all institutions)
1. Sign in at **https://developer.anthology.com** (a.k.a. `developer.blackboard.com`).
2. **Register a REST or LTI application**. Fill **Application Name**, **Description**,
   **Domain(s)** = `YOUR-HOST` (no scheme).
3. Toggle **My integration Supports LTI 1.3 = ON**, then enter:
   - **Login Initiation URL** = `https://YOUR-HOST/api/v1/lti/login`
   - **Tool Redirect URL(s)** = `https://YOUR-HOST/api/v1/lti/launch`
   - **Tool JWKS URL** = `https://YOUR-HOST/api/v1/lti/jwks`
   - **Signing Algorithm** = RS256
4. **Register Application**. The portal shows (once — save them) the **Application ID (= Client
   ID)** and the global endpoints.
5. Record the global Blackboard endpoints in LMS Bridge's **LMS (LTI)** tab (one registration serves
   every Blackboard institution that uses this Client ID):

| Blackboard value | LMS Bridge field |
|------------------|------------------|
| **Issuer** | `https://blackboard.com` |
| **OIDC auth request URL** | `https://developer.blackboard.com/api/v1/gateway/oidcauth` |
| **Auth token URL** | `https://developer.blackboard.com/api/v1/gateway/oauth2/jwttoken` |
| **Platform JWKS** | `https://developer.blackboard.com/api/v1/management/applications/<APPLICATION_ID>/jwks.json` |

> Tip: turn on **auto-register deployments** for this registration in the **LMS (LTI)** tab, so each
> new institution's Deployment ID is trusted automatically on its first verified launch — no manual
> deployment entry per school.

### Step 2 — Each institution's Blackboard admin: deploy the Client ID
1. **Admin** (Ultra: left nav **Admin**; Original: **System Admin** tab) → **Integrations → LTI Tool
   Providers**.
2. **Register LTI 1.3/Advantage Tool** → paste the **Client ID** → **Submit**.
3. On **Modify LTI 1.3 Tool** (Login/Redirect/JWKS/Domain auto-populate from the portal):
   - **Tool Status = Approved**.
   - **Institution Policies → User Fields to Send**: enable **Role in Course**, **Name**, **Email
     Address**.
   - **Allow grade service access = Yes** (AGS).
   - **Allow Membership Service access = Yes** (NRPS).
   - **Submit**.
4. Also ensure **LTI Tool Providers → Manage Global Properties → "Allow configured tool providers to
   post grades"** is enabled.
5. Copy the generated **Deployment ID** (shown after Submit; later via the tool's **Edit**) — if you
   did **not** enable auto-register, add it under this registration in LMS Bridge's **LMS (LTI)** tab.

### Admin's choice — who can use it
After the tool is **Approved** (Step 2), control availability:
- **All courses (account-wide):** leave it available in the **Content Market / Institution Tools** so
  every course sees it; any instructor self-adds it (below).
- **Restricted pilot:** use Blackboard's tool-availability / course-tool settings to limit it to
  specific courses or terms.

Instructors always place it via the Content Market — Blackboard doesn't auto-insert it into every
course.

### Instructor places it in a course
- **Ultra:** Course Content → **+** → **Content Market** → **Institution Tools** → **LMS Bridge**.
- **Original:** in a content area, **Build Content** → the LMS Bridge placement (or **Build Content →
  Web Link** with **"This link is to a Tool Provider"** checked).

---

## 5. Verify the install worked

1. As an instructor, launch LMS Bridge from the course → you should land in the **instructor
   console** (no separate login).
2. As a student, launch it → you should land on the **adaptive dashboard**.
3. Check the connection appears in LMS Bridge's **LMS (LTI)** tab. If a launch is rejected, the most
   common causes are: a mismatched **Redirect URI**, the wrong **JWKS** URL, `TOOL_BASE_URL` not set
   to your real host, or a **Deployment ID** that wasn't recorded (unless auto-register is on).

## 6. Data-flow notes

- **Scores** arrive via **AGS** at the line-item level — map each LMS line item to a concept when you
  set up the course so results become concept-level signals.
- For **per-question multiple-choice answers** (the distractor-level misconception diagnosis),
  deliver the formative quiz **through LMS Bridge** — AGS alone exposes only aggregate scores.
- Any write-back to the LMS gradebook is a **non-graded** column; LMS Bridge never sets grades.

## 7. Production / certification notes

- The tool's signing key is generated once (table `lti_tool_keys`) and published at
  `/api/v1/lti/jwks`; keep it stable across instances (shared database).
- Pursue **1EdTech LTI Advantage certification** and a **TrustEd Apps** listing, and prepare FERPA /
  accessibility (VPAT) / security (HECVAT) documentation, to ease institutional procurement.
- Endpoints and labels above were verified against current vendor docs (2025–2026); confirm against
  your specific LMS version, since admin UIs change.

#!/usr/bin/env python3
"""Generate the one-page per-LMS install guides (PDF) in en/ar/es/fr.

Reproducible source for marketing/guides/install-<lms>[.<lang>].pdf. English keeps the base
filename; other languages use install-<lms>.<lang>.pdf. Rendered with WeasyPrint (HarfBuzz does
the Arabic shaping; DejaVu Sans carries the glyphs). Vendor menu breadcrumbs and URLs are kept
verbatim in English inside translated prose, since admin consoles are almost always in English.

Run:  python3 build_guides.py    (needs: weasyprint)
"""
from __future__ import annotations
import html
from pathlib import Path
from weasyprint import HTML

OUT = Path(__file__).parent
ACCENT = "#4f46e5"
LMS = ["canvas", "moodle", "brightspace", "blackboard"]
LANGS = ["en", "ar", "es", "fr"]

# ---- shared strings ---------------------------------------------------------
URL_ROWS = [
    ("OIDC login URL", "https://YOUR-HOST/api/v1/lti/login"),
    ("Launch / Target Link URI", "https://YOUR-HOST/api/v1/lti/launch"),
    ("Redirect URI", "https://YOUR-HOST/api/v1/lti/launch"),
    ("Public keyset (JWKS) URL", "https://YOUR-HOST/api/v1/lti/jwks"),
    ("Dynamic Registration URL", "https://YOUR-HOST/api/v1/lti/register"),
]
URL_LABELS = {
    "en": ["OIDC login URL", "Launch / Target Link URI", "Redirect URI",
           "Public keyset (JWKS) URL", "Dynamic Registration URL"],
    "ar": ["رابط تسجيل الدخول OIDC", "رابط التشغيل / الهدف (Launch/Target)", "رابط إعادة التوجيه (Redirect)",
           "رابط مجموعة المفاتيح العامة (JWKS)", "رابط التسجيل الديناميكي"],
    "es": ["URL de inicio de sesión OIDC", "URI de lanzamiento / destino (Launch/Target)", "URI de redirección (Redirect)",
           "URL del conjunto de claves públicas (JWKS)", "URL de registro dinámico"],
    "fr": ["URL de connexion OIDC", "URI de lancement / cible (Launch/Target)", "URI de redirection (Redirect)",
           "URL du jeu de clés publiques (JWKS)", "URL d'enregistrement dynamique"],
}
COMMON = {
    "en": {
        "sub": "Learning Mastery Support · free & open-source LTI 1.3 / Advantage tool · lmsbridge.app",
        "intro": "You need LMS-admin access. Replace YOUR-HOST with your LMS Bridge address. These URLs (also at /api/v1/lti/config and the admin LMS (LTI) tab) are what the LMS needs:",
        "placement_h": "Instructor places it",
        "footer": "After any launch, LMS Bridge auto-provisions the user, course, and role (no extra password). Free & open-source under AGPL-3.0. UI labels verified against current vendor docs (2025–2026); confirm against your LMS version. Full guide: docs/INSTALL_LTI.md.",
    },
    "ar": {
        "sub": "Learning Mastery Support · أداة LTI 1.3 / Advantage مجانية ومفتوحة المصدر · lmsbridge.app",
        "intro": "تحتاج إلى صلاحية مسؤول النظام التعليمي. استبدل YOUR-HOST بعنوان LMS Bridge لديك. هذه الروابط (المتاحة أيضًا في /api/v1/lti/config وفي تبويب LMS (LTI) بلوحة الإدارة) هي ما يحتاجه النظام التعليمي:",
        "placement_h": "كيف يضيفه المدرّس",
        "footer": "بعد أي تشغيل، يهيّئ LMS Bridge المستخدم والمقرّر والدور تلقائيًا (دون كلمة مرور إضافية). مجاني ومفتوح المصدر بموجب AGPL-3.0. جرى التحقق من تسميات الواجهة مقابل وثائق المزوّدين الحالية (2025–2026)؛ تأكّد وفق إصدار نظامك التعليمي. الدليل الكامل: docs/INSTALL_LTI.md.",
    },
    "es": {
        "sub": "Learning Mastery Support · herramienta LTI 1.3 / Advantage gratuita y de código abierto · lmsbridge.app",
        "intro": "Necesitas acceso de administrador del LMS. Sustituye YOUR-HOST por la dirección de tu LMS Bridge. Estas URL (también en /api/v1/lti/config y en la pestaña LMS (LTI) del panel de administración) son las que necesita el LMS:",
        "placement_h": "Cómo lo añade el docente",
        "footer": "Tras cualquier lanzamiento, LMS Bridge aprovisiona automáticamente el usuario, el curso y el rol (sin contraseña adicional). Gratuito y de código abierto bajo AGPL-3.0. Etiquetas de interfaz verificadas con la documentación vigente de los proveedores (2025–2026); confírmalo con la versión de tu LMS. Guía completa: docs/INSTALL_LTI.md.",
    },
    "fr": {
        "sub": "Learning Mastery Support · outil LTI 1.3 / Advantage gratuit et open source · lmsbridge.app",
        "intro": "Vous devez disposer d'un accès administrateur du LMS. Remplacez YOUR-HOST par l'adresse de votre LMS Bridge. Ces URL (également sur /api/v1/lti/config et dans l'onglet LMS (LTI) de l'administration) sont celles dont le LMS a besoin :",
        "placement_h": "Comment l'enseignant l'ajoute",
        "footer": "Après tout lancement, LMS Bridge provisionne automatiquement l'utilisateur, le cours et le rôle (sans mot de passe supplémentaire). Gratuit et open source sous AGPL-3.0. Libellés d'interface vérifiés avec la documentation actuelle des éditeurs (2025–2026) ; confirmez selon la version de votre LMS. Guide complet : docs/INSTALL_LTI.md.",
    },
}
RECO = {"en": "Register (Dynamic Registration — recommended)",
        "ar": "التسجيل (التسجيل الديناميكي — مُوصى به)",
        "es": "Registro (registro dinámico — recomendado)",
        "fr": "Enregistrement (enregistrement dynamique — recommandé)"}

# ---- per-LMS content, per language -----------------------------------------
# Block kinds: ("h", text) ("ol", [..]) ("p", text) ("table", [[label,value],..])
def guides(lang: str) -> dict:
    reco = RECO[lang]
    ph = COMMON[lang]["placement_h"]

    def L(en, ar, es, fr):
        return {"en": en, "ar": ar, "es": es, "fr": fr}[lang]

    canvas = (
        L("Install LMS Bridge in Canvas (Instructure)", "تثبيت LMS Bridge في Canvas (Instructure)",
          "Instalar LMS Bridge en Canvas (Instructure)", "Installer LMS Bridge dans Canvas (Instructure)"),
        [
            ("h", reco),
            ("ol", [
                L("Admin → click your account name → Developer Keys.", "Admin ← انقر اسم حسابك ← Developer Keys.",
                  "Admin → haz clic en el nombre de tu cuenta → Developer Keys.", "Admin → cliquez sur le nom de votre compte → Developer Keys."),
                "+ Developer Key → + LTI Registration.",
                L("Dynamic Registration URL = https://YOUR-HOST/api/v1/lti/register → Continue → confirm in LMS Bridge.",
                  "Dynamic Registration URL = https://YOUR-HOST/api/v1/lti/register ← Continue ← أكِّد في LMS Bridge.",
                  "Dynamic Registration URL = https://YOUR-HOST/api/v1/lti/register → Continue → confirma en LMS Bridge.",
                  "Dynamic Registration URL = https://YOUR-HOST/api/v1/lti/register → Continue → confirmez dans LMS Bridge."),
                L("Leave Permissions + Placements on → Enable & Close.", "اترك Permissions + Placements مفعّلة ← Enable & Close.",
                  "Deja Permissions + Placements activados → Enable & Close.", "Laissez Permissions + Placements activés → Enable & Close."),
                L("Set the key State = ON; copy the Client ID.", "اضبط State = ON للمفتاح؛ وانسخ Client ID.",
                  "Pon State = ON en la clave; copia el Client ID.", "Réglez State = ON pour la clé ; copiez le Client ID."),
                "Settings → Apps → View App Configurations → + App → By Client ID → paste → Install.",
            ]),
            ("p", L("Manual alternative: Developer Keys → + LTI Key (Manual Entry): Target Link URI = /launch, OIDC Initiation = /login, JWK Method = Public JWK URL = /jwks; enable AGS + NRPS toggles; add a Course Navigation placement.",
                    "البديل اليدوي: Developer Keys ← + LTI Key (Manual Entry): Target Link URI = /launch، OIDC Initiation = /login، JWK Method = Public JWK URL = /jwks؛ فعّل مفتاحَي AGS + NRPS؛ وأضف موضِع Course Navigation.",
                    "Alternativa manual: Developer Keys → + LTI Key (Manual Entry): Target Link URI = /launch, OIDC Initiation = /login, JWK Method = Public JWK URL = /jwks; activa AGS + NRPS; añade una ubicación Course Navigation.",
                    "Alternative manuelle : Developer Keys → + LTI Key (Manual Entry) : Target Link URI = /launch, OIDC Initiation = /login, JWK Method = Public JWK URL = /jwks ; activez AGS + NRPS ; ajoutez un emplacement Course Navigation.")),
            ("h", L("Canvas platform endpoints (record in LMS Bridge → LMS (LTI))", "نقاط اتصال منصّة Canvas (سجّلها في LMS Bridge ← LMS (LTI))",
                    "Endpoints de la plataforma Canvas (regístralos en LMS Bridge → LMS (LTI))", "Endpoints de la plateforme Canvas (à saisir dans LMS Bridge → LMS (LTI))")),
            ("table", [["Issuer", "https://canvas.instructure.com"],
                       ["OIDC auth (auth_login_url)", "https://sso.canvaslms.com/api/lti/authorize_redirect"],
                       ["Token (auth_token_url)", "https://sso.canvaslms.com/login/oauth2/token"],
                       ["JWKS (key_set_url)", "https://sso.canvaslms.com/api/lti/security/jwks"]]),
            ("p", L("Cloud values shown; for beta/test use sso.beta / sso.test.canvaslms.com.",
                    "القيم المعروضة للسحابة؛ لبيئتَي beta/test استخدم sso.beta / sso.test.canvaslms.com.",
                    "Se muestran los valores de la nube; para beta/test usa sso.beta / sso.test.canvaslms.com.",
                    "Valeurs cloud affichées ; pour beta/test, utilisez sso.beta / sso.test.canvaslms.com.")),
            ("h", ph),
            ("p", L("Course → Settings → Navigation → drag LMS Bridge into the menu → Save (or Modules → + → External Tool).",
                    "Course ← Settings ← Navigation ← اسحب LMS Bridge إلى القائمة ← Save (أو Modules ← + ← External Tool).",
                    "Course → Settings → Navigation → arrastra LMS Bridge al menú → Save (o Modules → + → External Tool).",
                    "Course → Settings → Navigation → glissez LMS Bridge dans le menu → Save (ou Modules → + → External Tool).")),
        ],
    )

    moodle = (
        L("Install LMS Bridge in Moodle", "تثبيت LMS Bridge في Moodle",
          "Instalar LMS Bridge en Moodle", "Installer LMS Bridge dans Moodle"),
        [
            ("h", reco),
            ("ol", [
                "Site administration → Plugins → Activity modules → External tool → Manage tools.",
                L("Tool URL = https://YOUR-HOST/api/v1/lti/register → click Add LTI Advantage (not “Add Legacy LTI”).",
                  "Tool URL = https://YOUR-HOST/api/v1/lti/register ← انقر Add LTI Advantage (وليس «Add Legacy LTI»).",
                  "Tool URL = https://YOUR-HOST/api/v1/lti/register → haz clic en Add LTI Advantage (no «Add Legacy LTI»).",
                  "Tool URL = https://YOUR-HOST/api/v1/lti/register → cliquez sur Add LTI Advantage (pas « Add Legacy LTI »)."),
                L("Confirm in the LMS Bridge panel; the tool appears under Pending.",
                  "أكِّد في لوحة LMS Bridge؛ ستظهر الأداة ضمن Pending.",
                  "Confirma en el panel de LMS Bridge; la herramienta aparece en Pending.",
                  "Confirmez dans le panneau LMS Bridge ; l'outil apparaît sous Pending."),
                L("Activate it (Pending → Active) and set Show in activity chooser.",
                  "فعّلها (Pending ← Active) وحدّد Show in activity chooser.",
                  "Actívala (Pending → Active) y marca Show in activity chooser.",
                  "Activez-le (Pending → Active) et cochez Show in activity chooser."),
            ]),
            ("p", L("Manual alternative (“configure a tool manually”): Tool URL = /launch; LTI version = LTI 1.3; Public key type = Keyset URL = /jwks; Initiate login URL = /login; Redirection URI = /launch; Services: AGS = grade sync & column management, NRPS = retrieve members.",
                    "البديل اليدوي («configure a tool manually»): Tool URL = /launch؛ LTI version = LTI 1.3؛ Public key type = Keyset URL = /jwks؛ Initiate login URL = /login؛ Redirection URI = /launch؛ الخدمات: AGS = مزامنة الدرجات وإدارة الأعمدة، NRPS = جلب الأعضاء.",
                    "Alternativa manual («configure a tool manually»): Tool URL = /launch; LTI version = LTI 1.3; Public key type = Keyset URL = /jwks; Initiate login URL = /login; Redirection URI = /launch; Servicios: AGS = sincronización de notas y gestión de columnas, NRPS = obtener miembros.",
                    "Alternative manuelle (« configure a tool manually ») : Tool URL = /launch ; LTI version = LTI 1.3 ; Public key type = Keyset URL = /jwks ; Initiate login URL = /login ; Redirection URI = /launch ; Services : AGS = synchro des notes et gestion des colonnes, NRPS = récupérer les membres.")),
            ("h", L("Moodle platform values (Tool configuration details → LMS Bridge)", "قيم منصّة Moodle (Tool configuration details ← LMS Bridge)",
                    "Valores de la plataforma Moodle (Tool configuration details → LMS Bridge)", "Valeurs de la plateforme Moodle (Tool configuration details → LMS Bridge)")),
            ("table", [["Platform ID → issuer", L("your Moodle base URL", "عنوان Moodle الأساسي", "la URL base de tu Moodle", "l'URL de base de votre Moodle")],
                       ["Client ID", L("(generated by Moodle)", "(يولّده Moodle)", "(generado por Moodle)", "(généré par Moodle)")],
                       ["Deployment ID", L("(generated by Moodle)", "(يولّده Moodle)", "(generado por Moodle)", "(généré par Moodle)")],
                       ["Auth request (auth_login_url)", ".../mod/lti/auth.php"],
                       ["Access token (auth_token_url)", ".../mod/lti/token.php"],
                       ["Public keyset (key_set_url)", ".../mod/lti/certs.php"]]),
            ("p", L("Identical across Moodle 4.0–5.2.", "متطابقة عبر Moodle 4.0–5.2.",
                    "Idéntico en Moodle 4.0–5.2.", "Identique de Moodle 4.0 à 5.2.")),
            ("h", ph),
            ("p", L("Course → Edit mode → Add an activity or resource → LMS Bridge (or External tool → Preconfigured tool = LMS Bridge). Click Select content for deep linking.",
                    "Course ← Edit mode ← Add an activity or resource ← LMS Bridge (أو External tool ← Preconfigured tool = LMS Bridge). انقر Select content لإجراء الربط العميق.",
                    "Course → Edit mode → Add an activity or resource → LMS Bridge (o External tool → Preconfigured tool = LMS Bridge). Haz clic en Select content para el deep linking.",
                    "Course → Edit mode → Add an activity or resource → LMS Bridge (ou External tool → Preconfigured tool = LMS Bridge). Cliquez sur Select content pour le deep linking.")),
        ],
    )

    brightspace = (
        L("Install LMS Bridge in Brightspace (D2L)", "تثبيت LMS Bridge في Brightspace (D2L)",
          "Instalar LMS Bridge en Brightspace (D2L)", "Installer LMS Bridge dans Brightspace (D2L)"),
        [
            ("h", L("1) Register (Admin gear → Manage Extensibility → LTI Advantage)", "1) التسجيل (Admin gear ← Manage Extensibility ← LTI Advantage)",
                    "1) Registro (Admin gear → Manage Extensibility → LTI Advantage)", "1) Enregistrement (Admin gear → Manage Extensibility → LTI Advantage)")),
            ("ol", [
                L("Register Tool → Dynamic: paste https://YOUR-HOST/api/v1/lti/register, keep Configure Deployment, click Register (opens a new tab) → then enable the registration (disabled by default).",
                  "Register Tool ← Dynamic: الصق https://YOUR-HOST/api/v1/lti/register، أبقِ Configure Deployment، وانقر Register (يفتح تبويبًا جديدًا) ← ثم فعّل التسجيل (مُعطَّل افتراضيًا).",
                  "Register Tool → Dynamic: pega https://YOUR-HOST/api/v1/lti/register, mantén Configure Deployment, haz clic en Register (abre una pestaña nueva) → luego habilita el registro (deshabilitado por defecto).",
                  "Register Tool → Dynamic : collez https://YOUR-HOST/api/v1/lti/register, gardez Configure Deployment, cliquez sur Register (ouvre un nouvel onglet) → puis activez l'enregistrement (désactivé par défaut)."),
                L("Copy the platform block (Issuer = your tenant host; Client Id; OpenId Connect Auth Endpoint; OAuth2 Access Token URL; Brightspace Keyset URL) into LMS Bridge.",
                  "انسخ كتلة المنصّة (Issuer = مضيف مستأجرك؛ Client Id؛ OpenId Connect Auth Endpoint؛ OAuth2 Access Token URL؛ Brightspace Keyset URL) إلى LMS Bridge.",
                  "Copia el bloque de la plataforma (Issuer = host de tu tenant; Client Id; OpenId Connect Auth Endpoint; OAuth2 Access Token URL; Brightspace Keyset URL) en LMS Bridge.",
                  "Copiez le bloc plateforme (Issuer = hôte de votre tenant ; Client Id ; OpenId Connect Auth Endpoint ; OAuth2 Access Token URL ; Brightspace Keyset URL) dans LMS Bridge."),
            ]),
            ("p", L("Standard (manual) alt: Domain = YOUR-HOST; Redirect = /launch; OIDC Login URL = /login; Target Link URI = /launch; Keyset URL = /jwks; enable Assignment & Grade Services + Names & Role Provisioning.",
                    "البديل القياسي (اليدوي): Domain = YOUR-HOST؛ Redirect = /launch؛ OIDC Login URL = /login؛ Target Link URI = /launch؛ Keyset URL = /jwks؛ فعّل Assignment & Grade Services + Names & Role Provisioning.",
                    "Alternativa estándar (manual): Domain = YOUR-HOST; Redirect = /launch; OIDC Login URL = /login; Target Link URI = /launch; Keyset URL = /jwks; habilita Assignment & Grade Services + Names & Role Provisioning.",
                    "Alternative standard (manuelle) : Domain = YOUR-HOST ; Redirect = /launch ; OIDC Login URL = /login ; Target Link URI = /launch ; Keyset URL = /jwks ; activez Assignment & Grade Services + Names & Role Provisioning.")),
            ("h", L("2) Deploy (Admin gear → External Learning Tools → LTI Advantage)", "2) النشر (Admin gear ← External Learning Tools ← LTI Advantage)",
                    "2) Despliegue (Admin gear → External Learning Tools → LTI Advantage)", "2) Déploiement (Admin gear → External Learning Tools → LTI Advantage)")),
            ("ol", [
                L("New Deployment → Tool = your registration; tick AGS + NRPS; Security: send Name/Email/User ID + Org Unit Info.",
                  "New Deployment ← Tool = تسجيلك؛ ضع علامة على AGS + NRPS؛ Security: أرسل Name/Email/User ID + Org Unit Info.",
                  "New Deployment → Tool = tu registro; marca AGS + NRPS; Security: envía Name/Email/User ID + Org Unit Info.",
                  "New Deployment → Tool = votre enregistrement ; cochez AGS + NRPS ; Security : envoyez Name/Email/User ID + Org Unit Info."),
                L("Add Org Units (and descendants) the tool should appear in → Create Deployment; copy the Deployment Id into LMS Bridge.",
                  "أضِف Org Units (والفروع التابعة) التي ينبغي أن تظهر فيها الأداة ← Create Deployment؛ وانسخ Deployment Id إلى LMS Bridge.",
                  "Añade las Org Units (y descendientes) donde debe aparecer la herramienta → Create Deployment; copia el Deployment Id en LMS Bridge.",
                  "Ajoutez les Org Units (et descendants) où l'outil doit apparaître → Create Deployment ; copiez le Deployment Id dans LMS Bridge."),
                L("On the deployment → View Links → New Link → URL = /launch → Save and Close.",
                  "على النشر ← View Links ← New Link ← URL = /launch ← Save and Close.",
                  "En el despliegue → View Links → New Link → URL = /launch → Save and Close.",
                  "Sur le déploiement → View Links → New Link → URL = /launch → Save and Close."),
            ]),
            ("p", L("Requires the Manage LTI Tools permission. Registration lives under Manage Extensibility; deployment under External Learning Tools.",
                    "يتطلّب صلاحية Manage LTI Tools. يوجد التسجيل ضمن Manage Extensibility؛ والنشر ضمن External Learning Tools.",
                    "Requiere el permiso Manage LTI Tools. El registro está en Manage Extensibility; el despliegue en External Learning Tools.",
                    "Nécessite l'autorisation Manage LTI Tools. L'enregistrement se trouve sous Manage Extensibility ; le déploiement sous External Learning Tools.")),
            ("h", ph),
            ("p", L("Course → Content → Add Existing → External Learning Tools → select the LMS Bridge link (or Insert Stuff / a Quicklink).",
                    "Course ← Content ← Add Existing ← External Learning Tools ← اختر رابط LMS Bridge (أو Insert Stuff / Quicklink).",
                    "Course → Content → Add Existing → External Learning Tools → selecciona el enlace de LMS Bridge (o Insert Stuff / un Quicklink).",
                    "Course → Content → Add Existing → External Learning Tools → sélectionnez le lien LMS Bridge (ou Insert Stuff / un Quicklink).")),
        ],
    )

    blackboard = (
        L("Install LMS Bridge in Blackboard (Anthology)", "تثبيت LMS Bridge في Blackboard (Anthology)",
          "Instalar LMS Bridge en Blackboard (Anthology)", "Installer LMS Bridge dans Blackboard (Anthology)"),
        [
            ("h", L("Part A — tool owner registers once (Anthology Developer Portal)", "الجزء أ — مالك الأداة يسجّل مرة واحدة (Anthology Developer Portal)",
                    "Parte A — el propietario de la herramienta se registra una vez (Anthology Developer Portal)", "Partie A — le propriétaire de l'outil s'enregistre une fois (Anthology Developer Portal)")),
            ("ol", [
                L("Sign in at developer.anthology.com → Register a REST or LTI application; Domain = YOUR-HOST.",
                  "سجّل الدخول في developer.anthology.com ← Register a REST or LTI application؛ Domain = YOUR-HOST.",
                  "Inicia sesión en developer.anthology.com → Register a REST or LTI application; Domain = YOUR-HOST.",
                  "Connectez-vous sur developer.anthology.com → Register a REST or LTI application ; Domain = YOUR-HOST."),
                L("Supports LTI 1.3 = ON: Login Initiation URL = /login; Tool Redirect URL = /launch; Tool JWKS URL = /jwks; Signing = RS256 → Register.",
                  "Supports LTI 1.3 = ON: Login Initiation URL = /login؛ Tool Redirect URL = /launch؛ Tool JWKS URL = /jwks؛ Signing = RS256 ← Register.",
                  "Supports LTI 1.3 = ON: Login Initiation URL = /login; Tool Redirect URL = /launch; Tool JWKS URL = /jwks; Signing = RS256 → Register.",
                  "Supports LTI 1.3 = ON : Login Initiation URL = /login ; Tool Redirect URL = /launch ; Tool JWKS URL = /jwks ; Signing = RS256 → Register."),
                L("Save the Application ID (= Client ID). Record the global endpoints in LMS Bridge (below).",
                  "احفظ Application ID (= Client ID). وسجّل نقاط الاتصال العامة في LMS Bridge (أدناه).",
                  "Guarda el Application ID (= Client ID). Registra los endpoints globales en LMS Bridge (abajo).",
                  "Enregistrez l'Application ID (= Client ID). Saisissez les endpoints globaux dans LMS Bridge (ci-dessous)."),
            ]),
            ("table", [["Issuer", "https://blackboard.com"],
                       ["OIDC auth", "https://developer.blackboard.com/api/v1/gateway/oidcauth"],
                       ["Token", "https://developer.blackboard.com/api/v1/gateway/oauth2/jwttoken"],
                       ["Platform JWKS", ".../management/applications//jwks.json"]]),
            ("p", L("Tip: enable auto-register deployments on this registration so each school’s Deployment ID is trusted on first launch.",
                    "نصيحة: فعّل auto-register deployments على هذا التسجيل كي يُوثَّق Deployment ID لكل مؤسسة عند أول تشغيل.",
                    "Consejo: activa auto-register deployments en este registro para que el Deployment ID de cada institución se confíe en el primer lanzamiento.",
                    "Astuce : activez auto-register deployments sur cet enregistrement pour que le Deployment ID de chaque établissement soit approuvé au premier lancement.")),
            ("h", L("Part B — each institution’s Blackboard admin", "الجزء ب — مسؤول Blackboard في كل مؤسسة",
                    "Parte B — el administrador de Blackboard de cada institución", "Partie B — l'administrateur Blackboard de chaque établissement")),
            ("ol", [
                L("Admin (Ultra) or System Admin (Original) → Integrations → LTI Tool Providers.",
                  "Admin (Ultra) أو System Admin (Original) ← Integrations ← LTI Tool Providers.",
                  "Admin (Ultra) o System Admin (Original) → Integrations → LTI Tool Providers.",
                  "Admin (Ultra) ou System Admin (Original) → Integrations → LTI Tool Providers."),
                L("Register LTI 1.3/Advantage Tool → paste the Client ID → Submit.",
                  "Register LTI 1.3/Advantage Tool ← الصق Client ID ← Submit.",
                  "Register LTI 1.3/Advantage Tool → pega el Client ID → Submit.",
                  "Register LTI 1.3/Advantage Tool → collez le Client ID → Submit."),
                L("Set Tool Status = Approved; User Fields = Role/Name/Email; Allow grade service = Yes (AGS); Allow Membership service = Yes (NRPS) → Submit.",
                  "اضبط Tool Status = Approved؛ User Fields = Role/Name/Email؛ Allow grade service = Yes (AGS)؛ Allow Membership service = Yes (NRPS) ← Submit.",
                  "Pon Tool Status = Approved; User Fields = Role/Name/Email; Allow grade service = Yes (AGS); Allow Membership service = Yes (NRPS) → Submit.",
                  "Réglez Tool Status = Approved ; User Fields = Role/Name/Email ; Allow grade service = Yes (AGS) ; Allow Membership service = Yes (NRPS) → Submit."),
                L("Also: Manage Global Properties → allow tool providers to post grades. Copy the Deployment ID (if not auto-registering).",
                  "أيضًا: Manage Global Properties ← اسمح لمزوّدي الأدوات بإرسال الدرجات. وانسخ Deployment ID (إن لم يكن التسجيل تلقائيًا).",
                  "Además: Manage Global Properties → permite que los proveedores publiquen notas. Copia el Deployment ID (si no es auto-registro).",
                  "Également : Manage Global Properties → autorisez les fournisseurs à publier les notes. Copiez le Deployment ID (si pas d'auto-enregistrement)."),
            ]),
            ("h", ph),
            ("p", L("Ultra: Course Content → + → Content Market → Institution Tools → LMS Bridge. Original: Build Content → the LMS Bridge placement (or Web Link with “This link is to a Tool Provider”).",
                    "Ultra: Course Content ← + ← Content Market ← Institution Tools ← LMS Bridge. Original: Build Content ← موضِع LMS Bridge (أو Web Link مع «This link is to a Tool Provider»).",
                    "Ultra: Course Content → + → Content Market → Institution Tools → LMS Bridge. Original: Build Content → la ubicación de LMS Bridge (o Web Link con «This link is to a Tool Provider»).",
                    "Ultra : Course Content → + → Content Market → Institution Tools → LMS Bridge. Original : Build Content → l'emplacement LMS Bridge (ou Web Link avec « This link is to a Tool Provider »).")),
        ],
    )

    return {"canvas": canvas, "moodle": moodle, "brightspace": brightspace, "blackboard": blackboard}


# ---- rendering --------------------------------------------------------------
def esc(s: str) -> str:
    return html.escape(s, quote=False)


def code(v: str) -> str:
    # URLs / field values always read left-to-right, even inside an RTL page.
    return f'<span class="mono" dir="ltr">{esc(v)}</span>'


def render(lms: str, lang: str) -> bytes:
    title, blocks = guides(lang)[lms]
    c = COMMON[lang]
    rtl = lang == "ar"
    parts = [f'<div class="title">{esc(title)}</div>',
             f'<div class="sub">{esc(c["sub"])}</div>',
             f'<p class="intro">{esc(c["intro"])}</p>']
    # shared URL table
    rows = "".join(f'<tr><td class="lbl">{esc(l)}</td><td>{code(v)}</td></tr>'
                   for l, (_, v) in zip(URL_LABELS[lang], URL_ROWS))
    parts.append(f'<table>{rows}</table>')
    for kind, val in blocks:
        if kind == "h":
            parts.append(f'<h2>{esc(val)}</h2>')
        elif kind == "p":
            parts.append(f'<p class="note">{esc(val)}</p>')
        elif kind == "ol":
            items = "".join(f"<li>{esc(s)}</li>" for s in val)
            parts.append(f"<ol>{items}</ol>")
        elif kind == "table":
            trs = "".join(f'<tr><td class="lbl">{esc(l)}</td><td>{code(v)}</td></tr>' for l, v in val)
            parts.append(f'<table>{trs}</table>')
    parts.append(f'<p class="footer">{esc(c["footer"])}</p>')
    body = "\n".join(parts)
    doc = f"""<!doctype html><html lang="{lang}" dir="{'rtl' if rtl else 'ltr'}"><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 1.5cm 1.6cm; }}
* {{ font-family: 'DejaVu Sans', sans-serif; }}
body {{ color: #1f2430; font-size: 10.5px; line-height: 1.5; }}
.title {{ color: {ACCENT}; font-size: 19px; font-weight: 700; }}
.sub {{ color: #6b7280; font-size: 9.5px; margin: 2px 0 12px; }}
.intro {{ margin: 0 0 10px; }}
h2 {{ color: #111827; font-size: 12.5px; margin: 14px 0 6px; }}
table {{ width: 100%; border-collapse: collapse; margin: 6px 0 4px; }}
td {{ border-top: 1px solid #e6e8ec; padding: 4px 8px; vertical-align: top; }}
td.lbl {{ color: #4b5563; font-weight: 600; width: 42%; }}
.mono {{ font-family: 'DejaVu Sans Mono', monospace; font-size: 9.5px; color: #111827;
  unicode-bidi: isolate; word-break: break-all; }}
ol {{ margin: 4px 0 4px; padding-inline-start: 20px; }}
li {{ margin: 3px 0; }}
.note {{ color: #374151; font-size: 9.7px; margin: 6px 0; }}
.footer {{ color: #6b7280; font-size: 8.8px; margin-top: 16px; border-top: 1px solid #e6e8ec; padding-top: 8px; }}
</style></head><body>{body}</body></html>"""
    return HTML(string=doc).write_pdf()


def main():
    for lms in LMS:
        for lang in LANGS:
            name = f"install-{lms}.pdf" if lang == "en" else f"install-{lms}.{lang}.pdf"
            (OUT / name).write_bytes(render(lms, lang))
            print("wrote", name)


if __name__ == "__main__":
    main()

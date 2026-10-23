# Watch7 assistant bridge: feasibility and decision gates

Research date: 2026-10-23. Status: researched proposal, **not a verified implementation**.

## Decision

**A separately signed, watch-local bridge is plausible for forwarding a user invocation to official Herald, but Samsung Galaxy Watch7 Home-button long-hold routing is unproven. Do not promise that an `ACTION_ASSIST` filter or a `VoiceInteractionService` will make it selectable.** Android assistant qualification, actual assistant-role ownership, and Samsung's button assignment are separate gates.

Start with the activity-based assistant hypothesis, not a full voice-interaction stack. Android explicitly permits an assistant activity instead of a voice interaction service [S1–S3]. However, Samsung documents specific long-hold choices and explicitly excludes Alexa from button assignment [S7–S8]. That is evidence of restricted product behavior, **not proof of a particular package/signature allowlist implementation**. No reviewed official source establishes an open third-party registration mechanism for Watch7 long-hold selection.

No application was built or installed, no device configuration or assistant role was changed, no voice was launched, and no GitHub operation was performed during this research. Only this local research document is a deliverable.

## Evidence boundaries

### Provided parent tool evidence — not independently repeated here

The following observations were supplied with the task and follow-up. They describe one device at observation time, not all Watch7 firmware:

| Observation | What it establishes | What it does not establish |
| --- | --- | --- |
| Galaxy Watch7 model supplied as `SM_L310`; Android release `16`, SDK `36`, `ro.build.version.oneui=80000` | Target platform for subsequent feasibility work | Exact Samsung firmware implementation or compatibility of every One UI 8 watch |
| Secure `assistant=com.google.android.wearable.assistant/.MainActivity` | Configured assistant component is a Google activity | That the Home-button handler dynamically consults this setting |
| Secure `voice_interaction_service` is empty; query for `android.service.voice.VoiceInteractionService` returned none | No selected voice interaction service and none returned by that query | That third-party voice interaction services are prohibited or required |
| `cmd role get-role-holders --user 0 android.app.role.ASSISTANT` returned `com.google.android.wearable.assistant` | Google holds the Android assistant role for user 0 | Samsung's Home-button configuration value, or bridge eligibility |
| `ACTION_ASSIST` and `ACTION_VOICE_ASSIST` queries/resolution returned only Google `MainActivity` | Google is the observed handler for those queries with currently installed apps | That a newly installed qualifying activity would be included or excluded |
| Home-button settings UI showed Bixby and Google | Those assistant choices were visible on this device | A demonstrated hardcoded allowlist, or what happens after changing role holder |
| No device changes or voice launches performed for the additional observations | Observations are read-only | End-to-end launch success |

The supplied role-holder observation is stronger than inferring role ownership from secure settings. Neither is itself a readback of Samsung's Home-button setting. A later parent readback supplies that missing, distinct field:

```text
global setting_home_key_long_press=com.samsung.android.bixby.agent/com.samsung.android.bixby.WinkService
global setting_home_key_double_press=lastapp
global setting_raise_to_talk_assistant=gemini
```

These exact values are provided parent tool evidence, not independently queried here. With `assistant` and the assistant role pointing to Google, the simultaneous Bixby-valued Samsung long-hold preference demonstrates **separate persisted configuration**, not a single shared assistant selector. The baseline names a `WinkService` component; a class-name suffix alone does not prove its Android component type, exported state, binding/start mechanism, or support for arbitrary third-party replacements. `gemini` is a literal value of a separate raise-to-talk preference, not proof that long hold routes to Gemini. No physical invocation was reported to establish dispatch behavior. Preserve all baseline values verbatim for any reversible parent-run experiment; do not normalize `SM_L310` or these identifiers.

### Provided Herald integration evidence — not Android/Samsung documentation

Task context reports official Herald `0.13.0` installed, watch application ID `dev.herald.android`, and exported activity `dev.hermeskotlin.wear.MainActivity`. Its boolean extra `listen=true` calls `talk()`: live voice requires both Gateway capability and the user's setting; otherwise speech-recognizer or recorder fallback applies.

These are provided application-specific facts, not findings certified by Android or Samsung. No device launch or installed-APK verification was performed here. Component names and this extra are a version-specific integration assumption, not an official Android voice API or a guaranteed stable Herald public contract. The repository glossary and existing proposed ADRs were read; this bridge does not propose changing Herald's Gateway protocol or Bot Chat continuity decisions.

## 1. Android default assistant: activity and service are alternatives

### Activity route (`ACTION_ASSIST`)

Android's role documentation says an assistant may qualify through an assist activity **or** an assist-capable voice interaction service [S1–S2]. The Android 16 AOSP implementation makes the activity rule concrete [S3]:

- Query activities handling `Intent.ACTION_ASSIST` with `MATCH_DEFAULT_ONLY` and direct-boot matching flags.
- Accept exported activity components.
- Add their packages to qualifying assistant candidates.

A proposed bridge would therefore expose an explicitly exported assist activity with `android.intent.action.ASSIST` and `android.intent.category.DEFAULT`. It would be a system-invoked entry point that forwards to Herald, not a global key-event listener. The inspected AOSP activity qualification branch contains no Google/Bixby package-name or signature allowlist [S3]. **That statement is limited to this AOSP branch; it says nothing about Samsung's selector or firmware overlays.**

`ACTION_ASSIST` is the public assist activity action. Android 16 AOSP defines `ACTION_VOICE_ASSIST` separately and marks that constant `@SystemApi`/`@hide` [S6]. Both resolving to Google does not demonstrate a voice interaction service. Adding the voice-assist action is not an alternative to the documented `ACTION_ASSIST` qualification rule, nor proof that Samsung will invoke it.

### Voice interaction service route

`VoiceInteractionService` is the top-level global voice interactor, kept running when selected; it is not merely an activity filter or a generic speech-recognition service [S5]. Android 16 AOSP assistant qualification checks [S3]:

- A service resolving `android.service.voice.VoiceInteractionService`.
- Its service declaration requires `android.permission.BIND_VOICE_INTERACTION`.
- It publishes `android.voice_interaction` XML metadata with non-null `sessionService`, non-null `recognitionService`, and `supportsAssist=true`.
- The service-candidate branch is skipped on low-RAM devices. The activity branch is separate.

`BIND_VOICE_INTERACTION` here protects binding **to** the service; it is not a permission a bridge simply requests to seize assistant status. A valid service/session implementation is materially larger than a forwarding activity, and role qualification alone does not prove its runtime behavior. Hotword capture is not necessary for the proposed button-triggered bridge and should not be added speculatively.

**Do not implement a dummy voice stack solely because the target's service query was empty.** There is no inspected Android rule requiring a voice interaction service for every assistant, and no reviewed Samsung rule promising that adding one unlocks long hold.

### Why an empty voice-interaction setting is coherent

The Android 16 AOSP `VoiceInteractionManagerService.RoleObserver` converts assistant-role ownership into secure settings [S4]:

1. Look for an assist-capable voice interaction service in the role holder's package; if chosen, set both `assistant` and `voice_interaction_service` to that service.
2. Otherwise look for an `ACTION_ASSIST` activity in that package; set `assistant` to the activity and set `voice_interaction_service` to an empty string.

Thus Google's observed role ownership plus activity-valued `assistant` plus empty `voice_interaction_service` is consistent with the AOSP activity-assistant path. It is not evidence of a broken assistant or of third-party rejection. It also does not prove Samsung uses unmodified AOSP routing.

## 2. Qualification, selection UI, requestability, and ownership differ

These distinctions are important before specifying an onboarding flow:

- **Qualification:** package satisfies component rules [S3].
- **Availability:** `RoleManager.isRoleAvailable(ROLE_ASSISTANT)` reports whether the role exists on the system; it does not report whether this bridge qualifies or whether a selector is visible [S10]. The provided role-holder output already shows role ownership on this watch, but an eventual app should still check APIs rather than assume availability.
- **Visibility:** AOSP assistant role behavior uses `config_showDefaultAssistant` with a false fallback to decide role visibility [S3]. A role existing does not guarantee a user-facing default-assistant chooser. Samsung's actual configuration/overlay has not been established.
- **Requestability:** Android 16 AOSP `roles.xml` marks this role `requestable="false"` [S9]. Do not specify `createRequestRoleIntent(ROLE_ASSISTANT)` as guaranteed to show a grant dialog. The existence of that generic public method is not proof that this role can be requested on this watch.
- **Ownership:** the role holder is a package; the selected implementation can be a component mapped into settings [S4]. A query returning an eligible activity is not ownership. A successful role assignment, if ever authorized for testing, would need exact role-holder and settings readback.
- **Button assignment:** Samsung's Home-button preference is another control plane; Android role ownership does not establish its value or dispatch behavior [S7–S8].

A hypothetical shell-forced role assignment or secure-settings write is a configuration experiment, not proof of a supported end-user selection flow. Neither is authorized by this research task. A secure `assistant` write alone would also bypass the role-to-settings path documented in AOSP [S4], so it would be poor evidence of durable integration.

## 3. Samsung Home-button long hold: restriction is documented, mechanism is unknown

Samsung's official assistant article says to open **Settings → Buttons and gestures → Press and hold**, then choose Bixby, Google Assistant, or the Power off menu. It explicitly states: **“The Alexa assistant cannot be assigned to the button.”** [S7]

Samsung's official navigation article distinguishes [S8]:

- **Double press:** choose a preferred function from the list.
- **Press and hold:** Bixby or Power off menu; Assistant appears if Google Assistant is installed.

Consequences:

1. Installing an assistant application is not enough to infer long-hold assignability: Samsung itself provides Alexa as a counterexample.
2. These are product support instructions, not a published third-party SDK contract. They do not expose a package allowlist, signature check, privilege requirement, or eligibility callback.
3. Bixby being visible while only Google resolves the assist queries is further reason not to equate Samsung's button choices with a raw Android assist-candidate list.
4. At least two explanations remain open: a Google-specific button path, or an “Assistant” button mode that invokes the currently configured Android assistant after a separate selection. Reviewed sources and supplied observations do not distinguish them. A hybrid policy is also possible.
5. Do not extrapolate Samsung phone/tablet default-assistant instructions to the watch. Do not extrapolate this broad support page to an exact Watch7 firmware implementation. The assistant article also discusses newer Watch8/Gemini behavior; it is not firmware-pinned evidence for this target.

**Allowlist finding:** documented limited choices; internal allowlist existence and contents **unknown**. No reviewed Android/Samsung primary source guarantees that an arbitrary sideloaded bridge can appear in this long-hold picker. Conversely, these sources do not prove every third-party bridge is impossible.

### `setting_home_key_long_press`: custom activity/service pattern research

Targeted searches for the exact key against `samsung.com`, `developer.samsung.com`, and `android.googlesource.com`, followed by broader Samsung-developer searches for custom watch Home-button long-press activities/services, did not yield an authoritative schema or dispatch implementation. Several search responses were broad fallback results rather than exact matches; this is **not** an exhaustive proof that documentation/source does not exist. Community remapping instructions surfaced but are excluded by the primary-source-only requirement.

Accordingly, **no primary-source-backed custom setting value or write command can be specified**. The observed `package/class`-shaped Bixby value is evidence of an existing vendor preference, not a contract saying that any flattened `ComponentName` works. It remains unknown whether the Samsung consumer:

- recognizes only enumerated built-in values/components;
- validates package/signature/privilege or installation origin;
- parses a component and resolves an activity, starts a service, binds a service, or special-cases Bixby/Google;
- requires an OEM intent action/extra or a permission unavailable to ordinary apps;
- rewrites unsupported values or mirrors state from Galaxy Wearable.

A future parent-run reversible experiment must first distinguish these possibilities using observed dispatch evidence and actual component metadata. Merely storing a custom string and reading it back would prove persistence, **not launchability, eligibility, or correct component type**. Do not assume that an assistant-role switch updates this Samsung key: the supplied mismatched baseline is concrete evidence that these persisted states can differ. Prefer an official UI transition plus exact before/after readback to discover the firmware's supported Google representation; do not invent it from the Bixby pattern. This document provides no proposed custom value because none has been established from permitted sources.

Android's Wear button documentation describes handling multifunction stems in an app [S11]. That is not a documented global interception/remapping API for the Home-button long hold. A bridge should use an assistant dispatch path if one is genuinely available, not claim ordinary `onKeyDown()` can take over the OS gesture.

## 4. Separate bridge → official Herald forwarding

Proposed boundary, contingent on later approval and validation:

```text
Samsung Home long hold
    → Samsung button policy (unverified routing)
    → selected Android assistant bridge activity (unverified selectability)
    → explicit component dev.herald.android/dev.hermeskotlin.wear.MainActivity
       boolean extra: listen = true
    → official Herald talk() and its existing voice/fallback decision
```

An explicit launch to another application's exported activity is an Android-supported component boundary, subject to component permissions and activity-start rules [S12–S13]. It does not inherently require both applications to share a signing key. The component's actual permission requirements and runtime behavior must still be checked; `exported=true` alone is not a promise that every launch succeeds.

Keeping Herald unchanged preserves its official package/signing identity. Android's Wear Data Layer documentation requires matching package names and matching package signatures between a watch app and its phone counterpart [S14]. The bridge would **not** become a Data Layer peer of Herald and should not try to replace Herald's phone/watch transport. Its separate signature is acceptable only because the intended boundary is a watch-local exported activity, not cross-device Herald Data Layer access.

Recommended limits for a later prototype specification:

- New, distinct application ID and own signature; no impersonation of Google, Bixby, or Herald.
- Do not modify/re-sign either official Herald app, read its private data, or replicate Gateway credentials.
- Forward only the exact intended boolean extra to the explicit Herald component, not arbitrary incoming assist extras, contexts, screenshots, or caller-chosen destinations.
- Do not request microphone permission or start recording in the bridge. Herald owns permissions, user intent, Gateway capability checks, capture, and transport.
- A foreground activity-to-activity handoff is the smallest hypothesis. Android documents restrictions on background activity starts [S13]; a service-only or invisible trampoline is not automatically equivalent. Android 16/SDK36 behavior must be validated later.
- Check missing/disabled/incompatible Herald and provide an honest failure state. Avoid automatic repeated launches.
- Decide task/flag/lifecycle behavior only after inspecting the actual installed activity contract. Test cold start, already-open activity/`onNewIntent`, repeated button holds, and return navigation. Do not assume `listen=true` will be consumed on every warm launch.
- “Opened Herald,” “invoked `talk()`,” “started recognizer/recording,” and “started live voice” are different acceptance outcomes. Live voice must separately satisfy Herald's existing user setting and Gateway capability prerequisites.

## 5. Recommended feasibility gates

These are future gates, not actions executed by this researcher. A later parent message reports explicit user authorization for reversible spec/tickets/build/install/default switching; the parent owns that execution and exact-baseline preservation. This delegated deliverable remains research only. Voice capture/launch acceptance should still be deliberate and distinguished from configuration-only tests.

| Gate | Evidence required | Pass / stop rule |
| --- | --- | --- |
| G0 — preserve baseline, read-only | Exact target build fingerprint/security patch, enabled assistant components, role holder, secure assistant/service settings, Samsung long-hold screen and configured choice; confirm installed Herald version/component permissions and intent lifecycle from existing evidence or permitted inspection | Current supplied baseline is useful but does not identify Samsung's internal routing. Do not infer unsupported values or perform settings writes. |
| G1 — OEM eligibility/routing, research first | Samsung official technical documentation or support answer specific to Watch7/One UI 8 explaining whether a non-preinstalled third-party `ACTION_ASSIST` activity can be chosen, and whether long-hold “Assistant” invokes the role holder or a fixed Google target | A documented Google-only/preinstalled/signature restriction is a no-go for an ordinary separate bridge. No answer means **unknown**, not pass. A third-party default-assistant chooser and long-hold selector must not be conflated. |
| G2 — minimal candidate, only if approved later | Small separately signed activity-based candidate with explicit assist/default/exported declarations; evidence of actual qualification and an available user-consent selection route on this firmware | Intent resolution alone is insufficient. If no supported selection route exists, do not escalate silently to shell forcing or a voice service. |
| G3 — role and button independently verified, only if approved later | Readback of exact assistant role holder, assistant component, service setting, and Samsung button choice after intentional selection; then observed physical Home long-hold dispatch to a harmless diagnostic screen | Role changes without physical long-hold dispatch do not pass the requested use case. Diagnostic callback avoids recording while testing OEM routing. |
| G4 — official Herald handoff, only if approved later | A consented explicit launch reaches official Herald and delivers boolean `listen=true`, with cold/warm starts, errors, and repeated invocations checked | Signature/package transport remains intact; unsupported or ignored warm-start extra is a blocker or contract issue, not permission to patch/re-sign Herald. |
| G5 — voice correctness and persistence, separately consented | Microphone/user-setting/Gateway checks; live voice versus recognizer/recorder outcomes; unlocked/locked, ambient/screen-off, reboot and update persistence; rollback readback | No lock-screen bypass, accidental recording, duplicate capture, or claim that fallback equals live voice. Revalidate after firmware/assistant/Herald updates. |

If G1 stays undocumented, a separately authorized, bounded G2/G3 experiment may establish **device-specific feasibility**, but cannot retroactively create a Samsung-supported integration contract. Implement a voice interaction service only if evidence shows the activity path is insufficient and the service path is actually eligible; include its own selection, runtime, background-launch, and power-cost gates.

If G3 fails because long hold is genuinely Google/Bixby-only, stop the long-hold bridge work. A double-press shortcut or a watch launcher/tile/complication entry could be a separately scoped fallback, subject to its own eligibility and launch checks [S8]. It is not completion of the long-hold requirement. Accessibility interception, hidden-setting hacks, root, package spoofing, and re-signing official Herald are outside this proposal.

## Known / unknown summary

**Known from primary sources:** Android supports activity-based assistants; an assist-capable voice service is an alternative with extra requirements; role mapping can produce an empty voice-interaction setting; AOSP assistant-role requestability and UI visibility are separate; Samsung documents limited long-hold choices and explicitly excludes Alexa; exported activity forwarding and preserving the original Herald Data Layer identity are architecturally distinct.

**Known only from provided parent evidence:** this watch's Android/One UI values, Google activity/role state, absence of returned voice interaction services, visible Bixby/Google choices, and Herald's version/component/`listen` behavior.

**Unknown:** Samsung's actual long-hold allowlist/policy implementation, a supported third-party role-selection UI on this firmware, whether long-hold Assistant follows the Android role holder, any third-party service exception, and successful/correct/persistent forwarding to official Herald voice.

**Recommendation:** retain the separate bridge as a conditional design; resolve OEM routing/selectability before committing to implementation. The current evidence supports **research go; production feasibility not yet proven**, not “just add a service” or “third-party assistants are impossible.”

## Sources (primary only)

AOSP implementation links are pinned to `android-16.0.0_r1`, not claimed to be Samsung's fork or its currently installed PermissionController module. Official documentation was consulted on the research date; live pages can change. Parent observations above are separately labeled and are not substituted for published platform documentation.

- **S1 — AOSP: Android roles, ASSISTANT requirements.** https://source.android.com/docs/core/permissions/android-roles
- **S2 — Android Developers: RoleManagerCompat, ROLE_ASSISTANT.** Explicit service-or-`ACTION_ASSIST` qualification and availability warning. https://developer.android.com/reference/androidx/core/role/RoleManagerCompat#ROLE_ASSISTANT
- **S3 — AOSP Android 16: AssistantRoleBehavior.java.** `getQualifyingPackagesInternal`, `isAssistantVoiceInteractionService`, `isVisibleAsUser`. https://android.googlesource.com/platform/packages/modules/Permission/+/refs/tags/android-16.0.0_r1/PermissionController/role-controller/java/com/android/role/controller/behavior/AssistantRoleBehavior.java
- **S4 — AOSP Android 16: VoiceInteractionManagerService.java.** `RoleObserver.onRoleHoldersChanged`, especially activity fallback and empty service setting. https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-16.0.0_r1/services/voiceinteraction/java/com/android/server/voiceinteraction/VoiceInteractionManagerService.java#2398
- **S5 — AOSP Android 16: VoiceInteractionService.java.** Class contract, `SERVICE_INTERFACE`, `SERVICE_META_DATA`, binding permission and keyguard callback. https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-16.0.0_r1/core/java/android/service/voice/VoiceInteractionService.java#70
- **S6 — AOSP Android 16: Intent.java.** Public `ACTION_ASSIST` and system/hidden `ACTION_VOICE_ASSIST`. https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-16.0.0_r1/core/java/android/content/Intent.java#1452
- **S7 — Samsung Support: Use an AI assistant like Gemini, Alexa, or Bixby on your Galaxy watch.** Section “Assign an assistant to your watch's button”; explicit Alexa exclusion. https://www.samsung.com/us/support/answer/ANS10003405/
- **S8 — Samsung Support: Navigate your Galaxy watch with Wear OS.** Section “Customize the watch buttons”; separate double-press and long-hold choices. https://www.samsung.com/us/support/answer/ANS10003406/
- **S9 — AOSP Android 16: roles.xml.** ASSISTANT definition, `requestable="false"`; component comment explicitly described there as rough/non-executable, with actual qualification in S3. https://android.googlesource.com/platform/packages/modules/Permission/+/refs/tags/android-16.0.0_r1/PermissionController/res/xml/roles.xml#104
- **S10 — Android Developers: RoleManager.** Role availability/ownership and generic role-request APIs. https://developer.android.com/reference/android/app/role/RoleManager
- **S11 — Android Developers: Physical buttons on Wear OS.** Multifunction button API and event handling. https://developer.android.com/training/wearables/user-input/physical-buttons
- **S12 — Android Developers: android:exported.** Cross-application component access by exact class name. https://developer.android.com/privacy-and-security/risks/android-exported ; activity permission and launch-mode reference: https://developer.android.com/guide/topics/manifest/activity-element
- **S13 — Android Developers: activity-start security and restrictions.** Live documentation currently titled “Activity security.” https://developer.android.com/guide/components/activities/background-starts
- **S14 — Android Developers: Overview of Data Layer API, Security of communications.** Matching package and signature across phone/watch. https://developer.android.com/training/wearables/data/overview#security

### Retrieval limitations

Search/extraction intermittently rate-limited, and direct non-browser Samsung requests returned HTTP 403. Both critical Samsung button sections were successfully read from the live official pages through a browser, including collapsed-section DOM text. No community posts, third-party remapping tutorials, or secondary articles were used as evidence. Several initially guessed AOSP class paths returned 404; the role-controller source tree was then enumerated read-only and the actual Android 16 `AssistantRoleBehavior` implementation was retrieved. No failed fetch was treated as negative eligibility evidence.

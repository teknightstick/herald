# Herald Voice Bridge (isolated experiment)

A separately signed Wear OS activity (`dev.herald.voicebridge/.AssistActivity`),
not a replacement or rebuild of official Herald. No project Gradle changes.

## Contract and limits

- Exported `android.intent.action.ASSIST` and `android.intent.action.VOICE_ASSIST`
  with `DEFAULT`; `MAIN`/`LAUNCHER` is also available for direct access.
- Always constructs a fresh explicit intent to
  `dev.herald.android/dev.hermeskotlin.wear.MainActivity`, with **only the boolean
  extra `listen=true`**. Incoming assist context/extras/URI grants are not copied.
- `NEW_TASK | CLEAR_TOP | SINGLE_TOP` brings the existing Herald activity forward
  and allows its `onNewIntent` voice handler, instead of duplicating the talk
  activity. This is a contract to verify on the installed official version, not
  a claim that warm Herald voice has been demonstrated.
- Finishes immediately after an accepted start. Missing/incompatible Herald
  (`ActivityNotFoundException`) or a denied start (`SecurityException`) leaves
  readable error text. Recreation restores that error without retrying voice;
  only a genuine new invocation (`onNewIntent`) retries on a retained activity.
  No silent fallback/retry, services, receivers or test endpoints. The user can
  dismiss the error normally.
- **No permissions**, including microphone, network, accessibility or notification
  listener. Herald owns microphone consent, recognition, live-voice preference,
  gateway access and existing chat identity.
- Manifest filters alone do **not** establish assistant-role selection, Samsung
  Home-button routing, physical button behavior, keyguard behavior, or voice
  compatibility. No role-request UI is assumed. VOICE_ASSIST is a system-origin
  action, not a general third-party shell invocation guarantee.

## Offline build

Requires Python 3.9+ and independently licensed tools prepared separately:

```text
~/.local/share/herald-voice-bridge-toolchain/
  jdk-21.0.13+9/bin/{java,javac,javap,keytool}
  independent/android.jar            # com.google.android:android:4.1.1.4, API16
  independent/aapt2/aapt2            # 8.13.0 Linux
  independent/r8.jar                 # 8.13.17
  independent/apksig.jar              # 8.13.0
  bridge-tests/android-all.jar        # optional test compile-only jar, see below
```

```sh
python3 tools/watch-voice-bridge/build.py
python3 tools/watch-voice-bridge/build.py --with-tests
```

Overrides: `--toolchain`, `--java-home`, `--android-jar`, `--test-android-jar`,
`--out`, `--signing-dir`. The script never downloads, accepts licenses, invokes
Gradle, connects to ADB, or installs anything. Missing tools fail explicitly.
Release source uses only API16-compatible Java APIs; manifest minSdk is 30 and
explicit targetSdk is 36. The old stubs are not proof of runtime compatibility.

The script creates a **stable local identity** on its first successful key
creation in `~/.local/share/herald-voice-bridge-signing/`: `bridge.p12` and
`password`. Directory mode 0700, files 0600; password randomly generated and
passed to keytool by filename, never embedded in the repo/command line.
Back up both securely to maintain update compatibility. Do not commit keys or
passwords; do not use this local experiment key for official Herald.
The test APK is signed with the same local identity for instrumentation access.

Outputs under ignored `out/` include release APK, optional test APK, compiled
manifest/badging text and `build-report.json` (tool hashes and APK SHA256).
Signing enables v2/v3 and verifies v3 for API30–36 using apksig. All zip entries
use fixed timestamps and deterministic order. `resources.arsc` is **STORED** and
its local-header data is four-byte aligned with a deterministic ZIP extra field
before signing (stdlib only, no SDK zipalign). The builder asserts storage and
actual data alignment again on the **signed** APK and records offsets in the
report. Android R+ rejects compressed/misaligned resource tables at install.
Repeat builds with the same
sources, tools and local signing identity are checked for byte reproducibility;
fresh identity generation intentionally changes the APK.

### Test-only modern framework dependency

The release builds with the API16 Maven jar. **The test monitor needs API26+
`ActivityMonitor()` and `onStartActivity(Intent)`, absent from those stubs.**
Do not weaken the guard or claim compilation from old stubs succeeds.

The locally verified, independently licensed compile-only alternative is Maven
`org.robolectric:android-all:9-robolectric-4913185-2` (Android 9/API28). Its POM
explicitly licenses this source-built artifact under Apache 2.0, unlike the SDK
EULA. Artifact is not packaged in either APK and no Robolectric runtime is used.

- Base URL: https://repo.maven.apache.org/maven2/org/robolectric/android-all/9-robolectric-4913185-2/
- Files: `android-all-9-robolectric-4913185-2.jar`, corresponding `.jar.sha1`, `.pom`
- Jar SHA256: `cf4aed5e458deb48ddc0ca92fc25156e6f478d9d5c1d948cdd1817a67ee11b32`
- Place jar at the optional path above, or provide `--test-android-jar`.
- Retain its POM/license metadata alongside the local jar; obtain/review tools
  explicitly, not through hidden downloads or SDK license acceptance.

## Boundary instrumentation (separate APK)

Agreed seam: public assist invocation → actual outgoing explicit Herald intent.
`tests/src/.../HandoffInstrumentation.java` uses the **real framework** monitor
and intercepts every non-bridge activity start before it can run. Explicit
components take precedence: only the exact bridge `AssistActivity` is allowed;
package-scoped implicit bridge starts are allowed only without a component.
A conflicting bridge package plus explicit Herald component is always blocked.
The suite calls the actual monitor with that sabotage intent without dispatching
it, before any test launch. It checks:

1. Both public action filters resolve to this package.
2. Cold and repeated bridge launches produce exactly one official component
   handoff, only boolean `listen=true`, sanitized context and task-reuse flags.
3. Retaining the bridge via an injected missing-target failure, recreating it
   with no new outgoing intent and preserved visible error, then delivering
   `callActivityOnNewIntent` exercises its warm lifecycle forwarding and finish.
4. Injected missing-target/security exceptions leave the corresponding visible
   error instead of finishing or launching a fallback.

The warm test is **framework lifecycle delivery**, not a real warm Herald
process: target starts are always blocked. It cannot prove microphone behavior,
Herald live voice/chat continuity, installed APK compatibility, role eligibility,
keyguard transitions or Samsung hardware routing. It intentionally cannot start
Herald's microphone or submit any prompt. Error injections do not uninstall,
disable or change official Herald. Release APK contains no harness.

**Only the device-owning parent/operator may deploy/run this.** Example after
explicitly choosing the device and approving changes (not executed by this task):

```sh
adb -s "$WATCH_SERIAL" install -r tools/watch-voice-bridge/out/herald-voice-bridge.apk
adb -s "$WATCH_SERIAL" install -r tools/watch-voice-bridge/out/herald-voice-bridge-tests.apk
timeout 60s adb -s "$WATCH_SERIAL" shell am instrument -w \
  dev.herald.voicebridge.tests/dev.herald.voicebridge.tests.HandoffInstrumentation
```

Read the reported `stream` and `INSTRUMENTATION_CODE`, not merely ADB's exit
status. Successful runner returns Android `RESULT_OK` (-1); assertion failures
return `RESULT_CANCELED` (0) with `FAIL:`. A 45-second runner watchdog also
terminates a stalled boundary run; the 60-second host timeout is a second bound.
Do not infer a passing test from a build.
Keep the watch locked if appropriate; do not bypass keyguard. Parent owns
cancellation, deployment verification, test APK removal and all device changes.

## Execution evidence and remaining acceptance

- Test source was written before bridge source. Initial preimplementation
  existence check failed (`RED: public assistant bridge does not exist yet`).
  Compiling the boundary test with API16 stubs genuinely failed for the missing
  modern monitor constructor/callback; this was a **compile blocker**, not a
  behavioral red/green device test.
- Resolved test compilation using the Apache-licensed API28 jar above. Real
  release and instrumentation source compiled, D8 generated DEX, aapt2 linked
  manifest, and apksig verified both signed APKs. Build checks examine compiled
  permission-free manifests and exclude the test harness from the release DEX.
- First manifest attempt exposed API16's non-public `supportsRtl`; removed this
  optional attribute instead of bypassing resource visibility.
- **No device test, install, assistant setting change or microphone invocation
  was performed by the implementation task.** The executable **device** boundary
  suite remains unrun; the host-only sabotage/lifecycle regressions below passed.
- Parent must separately verify installed official Herald contract, real
  cold/warm voice flow, actual absence/failure behavior where safe, assistant
  qualification, Samsung routing and physical hold-to-talk. Watch unlock may
  require the user; do not claim unattended end-to-end voice acceptance.

### Review-fix host evidence

Run without a device (the Java checks use the prepared JDK):

```sh
python3 -m unittest discover -s tools/watch-voice-bridge/tests -p 'test_host.py' -v
python3 tools/watch-voice-bridge/build.py --with-tests
```

- Packaging regression first failed with `8 != 0` (DEFLATED instead of STORED),
  matching the parent's real install failure (-124: targeting R+ requires a
  stored/aligned resource table). The
  parent's old release observation was compression 8, data offset 2193, unaligned.
  The regression now checks deterministic bytes and alignment across 16 prefix
  lengths, and the verifier rejects both compressed and misaligned fixtures.
- Scripted public `adb -s ... shell ...` transport tests initially exposed
  reconnect rejection, acceptance of a wrong stable device, invalid identities,
  and a nonempty unrelated voice interactor. All now pass. They cover rollback
  after each configure write and each restore write, rollback failure reporting,
  unrelated-holder refusal, stale baselines, exact absent/empty/literal `null`
  and quoted value preservation, and schema1 backup preservation. No real `adb`
  process is started by these tests.
- Real Java bridge source compiled against minimal host lifecycle doubles first
  failed `Recreation MUST NOT re-trigger Herald/microphone`; it now preserves the
  error with no outgoing start and retries once on a new intent. The same pure
  Java allowlist used by the device monitor first failed the conflicting
  package/component sabotage case, then passed after explicit-component
  precedence and exact-component allowlisting. These doubles do not simulate
  Android process death or establish device lifecycle correctness.
- **17 host tests passed.** Release and instrumentation APKs were really built
  twice with the prepared independently licensed toolchain. apksig verified v3
  for API30–36 on both builds; the signed resource tables were STORED, with data
  offsets 2436 (release) and 6276 (tests), both divisible by four. Hashes matched
  byte-for-byte on the repeat build:

| APK | SHA256 |
| --- | --- |
| `herald-voice-bridge.apk` | `ec8136e6f352d3e8ba6c656433efbfe846d6a79db37d7959a57214cad8ca005e` |
| `herald-voice-bridge-tests.apk` | `271773608bb2da75508b39398f17bc9bdcdace8afa4f59830700e81406c75e02` |

The build also rejects output ancestors and nested source/test/build-support
paths; the old leaf-name-only guard admitted `src/nested`. The existing signer
emits a deprecation note, not a failed verification. No SDK tools/licenses were
introduced and no Gradle files changed. Device installation and the expanded
framework boundary suite remain the parent/operator's next prerequisite before
any real handoff, routing change, or physical/microphone acceptance.

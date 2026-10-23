# Watch7 assistant bridge: execution and acceptance

## Verified execution

- Built the isolated bridge and separate instrumentation APK with the prepared user-local toolchain. No main application Gradle modules changed and no SDK license was silently accepted.
- Initial Watch7 install failed with Android error -124 because resources.arsc was compressed and unaligned. Reproduced that defect against the signed APK, corrected deterministic packaging, and added signed-APK storage/alignment assertions.
- Final release APK SHA-256: `ec8136e6f352d3e8ba6c656433efbfe846d6a79db37d7959a57214cad8ca005e`.
- Final test APK SHA-256: `271773608bb2da75508b39398f17bc9bdcdace8afa4f59830700e81406c75e02`.
- Both corrected APKs installed successfully on the actual Galaxy Watch7, and both installed package paths were read back.
- All 17 host regression tests passed. They cover packaging rejection, deterministic alignment, dangerous output paths, launch-guard sabotage, recreation behavior, configuration write failures/rollback, exact absent/empty/literal-null settings, stable device identity, stale baselines, unrelated role holders, and voice-interaction mismatch.
- On-watch instrumentation ran twice successfully. Raw output returned `INSTRUMENTATION_CODE: -1` and `PASS: assist resolution, cold/repeated handoff, warm lifecycle, missing/security errors; ALL Herald starts blocked.`
- The instrumentation intercepted every outgoing Herald launch before execution. Thus it verified the bridge's real Android launch boundary without opening Herald's microphone or submitting a prompt. Retained-activity lifecycle testing is not equivalent to actual warm Herald voice.
- The watch accepted the bridge as the qualified assistant role holder without bypassing qualification. Readback showed role holder `dev.herald.voicebridge`, secure assistant `dev.herald.voicebridge/.AssistActivity`, empty `voice_interaction_service`, and Samsung selector `googlevoiceassistant/googlevoiceassistant`.
- Live policy readback showed `mLongPressOnPowerBehavior=LONG_PRESS_POWER_ASSISTANT`.
- The original role holders, exact secure values and Samsung selector were restored and verified. The candidate was then reapplied and the same assistant/selector/policy state read back successfully.
- Official Herald, Google and Bixby were preserved. No phone or Gateway configuration was changed. Recognition remained provided by the existing Google recognition service; replacing assistant invocation does not imply replacing speech recognition.

## Review findings corrected

- Explicit component takes precedence in the test guard, preventing a conflicting package/component from escaping interception.
- Recreating a retained bridge error restores the error rather than activating voice again; a genuine new intent can retry.
- Candidate configuration requires the empty voice-interaction-service state expected for this activity assistant.
- New private backups use stable device identity and Android user, rather than a changing wireless-debug endpoint.
- Existing schema-1 backups remain intact and same-endpoint-only. They are not silently rewritten.

## Current acceptance boundary

The bridge is installed and candidate assistant/Home-hold routing was configured and read back. Exact device rollback was exercised. This is stronger than a build or static firmware claim, but it is not full hold-to-talk acceptance.

Still unverified:

- A real physical Home-button hold invokes the bridge on an unlocked watch.
- Official Herald starts actual speech input/live voice from that invocation.
- Paired phone/Gateway readiness, microphone consent, live-voice preference, and end-to-end agent reply.
- Actual cold/warm Herald voice lifecycle and lock-screen behavior.

The watch was off-wrist on its charger with a lock icon visible. No unlock credential was requested or guessed, no keyguard bypass attempted, no unattended audio captured, and no test prompt sent. Wireless ADB intermittently went offline. After the successful configure/restore/reconfigure proof, a later attempt to begin refreshing the old private schema-1 backup stopped at its initial read-only identity query because ADB was offline; no rename or further device write ran in that attempt. The original private backup therefore remains preserved.

Do not mark physical-button or voice acceptance complete from these results. The PR stays draft until that check or an explicit scope reduction. Device identifiers, pairing codes, credentials and screenshots are deliberately excluded from this public note.

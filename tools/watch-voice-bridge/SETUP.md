# Watch7 assistant routing: reversible setup

**Preparatory source only. Deployment is blocked until ticket #2 proves the
bridge-to-official-Herald handoff on the installed release.** Ticket #3 is not
complete from a build, role assignment, or this document. No device test was
performed while preparing this helper.

This stdlib Python 3 helper changes only the assistant role, role-managed secure
assistant state, and Samsung's Home **long-hold** selector. It does not install
APKs, launch activities/voice, simulate keys, change double-press or raise-to-talk,
disable Google/Bixby, grant permissions, or alter Herald/phone/gateway settings.
Do not run it concurrently with another settings tool or change watch user,
assistant, or button preferences during a transaction.

## Prerequisites and evidence gates

- An explicitly authorized, already connected ADB target; Python 3 and `adb` on
  PATH. Supply its target through `WATCH_SERIAL` yourself. No target, network
  address, pairing code, or credentials are embedded here.
- A separately installed, qualifying `dev.herald.voicebridge` APK for the current
  Android user, with the ticket #2 handoff proven against official Herald.
- Preserve Google and Bixby installations. Use a quiet, controlled environment
  for later manual voice tests; cancel immediately and do not send ambient speech
  or unsolicited prompts.
- Read `docs/research/watch-assistant-bridge-spec.md` and
  `docs/research/watch7-firmware-routing.md` in the integration checkout.

The helper resolves `android.intent.action.ASSIST` **within the bridge package**;
it never guesses an activity class. It uses `cmd role add-role-holder` without
qualification bypass flags. Successful shell role assignment is **not proof**
that the normal watch assistant-selection UI exposes or accepts the bridge.

## Commands

From the repository root, after setting `WATCH_SERIAL` to your authorized target:

```sh
python3 tools/watch-voice-bridge/watch_config.py --help
python3 tools/watch-voice-bridge/watch_config.py --serial "$WATCH_SERIAL" status
python3 tools/watch-voice-bridge/watch_config.py --serial "$WATCH_SERIAL" snapshot
# Only AFTER ticket #2 handoff proof; this flag acknowledges that prerequisite.
python3 tools/watch-voice-bridge/watch_config.py --serial "$WATCH_SERIAL" configure --handoff-proven
python3 tools/watch-voice-bridge/watch_config.py --serial "$WATCH_SERIAL" status
python3 tools/watch-voice-bridge/watch_config.py --serial "$WATCH_SERIAL" restore
```

`--serial` is mandatory for every operational command. `status` is read-only and
prints current state plus policy diagnostics; its output can contain private
device information. Keep raw output and backups local, not in public issues.
`configure --handoff-proven` is an operator acknowledgment, not automatic proof
of ticket #2. Do not use it to bypass that gate.

### Snapshot and scope

The default snapshot is
`~/.local/state/herald-voice-bridge/watch-config-backup.json` (directory mode 700,
file mode 600). It records the explicit ADB target and Android user privately,
original assistant role holders, secure `assistant`, `voice_interaction_service`,
and `voice_recognition_service`, plus global `setting_home_key_long_press`.
Recognition-service state is saved because the role observer can update it.
Absent values are JSON `null`; empty strings and the literal string `"null"`
remain distinct. Reads use `settings list`, not ambiguous `settings get` output.

The parent investigation's **`watch-baseline.json` has a different schema and
must not be overwritten or passed to this tool**. The helper refuses that name.
There is no overwrite/force option. A second snapshot fails. Backups survive
configure, failure, and restore. `--backup PATH` (before the subcommand) selects
a separate private file; it is not a baseline importer. An existing backup directory
must already be owned by you, not a symlink, and mode 700; the helper refuses it
otherwise rather than changing permissions on an arbitrary directory. Snapshot
refuses an already-selected bridge, because that is not an original baseline.

To start a genuinely new baseline, first restore and verify the old one; then
archive its private JSON deliberately and take a fresh snapshot. Never remove
or replace the only original snapshot just to make configure proceed. Snapshot
file creation is exclusive, and helper operations use an advisory local lock.
An interrupted snapshot write may leave an incomplete file: do not configure
from it or treat it as a verified baseline; review it locally first.

### Configure and rollback

Configure requires current scoped state to match the saved baseline exactly,
then checks installation and package-scoped ASSIST resolution. It:

1. Requests the bridge assistant role using the normal shell role manager.
2. Reads back the exact bridge role holder and the secure assistant component
   produced by the role observer; short/full component notation is normalized.
   It never forces secure `assistant` to paper over role rejection.
3. Writes **only** global `setting_home_key_long_press` to exactly
   `googlevoiceassistant/googlevoiceassistant`, then reads it back.
4. Requires `dumpsys window policy` to report
   `mLongPressOnPowerBehavior=LONG_PRESS_POWER_ASSISTANT`, together with the role,
   secure assistant, and selector readbacks. Updates get a bounded convergence
   wait. Unsupported output/readback fails closed rather than claiming success.

That Samsung value is a firmware mode selector, **not a component name**.
Arbitrary bridge component strings select the wrong policy branch. The legacy
Google-named token dispatches the general assistant path on the inspected
firmware; it does not prove hardware delivery or a working Herald voice flow.

On any exception after role assignment begins (including interruption), configure
attempts rollback and verifies the saved role holders, all saved secure keys,
and Samsung selector. Absent settings are restored with `settings delete`;
empty/literal strings use quoted `settings put`. The bridge role is removed
explicitly, original holders are re-added as needed, and unrelated current role
holders cause refusal rather than being silently deleted. Restore does not
clear all roles, bypass qualification, uninstall the bridge, or delete the backup.
Role-related secure state is restored after the role observer has had a chance
to converge, then checked again for drift.

If rollback is **NOT VERIFIED**, stop acceptance testing. Retain the snapshot,
check the same target/user and ADB connection, and run `restore` once recovery
is possible. A lost connection, process kill, role-observer race, rejected
original role, or concurrent settings change cannot be made transactionally
safe by a host script. Do not claim the original behavior is restored until
readback succeeds. An unrelated role-holder conflict needs deliberate operator
review; this tool will not remove it for you. The separate `restore` command
also exits nonzero on incomplete restoration.

## Required device acceptance (not yet performed)

Record these separately; none is implied by helper success:

- Ticket #2's public assistant-invocation handoff on the installed official
  Herald: cold/warm, permission and connection limits, clean bridge finish,
  missing/incompatible Herald behavior, no Bot Chat replacement or loop.
- Normal watch assistant-selection UI eligibility, independently of shell role
  assignment; keep Google/Bixby available for recovery.
- Candidate readbacks above, then an actual **physical Home hold** from the
  wearer with Herald closed and open. An intent invocation is only integration
  evidence; a synthetic key is only a dispatch experiment, not acceptance.
- Watch locked and unlocked, including touch/water lock and relevant keyboard
  guards. Do not promise lock-screen behavior from static firmware analysis.
- Bounded voice start followed by immediate cancellation, no unsolicited prompt,
  double-press/raise-to-talk unchanged, no unrelated permissions or app changes.
- Exact rollback verified, previous behavior checked physically, and candidate
  reapplied only if viable using the retained original snapshot. After restore,
  `configure --handoff-proven` can reapply only while state still matches baseline.

If Samsung blocks routing, restore the functioning prior behavior and report
that blocker. Double press is not a replacement for Home hold. Keep evidence
labels distinct: **source prepared**, **handoff proven**, **candidate configured**,
**rollback verified**, and **hardware confirmed**.

## Host-only checks

CLI help and Python compilation can be checked without ADB/device access.
These do not validate Android command support, role qualification, routing,
rollback, or physical/locked-watch acceptance. Device validation remains the
parent integration task, after ticket #2.

#!/usr/bin/env python3
"""Reversible, explicitly targeted Watch7 assistant routing; never launches voice."""
import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import time

PACKAGE = "dev.herald.voicebridge"
ROLE = "android.app.role.ASSISTANT"
SELECTOR = "setting_home_key_long_press"
ASSISTANT_MODE = "googlevoiceassistant/googlevoiceassistant"
SECURE = ("assistant", "voice_interaction_service", "voice_recognition_service")
DEFAULT_BACKUP = Path.home() / ".local/state/herald-voice-bridge/watch-config-backup.json"


class ConfigError(RuntimeError):
    pass


class Watch:
    def __init__(self, serial):
        self.serial = serial
        self.user = self.shell("am", "get-current-user").strip()
        if not self.user.isdecimal():
            raise ConfigError("Cannot determine current Android user")

    def shell(self, *args):
        # adb shell reparses arguments remotely; preserve empty/literal values.
        result = subprocess.run(
            ["adb", "-s", self.serial, "shell", shlex.join(args)],
            capture_output=True, text=True, timeout=30, check=False,
        )
        if result.returncode or result.stderr.strip():
            raise ConfigError(f"ADB command failed ({args[0]}): {result.stderr.strip() or result.stdout.strip()}")
        return result.stdout.replace("\r\n", "\n")

    def settings(self, namespace):
        output = self.shell("settings", "--user", self.user, "list", namespace)
        values = {}
        for line in output.splitlines():
            key, sep, value = line.partition("=")
            if not sep or key in values:
                raise ConfigError("Ambiguous settings list; refusing lossy snapshot")
            values[key] = value
        return values

    def holders(self):
        output = self.shell("cmd", "role", "get-role-holders", "--user", self.user, ROLE)
        holders = output.splitlines()
        if any(not re.fullmatch(r"[\w]+(?:\.[\w]+)+", h) for h in holders):
            raise ConfigError("Unexpected role-holder output")
        return sorted(set(holders))

    def state(self):
        if self.shell("am", "get-current-user").strip() != self.user:
            raise ConfigError("Current Android user changed; stop and inspect manually")
        secure = self.settings("secure")
        global_values = self.settings("global")
        # None means absent; empty and literal 'null' remain strings.
        return {"holders": self.holders(),
                "secure": {key: secure.get(key) for key in SECURE},
                "long_press": global_values.get(SELECTOR)}

    def role(self, operation, package):
        self.shell("cmd", "role", operation + "-role-holder", "--user", self.user, ROLE, package, "0")

    def setting(self, namespace, key, value):
        args = ("delete", namespace, key) if value is None else ("put", namespace, key, value)
        self.shell("settings", "--user", self.user, *args)
        wait_for(lambda: self.settings(namespace).get(key) == value,
                 f"{namespace}.{key} readback mismatch")

    def resolve_assist(self):
        if not self.shell("pm", "path", "--user", self.user, PACKAGE).startswith("package:"):
            raise ConfigError("Bridge is not installed for this user")
        output = self.shell("cmd", "package", "resolve-activity", "--brief", "--user", self.user,
                            "-a", "android.intent.action.ASSIST", "-p", PACKAGE)
        components = [line.strip() for line in output.splitlines()
                      if re.fullmatch(re.escape(PACKAGE) + r"/[\w.$]+", line.strip())]
        if len(components) != 1:
            raise ConfigError("Cannot resolve a unique ASSIST activity within the bridge package")
        return canonical_component(components[0])

    def candidate(self, component):
        state = self.state()
        assistant = state["secure"]["assistant"]
        policy = self.shell("dumpsys", "window", "policy")
        return (state["holders"] == [PACKAGE]
                and isinstance(assistant, str)
                and canonical_component(assistant) == component
                and state["long_press"] == ASSISTANT_MODE
                and bool(re.search(r"mLongPressOnPowerBehavior\s*=\s*LONG_PRESS_POWER_ASSISTANT\b", policy)))


def canonical_component(component):
    package, sep, activity = component.partition("/")
    if not sep:
        return ""
    return package + "/" + (package + activity if activity.startswith(".") else activity)


def wait_for(predicate, message):
    for _ in range(20):
        if predicate():
            return
        time.sleep(0.25)
    raise ConfigError(message)


@contextlib.contextmanager
def backup_lock(path):
    parent = path.parent
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = parent.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise ConfigError("Backup directory must be an owned, non-symlink directory with mode 700")
    fd = os.open(str(path) + ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def save_backup(path, watch):
    if path.exists() or path.is_symlink():
        raise ConfigError("Backup already exists; never overwrite it. Restore first; archive deliberately if needed.")
    state = watch.state()
    if PACKAGE in state["holders"] or (state["secure"]["assistant"] or "").startswith(PACKAGE + "/"):
        raise ConfigError("Bridge already selected; cannot capture a pre-bridge baseline")
    data = {"schema": 1, "serial": watch.serial, "user": watch.user, "state": state}
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(data, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def load_backup(path, watch):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise ConfigError("Backup must be an owned regular file with mode 600")
        data = json.load(stream)
    if (not isinstance(data, dict) or data.get("schema") != 1
            or data.get("serial") != watch.serial or data.get("user") != watch.user):
        raise ConfigError("Backup schema/device/user mismatch")
    state = data.get("state", {})
    if (not isinstance(state, dict) or set(state) != {"holders", "secure", "long_press"}
            or not isinstance(state["holders"], list)
            or any(not isinstance(h, str) or not re.fullmatch(r"[\w]+(?:\.[\w]+)+", h) for h in state["holders"])
            or not isinstance(state["secure"], dict) or set(state["secure"]) != set(SECURE)
            or any(v is not None and not isinstance(v, str)
                   for v in [state["long_press"], *state["secure"].values()])
            or PACKAGE in state["holders"]):
        raise ConfigError("Malformed or non-baseline backup")
    return state


def restore(watch, original):
    allowed = set(original["holders"]) | {PACKAGE}
    unexpected = set(watch.holders()) - allowed
    if unexpected:
        raise ConfigError("Refusing to remove unrelated role holders: " + ", ".join(sorted(unexpected)))
    # Never clear the role wholesale. Only this helper's bridge may be removed.
    if PACKAGE in watch.holders():
        watch.role("remove", PACKAGE)
        wait_for(lambda: PACKAGE not in watch.holders(), "Bridge role removal not confirmed")
    for holder in original["holders"]:
        if holder not in watch.holders():
            watch.role("add", holder)
            wait_for(lambda: holder in watch.holders(), "Original role assignment not confirmed")
    wait_for(lambda: watch.holders() == original["holders"], "Original role holders not restored")
    # Role observer runs asynchronously; let it converge before restoring exact keys.
    time.sleep(0.5)
    for key, value in original["secure"].items():
        watch.setting("secure", key, value)
    watch.setting("global", SELECTOR, original["long_press"])
    wait_for(lambda: watch.state() == original, "Original settings not restored exactly")
    time.sleep(0.5)
    if watch.state() != original:
        raise ConfigError("Restored settings changed again; inspect role observer manually")


def configure(watch, original):
    component = watch.resolve_assist()
    if watch.state() != original:
        raise ConfigError("Current state differs from saved baseline; restore/review before configuring")
    try:
        watch.role("add", PACKAGE)  # No qualification bypass, no secure-assistant override.
        wait_for(lambda: watch.holders() == [PACKAGE], "Bridge role assignment not confirmed")
        wait_for(lambda: canonical_component(watch.state()["secure"]["assistant"] or "") == component,
                 "Role observer did not select resolved bridge ASSIST activity")
        watch.setting("global", SELECTOR, ASSISTANT_MODE)
        wait_for(lambda: watch.candidate(component), "Assistant/selector/policy readback failed")
    except BaseException as failure:
        try:
            restore(watch, original)
        except BaseException as rollback_failure:
            raise ConfigError(f"Configure failed: {failure}; ROLLBACK NOT VERIFIED: {rollback_failure}. Keep backup and restore manually.") from failure
        raise ConfigError(f"Configure failed: {failure}; original state restored and verified") from failure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True, help="Explicit adb target (no implicit device selection)")
    parser.add_argument("--backup", type=Path, default=DEFAULT_BACKUP, help="Private backup path; never overwritten")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("snapshot", help="Save original state without device writes")
    candidate = commands.add_parser("configure", help="Apply candidate with automatic rollback on failure")
    candidate.add_argument("--handoff-proven", action="store_true", required=True,
                           help="Confirm ticket #2 installed-release handoff proof is complete")
    commands.add_parser("status", help="Read current routing and policy without launching anything")
    commands.add_parser("restore", help="Restore saved state exactly; retain backup")
    args = parser.parse_args()
    if not args.serial.strip() or args.serial.startswith("-"):
        parser.error("--serial must be an explicit nonempty target")
    if args.backup.name == "watch-baseline.json":
        parser.error("watch-baseline.json belongs to the parent investigation; use watch-config-backup.json")
    try:
        watch = Watch(args.serial)
        if args.command == "status":
            print(json.dumps({"user": watch.user, "state": watch.state(),
                              "policy": watch.shell("dumpsys", "window", "policy")}, indent=2))
        else:
            with backup_lock(args.backup):
                if args.command == "snapshot":
                    save_backup(args.backup, watch)
                    print(f"Private baseline saved: {args.backup}")
                else:
                    original = load_backup(args.backup, watch)
                    if args.command == "configure":
                        configure(watch, original)
                        print("Candidate routing read back; voice and physical-button acceptance NOT tested.")
                    else:
                        restore(watch, original)
                        print("Original role holders, secure values and Samsung selector restored and verified.")
    except (ConfigError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted; retain backup and inspect/restore state.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())

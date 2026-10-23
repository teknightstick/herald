"""Host-only regressions; no ADB access or device mutations."""
import importlib.util
import json
import shlex
import subprocess
from unittest.mock import patch
import copy
from pathlib import Path
import struct
import tempfile
from typing import Optional
import unittest
import zipfile

HERE = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = load("build")
config = load("watch_config")


def resource_layout(path):
    with zipfile.ZipFile(path) as archive, path.open("rb") as stream:
        info = archive.getinfo("resources.arsc")
        stream.seek(info.header_offset + 26)
        name_size, extra_size = struct.unpack("<HH", stream.read(4))
        return info.compress_type, info.header_offset + 30 + name_size + extra_size


class PackagingTests(unittest.TestCase):
    def test_unsafe_output_ancestors_and_source_descendants_refused(self):
        for directory in [HERE, HERE.parent, HERE / "src/nested", HERE / "tests/scratch", HERE / "build-support/x"]:
            with self.subTest(directory=directory), self.assertRaises(ValueError):
                build.validate_output_directory(directory)
        build.validate_output_directory(HERE / "out")

    def test_resource_verifier_rejects_deflated_or_unaligned(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.apk"
            for compression in [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED]:
                with zipfile.ZipFile(path, "w") as archive:
                    info = zipfile.ZipInfo("resources.arsc")
                    info.compress_type = compression
                    info.extra = struct.pack("<HH", 0xCAFE, 1) + b"\0"
                    archive.writestr(info, b"resource table")
                with self.assertRaisesRegex(RuntimeError, "STORED and four-byte aligned"):
                    build.verify_resource_layout(path)

    def test_resources_are_stored_aligned_and_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            for length in range(16):
                entries = [("AndroidManifest.xml", b"a" * length),
                           ("resources.arsc", b"resource table"), ("classes.dex", b"dex")]
                first, second = (Path(directory) / n for n in ("a.apk", "b.apk"))
                build.deterministic_zip(first, entries)
                build.deterministic_zip(second, reversed(entries))
                compression, offset = resource_layout(first)
                self.assertEqual(compression, zipfile.ZIP_STORED)
                self.assertEqual(offset % 4, 0)
                self.assertEqual(first.read_bytes(), second.read_bytes())


class ScriptedADB:
    """Script the public adb shell protocol, including role-observer side effects."""
    def __init__(self):
        self.identity = "TESTWATCH42"
        self.user = "0"
        self.state = {"holders": ["com.google.assistant"],
                      "secure": {"assistant": "com.google.assistant/.Main",
                                 "voice_interaction_service": "", "voice_recognition_service": "null"},
                      "long_press": None}
        self.calls = []
        self.writes = 0
        self.fail_write: Optional[int] = None
        self.fail_all_writes = False
        self.interactor = ""

    def __call__(self, argv, **kwargs):
        if argv[:2] != ["adb", "-s"] or argv[3] != "shell":
            raise AssertionError(argv)
        args = shlex.split(argv[4])
        self.calls.append((argv[2], args))
        output = ""
        writing = False
        if args == ["am", "get-current-user"]:
            output = self.user
        elif args == ["getprop", "ro.serialno"]:
            output = self.identity
        elif args[:2] == ["pm", "path"]:
            output = "package:/data/app/bridge/base.apk"
        elif args[:3] == ["cmd", "package", "resolve-activity"]:
            output = config.PACKAGE + "/.AssistActivity"
        elif args[:3] == ["dumpsys", "window", "policy"]:
            output = "mLongPressOnPowerBehavior=LONG_PRESS_POWER_ASSISTANT"
        elif args[:3] == ["cmd", "role", "get-role-holders"]:
            output = "\n".join(self.state["holders"])
        elif args[:2] == ["cmd", "role"]:
            writing = True
            package = args[-2]
            if args[2] == "add-role-holder":
                self.state["holders"] = [package]
                self.state["secure"]["assistant"] = package + "/.AssistActivity"
                self.state["secure"]["voice_interaction_service"] = self.interactor
            else:
                self.state["holders"].remove(package)
        elif args[:1] == ["settings"]:
            operation, namespace = args[3:5]
            values = (self.state["secure"] if namespace == "secure" else
                      {config.SELECTOR: self.state["long_press"]})
            if operation == "list":
                output = "\n".join(k + "=" + v for k, v in values.items() if v is not None)
            else:
                writing = True
                key = args[5]
                value = None if operation == "delete" else args[6]
                if namespace == "secure":
                    self.state["secure"][key] = value
                else:
                    self.state["long_press"] = value
        else:
            raise AssertionError(args)
        if writing:
            self.writes += 1
            if self.fail_all_writes or self.writes == self.fail_write:
                return subprocess.CompletedProcess(argv, 1, "", "injected failure after write")
        return subprocess.CompletedProcess(argv, 0, output + "\n" if output else "", "")


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "baseline.json"
        self.adb = ScriptedADB()
        self.patch = patch.object(config.subprocess, "run", self.adb)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        sleeper = patch.object(config.time, "sleep", lambda _: None)
        sleeper.start()
        self.addCleanup(sleeper.stop)
        self.watch = config.Watch("watch.local:1111")
        self.original = copy.deepcopy(self.adb.state)
        config.save_backup(self.path, self.watch)

    def test_reconnect_same_device_different_port(self):
        watch = config.Watch("watch.local:2222")
        self.assertEqual(config.load_backup(self.path, watch), self.original)
        data = json.loads(self.path.read_text())
        self.assertEqual(data["schema"], 2)
        self.assertEqual(data["device_id"], self.adb.identity)

    def test_wrong_device_or_user_refused_before_writes(self):
        for identity, user in [("OTHER", "0"), ("TESTWATCH42", "10")]:
            self.adb.identity, self.adb.user = identity, user
            with self.assertRaises(config.ConfigError):
                config.load_backup(self.path, config.Watch("watch.local:1111"))
        self.assertEqual(self.adb.writes, 0)

    def test_invalid_stable_identity_refused(self):
        for value in ["", "unknown", "null", "bad id", "bad\nserial"]:
            self.adb.identity = value
            with self.assertRaises(config.ConfigError):
                config.Watch("watch.local:1111")

    def test_legacy_same_serial_only_and_backup_unchanged(self):
        data = json.loads(self.path.read_text())
        data["schema"] = 1
        data.pop("device_id", None)
        self.path.write_text(json.dumps(data))
        baseline = self.path.read_bytes()
        self.assertEqual(config.load_backup(self.path, self.watch), self.original)
        with self.assertRaises(config.ConfigError):
            config.load_backup(self.path, config.Watch("watch.local:2222"))
        with self.assertRaises(config.ConfigError):
            config.save_backup(self.path, self.watch)
        self.assertEqual(self.path.read_bytes(), baseline)

    def test_configure_and_restore_exact_absent_empty_literal_null(self):
        config.configure(self.watch, self.original)
        self.assertTrue(self.watch.candidate(config.PACKAGE + "/dev.herald.voicebridge.AssistActivity"))
        config.restore(self.watch, self.original)
        self.assertEqual(self.adb.state, self.original)
        self.assertTrue(self.path.exists())

    def test_failure_after_each_configure_write_rolls_back(self):
        # The candidate performs exactly role assignment and selector writes.
        for write in [1, 2]:
            with self.subTest(write=write):
                self.adb.state = copy.deepcopy(self.original)
                self.adb.writes = 0
                self.adb.fail_write = write
                with self.assertRaisesRegex(config.ConfigError, "original state restored and verified"):
                    config.configure(self.watch, self.original)
                self.assertEqual(self.adb.state, self.original)

    def test_failure_after_each_restore_write_retains_baseline_and_can_recover(self):
        for write in range(1, 7):
            with self.subTest(write=write):
                self.adb.state = copy.deepcopy(self.original)
                self.adb.fail_write = None
                config.configure(self.watch, self.original)
                self.adb.writes = 0
                self.adb.fail_write = write
                baseline = self.path.read_bytes()
                with self.assertRaises(config.ConfigError):
                    config.restore(self.watch, self.original)
                self.assertEqual(self.path.read_bytes(), baseline)
                self.adb.fail_write = None
                config.restore(self.watch, self.original)
                self.assertEqual(self.adb.state, self.original)

    def test_all_setting_value_forms_round_trip(self):
        for value in [None, "", "null", "quoted ' and ; text"]:
            with self.subTest(value=value):
                original = copy.deepcopy(self.original)
                original["secure"] = dict.fromkeys(config.SECURE, value)
                original["long_press"] = value
                self.adb.state = copy.deepcopy(original)
                config.configure(self.watch, original)
                config.restore(self.watch, original)
                self.assertEqual(self.adb.state, original)

    def test_rollback_failure_is_explicit_and_retains_backup(self):
        self.adb.fail_all_writes = True
        baseline = self.path.read_bytes()
        with self.assertRaisesRegex(config.ConfigError, "ROLLBACK NOT VERIFIED"):
            config.configure(self.watch, self.original)
        self.assertEqual(self.path.read_bytes(), baseline)

    def test_unrelated_holder_refused_without_write(self):
        self.adb.state["holders"] = ["com.unrelated.assistant"]
        with self.assertRaisesRegex(config.ConfigError, "unrelated role holders"):
            config.restore(self.watch, self.original)
        self.assertEqual(self.adb.writes, 0)

    def test_stale_baseline_refused_without_write(self):
        self.adb.state["long_press"] = "changed"
        with self.assertRaisesRegex(config.ConfigError, "differs from saved baseline"):
            config.configure(self.watch, self.original)
        self.assertEqual(self.adb.writes, 0)

    def test_nonempty_interactor_fails_and_rolls_back(self):
        self.adb.interactor = "com.unrelated/.VoiceService"
        with self.assertRaisesRegex(config.ConfigError, "original state restored and verified"):
            config.configure(self.watch, self.original)
        self.assertEqual(self.adb.state, self.original)


class JavaBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from java_fixtures import SOURCES
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.jdk = next(iter(sorted((Path.home() / ".local/share/herald-voice-bridge-toolchain").glob("jdk-*"))))
        sources = []
        for name, content in SOURCES.items():
            path = cls.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            sources.append(path)
        sources += [HERE / "src/dev/herald/voicebridge/AssistActivity.java",
                    HERE / "tests/src/dev/herald/voicebridge/tests/LaunchPolicy.java"]
        subprocess.run([str(cls.jdk / "bin/javac"), "-d", str(cls.root), *map(str, sources)], check=True)

    def check_boundary(self, name):
        result = subprocess.run([str(self.jdk / "bin/java"), "-cp", str(self.root), "HostChecks", name],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_guard_conflicting_component_sabotage(self):
        self.check_boundary("guard")

    def test_recreation_preserves_error_without_retry(self):
        self.check_boundary("lifecycle")


if __name__ == "__main__":
    unittest.main()

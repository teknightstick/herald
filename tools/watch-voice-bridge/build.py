#!/usr/bin/env python3
"""Offline isolated Java APK build. Never installs, downloads or accepts licenses."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent


def run(*args, capture=False):
    return subprocess.run([str(a) for a in args], check=True, text=True,
                          stdout=subprocess.PIPE if capture else None).stdout


def deterministic_zip(destination, entries):
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(entries):
            info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", type=Path, default=Path.home() / ".local/share/herald-voice-bridge-toolchain")
    parser.add_argument("--java-home", type=Path)
    parser.add_argument("--android-jar", type=Path)
    parser.add_argument("--test-android-jar", type=Path,
                        help="API26+ independently licensed Android framework jar, compile-only")
    parser.add_argument("--with-tests", action="store_true", help="Also build the separate blocking instrumentation APK")
    parser.add_argument("--out", type=Path, default=HERE / "out")
    parser.add_argument("--signing-dir", type=Path, default=Path.home() / ".local/share/herald-voice-bridge-signing")
    args = parser.parse_args()
    root = args.toolchain.expanduser().resolve()
    independent = root / "independent"
    java_home = args.java_home or next(iter(sorted(root.glob("jdk-*"))), None)
    if java_home is None:
        parser.error("JDK missing: supply --java-home (no tools are downloaded automatically)")
    java_home = java_home.resolve()
    java, javac, keytool = (java_home / "bin" / name for name in ("java", "javac", "keytool"))
    android = (args.android_jar or independent / "android.jar").resolve()
    test_android = (args.test_android_jar or root / "bridge-tests/android-all.jar").resolve()
    aapt = independent / "aapt2/aapt2"
    r8, apksig = independent / "r8.jar", independent / "apksig.jar"
    needed = [java, javac, keytool, android, aapt, r8, apksig]
    if args.with_tests:
        needed.append(test_android)
    for path in needed:
        if not path.is_file():
            parser.error(f"Required tool missing: {path}; see README, no license accepted or download attempted")
    if args.with_tests:
        # API16 stubs cannot compile the public ActivityMonitor interceptor added in API26.
        api = run(java_home / "bin/javap", "-classpath", test_android,
                  "android.app.Instrumentation$ActivityMonitor", capture=True)
        if "onStartActivity(android.content.Intent)" not in api or "ActivityMonitor();" not in api:
            parser.error("Test compile jar lacks API26+ ActivityMonitor() / onStartActivity(Intent)")
    out = args.out.resolve()
    if out == HERE or HERE in out.parents and out.name in {"src", "tests", "build-support"}:
        parser.error("Unsafe output directory")
    out.mkdir(parents=True, exist_ok=True)
    signing = args.signing_dir.expanduser().resolve()
    # User-local keys must never live inside ANY checkout/worktree.
    try:
        repository = Path(run("git", "-C", HERE, "rev-parse", "--show-toplevel", capture=True).strip())
    except subprocess.CalledProcessError:
        repository = HERE
    if signing == repository or repository in signing.parents:
        parser.error("Signing directory must be outside repository")
    signing.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(signing, 0o700)
    key, password = signing / "bridge.p12", signing / "password"
    if key.exists() != password.exists():
        parser.error("Incomplete signing identity: refusing to replace existing key/password")
    if not key.exists():
        fd = os.open(password, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as secret:
            secret.write(secrets.token_hex(32) + "\n")
        run(keytool, "-genkeypair", "-storetype", "PKCS12", "-keystore", key,
            "-storepass:file", password, "-keypass:file", password, "-alias", "bridge",
            "-keyalg", "RSA", "-keysize", "3072", "-validity", "10000",
            "-dname", "CN=Herald Voice Bridge Local")
        os.chmod(key, 0o600)
    host = out / "host"
    host.mkdir(exist_ok=True)
    run(javac, "-cp", apksig, "-d", host, HERE / "build-support/SignApk.java")
    tools = {str(p.relative_to(root)) if p.is_relative_to(root) else str(p):
             hashlib.sha256(p.read_bytes()).hexdigest() for p in [android, aapt, r8, apksig]}
    if args.with_tests:
        tools[str(test_android)] = hashlib.sha256(test_android.read_bytes()).hexdigest()

    def build(name, sources, manifest, compile_android):
        work = out / name
        if work.exists():
            shutil.rmtree(work)
        classes, dex = work / "classes", work / "dex"
        classes.mkdir(parents=True)
        dex.mkdir()
        run(javac, "--release", "8", "-Xlint:-options", "-cp", compile_android,
            "-d", classes, *sorted(sources.rglob("*.java")))
        class_jar = work / "classes.jar"
        deterministic_zip(class_jar, [(str(p.relative_to(classes)), p.read_bytes())
                                     for p in classes.rglob("*.class")])
        run(java, "-cp", r8, "com.android.tools.r8.D8", "--release", "--min-api", "30",
            "--lib", java_home, "--lib", compile_android, "--output", dex, class_jar)
        resources, unsigned = work / "resources.apk", work / "unsigned.apk"
        run(aapt, "link", "-I", android, "--manifest", manifest,
            "--min-sdk-version", "30", "--target-sdk-version", "36", "-o", resources)
        with zipfile.ZipFile(resources) as zipped:
            entries = [(n, zipped.read(n)) for n in zipped.namelist()]
        entries += [(p.name, p.read_bytes()) for p in sorted(dex.glob("*.dex"))]
        deterministic_zip(unsigned, entries)
        apk = out / f"{name}.apk"
        run(java, "-cp", f"{host}{os.pathsep}{apksig}", "SignApk", unsigned, apk, key, password)
        badging = run(aapt, "dump", "badging", apk, capture=True)
        xml = run(aapt, "dump", "xmltree", "--file", "AndroidManifest.xml", apk, capture=True)
        if "uses-permission" in xml or "android:debuggable" in xml:
            raise RuntimeError("Unexpected manifest permissions or debug attribute")
        (out / f"{name}-manifest.txt").write_text(xml)
        (out / f"{name}-badging.txt").write_text(badging)
        if name == "herald-voice-bridge":
            with zipfile.ZipFile(apk) as zipped:
                content = b"".join(zipped.read(n) for n in zipped.namelist() if n.endswith(".dex"))
            if b"HandoffInstrumentation" in content or "instrumentation" in xml:
                raise RuntimeError("Test harness leaked into release APK")
            for value in ("dev.herald.voicebridge", "android.intent.action.ASSIST", "android.intent.action.VOICE_ASSIST"):
                if value not in xml:
                    raise RuntimeError(f"Missing public contract in compiled manifest: {value}")
        digest = hashlib.sha256(apk.read_bytes()).hexdigest()
        print(f"SHA256 {digest}  {apk}")
        return {"apk": str(apk), "sha256": digest}

    artifacts = [build("herald-voice-bridge", HERE / "src", HERE / "AndroidManifest.xml", android)]
    if args.with_tests:
        artifacts.append(build("herald-voice-bridge-tests", HERE / "tests/src",
                               HERE / "tests/AndroidManifest.xml", test_android))
    (out / "build-report.json").write_text(json.dumps({"tools_sha256": tools, "artifacts": artifacts}, indent=2) + "\n")
    print("Build/artifact checks complete. No device tests run; nothing installed.")


if __name__ == "__main__":
    main()

import com.android.apksig.ApkSigner;
import com.android.apksig.ApkVerifier;
import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.cert.X509Certificate;
import java.util.Arrays;
import java.util.List;

/** Host-only signer; never packaged into either Android APK. */
public final class SignApk {
    public static void main(String[] args) throws Exception {
        if (args.length != 4) throw new IllegalArgumentException("input output keystore password-file");
        char[] password = Files.readString(Path.of(args[3])).trim().toCharArray();
        KeyStore store = KeyStore.getInstance("PKCS12");
        try (InputStream in = Files.newInputStream(Path.of(args[2]))) { store.load(in, password); }
        PrivateKey key = (PrivateKey) store.getKey("bridge", password);
        X509Certificate certificate = (X509Certificate) store.getCertificate("bridge");
        Arrays.fill(password, '\0');
        var signer = new ApkSigner.SignerConfig.Builder("bridge", key, List.of(certificate)).build();
        new ApkSigner.Builder(List.of(signer)).setInputApk(new File(args[0]))
                .setOutputApk(new File(args[1])).setMinSdkVersion(30)
                .setV1SigningEnabled(false).setV2SigningEnabled(true)
                .setV3SigningEnabled(true).setV4SigningEnabled(false).build().sign();
        var result = new ApkVerifier.Builder(new File(args[1])).setMinCheckedPlatformVersion(30)
                .setMaxCheckedPlatformVersion(36).build().verify();
        if (!result.isVerified() || !result.isVerifiedUsingV3Scheme())
            throw new IllegalStateException("APK signature verification failed: " + result.getErrors());
        System.out.println("Verified APK v3 for API30–36 (v2 also enabled): " + args[1]);
    }
}

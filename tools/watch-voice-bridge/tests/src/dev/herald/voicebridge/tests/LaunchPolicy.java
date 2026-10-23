package dev.herald.voicebridge.tests;

/** Pure allowlist shared by the real monitor and host sabotage regression. */
public final class LaunchPolicy {
    private LaunchPolicy() {}

    public static boolean allows(String intentPackage, String componentPackage, String componentClass) {
        // Android resolves an explicit component before the package restriction.
        if (componentPackage != null || componentClass != null) {
            return "dev.herald.voicebridge".equals(componentPackage)
                    && "dev.herald.voicebridge.AssistActivity".equals(componentClass);
        }
        return "dev.herald.voicebridge".equals(intentPackage);
    }
}

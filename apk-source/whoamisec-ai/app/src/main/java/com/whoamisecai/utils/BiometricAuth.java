package com.whoamisecai.utils;

import android.app.Activity;
import android.os.Build;
import androidx.annotation.NonNull;
import androidx.biometric.BiometricManager;
import androidx.biometric.BiometricPrompt;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.FragmentActivity;

public class BiometricAuth {

    public interface AuthCallback {
        void onSuccess();
        void onFailure();
    }

    public static void authenticate(Activity activity,
                                    String title, String subtitle,
                                    AuthCallback callback) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) {
            callback.onFailure();
            return;
        }
        try {
            BiometricManager biometricManager = BiometricManager.from(activity);
            switch (biometricManager.canAuthenticate()) {
                case BiometricManager.BIOMETRIC_SUCCESS:
                    showBiometricPrompt(activity, title, subtitle, callback);
                    break;
                default:
                    callback.onFailure();
            }
        } catch (Exception e) {
            callback.onFailure();
        }
    }

    private static void showBiometricPrompt(Activity activity,
                                            String title, String subtitle,
                                            AuthCallback callback) {
        try {
            BiometricPrompt.PromptInfo promptInfo = new BiometricPrompt.PromptInfo.Builder()
                .setTitle(title)
                .setSubtitle(subtitle)
                .setNegativeButtonText("Skip")
                .build();

            BiometricPrompt biometricPrompt = new BiometricPrompt(
                (FragmentActivity) activity,
                ContextCompat.getMainExecutor(activity),
                new BiometricPrompt.AuthenticationCallback() {
                    @Override
                    public void onAuthenticationSucceeded(@NonNull BiometricPrompt.AuthenticationResult result) {
                        callback.onSuccess();
                    }
                    @Override
                    public void onAuthenticationFailed() { callback.onFailure(); }
                    @Override
                    public void onAuthenticationError(int errorCode, @NonNull CharSequence errString) {
                        callback.onFailure();
                    }
                }
            );
            biometricPrompt.authenticate(promptInfo);
        } catch (Exception e) {
            callback.onFailure();
        }
    }
}

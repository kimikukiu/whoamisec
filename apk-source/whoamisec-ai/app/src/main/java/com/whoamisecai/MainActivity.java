/**
 * WHOAMISecAI Android v10 — Main Activity
 *
 * Hub with bottom navigation routing to:
 *  - Home: WebView loading whoamisecai.vercel.app
 *  - Chat: Native AI Chat with 80+ model selector
 *  - Builder: 28-Phase Neural Pipeline IDE
 *  - JARVIS: Voice-controlled HUD (Iron Man style)
 *  - Settings: API key + config panel
 *
 * @author WHOAMISecAI — whoamisecai | @proplanwh
 */

package com.whoamisecai;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.ConsoleMessage;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.util.Log;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import com.whoamisecai.api.AiClient;
import com.whoamisecai.builder.BuilderActivity;
import com.whoamisecai.chat.ChatActivity;
import com.whoamisecai.jarvis.JarvisHudActivity;
import com.whoamisecai.settings.SettingsActivity;
import com.whoamisecai.utils.BiometricAuth;

public class MainActivity extends Activity {

    private static final String APP_URL = "https://whoamisecai.vercel.app";
    private static final String PREFS_NAME = "whoamisecai_prefs";
    private static final String KEY_ADMIN = "admin_key";
    private static final String KEY_PIPELINE = "pipeline_mode";
    private static final String KEY_MODEL = "selected_model";

    private WebView webView;
    private FrameLayout splashOverlay;
    private ProgressBar splashProgress;
    private TextView splashStatus;
    private LinearLayout webviewContainer;

    private LinearLayout navHome, navChat, navBuilder, navJarvis, navSettings;

    private SharedPreferences prefs;
    private AiClient aiClient;
    private Handler mainHandler;
    private boolean isWebVisible = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN
        );
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            getWindow().setStatusBarColor(0xFF0a0a0f);
            getWindow().setNavigationBarColor(0xFF0a0a0f);
        }

        setContentView(R.layout.activity_main);
        mainHandler = new Handler(Looper.getMainLooper());
        prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        aiClient = new AiClient(APP_URL, getAdminKey());

        initViews();
        initWebView();
        initBottomNav();
        initBiometric();
        loadWebApp();
    }

    private void initViews() {
        webView = findViewById(R.id.webview);
        splashOverlay = findViewById(R.id.splash_overlay);
        splashProgress = findViewById(R.id.splash_progress);
        splashStatus = findViewById(R.id.splash_status);
        webviewContainer = findViewById(R.id.webview_container);

        navHome = findViewById(R.id.nav_home);
        navChat = findViewById(R.id.nav_chat);
        navBuilder = findViewById(R.id.nav_builder);
        navJarvis = findViewById(R.id.nav_jarvis);
        navSettings = findViewById(R.id.nav_settings);
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void initWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setRenderPriority(WebSettings.RenderPriority.HIGH);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setMixedContentMode(0);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setUserAgentString(settings.getUserAgentString() + " WHOAMISecAI/10.0 Android (Native)");
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        CookieManager.getInstance().setAcceptCookie(true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                splashStatus.setText("Loading " + url.substring(0, Math.min(url.length(), 40)) + "...");
                splashProgress.setProgress(30);
            }
            @Override
            public void onPageFinished(WebView view, String url) {
                splashProgress.setProgress(100);
                new Handler(Looper.getMainLooper()).postDelayed(() -> {
                    splashOverlay.animate().alpha(0f).setDuration(300)
                        .withEndAction(() -> splashOverlay.setVisibility(View.GONE));
                }, 300);
            }
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();
                if (url.contains("whoamisecai.vercel.app") || url.contains("vercel.app")) return false;
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                } catch (Exception ignored) {}
                return true;
            }
            @Override
            public void onReceivedError(WebView view, WebResourceRequest request,
                                        android.webkit.WebResourceError error) {
                if (error.getErrorCode() == -2) showOfflineMessage();
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                splashProgress.setProgress(Math.min(newProgress, 100));
                if (newProgress < 30) splashStatus.setText("Connecting...");
                else if (newProgress < 70) splashStatus.setText("Loading content...");
                else if (newProgress < 100) splashStatus.setText("Almost ready...");
            }
            @Override
            public boolean onConsoleMessage(ConsoleMessage consoleMessage) {
                Log.d("WHOAMISecAI-Web",
                    consoleMessage.message() + " [" + consoleMessage.sourceId() + ":" + consoleMessage.lineNumber() + "]");
                return true;
            }
            @Override
            public boolean onShowFileChooser(WebView webView,
                                            android.webkit.ValueCallback<Uri[]> filePathCallback,
                                            android.webkit.WebChromeClient.FileChooserParams fileChooserParams) {
                filePathCallback.onReceiveValue(new Uri[]{});
                return true;
            }
        });

        webView.addJavascriptInterface(new NativeBridge(), "AndroidNative");
    }

    private void loadWebApp() {
        if (!isNetworkAvailable()) { showOfflineMessage(); return; }
        splashStatus.setText("Connecting to WHOAMISecAI...");
        webView.loadUrl(APP_URL);
    }

    private void showOfflineMessage() {
        splashStatus.setText("Offline — check connection");
        splashOverlay.setVisibility(View.VISIBLE);
        webView.loadData(
            "<html><body style='background:#0a0a0f;color:#888;font-family:monospace;display:flex;align-items:center;justify-content:center;height:100vh;text-align:center;padding:20px'>" +
            "<div><h1 style='color:#8b5cf6'>WHOAMISecAI</h1><p>You are offline.</p>" +
            "<p style='color:#555;margin-top:12px'>Check your internet connection.</p></div></body></html>",
            "text/html", "UTF-8");
    }

    private void initBottomNav() {
        // Home — WebView
        navHome.setOnClickListener(v -> {
            setNavActive(0);
            webviewContainer.setVisibility(View.VISIBLE);
            isWebVisible = true;
            if (webView.getUrl() == null || !webView.getUrl().contains("whoamisecai")) {
                webView.loadUrl(APP_URL);
            }
        });

        // Chat — Native Chat Activity
        navChat.setOnClickListener(v -> {
            setNavActive(1);
            startActivity(new Intent(this, ChatActivity.class));
        });

        // Builder — 28-Phase Pipeline
        navBuilder.setOnClickListener(v -> {
            setNavActive(2);
            startActivity(new Intent(this, BuilderActivity.class));
        });

        // JARVIS — Voice HUD
        navJarvis.setOnClickListener(v -> {
            setNavActive(3);
            startActivity(new Intent(this, JarvisHudActivity.class));
        });

        // Settings
        navSettings.setOnClickListener(v -> {
            setNavActive(4);
            startActivity(new Intent(this, SettingsActivity.class));
        });
    }

    private void setNavActive(int index) {
        LinearLayout[] navItems = {navHome, navChat, navBuilder, navJarvis, navSettings};
        int activeColor = 0xFF8B5CF6;
        int inactiveColor = 0xFF555555;
        for (int i = 0; i < navItems.length; i++) {
            boolean active = (i == index);
            if (navItems[i].getChildCount() > 1) {
                TextView label = (TextView) navItems[i].getChildAt(1);
                label.setTextColor(active ? activeColor : inactiveColor);
            }
        }
    }

    private void initBiometric() {
        String adminKey = getAdminKey();
        if (adminKey != null && !adminKey.isEmpty()) {
            BiometricAuth.authenticate(this, "WHOAMISecAI", "Authenticate to access",
                new BiometricAuth.AuthCallback() {
                    @Override public void onSuccess() {}
                    @Override public void onFailure() {
                        Toast.makeText(MainActivity.this, "Biometric skipped", Toast.LENGTH_SHORT).show();
                    }
                });
        }
    }

    private String getAdminKey() {
        return prefs.getString(KEY_ADMIN, "wsec_4ead532b0d0b02c7eab1791978d7d4ac");
    }

    private boolean isNetworkAvailable() {
        ConnectivityManager cm = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        NetworkInfo activeNetwork = cm.getActiveNetworkInfo();
        return activeNetwork != null && activeNetwork.isConnected();
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && isWebVisible && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onResume() { super.onResume(); if (webView != null) webView.onResume(); }
    @Override
    protected void onPause() { super.onPause(); if (webView != null) webView.onPause(); }
    @Override
    protected void onDestroy() { if (webView != null) webView.destroy(); super.onDestroy(); }

    // ── JavaScript Bridge ──
    public class NativeBridge {
        @android.webkit.JavascriptInterface
        public String getAppVersion() { return "10.0.0"; }
        @android.webkit.JavascriptInterface
        public String getPipelineMode() { return prefs.getString(KEY_PIPELINE, "allm"); }
        @android.webkit.JavascriptInterface
        public void setPipelineMode(String mode) { prefs.edit().putString(KEY_PIPELINE, mode).apply(); }
        @android.webkit.JavascriptInterface
        public String getAdminKey() { return prefs.getString(KEY_ADMIN, ""); }
        @android.webkit.JavascriptInterface
        public boolean isAdmin() { String k = prefs.getString(KEY_ADMIN, ""); return k != null && !k.isEmpty(); }
        @android.webkit.JavascriptInterface
        public String getSelectedModel() { return prefs.getString(KEY_MODEL, "openai/gpt-4o"); }
        @android.webkit.JavascriptInterface
        public void setSelectedModel(String model) { prefs.edit().putString(KEY_MODEL, model).apply(); }
        @android.webkit.JavascriptInterface
        public void showToast(String message) { mainHandler.post(() -> Toast.makeText(MainActivity.this, message, Toast.LENGTH_SHORT).show()); }
        @android.webkit.JavascriptInterface
        public String getDeviceInfo() {
            return "{\n" +
                "  \"model\": \"" + Build.MODEL + "\",\n" +
                "  \"brand\": \"" + Build.BRAND + "\",\n" +
                "  \"manufacturer\": \"" + Build.MANUFACTURER + "\",\n" +
                "  \"sdk\": " + Build.VERSION.SDK_INT + ",\n" +
                "  \"release\": \"" + Build.VERSION.RELEASE + "\"\n" +
                "  \"abis\": \"" + String.join(",", Build.SUPPORTED_ABIS) + "\"\n" +
                "}";
        }
        @android.webkit.JavascriptInterface
        public void requestOsintScan(String target) {
            mainHandler.post(() -> Toast.makeText(MainActivity.this, "📡 OSINT: " + target, Toast.LENGTH_SHORT).show());
        }
        @android.webkit.JavascriptInterface
        public void sendToTelegramBot(String message) {
            mainHandler.post(() -> {
                try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/whoamisecai")));
                } catch (Exception e) { Toast.makeText(MainActivity.this, "Telegram not installed", Toast.LENGTH_SHORT).show(); }
            });
        }
        @android.webkit.JavascriptInterface
        public void jarvisOrchestrate(String message) {
            Log.d("NativeBridge", "jarvisOrchestrate: " + message);
            if (aiClient != null) aiClient.jarvisOrchestrate(message);
        }
        @android.webkit.JavascriptInterface
        public void claudeChat(String message) { if (aiClient != null) aiClient.claudeChat(message); }
        @android.webkit.JavascriptInterface
        public void jarvisStatus() { if (aiClient != null) aiClient.jarvisStatus(); }
        @android.webkit.JavascriptInterface
        public void skillsList() { if (aiClient != null) aiClient.skillsList(); }
    }
}

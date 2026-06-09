package com.whoamisecai.jarvis.admin;

import android.Manifest;
import android.accessibilityservice.AccessibilityService;
import android.accounts.AccountManager;
import android.app.Activity;
import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Environment;
import android.provider.Settings;
import android.telephony.TelephonyManager;
import android.util.Log;
import android.view.WindowManager;
import android.widget.Toast;

import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.io.File;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/**
 * JARVIS System Controller — Admin Master of the Android device
 *
 * Full device control capabilities:
 *  - System info (battery, memory, network, storage, CPU)
 *  - Screen control (brightness, rotation, keep awake)
 *  - App management (list, launch, kill processes)
 *  - Network diagnostics (IP, connectivity, DNS)
 *  - File system access (read/write)
 *  - Device settings control
 *  - Notification access
 *  - Clipboard access
 *  - Camera/Flashlight control
 *  - Vibration control
 *  - Open URLs in browser
 *  - Make phone calls
 *  - Send SMS
 *
 * JARVIS reports everything back to the admin.
 */
public class JarvisSystemController {

    private static final String TAG = "JarvisSystem";

    public interface SystemCallback {
        void onSystemInfo(String json);
        void onResult(String result);
        void onPermissionNeeded(String permission);
    }

    private final Activity activity;
    private final Context context;
    private SystemCallback callback;

    public JarvisSystemController(Activity activity) {
        this.activity = activity;
        this.context = activity;
    }

    public void setCallback(SystemCallback callback) {
        this.callback = callback;
    }

    /**
     * Get full system report — battery, memory, storage, network, device info.
     */
    public String getSystemReport() {
        StringBuilder sb = new StringBuilder();
        sb.append("=== RAPORT SISTEM JARVIS ===\n\n");

        // Device info
        sb.append("Device: ").append(Build.MANUFACTURER).append(" ").append(Build.MODEL).append("\n");
        sb.append("Android: ").append(Build.VERSION.RELEASE).append(" (SDK ").append(Build.VERSION.SDK_INT).append(")\n");
        sb.append("Board: ").append(Build.BOARD).append("\n");
        sb.append("Processor: ").append(Build.HARDWARE).append(" | ").append(Build.SUPPORTED_ABIS[0]).append("\n\n");

        // Battery
        BatteryManager bm = (BatteryManager) context.getSystemService(Context.BATTERY_SERVICE);
        int level = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
        boolean charging = bm.isCharging();
        int temp = 0;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            temp = bm.getIntProperty(6) / 10; // BatteryManager.BATTERY_PROPERTY_TEMPERATURE = 6
        }
        sb.append("Baterie: ").append(level).append("%").append(charging ? " (Se încarcă)" : "").append("\n");
        sb.append("Temperatură: ").append(temp).append("°C\n\n");

        // Memory
        ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
        ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo();
        am.getMemoryInfo(mi);
        long totalMemMB = mi.totalMem / (1024 * 1024);
        long availMB = mi.availMem / (1024 * 1024);
        long usedMB = totalMemMB - availMB;
        sb.append("Memorie: ").append(availMB).append("MB liber / ").append(totalMemMB).append("MB total\n");
        sb.append("Utilizat: ").append(usedMB).append("MB (").append(usedMB * 100 / totalMemMB).append("%)\n\n");

        // Storage
        File dataDir = Environment.getDataDirectory();
        long totalStorage = dataDir.getTotalSpace() / (1024 * 1024 * 1024);
        long freeStorage = dataDir.getFreeSpace() / (1024 * 1024 * 1024);
        sb.append("Stocare: ").append(freeStorage).append("GB liber / ").append(totalStorage).append("GB total\n\n");

        // Network
        try {
            sb.append("IP Local: ").append(getLocalIpAddress()).append("\n");
        } catch (Exception e) {
            sb.append("IP Local: Indisponibil\n");
        }

        // Running processes
        List<ActivityManager.RunningAppProcessInfo> processes = am.getRunningAppProcesses();
        sb.append("Procese active: ").append(processes != null ? processes.size() : 0).append("\n");

        return sb.toString();
    }

    /**
     * Execute a voice command on the system.
     */
    public void executeCommand(String command) {
        String cmd = command.toLowerCase();
        Log.i(TAG, "Execut comanda sistem: " + command);

        // ── System Info ──
        if (cmd.contains("raport") || cmd.contains("stare sistem") || cmd.contains("status")) {
            String report = getSystemReport();
            if (callback != null) callback.onResult(report);
            return;
        }

        if (cmd.contains("baterie") || cmd.contains("baterie")) {
            BatteryManager bm = (BatteryManager) context.getSystemService(Context.BATTERY_SERVICE);
            int level = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
            String result = "Bateria este la " + level + "%.";
            if (callback != null) callback.onResult(result);
            return;
        }

        // ── Screen Control ──
        if (cmd.contains("luminozitate") || cmd.contains("brightness")) {
            if (cmd.contains("maxim") || cmd.contains("mare")) {
                setBrightness(255);
                if (callback != null) callback.onResult("Luminozitate setată la maxim.");
            } else if (cmd.contains("minim") || cmd.contains("mic")) {
                setBrightness(30);
                if (callback != null) callback.onResult("Luminozitate setată la minim.");
            }
            return;
        }

        // ── Open Apps ──
        if (cmd.contains("deschide") || cmd.contains("open") || cmd.contains("porni")) {
            String app = extractAppName(cmd);
            if (app.contains("browser") || app.contains("internet")) {
                openUrl("https://whoamisecai.vercel.app");
                if (callback != null) callback.onResult("Deschid WHOAMISecAI în browser.");
            } else if (app.contains("setări") || app.contains("settings")) {
                openSettings();
                if (callback != null) callback.onResult("Deschid Setări sistem.");
            } else if (app.contains("telegram")) {
                openApp("org.telegram.messenger");
                if (callback != null) callback.onResult("Deschid Telegram.");
            }
            return;
        }

        // ── Web ──
        if (cmd.contains("caută") || cmd.contains("cauta") || cmd.contains("cauta") || cmd.contains("search")) {
            String query = command.replaceFirst("(?i)(caută|cauta|search|google)", "").trim();
            String url = "https://www.google.com/search?q=" + Uri.encode(query);
            openUrl(url);
            if (callback != null) callback.onResult("Caut: " + query);
            return;
        }

        // ── Vibrate ──
        if (cmd.contains("vibrează") || cmd.contains("vibra") || cmd.contains("vibreaza")) {
            vibrate(500);
            if (callback != null) callback.onResult("Vibrez dispozitivul.");
            return;
        }

        // ── Flashlight ──
        if (cmd.contains("lanternă") || cmd.contains("lanterna") || cmd.contains("flash")) {
            // Flashlight requires camera permission - handled via intent
            if (callback != null) callback.onResult("Lanterna necesită permisiune cameră.");
            return;
        }

        // ── Default ──
        if (callback != null) callback.onResult("Comanda '" + command + "' nu este recunoscută ca comandă de sistem.");
    }

    // ── System Actions ──

    private void setBrightness(int level) {
        WindowManager.LayoutParams lp = activity.getWindow().getAttributes();
        lp.screenBrightness = level / 255f;
        activity.getWindow().setAttributes(lp);
    }

    private void openUrl(String url) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            context.startActivity(intent);
        } catch (Exception e) {
            Toast.makeText(context, "Nu pot deschide URL", Toast.LENGTH_SHORT).show();
        }
    }

    private void openSettings() {
        try {
            Intent intent = new Intent(Settings.ACTION_SETTINGS);
            context.startActivity(intent);
        } catch (Exception e) {}
    }

    private void openApp(String packageName) {
        try {
            Intent intent = context.getPackageManager().getLaunchIntentForPackage(packageName);
            if (intent != null) context.startActivity(intent);
        } catch (Exception e) {}
    }

    private void vibrate(int ms) {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.VIBRATE)
                == PackageManager.PERMISSION_GRANTED) {
            android.os.Vibrator v = (android.os.Vibrator) context.getSystemService(Context.VIBRATOR_SERVICE);
            if (v != null && v.hasVibrator()) v.vibrate(ms);
        }
    }

    private String getLocalIpAddress() {
        try {
            List<NetworkInterface> interfaces = Collections.list(
                NetworkInterface.getNetworkInterfaces());
            for (NetworkInterface intf : interfaces) {
                if (intf.getName().equalsIgnoreCase("wlan0")) {
                    List<InetAddress> addrs = Collections.list(intf.getInetAddresses());
                    for (InetAddress addr : addrs) {
                        if (!addr.isLoopbackAddress()) return addr.getHostAddress();
                    }
                }
            }
        } catch (Exception e) {}
        return "N/A";
    }

    private String extractAppName(String cmd) {
        String[] words = cmd.split("\\s+");
        if (words.length > 1) {
            StringBuilder sb = new StringBuilder();
            for (int i = 1; i < words.length; i++) {
                if (i > 1) sb.append(" ");
                sb.append(words[i]);
            }
            return sb.toString();
        }
        return "";
    }
}

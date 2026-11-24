"""Behavior checks for the SystemUI lifecycle patch without a device."""

import hashlib
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


_SOURCE_SHA256 = "35f68e33741a33f7ad59cee9b47995f03423ad43aca47287b2dca2b376e85fc4"
_STATUS_BAR = Path(
    "packages/SystemUI/src/com/android/systemui/statusbar/phone/"
    "StatusBarKeyguardViewManager.java"
)

# Minimal patch context from AOSP r34, licensed under Apache-2.0.
_PREIMAGE = """import android.view.View;
import android.view.ViewGroup;
import android.view.ViewRootImpl;
import android.view.WindowManagerGlobal;

import androidx.annotation.NonNull;

    @Override
    public void onStartedWakingUp() {
        mStatusBar.getNotificationShadeWindowView().getWindowInsetsController()
                .setAnimationsDisabled(false);
    }

    @Override
    public void onStartedGoingToSleep() {
        mStatusBar.getNotificationShadeWindowView().getWindowInsetsController()
                .setAnimationsDisabled(true);
    }

    @Override
    public void onFinishedGoingToSleep() {
        mBouncer.onScreenTurnedOff();
    }

    @Override
"""

_JAVA_HARNESS = """interface Lifecycle {
    void onStartedWakingUp();
    void onStartedGoingToSleep();
    void onFinishedGoingToSleep();
}

public class LifecycleCheck implements Lifecycle {
    private static final class WindowInsetsController {
        boolean disabled;
        int updates;

        void setAnimationsDisabled(boolean value) {
            disabled = value;
            updates++;
        }
    }

    private static final class NotificationShadeWindowView {
        WindowInsetsController controller;
        WindowInsetsController getWindowInsetsController() {
            return controller;
        }
    }

    private static final class StatusBar {
        NotificationShadeWindowView shade;
        NotificationShadeWindowView getNotificationShadeWindowView() {
            return shade;
        }
    }

    private static final class Bouncer {
        int turnedOff;
        void onScreenTurnedOff() {
            turnedOff++;
        }
    }

    private StatusBar mStatusBar;
    private Bouncer mBouncer;

    private void transition() {
        onStartedGoingToSleep();
        onFinishedGoingToSleep();
        onStartedWakingUp();
    }

    public static void main(String[] args) {
        var check = new LifecycleCheck();
        check.transition();
        check.mStatusBar = new StatusBar();
        check.transition();
        check.mStatusBar.shade = new NotificationShadeWindowView();
        check.transition();
        var controller = new WindowInsetsController();
        check.mStatusBar.shade.controller = controller;
        check.mBouncer = new Bouncer();
        check.onStartedGoingToSleep();
        if (!controller.disabled || controller.updates != 1) {
            throw new AssertionError("phone shade animations must stop on sleep");
        }
        check.onFinishedGoingToSleep();
        if (check.mBouncer.turnedOff != 1) {
            throw new AssertionError("phone bouncer must be notified after sleep");
        }
        check.onStartedWakingUp();
        if (controller.disabled || controller.updates != 2) {
            throw new AssertionError("phone shade animations must resume on wake");
        }
    }
"""


def verify_lifecycle(patch):
    original = _PREIMAGE.encode()
    if source := os.environ.get("D9W_AOSP12_STATUSBAR_SOURCE"):
        original = Path(source).read_bytes()
        if hashlib.sha256(original).hexdigest() != _SOURCE_SHA256:
            raise ValueError("SystemUI test input differs from the pinned r34 source")

    with TemporaryDirectory(prefix="d9w-systemui-") as temp:
        root = Path(temp)
        java_path = root / _STATUS_BAR
        java_path.parent.mkdir(parents=True)
        java_path.write_bytes(original)
        subprocess.run(["git", "apply", str(patch)], cwd=root, check=True)
        source = java_path.read_text(encoding="utf-8")
        start = source.index("    @Override\n    public void onStartedWakingUp()")
        finish = source.index("    public void onFinishedGoingToSleep()", start)
        end = source.index("    @Override", finish)
        java_test = root / "LifecycleCheck.java"
        java_test.write_text(_JAVA_HARNESS + source[start:end] + "}\n", encoding="utf-8")
        subprocess.run(["javac", "--release", "11", java_test.name], cwd=root, check=True)
        subprocess.run(["java", "-cp", str(root), "LifecycleCheck"], cwd=root, check=True)

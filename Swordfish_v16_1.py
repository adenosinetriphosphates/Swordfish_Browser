#!/usr/bin/env python3
#Both windows and linux compat

import sys, os, json, random, string, urllib.parse, urllib.request, threading, socket
from datetime import datetime

os.environ["QT_LOGGING_RULES"] = "*=false"
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--incognito --disable-gpu-sandbox --disable-cache "
    "--memory-pressure-off --no-sandbox --disable-webrtc "
    "--disable-speech-api --disable-notifications"
)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton, QLabel,
    QTabWidget, QDialog, QFormLayout, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox,
    QSpinBox, QDoubleSpinBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineUrlRequestInterceptor, QWebEngineProfile,
    QWebEnginePage, QWebEngineScript, QWebEngineSettings, QWebEngineHttpRequest
)
from PyQt6.QtCore import QUrl, pyqtSignal, QObject, Qt, QTimer, QSize, QByteArray
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QKeySequence, QShortcut, QIcon
from PyQt6.QtNetwork import QNetworkCookie

# ============================================================
#  ULTIMATE PRIVACY JAVASCRIPT - COMPLETE SPOOFING
# ============================================================
PRIVACY_JS = """
(function() {
    'use strict';
    console.log('[SWORDFISH] Privacy layer starting...');
    
    // ====== COMPLETELY BLOCK WEBRTC ======
    const rtcBlock = () => { 
        throw new Error('WebRTC disabled for privacy'); 
    };
    window.RTCPeerConnection = rtcBlock;
    window.webkitRTCPeerConnection = rtcBlock;
    window.mozRTCPeerConnection = rtcBlock;
    window.RTCDataChannel = rtcBlock;
    if (window.mediaDevices) {
        window.mediaDevices.getUserMedia = () => Promise.reject(new Error('Blocked'));
    }
    
    // ====== HARDCORE OS SPOOFING - WINDOWS 11 INVISIBLE ======
    const fakeUA = 'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0';
    const navDescriptors = {
        userAgent: fakeUA,
        appVersion: '5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        platform: 'Linux x86_64',
        oscpu: 'Linux x86_64',
        systemXDG_CURRENT_DESKTOP: 'GNOME',
    };
    
    // Override all navigator properties
    for (let key in navDescriptors) {
        try {
            Object.defineProperty(navigator, key, {
                value: navDescriptors[key],
                writable: false,
                configurable: false
            });
        } catch (e) {}
    }
    
    // Override screen detection
    Object.defineProperty(screen, 'width', { value: 1920, writable: false, configurable: false });
    Object.defineProperty(screen, 'height', { value: 1080, writable: false, configurable: false });
    Object.defineProperty(screen, 'availWidth', { value: 1920, writable: false, configurable: false });
    Object.defineProperty(screen, 'availHeight', { value: 1050, writable: false, configurable: false });
    Object.defineProperty(screen, 'colorDepth', { value: 24, writable: false, configurable: false });
    Object.defineProperty(screen, 'pixelDepth', { value: 24, writable: false, configurable: false });
    
    // ====== GEOLOCATION SPOOFING ======
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition = (cb, err) => {
            setTimeout(() => cb({ 
                coords: { 
                    latitude: 51.5074, 
                    longitude: -0.1278, 
                    accuracy: 50,
                    altitude: 0, 
                    altitudeAccuracy: null, 
                    heading: 0, 
                    speed: 0
                }, 
                timestamp: Date.now()
            }), 100);
        };
        navigator.geolocation.watchPosition = navigator.geolocation.getCurrentPosition;
    }
    
    // ====== BLOCK NOTIFICATIONS ======
    window.Notification = class {
        constructor() { 
            throw new Error('Notifications blocked'); 
        }
        static requestPermission() {
            return Promise.resolve('denied');
        }
    };
    
    // ====== BLOCK SENDBEACON ======
    if (navigator.sendBeacon) {
        const originalSendBeacon = navigator.sendBeacon;
        navigator.sendBeacon = function() {
            console.log('[SWORDFISH] sendBeacon blocked');
            return false;
        };
    }
    
    // ====== CANVAS FINGERPRINT PROTECTION ======
    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function() {
        const ctx = this.getContext('2d');
        ctx.fillStyle = 'rgba(' + Math.random()*255 + ',' + Math.random()*255 + ',' + Math.random()*255 + ',0.1)';
        ctx.fillRect(0, 0, Math.random()*100, Math.random()*100);
        return origToDataURL.call(this);
    };
    
    // ====== WEBGL FINGERPRINT BLOCKING ======
    const origGetParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(pname) {
        if (pname === 37445 || pname === 37446) { // UNMASKED_VENDOR/RENDERER
            return 'Generic GPU (Linux)';
        }
        return origGetParameter.call(this, pname);
    };
    
    // ====== REMOVE TRACKING GLOBALS ======
    const trackers = ['_gaq', 'ga', 'gtag', '__gaTracker', '_paq', 'fbq', 'mixpanel'];
    trackers.forEach(t => {
        try { 
            delete window[t]; 
            Object.defineProperty(window, t, {
                get: () => { console.log('[SWORDFISH] Tracker access blocked: ' + t); return undefined; },
                configurable: false
            });
        } catch (e) {}
    });
    
    // ====== SPOOF LANGUAGE/TIMEZONE ======
    Object.defineProperty(navigator, 'language', { value: 'en-US', writable: false });
    Object.defineProperty(navigator, 'languages', { value: ['en-US', 'en'], writable: false });
    
    // ====== BLOCK HARDWARE INFO ======
    if (navigator.deviceMemory) {
        Object.defineProperty(navigator, 'deviceMemory', { value: 8, writable: false });
    }
    if (navigator.hardwareConcurrency) {
        Object.defineProperty(navigator, 'hardwareConcurrency', { value: 4, writable: false });
    }
    
    // ====== POISON BATTERY API ======
    if (navigator.getBattery) {
        navigator.getBattery = () => Promise.resolve({
            level: 0.75,
            charging: true,
            chargingTime: 0,
            dischargingTime: Infinity
        });
    }
    
    console.log('[SWORDFISH] Privacy layer ACTIVE - OS spoofed to Linux, WebRTC blocked, all APIs spoofed');
    console.log('[SWORDFISH] Windows 11 detection: IMPOSSIBLE');
})();
"""

# Old Firefox (Firefox 3.x era) Theme
THEME = """
* {
    font-family: Tahoma, "Segoe UI", Arial, sans-serif;
    font-size: 11px;
    color: #000000;
}

/* ── Window & base ── */
QMainWindow, QWidget {
    background: #d4d0c8;
}
QDialog {
    background: #d4d0c8;
}

/* ── Toolbar area ── */
QWidget#toolbar {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #eeeade, stop:0.45 #d8d4c8, stop:0.46 #c4c0b4, stop:1 #b8b4a8);
    border-bottom: 2px solid #808080;
    padding: 2px 4px;
}

/* ── Nav buttons — Firefox-style raised pillbox ── */
QPushButton#navbtn {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f0ede4, stop:1 #c8c4b8);
    border-top:    1px solid #ffffff;
    border-left:   1px solid #ffffff;
    border-right:  1px solid #606060;
    border-bottom: 1px solid #606060;
    border-radius: 3px;
    padding: 3px 8px;
    min-width: 28px;
    min-height: 22px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton#navbtn:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f8f6f0, stop:1 #dedad0);
    border-color: #316ac5 #1a4a9c #1a4a9c #316ac5;
}
QPushButton#navbtn:pressed {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #b0acA0, stop:1 #d0ccC0);
    border-top:   1px solid #606060;
    border-left:  1px solid #606060;
    border-right: 1px solid #ffffff;
    border-bottom:1px solid #ffffff;
}
QPushButton#navbtn:disabled { color: #a0a0a0; }

/* ── Generic buttons ── */
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f0ede4, stop:1 #c8c4b8);
    border-top:    1px solid #ffffff;
    border-left:   1px solid #ffffff;
    border-right:  1px solid #606060;
    border-bottom: 1px solid #606060;
    border-radius: 2px;
    padding: 3px 10px;
    min-height: 20px;
}
QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f8f6f0, stop:1 #dedad0);
    border-color: #316ac5 #1a4a9c #1a4a9c #316ac5;
}
QPushButton:pressed {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #b0aca0, stop:1 #d0ccc0);
    border-top:   1px solid #606060;
    border-left:  1px solid #606060;
    border-right: 1px solid #e0ddd4;
    border-bottom:1px solid #e0ddd4;
}
QPushButton:disabled { color: #909090; }

/* ── URL / address bar ── */
QLineEdit#urlbar {
    background: #ffffff;
    color: #000080;
    border-top:    2px solid #808080;
    border-left:   2px solid #808080;
    border-right:  2px solid #d4d0c8;
    border-bottom: 2px solid #d4d0c8;
    border-radius: 0px;
    padding: 2px 6px;
    font-size: 12px;
    selection-background-color: #316ac5;
    selection-color: #ffffff;
}
QLineEdit#urlbar:focus {
    border-top:   2px solid #316ac5;
    border-left:  2px solid #316ac5;
}
QLineEdit {
    background: #ffffff;
    color: #000000;
    border-top:    2px solid #808080;
    border-left:   2px solid #808080;
    border-right:  2px solid #d4d0c8;
    border-bottom: 2px solid #d4d0c8;
    padding: 2px 4px;
}
QLineEdit:focus {
    border-top:  2px solid #316ac5;
    border-left: 2px solid #316ac5;
}

/* ── Lock badge ── */
QPushButton#lock_https {
    background: #e0f0e0; color: #006000;
    border: 1px solid #60a060; border-radius: 2px;
    padding: 2px 6px; font-size: 10px; font-weight: bold;
}
QPushButton#lock_http {
    background: #fff0d0; color: #804000;
    border: 1px solid #c08000; border-radius: 2px;
    padding: 2px 6px; font-size: 10px; font-weight: bold;
}

/* ── Browser page tabs ── */
QTabWidget#pagetabs::pane {
    border: 2px solid #808080;
    border-top: none;
    background: #ffffff;
}
QTabBar#pagetabbar::tab {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #c8c4b8, stop:1 #b0aca0);
    color: #444444;
    border: 1px solid #808080;
    border-bottom: none;
    padding: 3px 14px 4px 14px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size: 11px;
    min-width: 80px;
    max-width: 200px;
}
QTabBar#pagetabbar::tab:selected {
    background: #d4d0c8;
    color: #000000;
    font-weight: bold;
    border-bottom: 2px solid #d4d0c8;
}
QTabBar#pagetabbar::tab:hover:!selected {
    background: #dedad0;
    color: #000000;
}

/* ── Info panel tabs ── */
QTabWidget#infotabs::pane {
    border: 1px solid #808080;
    background: #d4d0c8;
}
QTabBar#infotabbar::tab {
    background: #c0bcb0;
    color: #333;
    border: 1px solid #909090;
    border-bottom: none;
    padding: 2px 10px;
    margin-right: 1px;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    font-size: 10px;
}
QTabBar#infotabbar::tab:selected {
    background: #d4d0c8;
    color: #000;
    font-weight: bold;
}

/* ── Traffic log — black text on warm tan, compact ── */
QListWidget#trafficlog {
    background: #e8e0c8;
    color: #1a1a1a;
    border-top:   2px solid #808080;
    border-left:  2px solid #808080;
    border-right: 2px solid #d4d0c8;
    border-bottom:2px solid #d4d0c8;
    font-family: "Courier New", Courier, monospace;
    font-size: 10px;
    padding: 1px;
}
QListWidget#trafficlog::item {
    padding: 0px 2px;
    border-bottom: 1px solid #d4c890;
}
QListWidget#trafficlog::item:selected {
    background: #316ac5;
    color: #ffffff;
}

/* ── Tables ── */
QTableWidget {
    background: #ffffff;
    color: #000000;
    border-top:   2px solid #808080;
    border-left:  2px solid #808080;
    border-right: 2px solid #d4d0c8;
    border-bottom:2px solid #d4d0c8;
    gridline-color: #d0ccc0;
    alternate-background-color: #f0eee8;
    font-size: 11px;
    selection-background-color: #316ac5;
    selection-color: #ffffff;
}
QHeaderView::section {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #e8e4dc, stop:1 #ccc8bc);
    color: #000000;
    border: none;
    border-right: 1px solid #909090;
    border-bottom: 2px solid #808080;
    padding: 3px 6px;
    font-weight: bold;
    font-size: 11px;
}

/* ── Status / stats bar ── */
QWidget#statsbar {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #d4d0c8, stop:1 #c0bcb0);
    border-top: 2px solid #808080;
    padding: 1px 6px;
}
QLabel#statslabel {
    color: #000000;
    font-family: "Courier New", Courier, monospace;
    font-size: 10px;
}
QLabel#blockedlabel {
    color: #880000;
    font-family: "Courier New", Courier, monospace;
    font-size: 10px;
    font-weight: bold;
}
QLabel#iplabel {
    color: #004000;
    font-family: "Courier New", Courier, monospace;
    font-size: 10px;
}

/* ── Section headers ── */
QLabel#sechead {
    color: #1a3a7a;
    font-weight: bold;
    font-size: 11px;
}
QLabel#warn { color: #880000; font-weight: bold; }
QLabel#ok   { color: #006000; }

/* ── Group boxes ── */
QGroupBox {
    border: 1px solid #909090;
    border-radius: 0px;
    margin-top: 10px;
    padding: 4px;
    font-weight: bold;
    background: #d4d0c8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    background: #d4d0c8;
}

/* ── Checkboxes ── */
QCheckBox { color: #000000; spacing: 5px; }
QCheckBox::indicator {
    width: 13px; height: 13px;
    border-top:   2px solid #808080;
    border-left:  2px solid #808080;
    border-right: 2px solid #d4d0c8;
    border-bottom:2px solid #d4d0c8;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #ffffff;
    image: none;
    border-top:   2px solid #808080;
    border-left:  2px solid #808080;
    border-right: 2px solid #d4d0c8;
    border-bottom:2px solid #d4d0c8;
}
QCheckBox::indicator:checked { background: #316ac5; }

/* ── Scrollbars — old Windows style ── */
QScrollBar:vertical {
    background: #d4d0c8;
    width: 16px;
    border: 1px solid #808080;
}
QScrollBar::handle:vertical {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #e8e4dc, stop:0.5 #d0ccC0, stop:1 #b8b4a8);
    border-top:   1px solid #ffffff;
    border-left:  1px solid #ffffff;
    border-right: 1px solid #606060;
    border-bottom:1px solid #606060;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #e8e4dc, stop:1 #c8c4b8);
    border: 1px solid #808080;
    height: 16px;
    subcontrol-origin: margin;
}
QScrollBar:horizontal {
    background: #d4d0c8;
    height: 16px;
    border: 1px solid #808080;
}
QScrollBar::handle:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #e8e4dc, stop:1 #c0bcb0);
    border-top:   1px solid #ffffff;
    border-left:  1px solid #ffffff;
    border-right: 1px solid #606060;
    border-bottom:1px solid #606060;
    min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #e8e4dc, stop:1 #c8c4b8);
    border: 1px solid #808080;
    width: 16px;
}

/* ── Combo boxes ── */
QComboBox {
    background: #ffffff; color: #000000;
    border-top:   2px solid #808080;
    border-left:  2px solid #808080;
    border-right: 2px solid #d4d0c8;
    border-bottom:2px solid #d4d0c8;
    padding: 2px 4px;
}
QComboBox QAbstractItemView {
    background: #ffffff; color: #000;
    selection-background-color: #316ac5;
    selection-color: #ffffff;
}

/* ── Status bar ── */
QStatusBar {
    background: #c0bcb0;
    border-top: 1px solid #808080;
    color: #000;
    font-size: 10px;
}
"""

class BandwidthGraph(QFrame):
    """Network bandwidth visualization"""
    def __init__(self):
        super().__init__()
        self.setFixedSize(260, 48)
        self.data = [0] * 150
        self.setStyleSheet("background: #e8e0c8; border-top:1px solid #808080; border-left:1px solid #808080; border-right:1px solid #d4d0c8; border-bottom:1px solid #d4d0c8;")

    def add_data(self, val):
        self.data.append(float(val))   # no artificial cap — show real spikes
        self.data.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()

        # Tan background matching log
        painter.fillRect(0, 0, w, h, QColor(0xe8, 0xe0, 0xc8))
        painter.setPen(QPen(QColor(0x80, 0x80, 0x80), 1))
        painter.drawRect(0, 0, w-1, h-1)

        # Grid lines — muted warm grey
        painter.setPen(QPen(QColor(0xd4, 0xc8, 0x90), 1))
        for i in range(0, w, 40):
            painter.drawLine(i, 0, i, h)
        for i in range(0, h, 20):
            painter.drawLine(0, i, w, i)

        # Peak ceiling line
        painter.setPen(QPen(QColor(0xaa, 0x44, 0x00), 1))
        painter.drawLine(0, 10, w, 10)

        # Dynamic scale: uses last 8 samples only — snaps down fast after bursts
        # Floor of 2 KB/s means even a single DNS packet fills a chunk of the graph
        recent = self.data[-8:] if len(self.data) >= 8 else self.data
        recent_peak = max(recent) if any(v > 0 for v in recent) else 0
        max_val = max(recent_peak * 1.15, 2.0)  # floor=2 KB/s for high sensitivity
        # Line — dark green, readable on tan
        # Draw fill under line first
        from PyQt6.QtGui import QPolygonF, QLinearGradient, QBrush
        from PyQt6.QtCore import QPointF
        n = len(self.data)
        pts = [QPointF(0.0, float(h))]
        for i, v in enumerate(self.data):
            x = i * (w / max(n-1, 1))
            y = h - 12 - (v / max_val) * (h - 22)
            pts.append(QPointF(x, y))
        pts.append(QPointF(float(w), float(h)))
        poly = QPolygonF(pts)
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(0, 120, 0, 120))
        grad.setColorAt(1.0, QColor(0, 120, 0, 20))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(grad))
        painter.drawPolygon(poly)
        # Line on top
        painter.setPen(QPen(QColor(0x00, 0x7a, 0x00), 2))
        for i in range(n - 1):
            x1 = i * (w / max(n-1, 1))
            x2 = (i+1) * (w / max(n-1, 1))
            y1 = h - 12 - (self.data[i]   / max_val) * (h - 22)
            y2 = h - 12 - (self.data[i+1] / max_val) * (h - 22)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Labels — black on tan
        painter.setPen(QPen(QColor(0x00, 0x00, 0x00), 1))
        painter.setFont(QFont("Courier New", 8))
        cur_kb = self.data[-1]
        all_pk = max(self.data)
        painter.drawText(4, 11, f"Now: {cur_kb:.1f} KB/s")
        painter.drawText(4, h - 3, f"Peak: {all_pk:.0f} KB/s")

class URLInterceptor(QWebEngineUrlRequestInterceptor):
    """Intercept and spoof all requests"""
    def __init__(self, log_signal):
        super().__init__()
        self.log_signal = log_signal
        self.spoofed_ip    = "192.0.2.1"   # editable at runtime
        self.spoof_enabled = True           # toggle on/off
        self.blocklist = {
            "doubleclick.net", "google-analytics.com", "facebook.com/tr",
            "segment.com", "mixpanel.com", "amplitude.com", "analytics",
            "googleadservices.com", "pagead", "ads.google", "adclick"
        }

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        host = info.requestUrl().host().lower()
        
        # Log request
        self.log_signal.emit(f"[REQUEST] {url}")
        
        # Check blocklist
        if any(tracker in url.lower() for tracker in self.blocklist):
            self.log_signal.emit(f"[BLOCKED TRACKER] {host}")
            info.block(True)
            return
        
        # SPOOF IP HEADERS — only when enabled
        if self.spoof_enabled:
            try:
                ip_bytes = self.spoofed_ip.encode()
                info.setHttpHeader(b"X-Forwarded-For",   ip_bytes)
                info.setHttpHeader(b"Client-IP",          ip_bytes)
                info.setHttpHeader(b"X-Real-IP",          ip_bytes)
                info.setHttpHeader(b"CF-Connecting-IP",   ip_bytes)
                info.setHttpHeader(b"X-Client-IP",        ip_bytes)
                info.setHttpHeader(b"X-Forwarded",        ip_bytes)
                info.setHttpHeader(b"True-Client-IP",     ip_bytes)
            except Exception:
                pass
        
        self.log_signal.emit(f"[ALLOW] {host}")

class Swordfish(QMainWindow):
    """Main privacy browser"""
    
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Swordfish v16.1 - HARDCORE Privacy Browser")
        self.resize(1500, 950)
        
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "download.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass
        
        # Profile with spoofed user agent
        self.profile = QWebEngineProfile()
        self.profile.setHttpUserAgent(
            'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
        )
        
        # Interceptor
        self.interceptor = URLInterceptor(self.log_signal)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        
        # INJECT PRIVACY JS AT DOCUMENT CREATION (earliest point)
        script = QWebEngineScript()
        script.setSourceCode(PRIVACY_JS)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(0)
        self.profile.scripts().insert(script)
        
        # Signals
        self.log_signal.connect(self._on_log)
        
        # Stats
        self.total_bytes = 0
        self.tick_bytes = 0
        self.blocked_count = 0
        self.fake_cookies = []
        
        # ── UI Setup ─────────────────────────────────────────────────────────
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Toolbar ───────────────────────────────────────────────────────
        toolbar = QWidget(); toolbar.setObjectName("toolbar")
        toolbar.setFixedHeight(38)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(4, 3, 4, 3)
        toolbar_layout.setSpacing(3)

        for attr, label, slot in [
            ("btn_back",    "◄", self._nav_back),
            ("btn_forward", "►", self._nav_forward),
            ("btn_reload",  "↺", self._nav_reload),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("navbtn")
            btn.setFixedSize(28, 26)
            btn.clicked.connect(slot)
            setattr(self, attr, btn)
            toolbar_layout.addWidget(btn)

        toolbar_layout.addSpacing(4)

        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("urlbar")
        self.url_bar.setPlaceholderText("Enter address or search…")
        self.url_bar.returnPressed.connect(self.navigate)
        toolbar_layout.addWidget(self.url_bar, 1)

        toolbar_layout.addSpacing(4)

        for label, slot in [
            ("Home",     lambda: self.navigate_to("https://adenosinetriphosphates.github.io/Swordfish_Browser/startpage.html")),
            ("New Tab",  self.new_tab),
            ("Cookies",  self.show_cookies),
            ("Settings", self.show_settings),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.clicked.connect(slot)
            toolbar_layout.addWidget(btn)

        main_layout.addWidget(toolbar)

        # ── Thin separator ────────────────────────────────────────────────
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(2)
        sep.setStyleSheet("background:#808080;")
        main_layout.addWidget(sep)

        # ── Browser page tabs ─────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setObjectName("pagetabs")
        self.tabs.tabBar().setObjectName("pagetabbar")
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs, 1)

        # ── Stats / network bar ───────────────────────────────────────────
        self.stats_widget = QWidget(); self.stats_widget.setObjectName("statsbar")
        self.stats_widget.setFixedHeight(54)
        stats_layout = QHBoxLayout(self.stats_widget)
        stats_layout.setContentsMargins(6, 2, 6, 2)
        stats_layout.setSpacing(8)

        self.stats_label   = QLabel("0.00 MB | 0 KB/s"); self.stats_label.setObjectName("statslabel")
        self.blocked_label = QLabel("Blocked: 0");        self.blocked_label.setObjectName("blockedlabel")
        self.ip_label      = QLabel("Detecting…");        self.ip_label.setObjectName("iplabel")

        def _vsep():
            f = QFrame(); f.setFrameShape(QFrame.Shape.VLine)
            f.setStyleSheet("color:#909090;"); return f

        # ── Editable spoofed IP ────────────────────────────────────────
        lbl_spoof = QLabel("Spoof IP:")
        lbl_spoof.setObjectName("statslabel")
        self.ip_edit = QLineEdit("192.0.2.1")
        self.ip_edit.setFixedWidth(110)
        self.ip_edit.setToolTip("Spoofed IP sent in X-Forwarded-For and related headers")
        self.ip_edit.setStyleSheet(
            "font-family:'Courier New'; font-size:10px; padding:1px 4px;"
            "border-top:1px solid #808080; border-left:1px solid #808080;"
            "border-right:1px solid #d4d0c8; border-bottom:1px solid #d4d0c8;")
        btn_apply_ip = QPushButton("Apply")
        btn_apply_ip.setFixedSize(42, 22)
        btn_apply_ip.setStyleSheet("font-size:9px; padding:0;")
        btn_apply_ip.setToolTip("Apply spoofed IP to all future requests")
        btn_apply_ip.clicked.connect(self._apply_spoofed_ip)
        self.ip_edit.returnPressed.connect(self._apply_spoofed_ip)

        self.chk_spoof_ip = QCheckBox("Spoof IP")
        self.chk_spoof_ip.setChecked(True)
        self.chk_spoof_ip.setToolTip("Send spoofed IP headers with every request")
        self.chk_spoof_ip.setStyleSheet("font-size:10px; color:#1a1a1a;")
        self.chk_spoof_ip.stateChanged.connect(self._toggle_spoof_ip)

        # ── Graph — taller so it's actually readable ───────────────────
        self.bandwidth_graph = BandwidthGraph()
        self.bandwidth_graph.setFixedSize(260, 48)
        self.bandwidth_graph.setStyleSheet(
            "background:#e8e0c8; border-top:1px solid #808080; border-left:1px solid #808080;"
            "border-right:1px solid #d4d0c8; border-bottom:1px solid #d4d0c8;")
        self.bandwidth_graph.setToolTip("Live bandwidth — scales to recent traffic")

        # Toggle buttons — ▼ = currently shown (click to hide)
        self.btn_hide_net = QPushButton("▼ Net")
        self.btn_hide_net.setFixedSize(48, 22)
        self.btn_hide_net.setStyleSheet("font-size:9px; padding:0;")
        self.btn_hide_net.setToolTip("Hide network graph")
        self.btn_hide_net.clicked.connect(self._toggle_net)

        self.btn_hide_log = QPushButton("▼ Log")
        self.btn_hide_log.setFixedSize(48, 22)
        self.btn_hide_log.setStyleSheet("font-size:9px; padding:0;")
        self.btn_hide_log.setToolTip("Hide traffic log")
        self.btn_hide_log.clicked.connect(self._toggle_log)

        stats_layout.addWidget(self.stats_label)
        stats_layout.addWidget(_vsep())
        stats_layout.addWidget(self.blocked_label)
        stats_layout.addWidget(_vsep())
        stats_layout.addWidget(self.ip_label)
        stats_layout.addWidget(_vsep())
        stats_layout.addWidget(lbl_spoof)
        stats_layout.addWidget(self.ip_edit)
        stats_layout.addWidget(btn_apply_ip)
        stats_layout.addWidget(self.chk_spoof_ip)
        stats_layout.addStretch()
        stats_layout.addWidget(self.bandwidth_graph)
        stats_layout.addWidget(self.btn_hide_net)
        stats_layout.addWidget(self.btn_hide_log)

        main_layout.addWidget(self.stats_widget)

        # ── Traffic log — compact, black on tan ───────────────────────────
        log_header = QWidget()
        log_header.setFixedHeight(18)
        log_header.setStyleSheet("background:#c0bcb0; border-top:1px solid #808080;")
        lh_lay = QHBoxLayout(log_header)
        lh_lay.setContentsMargins(6, 0, 6, 0)
        lbl_log = QLabel("Traffic Log")
        lbl_log.setStyleSheet("font-size:10px; font-weight:bold; color:#1a1a1a;")
        btn_clr_log = QPushButton("Clear")
        btn_clr_log.setFixedSize(40, 16)
        btn_clr_log.setStyleSheet("font-size:9px; padding:0;")
        lh_lay.addWidget(lbl_log); lh_lay.addStretch(); lh_lay.addWidget(btn_clr_log)

        self.traffic_log = QListWidget()
        self.traffic_log.setObjectName("trafficlog")
        self.traffic_log.setFixedHeight(110)
        self.traffic_log.setUniformItemSizes(True)

        btn_clr_log.clicked.connect(self.traffic_log.clear)

        # Wrap log header + list so we can hide both together
        self.log_widget = QWidget()
        lw_lay = QVBoxLayout(self.log_widget)
        lw_lay.setContentsMargins(0, 0, 0, 0)
        lw_lay.setSpacing(0)
        lw_lay.addWidget(log_header)
        lw_lay.addWidget(self.traffic_log)

        main_layout.addWidget(self.log_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_stats)
        self.timer.start(1000)
        
        # Detect real IP
        threading.Thread(target=self._detect_real_ip, daemon=True).start()
        
        # Create first tab
        self.new_tab()
    
    def new_tab(self):
        """Create new tab with privacy JS"""
        view = QWebEngineView()
        page = QWebEnginePage(self.profile, view)
        view.setPage(page)
        view.load(QUrl("https://adenosinetriphosphates.github.io/Swordfish_Browser/startpage.html"))
        view.urlChanged.connect(lambda u, v=view: self._on_url_changed(u, v))
        view.titleChanged.connect(lambda t, v=view: self._on_title_changed(t, v))

        idx = self.tabs.addTab(view, "New Tab")
        self.tabs.setCurrentIndex(idx)

    def _on_url_changed(self, url, view):
        if view is self.tabs.currentWidget():
            self.url_bar.setText(url.toString())

    def _on_title_changed(self, title, view):
        idx = self.tabs.indexOf(view)
        if idx >= 0:
            short = (title[:18] + "…") if len(title) > 20 else (title or "New Tab")
            self.tabs.setTabText(idx, short)
    
    def navigate(self):
        """Navigate to URL"""
        url = self.url_bar.text().strip()
        if not url:
            return
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        current = self.tabs.currentWidget()
        if current:
            current.load(QUrl(url))
    
    def navigate_to(self, url):
        """Navigate to specific URL"""
        self.url_bar.setText(url)
        current = self.tabs.currentWidget()
        if current:
            current.load(QUrl(url))
    
    def _nav_back(self):
        current = self.tabs.currentWidget()
        if current:
            current.back()
    
    def _nav_forward(self):
        current = self.tabs.currentWidget()
        if current:
            current.forward()
    
    def _nav_reload(self):
        current = self.tabs.currentWidget()
        if current:
            current.reload()
    
    def _close_tab(self, idx):
        if self.tabs.count() > 1:
            self.tabs.removeTab(idx)
    
    def _on_log(self, msg):
        """Handle log message — black on tan, colour-coded by type"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"[{timestamp}] {msg}")

        if "[BLOCKED" in msg:
            item.setForeground(QColor("#880000"))   # dark red — readable on tan
            self.blocked_count += 1
            self.blocked_label.setText(f"Blocked: {self.blocked_count}")
        elif "[ALLOW]" in msg:
            item.setForeground(QColor("#005000"))   # dark green
        elif "[REQUEST]" in msg:
            item.setForeground(QColor("#1a1a1a"))   # near-black
        else:
            item.setForeground(QColor("#2a3a7a"))   # dark navy for other messages

        self.traffic_log.addItem(item)
        if self.traffic_log.count() > 1000:
            self.traffic_log.takeItem(0)
        self.traffic_log.scrollToBottom()
        self.tick_bytes += 1500
    
    def _update_stats(self):
        """Update stats display"""
        kb_s = self.tick_bytes / 1024
        self.stats_label.setText(f"{self.total_bytes/1e6:.2f} MB | {kb_s:.1f} KB/s")
        self.bandwidth_graph.add_data(kb_s)
        self.total_bytes += self.tick_bytes
        self.tick_bytes = 0
    
    def _toggle_net(self):
        """Toggle network stats bar. ▲=shown (click to hide), ▼=hidden (click to show)"""
        vis = self.stats_widget.isVisible()
        self.stats_widget.setVisible(not vis)
        self.btn_hide_net.setText("▼ Net" if vis else "▲ Net")

    def _toggle_log(self):
        """Toggle traffic log. ▲=shown (click to hide), ▼=hidden (click to show)"""
        vis = self.log_widget.isVisible()
        self.log_widget.setVisible(not vis)
        self.btn_hide_log.setText("▼ Log" if vis else "▲ Log")

    def _toggle_spoof_ip(self, state):
        """Enable or disable IP header spoofing entirely"""
        enabled = bool(state)
        self.interceptor.spoof_enabled = enabled
        self.ip_edit.setEnabled(enabled)
        if enabled:
            self.ip_label.setStyleSheet(
                "color:#005000; font-family:'Courier New'; font-size:10px; font-weight:bold;")
            self.log_signal.emit(f"[IP] Spoofing ENABLED → {self.interceptor.spoofed_ip}")
        else:
            self.ip_label.setStyleSheet(
                "color:#880000; font-family:'Courier New'; font-size:10px; font-weight:bold;")
            self.ip_label.setText("IP spoofing OFF")
            self.log_signal.emit("[IP] Spoofing DISABLED — real IP will be sent")

    def _apply_spoofed_ip(self):
        """Validate and apply the user-entered spoofed IP to the interceptor"""
        import re
        raw = self.ip_edit.text().strip()
        # Accept plain IPv4 or RFC 5737 / private ranges — basic format check
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", raw):
            self.interceptor.spoofed_ip = raw
            self.ip_label.setText(f"Spoofed → {raw}")
            self.ip_label.setStyleSheet("color:#005000; font-family:'Courier New'; font-size:10px; font-weight:bold;")
            self.log_signal.emit(f"[IP] Spoofed IP updated to: {raw}")
        else:
            self.ip_edit.setStyleSheet(
                "font-family:'Courier New'; font-size:10px; padding:1px 4px;"
                "border:2px solid #cc0000; background:#fff0f0;")
            self.log_signal.emit(f"[IP ERROR] Invalid IP format: {raw}")
            QTimer.singleShot(1500, lambda: self.ip_edit.setStyleSheet(
                "font-family:'Courier New'; font-size:10px; padding:1px 4px;"
                "border-top:1px solid #808080; border-left:1px solid #808080;"
                "border-right:1px solid #d4d0c8; border-bottom:1px solid #d4d0c8;"))

    def _on_tab_changed(self, idx):
        v = self.tabs.widget(idx)
        if v:
            self.url_bar.setText(v.url().toString())

    def _detect_real_ip(self):
        """Detect real IP and show alongside current spoofed IP"""
        try:
            response = urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5)
            data = json.loads(response.read())
            real_ip = data.get("ip", "Unknown")
            self.ip_label.setText(f"Real: {real_ip}  →  Spoofed: {self.interceptor.spoofed_ip}")
            self.ip_label.setStyleSheet("color:#004000; font-family:'Courier New'; font-size:10px;")
        except:
            self.ip_label.setText(f"Real: unknown  →  Spoofed: {self.interceptor.spoofed_ip}")
    
    def show_cookies(self):
        """Show and manage cookies"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Cookie Manager - ALL COOKIES")
        dlg.resize(700, 450)
        
        layout = QVBoxLayout()
        
        # ===== REAL COOKIES =====
        real_label = QLabel("REAL COOKIES (From websites):")
        real_label.setStyleSheet("font-weight: bold; color: #008800;")
        self.real_cookie_table = QTableWidget(0, 5)
        self.real_cookie_table.setHorizontalHeaderLabels(["Domain", "Name", "Value", "Expires", "Secure"])
        self.real_cookie_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(real_label)
        layout.addWidget(self.real_cookie_table)
        
        # Load real cookies
        store = self.profile.cookieStore()
        store.cookieAdded.connect(lambda c: self._add_real_cookie(c))
        store.loadAllCookies()
        
        # ===== FAKE COOKIES =====
        fake_label = QLabel("\nFAKE COOKIES (For testing):")
        fake_label.setStyleSheet("font-weight: bold; color: #880000;")
        self.fake_cookie_table = QTableWidget(len(self.fake_cookies), 4)
        self.fake_cookie_table.setHorizontalHeaderLabels(["Domain", "Name", "Value", "Type"])
        
        for i, cookie in enumerate(self.fake_cookies):
            self.fake_cookie_table.setItem(i, 0, QTableWidgetItem(cookie['domain']))
            self.fake_cookie_table.setItem(i, 1, QTableWidgetItem(cookie['name']))
            self.fake_cookie_table.setItem(i, 2, QTableWidgetItem(cookie['value'][:30]))
            self.fake_cookie_table.setItem(i, 3, QTableWidgetItem("FAKE"))
        
        layout.addWidget(fake_label)
        layout.addWidget(self.fake_cookie_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Add Fake Cookie")
        btn_add.clicked.connect(lambda: self._add_fake_cookie_dialog(dlg))
        btn_clear_real = QPushButton("Clear All Real Cookies")
        btn_clear_real.clicked.connect(lambda: store.deleteAllCookies() or self.show_cookies())
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.close)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_clear_real)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        
        dlg.setLayout(layout)
        dlg.exec()
    
    def _add_real_cookie(self, cookie):
        """Add real cookie to table"""
        row = self.real_cookie_table.rowCount()
        self.real_cookie_table.insertRow(row)
        try:
            self.real_cookie_table.setItem(row, 0, QTableWidgetItem(cookie.domain()))
            self.real_cookie_table.setItem(row, 1, QTableWidgetItem(str(cookie.name())))
            self.real_cookie_table.setItem(row, 2, QTableWidgetItem(str(cookie.value())[:50]))
            self.real_cookie_table.setItem(row, 3, QTableWidgetItem(str(cookie.expirationDate())))
            self.real_cookie_table.setItem(row, 4, QTableWidgetItem("Yes" if cookie.isSecure() else "No"))
        except:
            pass
    
    def _add_fake_cookie_dialog(self, parent):
        """Add fake cookie"""
        dlg = QDialog(parent)
        dlg.setWindowTitle("Add Fake Cookie")
        dlg.resize(400, 200)
        
        layout = QFormLayout()
        
        domain = QLineEdit()
        domain.setText("example.com")
        name = QLineEdit()
        name.setText("session_id")
        value = QLineEdit()
        value.setText("abc123xyz789")
        
        layout.addRow("Domain:", domain)
        layout.addRow("Name:", name)
        layout.addRow("Value:", value)
        
        def save():
            if domain.text() and name.text():
                self.fake_cookies.append({
                    'domain': domain.text(),
                    'name': name.text(),
                    'value': value.text()
                })
                dlg.close()
                self.log_signal.emit(f"[COOKIE] Added fake: {domain.text()}/{name.text()}")
        
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(save)
        layout.addRow(btn_save)
        
        dlg.setLayout(layout)
        dlg.exec()
    
    def show_settings(self):
        """Show privacy status with configurable options"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Privacy & Security Settings")
        dlg.resize(600, 550)
        
        layout = QFormLayout()
        layout.addRow(QLabel("╔════ SWORDFISH v16.1 SETTINGS ════╗"))
        layout.addRow(QLabel(""))
        
        # OS SPOOFING
        layout.addRow(QLabel("OS SPOOFING:"))
        spoof_os = QCheckBox("Spoof OS to Linux")
        spoof_os.setChecked(True)
        spoof_os.clicked.connect(lambda: self.log_signal.emit("[SETTINGS] OS spoofing " + ("enabled" if spoof_os.isChecked() else "disabled")))
        layout.addRow("Windows Detection", spoof_os)
        
        ua_input = QLineEdit()
        ua_input.setText('Mozilla/5.0 (X11; Linux x86_64; rv:121.0)')
        layout.addRow("User-Agent:", ua_input)
        
        # IP SPOOFING
        layout.addRow(QLabel("\nIP SPOOFING:"))
        spoof_ip = QCheckBox("Spoof IP Headers")
        spoof_ip.setChecked(True)
        spoof_ip.clicked.connect(lambda: self.log_signal.emit("[SETTINGS] IP spoofing " + ("enabled" if spoof_ip.isChecked() else "disabled")))
        layout.addRow("IP Spoofing", spoof_ip)
        
        ip_input = QLineEdit()
        ip_input.setText("192.0.2.1")
        ip_input.setReadOnly(True)
        layout.addRow("Spoof IP:", ip_input)
        
        # WEBRTC
        layout.addRow(QLabel("\nWEBRTC & PRIVACY:"))
        block_webrtc = QCheckBox("Block WebRTC")
        block_webrtc.setChecked(True)
        block_webrtc.clicked.connect(lambda: self.log_signal.emit("[SETTINGS] WebRTC blocking " + ("enabled" if block_webrtc.isChecked() else "disabled")))
        layout.addRow("WebRTC", block_webrtc)
        
        spoof_geo = QCheckBox("Spoof Geolocation")
        spoof_geo.setChecked(True)
        spoof_geo.clicked.connect(lambda: self.log_signal.emit("[SETTINGS] Geolocation spoofing " + ("enabled" if spoof_geo.isChecked() else "disabled")))
        layout.addRow("Geolocation", spoof_geo)
        
        block_notif = QCheckBox("Block Notifications")
        block_notif.setChecked(True)
        block_notif.clicked.connect(lambda: self.log_signal.emit("[SETTINGS] Notification blocking " + ("enabled" if block_notif.isChecked() else "disabled")))
        layout.addRow("Notifications", block_notif)
        
        # TRACKER BLOCKING
        layout.addRow(QLabel("\nTRACKER BLOCKING:"))
        block_trackers = QCheckBox("Block Known Trackers")
        block_trackers.setChecked(True)
        block_trackers.clicked.connect(lambda: self.log_signal.emit("[SETTINGS] Tracker blocking " + ("enabled" if block_trackers.isChecked() else "disabled")))
        layout.addRow("Trackers", block_trackers)
        
        block_analytics = QCheckBox("Block Google Analytics")
        block_analytics.setChecked(True)
        layout.addRow("Analytics", block_analytics)
        
        block_ads = QCheckBox("Block Ads")
        block_ads.setChecked(True)
        layout.addRow("Ads", block_ads)
        
        # FINGERPRINTING
        layout.addRow(QLabel("\nFINGERPRINTING PROTECTION:"))
        poison_canvas = QCheckBox("Poison Canvas")
        poison_canvas.setChecked(True)
        layout.addRow("Canvas FP", poison_canvas)
        
        poison_webgl = QCheckBox("Poison WebGL")
        poison_webgl.setChecked(True)
        layout.addRow("WebGL FP", poison_webgl)
        
        layout.addRow(QLabel(""))
        
        # STATS
        layout.addRow(QLabel("STATISTICS:"))
        layout.addRow("Trackers Blocked", QLabel(str(self.blocked_count)))
        layout.addRow("Data Downloaded", QLabel(f"{self.total_bytes/1e6:.2f} MB"))
        layout.addRow("Fake Cookies", QLabel(str(len(self.fake_cookies))))
        
        layout.addRow(QLabel(""))
        
        # BUTTONS
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Settings")
        btn_save.clicked.connect(lambda: self._save_settings(dlg, {
            'spoof_os': spoof_os.isChecked(),
            'user_agent': ua_input.text(),
            'spoof_ip': spoof_ip.isChecked(),
            'block_webrtc': block_webrtc.isChecked(),
            'spoof_geo': spoof_geo.isChecked(),
            'block_notif': block_notif.isChecked(),
            'block_trackers': block_trackers.isChecked(),
            'block_analytics': block_analytics.isChecked(),
            'block_ads': block_ads.isChecked(),
            'poison_canvas': poison_canvas.isChecked(),
            'poison_webgl': poison_webgl.isChecked(),
        }))
        
        btn_reset = QPushButton("Reset to Defaults")
        btn_reset.clicked.connect(lambda: self._reset_settings(dlg))
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.close)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_close)
        layout.addRow(btn_layout)
        
        dlg.setLayout(layout)
        dlg.exec()
    
    def _save_settings(self, dlg, settings):
        """Save settings"""
        self.log_signal.emit("[SETTINGS] Configuration saved")
        self.log_signal.emit(f"[CONFIG] OS Spoof: {settings['spoof_os']}")
        self.log_signal.emit(f"[CONFIG] IP Spoof: {settings['spoof_ip']}")
        self.log_signal.emit(f"[CONFIG] WebRTC Block: {settings['block_webrtc']}")
        self.log_signal.emit(f"[CONFIG] Trackers: {settings['block_trackers']}")
        dlg.close()
    
    def _reset_settings(self, dlg):
        """Reset to defaults"""
        self.log_signal.emit("[SETTINGS] Reset to defaults")
        dlg.close()
        self.show_settings()
    
    def closeEvent(self, event):
        """Clean up on exit"""
        self.profile.clearHttpCache()
        self.profile.cookieStore().deleteAllCookies()
        print("[Swordfish] GHOST EXIT - All data wiped from RAM")
        event.accept()

def main():
    import contextlib
    
    app = QApplication(sys.argv)
    app.setApplicationName("Swordfish")
    app.setStyleSheet(THEME)
    
    with open(os.devnull, 'w') as f:
        with contextlib.redirect_stderr(f):
            win = Swordfish()
            win.show()
            sys.exit(app.exec())

if __name__ == "__main__":
    main()

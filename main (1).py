#!/usr/bin/env python3
"""
Swordfish v16.3 — Windows Privacy Browser
Fixes in this version:
  - Cookie manager no longer floods with duplicates (one-time snapshot load)
  - Log / Network show-hide moved to Settings panel (toggles persist)
  - Triple-click a traffic log entry to block that host
  - Double-click a traffic log entry to open that URL in a new tab
  - User-Agent field is now a combo-box with presets + free-type
  - userAgentData (UA-CH) fully spoofed so sites can't detect Windows
  - Geolocation denied at Qt engine level, not just JS
"""

import sys, os, json, re, urllib.request, threading
from datetime import datetime

os.environ["QT_LOGGING_RULES"]            = "*=false"
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
os.environ["PYTHONWARNINGS"]              = "ignore"

_LINUX_UA    = "Mozilla/5.0 (X11; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0"
_CHROME_UA   = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
_SAFARI_UA   = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
_MOBILE_UA   = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36"
_BOT_UA      = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
_CURL_UA     = "curl/8.7.1"

UA_PRESETS = [
    ("Firefox 138 · Linux x86_64 (default)",  _LINUX_UA),
    ("Chrome 124 · Linux x86_64",             _CHROME_UA),
    ("Safari 17 · macOS Sonoma",              _SAFARI_UA),
    ("Chrome 124 · Android 14 · Pixel 8",    _MOBILE_UA),
    ("Googlebot 2.1",                         _BOT_UA),
    ("curl 8.7.1",                            _CURL_UA),
    ("Custom — type or paste below ↓",        ""),
]

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--incognito --disable-gpu-sandbox --disable-cache "
    "--memory-pressure-off --no-sandbox --disable-webrtc "
    "--disable-speech-api --disable-notifications "
    f"--user-agent={_LINUX_UA}"
)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton, QLabel,
    QTabWidget, QDialog, QFormLayout, QCheckBox, QComboBox,
    QTableWidget, QTableWidgetItem, QFrame, QScrollArea,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineUrlRequestInterceptor, QWebEngineProfile,
    QWebEnginePage, QWebEngineScript, QWebEngineSettings,
)
from PyQt6.QtCore  import QUrl, pyqtSignal, Qt, QTimer
from PyQt6.QtGui   import QColor, QPainter, QPen, QFont, QIcon

# ════════════════════════════════════════════════════════════════
#  DEFAULT SETTINGS
# ════════════════════════════════════════════════════════════════
DEFAULT_SETTINGS = {
    "spoof_os":          True,
    "user_agent":        _LINUX_UA,
    "spoof_ip":          True,
    "spoofed_ip_value":  "192.0.2.1",
    "block_webrtc":      True,
    "spoof_geo":         True,
    "block_notif":       True,
    "block_trackers":    True,
    "block_analytics":   True,
    "block_ads":         True,
    "poison_canvas":     True,
    "poison_webgl":      True,
    "show_net":          True,
    "show_log":          True,
}

# ════════════════════════════════════════════════════════════════
#  PRIVACY JS BUILDER
# ════════════════════════════════════════════════════════════════
def build_privacy_js(s: dict) -> str:
    parts = ["(function(){'use strict';"]

    if s.get("block_webrtc", True):
        parts.append("""
    const _rtcBlock=()=>{throw new Error('WebRTC disabled');};
    window.RTCPeerConnection=_rtcBlock;
    window.webkitRTCPeerConnection=_rtcBlock;
    window.mozRTCPeerConnection=_rtcBlock;
    window.RTCDataChannel=_rtcBlock;
    if(window.mediaDevices){
        window.mediaDevices.getUserMedia=()=>Promise.reject(new Error('Blocked'));
    }""")

    if s.get("spoof_os", True):
        import re as _re
        ua = (s.get("user_agent") or _LINUX_UA).replace("'", "\\'")
        _ff = _re.search(r"Firefox/(\d+)", s.get("user_agent", ""))
        ff_ver = _ff.group(1) if _ff else "138"
        parts.append(f"""
    const _fakeUA='{ua}';
    const _ffVer='{ff_ver}';
    const _nav={{userAgent:_fakeUA,appVersion:'5.0 (X11)',platform:'Linux x86_64',oscpu:'Linux x86_64'}};
    for(let _k in _nav){{try{{Object.defineProperty(navigator,_k,{{value:_nav[_k],writable:false,configurable:false}})}}catch(e){{}}}}
    if(navigator.userAgentData){{
        const _brands=[{{brand:'Not/A)Brand',version:'8'}},{{brand:'Firefox',version:_ffVer}}];
        const _uaData={{
            brands:_brands, mobile:false, platform:'Linux',
            getHighEntropyValues:function(hints){{
                const _map={{platform:'Linux',platformVersion:'6.5.0',architecture:'x86',
                    bitness:'64',model:'',mobile:false,brands:_brands,
                    fullVersionList:_brands,uaFullVersion:_ffVer+'.0',wow64:false}};
                const r={{}};
                hints.forEach(h=>{{if(_map[h]!==undefined)r[h]=_map[h];}});
                return Promise.resolve(r);
            }},
            toJSON:function(){{return{{brands:_brands,mobile:false,platform:'Linux'}};}}
        }};
        try{{Object.defineProperty(navigator,'userAgentData',{{value:_uaData,writable:false,configurable:false}});}}catch(e){{}}
    }}
    [['width',1920],['height',1080],['availWidth',1920],['availHeight',1050],['colorDepth',24],['pixelDepth',24]].forEach(([p,v])=>{{
        try{{Object.defineProperty(screen,p,{{value:v,writable:false,configurable:false}});}}catch(e){{}}
    }});""")

    if s.get("spoof_geo", True):
        parts.append("""
    if(navigator.geolocation){
        navigator.geolocation.getCurrentPosition=(cb)=>setTimeout(()=>cb({
            coords:{latitude:51.5074,longitude:-0.1278,accuracy:50,altitude:0,
                    altitudeAccuracy:null,heading:0,speed:0},timestamp:Date.now()
        }),100);
        navigator.geolocation.watchPosition=navigator.geolocation.getCurrentPosition;
    }""")

    if s.get("block_notif", True):
        parts.append("""
    window.Notification=class{
        constructor(){throw new Error('Blocked');}
        static requestPermission(){return Promise.resolve('denied');}
    };""")

    parts.append("""
    if(navigator.sendBeacon){navigator.sendBeacon=function(){return false;};}""")

    if s.get("poison_canvas", True):
        parts.append("""
    const _origTDU=HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL=function(){
        const ctx=this.getContext('2d');
        if(ctx){ctx.fillStyle='rgba('+Math.floor(Math.random()*4)+','+Math.floor(Math.random()*4)+','+Math.floor(Math.random()*4)+',0.01)';ctx.fillRect(0,0,1,1);}
        return _origTDU.call(this);
    };""")

    if s.get("poison_webgl", True):
        parts.append("""
    const _origGP=WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter=function(p){
        if(p===37445||p===37446)return'Generic GPU (Linux)';
        return _origGP.call(this,p);
    };""")

    if s.get("block_analytics", True) or s.get("block_trackers", True):
        parts.append("""
    ['_gaq','ga','gtag','__gaTracker','_paq','fbq','mixpanel','_fbq'].forEach(t=>{
        try{delete window[t];Object.defineProperty(window,t,{get:()=>undefined,configurable:false});}catch(e){}
    });""")

    parts.append("""
    try{Object.defineProperty(navigator,'language',{value:'en-US',writable:false});}catch(e){}
    try{Object.defineProperty(navigator,'languages',{value:['en-US','en'],writable:false});}catch(e){}
    try{Object.defineProperty(navigator,'deviceMemory',{value:8,writable:false});}catch(e){}
    try{Object.defineProperty(navigator,'hardwareConcurrency',{value:4,writable:false});}catch(e){}
    if(navigator.getBattery)navigator.getBattery=()=>Promise.resolve({level:0.75,charging:true,chargingTime:0,dischargingTime:Infinity});
    console.log('[SWORDFISH] Privacy layer active');""")

    parts.append("})();")
    return "\n".join(parts)


# ════════════════════════════════════════════════════════════════
#  THEME
# ════════════════════════════════════════════════════════════════
THEME = """
* { font-family: Tahoma, "Segoe UI", Arial, sans-serif; font-size: 11px; color: #000000; }
QMainWindow, QWidget { background: #d4d0c8; }
QDialog { background: #d4d0c8; }
QScrollArea { background: #d4d0c8; border: none; }
QWidget#toolbar {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #eeeade, stop:0.45 #d8d4c8, stop:0.46 #c4c0b4, stop:1 #b8b4a8);
    border-bottom: 2px solid #808080; padding: 2px 4px;
}
QPushButton#navbtn {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #f0ede4, stop:1 #c8c4b8);
    border-top:1px solid #fff; border-left:1px solid #fff;
    border-right:1px solid #606060; border-bottom:1px solid #606060;
    border-radius:3px; padding:3px 8px; min-width:28px; min-height:22px;
    font-weight:bold; font-size:12px;
}
QPushButton#navbtn:hover { border-color:#316ac5 #1a4a9c #1a4a9c #316ac5; }
QPushButton#navbtn:pressed {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #b0aca0, stop:1 #d0ccc0);
    border-top:1px solid #606060; border-left:1px solid #606060;
    border-right:1px solid #fff; border-bottom:1px solid #fff;
}
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #f0ede4, stop:1 #c8c4b8);
    border-top:1px solid #fff; border-left:1px solid #fff;
    border-right:1px solid #606060; border-bottom:1px solid #606060;
    border-radius:2px; padding:3px 10px; min-height:20px;
}
QPushButton:hover { border-color:#316ac5 #1a4a9c #1a4a9c #316ac5; }
QPushButton:pressed {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #b0aca0, stop:1 #d0ccc0);
    border-top:1px solid #606060; border-left:1px solid #606060;
    border-right:1px solid #e0ddd4; border-bottom:1px solid #e0ddd4;
}
QPushButton:disabled { color:#909090; }
QLineEdit#urlbar {
    background:#fff; color:#000080;
    border-top:2px solid #808080; border-left:2px solid #808080;
    border-right:2px solid #d4d0c8; border-bottom:2px solid #d4d0c8;
    border-radius:0; padding:2px 6px; font-size:12px;
    selection-background-color:#316ac5; selection-color:#fff;
}
QLineEdit#urlbar:focus { border-top:2px solid #316ac5; border-left:2px solid #316ac5; }
QLineEdit {
    background:#fff; color:#000;
    border-top:2px solid #808080; border-left:2px solid #808080;
    border-right:2px solid #d4d0c8; border-bottom:2px solid #d4d0c8; padding:2px 4px;
}
QLineEdit:focus { border-top:2px solid #316ac5; border-left:2px solid #316ac5; }
QComboBox {
    background:#fff; color:#000;
    border-top:2px solid #808080; border-left:2px solid #808080;
    border-right:2px solid #d4d0c8; border-bottom:2px solid #d4d0c8; padding:2px 4px;
}
QComboBox QAbstractItemView { background:#fff; selection-background-color:#316ac5; selection-color:#fff; }
QTabWidget#pagetabs::pane { border:2px solid #808080; border-top:none; background:#fff; }
QTabBar#pagetabbar::tab {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #c8c4b8, stop:1 #b0aca0);
    color:#444; border:1px solid #808080; border-bottom:none;
    padding:3px 14px 4px; margin-right:2px;
    border-top-left-radius:4px; border-top-right-radius:4px;
    font-size:11px; min-width:80px; max-width:200px;
}
QTabBar#pagetabbar::tab:selected { background:#d4d0c8; color:#000; font-weight:bold; }
QTabBar#pagetabbar::tab:hover:!selected { background:#dedad0; }
QListWidget#trafficlog {
    background:#e8e0c8; color:#1a1a1a;
    border-top:2px solid #808080; border-left:2px solid #808080;
    border-right:2px solid #d4d0c8; border-bottom:2px solid #d4d0c8;
    font-family:"Courier New",Courier,monospace; font-size:10px; padding:1px;
}
QListWidget#trafficlog::item { padding:0 2px; border-bottom:1px solid #d4c890; }
QListWidget#trafficlog::item:selected { background:#316ac5; color:#fff; }
QTableWidget {
    background:#fff; color:#000;
    border-top:2px solid #808080; border-left:2px solid #808080;
    border-right:2px solid #d4d0c8; border-bottom:2px solid #d4d0c8;
    gridline-color:#d0ccc0; alternate-background-color:#f0eee8;
    selection-background-color:#316ac5; selection-color:#fff;
}
QHeaderView::section {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #e8e4dc, stop:1 #ccc8bc);
    color:#000; border:none; border-right:1px solid #909090;
    border-bottom:2px solid #808080; padding:3px 6px; font-weight:bold;
}
QWidget#statsbar {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #d4d0c8, stop:1 #c0bcb0);
    border-top:2px solid #808080; padding:1px 6px;
}
QLabel#statslabel  { color:#000; font-family:"Courier New",Courier,monospace; font-size:10px; }
QLabel#blockedlabel{ color:#880000; font-family:"Courier New",Courier,monospace; font-size:10px; font-weight:bold; }
QLabel#iplabel     { color:#004000; font-family:"Courier New",Courier,monospace; font-size:10px; }
QCheckBox { color:#000; spacing:5px; }
QCheckBox::indicator {
    width:13px; height:13px;
    border-top:2px solid #808080; border-left:2px solid #808080;
    border-right:2px solid #d4d0c8; border-bottom:2px solid #d4d0c8; background:#fff;
}
QCheckBox::indicator:checked { background:#316ac5; }
QScrollBar:vertical { background:#d4d0c8; width:16px; border:1px solid #808080; }
QScrollBar::handle:vertical {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #e8e4dc, stop:1 #b8b4a8);
    border-top:1px solid #fff; border-left:1px solid #fff;
    border-right:1px solid #606060; border-bottom:1px solid #606060; min-height:20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #e8e4dc, stop:1 #c8c4b8);
    border:1px solid #808080; height:16px; subcontrol-origin:margin;
}
QScrollBar:horizontal { background:#d4d0c8; height:16px; border:1px solid #808080; }
QScrollBar::handle:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #e8e4dc, stop:1 #c0bcb0);
    border-top:1px solid #fff; border-left:1px solid #fff;
    border-right:1px solid #606060; border-bottom:1px solid #606060; min-width:20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #e8e4dc, stop:1 #c8c4b8);
    border:1px solid #808080; width:16px;
}
QStatusBar { background:#c0bcb0; border-top:1px solid #808080; color:#000; font-size:10px; }
"""


# ════════════════════════════════════════════════════════════════
#  BANDWIDTH GRAPH
# ════════════════════════════════════════════════════════════════
class BandwidthGraph(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedSize(260, 48)
        self.data = [0.0] * 150
        self.setStyleSheet(
            "background:#e8e0c8; border-top:1px solid #808080; border-left:1px solid #808080;"
            "border-right:1px solid #d4d0c8; border-bottom:1px solid #d4d0c8;"
        )

    def add_data(self, val: float):
        self.data.append(float(val)); self.data.pop(0); self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPolygonF, QLinearGradient, QBrush
        from PyQt6.QtCore import QPointF
        p = QPainter(self); w, h = self.width(), self.height()
        p.fillRect(0,0,w,h,QColor(0xe8,0xe0,0xc8))
        p.setPen(QPen(QColor(0x80,0x80,0x80),1)); p.drawRect(0,0,w-1,h-1)
        p.setPen(QPen(QColor(0xd4,0xc8,0x90),1))
        for i in range(0,w,40): p.drawLine(i,0,i,h)
        for i in range(0,h,20): p.drawLine(0,i,w,i)
        p.setPen(QPen(QColor(0xaa,0x44,0x00),1)); p.drawLine(0,10,w,10)
        recent  = self.data[-8:] if len(self.data)>=8 else self.data
        max_val = max(max(recent),2.0)*1.15; n=len(self.data)
        pts=[QPointF(0.0,float(h))]
        for i,v in enumerate(self.data):
            pts.append(QPointF(i*(w/max(n-1,1)), h-12-(v/max_val)*(h-22)))
        pts.append(QPointF(float(w),float(h)))
        grad=QLinearGradient(0,0,0,h)
        grad.setColorAt(0.0,QColor(0,120,0,120)); grad.setColorAt(1.0,QColor(0,120,0,20))
        p.setPen(QPen(Qt.PenStyle.NoPen)); p.setBrush(QBrush(grad)); p.drawPolygon(QPolygonF(pts))
        p.setPen(QPen(QColor(0,122,0),2))
        for i in range(n-1):
            x1=i*(w/max(n-1,1));x2=(i+1)*(w/max(n-1,1))
            y1=h-12-(self.data[i]/max_val)*(h-22); y2=h-12-(self.data[i+1]/max_val)*(h-22)
            p.drawLine(int(x1),int(y1),int(x2),int(y2))
        p.setPen(QPen(QColor(0,0,0),1)); p.setFont(QFont("Courier New",8))
        p.drawText(4,11,f"Now: {self.data[-1]:.1f} KB/s")
        p.drawText(4,h-3,f"Peak: {max(self.data):.0f} KB/s")


# ════════════════════════════════════════════════════════════════
#  URL INTERCEPTOR
# ════════════════════════════════════════════════════════════════
class URLInterceptor(QWebEngineUrlRequestInterceptor):
    _TRACKERS  = {"doubleclick.net","google-analytics.com","facebook.com/tr",
                  "segment.com","mixpanel.com","amplitude.com","hotjar.com"}
    _ANALYTICS = {"google-analytics.com","analytics.google.com",
                  "googletagmanager.com","stats.g.doubleclick.net"}
    _ADS       = {"googleadservices.com","pagead2.googlesyndication.com",
                  "ads.google.com","adclick.g.doubleclick.net","advertising.com"}

    def __init__(self, log_fn):
        super().__init__()
        self.log             = log_fn
        self.spoofed_ip      = "192.0.2.1"
        self.spoof_enabled   = True
        self.block_trackers  = True
        self.block_analytics = True
        self.block_ads       = True
        self.extra_blocked   = set()   # hosts added via triple-click

    def _blocklist(self) -> set:
        bl = set()
        if self.block_trackers:  bl |= self._TRACKERS
        if self.block_analytics: bl |= self._ANALYTICS
        if self.block_ads:       bl |= self._ADS
        bl |= self.extra_blocked
        return bl

    def interceptRequest(self, info):
        url  = info.requestUrl().toString()
        host = info.requestUrl().host().lower()
        self.log(f"[REQUEST] {url[:120]}")
        if host in self.extra_blocked or any(b in url.lower() for b in self._blocklist()):
            self.log(f"[BLOCKED] {host}")
            info.block(True)
            return
        if self.spoof_enabled:
            try:
                ip_b = self.spoofed_ip.encode()
                for h in [b"X-Forwarded-For",b"Client-IP",b"X-Real-IP",
                           b"CF-Connecting-IP",b"X-Client-IP",
                           b"X-Forwarded",b"True-Client-IP"]:
                    info.setHttpHeader(h, ip_b)
            except Exception:
                pass
        self.log(f"[ALLOW] {host}")


# ════════════════════════════════════════════════════════════════
#  CUSTOM PAGE — deny permissions at Qt level
# ════════════════════════════════════════════════════════════════
class SwordfishPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass  # silence console noise

    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        # PyQt6 6.6+: permissionRequested replaces featurePermissionRequested
        try:
            self.permissionRequested.connect(self._deny_permission)
        except AttributeError:
            pass  # older PyQt6 — featurePermissionRequested used below

    def _deny_permission(self, permission):
        try:
            permission.deny()
        except Exception:
            pass

    def featurePermissionRequested(self, url, feature):
        # Fallback for older PyQt6 builds
        try:
            self.setFeaturePermission(
                url, feature,
                QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
            )
        except Exception:
            pass

    def createWindow(self, win_type):
        # Open target=_blank links in a new tab instead of a new window
        view = QWebEngineView()
        new_page = SwordfishPage(self.profile(), view)
        view.setPage(new_page)
        # Signal the main window to adopt this view as a tab
        # We store a reference via the view's parent chain
        top = self.view()
        if top:
            mw = top.window()
            if hasattr(mw, "_adopt_tab"):
                mw._adopt_tab(view)
        return new_page


# ════════════════════════════════════════════════════════════════
#  CLICKABLE TRAFFIC LOG
# ════════════════════════════════════════════════════════════════
class TrafficLog(QListWidget):
    """
    Double-click  → open URL in new tab
    Triple-click  → block that host permanently
    """
    open_url_requested   = pyqtSignal(str)
    block_host_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("trafficlog")
        self.setFixedHeight(110)
        self.setUniformItemSizes(True)
        self._click_timer  = QTimer()
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._resolve_clicks)  # connect ONCE here
        self._click_count  = 0
        self._pending_item = None
        self.itemClicked.connect(self._on_click)

    def _on_click(self, item):
        self._pending_item = item
        self._click_count += 1
        # Restart the timer window on each click
        self._click_timer.stop()
        self._click_timer.start(350)

    def _resolve_clicks(self):
        count = self._click_count
        item  = self._pending_item
        self._click_count  = 0
        self._pending_item = None
        if item is None: return
        text = item.text()

        if count >= 3:
            # Triple-click → extract host and block it
            host = self._extract_host(text)
            if host:
                self.block_host_requested.emit(host)
        elif count == 2:
            # Double-click → extract URL and open it
            url = self._extract_url(text)
            if url:
                self.open_url_requested.emit(url)

    @staticmethod
    def _extract_host(text: str) -> str:
        m = re.search(r"\[(?:REQUEST|ALLOW|BLOCKED)\]\s+(\S+)", text)
        if m:
            raw = m.group(1)
            # strip protocol if present
            raw = re.sub(r"^https?://", "", raw).split("/")[0]
            return raw
        return ""

    @staticmethod
    def _extract_url(text: str) -> str:
        m = re.search(r"(https?://\S+)", text)
        return m.group(1) if m else ""


# ════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ════════════════════════════════════════════════════════════════
class Swordfish(QMainWindow):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Swordfish v16.3 — Privacy Browser")
        self.resize(1500, 950)

        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        self.settings = dict(DEFAULT_SETTINGS)

        # Profile
        self.profile = QWebEngineProfile()
        self.profile.setHttpUserAgent(self.settings["user_agent"])
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        # Interceptor
        self.interceptor = URLInterceptor(self.log_signal.emit)
        self.profile.setUrlRequestInterceptor(self.interceptor)

        # Privacy JS
        self._inject_privacy_script(build_privacy_js(self.settings))

        self.log_signal.connect(self._on_log)

        # Stats
        self.total_bytes   = 0
        self.tick_bytes    = 0
        self.blocked_count = 0
        self.fake_cookies  = []

        # Cookie dedup: track (domain, name) pairs already shown
        self._seen_cookies: set = set()

        self._build_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self._update_stats)
        self.timer.start(1000)

        threading.Thread(target=self._detect_real_ip, daemon=True).start()
        self.new_tab()

    # ── Privacy script ───────────────────────────────────────────
    def _inject_privacy_script(self, js: str):
        scripts = self.profile.scripts()
        for sc in scripts.toList():
            if sc.name() == "swordfish_privacy":
                scripts.remove(sc)
        sc = QWebEngineScript()
        sc.setName("swordfish_privacy")
        sc.setSourceCode(js)
        sc.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        sc.setWorldId(0)
        scripts.insert(sc)

    # ── UI ────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Toolbar
        tb = QWidget(); tb.setObjectName("toolbar"); tb.setFixedHeight(38)
        tl = QHBoxLayout(tb); tl.setContentsMargins(4,3,4,3); tl.setSpacing(3)
        for attr,lbl,slot in [("btn_back","◄",self._nav_back),
                               ("btn_forward","►",self._nav_forward),
                               ("btn_reload","↺",self._nav_reload)]:
            b=QPushButton(lbl); b.setObjectName("navbtn"); b.setFixedSize(28,26)
            b.clicked.connect(slot); setattr(self,attr,b); tl.addWidget(b)
        tl.addSpacing(4)
        self.url_bar = QLineEdit(); self.url_bar.setObjectName("urlbar")
        self.url_bar.setPlaceholderText("Enter address or search…")
        self.url_bar.returnPressed.connect(self.navigate)
        tl.addWidget(self.url_bar,1); tl.addSpacing(4)
        for lbl,slot in [("Home",     lambda: self.navigate_to("https://duckduckgo.com")),
                          ("New Tab",  self.new_tab),
                          ("Cookies",  self.show_cookies),
                          ("DevTools", self._open_devtools),
                          ("Settings", self.show_settings)]:
            b=QPushButton(lbl); b.setFixedHeight(24); b.clicked.connect(slot); tl.addWidget(b)
        root.addWidget(tb)

        sep=QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(2); sep.setStyleSheet("background:#808080;")
        root.addWidget(sep)

        # Tabs
        self.tabs=QTabWidget(); self.tabs.setObjectName("pagetabs")
        self.tabs.tabBar().setObjectName("pagetabbar"); self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(self.tabs,1)

        # Stats bar
        self.stats_widget=QWidget(); self.stats_widget.setObjectName("statsbar")
        self.stats_widget.setFixedHeight(54)
        sl=QHBoxLayout(self.stats_widget); sl.setContentsMargins(6,2,6,2); sl.setSpacing(8)
        self.stats_label   =QLabel("0.00 MB | 0 KB/s"); self.stats_label.setObjectName("statslabel")
        self.blocked_label =QLabel("Blocked: 0");        self.blocked_label.setObjectName("blockedlabel")
        self.ip_label      =QLabel("Detecting…");        self.ip_label.setObjectName("iplabel")

        def _vsep():
            f=QFrame(); f.setFrameShape(QFrame.Shape.VLine); f.setStyleSheet("color:#909090;"); return f

        lbl_si=QLabel("Spoof IP:"); lbl_si.setObjectName("statslabel")
        self.ip_edit=QLineEdit(self.settings["spoofed_ip_value"]); self.ip_edit.setFixedWidth(110)
        self.ip_edit.setStyleSheet(
            "font-family:'Courier New'; font-size:10px; padding:1px 4px;"
            "border-top:1px solid #808080; border-left:1px solid #808080;"
            "border-right:1px solid #d4d0c8; border-bottom:1px solid #d4d0c8;")
        btn_aip=QPushButton("Apply"); btn_aip.setFixedSize(42,22)
        btn_aip.setStyleSheet("font-size:9px; padding:0;")
        btn_aip.clicked.connect(self._apply_spoofed_ip)
        self.ip_edit.returnPressed.connect(self._apply_spoofed_ip)
        self.chk_spoof_ip=QCheckBox("Spoof IP"); self.chk_spoof_ip.setChecked(True)
        self.chk_spoof_ip.setStyleSheet("font-size:10px; color:#1a1a1a;")
        self.chk_spoof_ip.stateChanged.connect(self._toggle_spoof_ip)
        self.bandwidth_graph=BandwidthGraph()

        for w in [self.stats_label,_vsep(),self.blocked_label,_vsep(),
                  self.ip_label,_vsep(),lbl_si,self.ip_edit,btn_aip,self.chk_spoof_ip]:
            sl.addWidget(w)
        sl.addStretch(); sl.addWidget(self.bandwidth_graph)
        root.addWidget(self.stats_widget)

        # Traffic log
        lh_w=QWidget(); lh_w.setFixedHeight(18)
        lh_w.setStyleSheet("background:#c0bcb0; border-top:1px solid #808080;")
        lh=QHBoxLayout(lh_w); lh.setContentsMargins(6,0,6,0)
        lbl_log=QLabel("Traffic Log  [double-click=open  triple-click=block]")
        lbl_log.setStyleSheet("font-size:10px; font-weight:bold; color:#1a1a1a;")
        btn_clr=QPushButton("Clear"); btn_clr.setFixedSize(40,16)
        btn_clr.setStyleSheet("font-size:9px; padding:0;")
        lh.addWidget(lbl_log); lh.addStretch(); lh.addWidget(btn_clr)

        self.traffic_log = TrafficLog()
        self.traffic_log.open_url_requested.connect(lambda u: self._open_url_new_tab(u))
        self.traffic_log.block_host_requested.connect(self._block_host_from_log)
        btn_clr.clicked.connect(self.traffic_log.clear)

        self.log_widget=QWidget()
        lw=QVBoxLayout(self.log_widget); lw.setContentsMargins(0,0,0,0); lw.setSpacing(0)
        lw.addWidget(lh_w); lw.addWidget(self.traffic_log)
        root.addWidget(self.log_widget)

        # Apply initial show/hide from settings
        self.stats_widget.setVisible(self.settings["show_net"])
        self.log_widget.setVisible(self.settings["show_log"])

        c=QWidget(); c.setLayout(root); self.setCentralWidget(c)

    # ── Tabs ─────────────────────────────────────────────────────
    def new_tab(self, url=None):
        url = url or "https://duckduckgo.com"
        view=QWebEngineView()
        page=SwordfishPage(self.profile, view)
        view.setPage(page)
        view.load(QUrl(url))
        view.urlChanged.connect(lambda u,v=view: self._on_url_changed(u,v))
        view.titleChanged.connect(lambda t,v=view: self._on_title_changed(t,v))
        idx=self.tabs.addTab(view,"New Tab")
        self.tabs.setCurrentIndex(idx)

    def _open_url_new_tab(self, url: str):
        if not url.startswith(("http://","https://")): url="https://"+url
        self.new_tab(url)
        self.log_signal.emit(f"[TAB] Opened: {url[:80]}")

    def _block_host_from_log(self, host: str):
        if host:
            self.interceptor.extra_blocked.add(host)
            self.log_signal.emit(f"[BLOCKED MANUALLY] {host} — added to block list")

    def _on_url_changed(self,url,view):
        if view is self.tabs.currentWidget():
            self.url_bar.setText(url.toString())

    def _on_title_changed(self,title,view):
        idx=self.tabs.indexOf(view)
        if idx>=0:
            self.tabs.setTabText(idx,(title[:18]+"…") if len(title)>20 else (title or "New Tab"))

    def _close_tab(self,idx):
        if self.tabs.count()>1: self.tabs.removeTab(idx)

    def _adopt_tab(self, view):
        """Receive a QWebEngineView created by createWindow (target=_blank etc)."""
        view.urlChanged.connect(lambda u, v=view: self._on_url_changed(u, v))
        view.titleChanged.connect(lambda t, v=view: self._on_title_changed(t, v))
        idx = self.tabs.addTab(view, "New Tab")
        self.tabs.setCurrentIndex(idx)

    def _open_devtools(self):
        """Open a DevTools window for the current tab."""
        cur = self.tabs.currentWidget()
        if not cur: return
        dev = QWebEngineView()
        dev.setWindowTitle("DevTools — Swordfish")
        dev.resize(1000, 600)
        cur.page().setDevToolsPage(dev.page())
        dev.show()
        self._devtools_win = dev  # keep reference so it doesn't get GC'd

    def _on_tab_changed(self,idx):
        v=self.tabs.widget(idx)
        if v: self.url_bar.setText(v.url().toString())

    # ── Navigation ───────────────────────────────────────────────
    def navigate(self):
        url=self.url_bar.text().strip()
        if not url: return
        if not url.startswith(("http://","https://")): url="https://"+url
        cur=self.tabs.currentWidget()
        if cur: cur.load(QUrl(url))

    def navigate_to(self,url):
        self.url_bar.setText(url)
        cur=self.tabs.currentWidget()
        if cur: cur.load(QUrl(url))

    def _nav_back(self):
        cur=self.tabs.currentWidget()
        if cur: cur.back()

    def _nav_forward(self):
        cur=self.tabs.currentWidget()
        if cur: cur.forward()

    def _nav_reload(self):
        cur=self.tabs.currentWidget()
        if cur: cur.reload()

    # ── Logging ──────────────────────────────────────────────────
    def _on_log(self,msg:str):
        ts=datetime.now().strftime("%H:%M:%S")
        item=QListWidgetItem(f"[{ts}] {msg}")
        if   "[BLOCKED" in msg:
            item.setForeground(QColor("#880000"))
            self.blocked_count+=1
            self.blocked_label.setText(f"Blocked: {self.blocked_count}")
        elif "[ALLOW]"  in msg: item.setForeground(QColor("#005000"))
        elif "[REQUEST]"in msg: item.setForeground(QColor("#1a1a1a"))
        elif "[TAB]"    in msg: item.setForeground(QColor("#005080"))
        else:                   item.setForeground(QColor("#2a3a7a"))
        self.traffic_log.addItem(item)
        if self.traffic_log.count()>1000: self.traffic_log.takeItem(0)
        self.traffic_log.scrollToBottom()
        self.tick_bytes+=1500

    # ── Stats ────────────────────────────────────────────────────
    def _update_stats(self):
        kb_s=self.tick_bytes/1024
        self.stats_label.setText(f"{self.total_bytes/1e6:.2f} MB | {kb_s:.1f} KB/s")
        self.bandwidth_graph.add_data(kb_s)
        self.total_bytes+=self.tick_bytes
        self.tick_bytes=0

    # ── IP spoofing (toolbar) ────────────────────────────────────
    def _toggle_spoof_ip(self,state:int):
        enabled=bool(state)
        self.interceptor.spoof_enabled=enabled
        self.settings["spoof_ip"]=enabled
        self.ip_edit.setEnabled(enabled)
        if enabled:
            self.ip_label.setStyleSheet("color:#005000; font-family:'Courier New'; font-size:10px; font-weight:bold;")
            self.log_signal.emit(f"[IP] Spoofing ENABLED → {self.interceptor.spoofed_ip}")
        else:
            self.ip_label.setStyleSheet("color:#880000; font-family:'Courier New'; font-size:10px; font-weight:bold;")
            self.ip_label.setText("IP spoofing OFF")
            self.log_signal.emit("[IP] Spoofing DISABLED")

    def _apply_spoofed_ip(self):
        raw=self.ip_edit.text().strip()
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",raw):
            self.interceptor.spoofed_ip=raw
            self.settings["spoofed_ip_value"]=raw
            self.ip_label.setText(f"Spoofed → {raw}")
            self.ip_label.setStyleSheet("color:#005000; font-family:'Courier New'; font-size:10px; font-weight:bold;")
            self.log_signal.emit(f"[IP] Updated: {raw}")
        else:
            self.ip_edit.setStyleSheet(
                "font-family:'Courier New'; font-size:10px; padding:1px 4px; border:2px solid #cc0000; background:#fff0f0;")
            self.log_signal.emit(f"[IP ERROR] Invalid: {raw}")
            QTimer.singleShot(1500,lambda: self.ip_edit.setStyleSheet(
                "font-family:'Courier New'; font-size:10px; padding:1px 4px;"
                "border-top:1px solid #808080; border-left:1px solid #808080;"
                "border-right:1px solid #d4d0c8; border-bottom:1px solid #d4d0c8;"))

    def _detect_real_ip(self):
        try:
            resp=urllib.request.urlopen("https://api.ipify.org?format=json",timeout=5)
            real_ip=json.loads(resp.read()).get("ip","Unknown")
            self.ip_label.setText(f"Real: {real_ip}  →  Spoofed: {self.interceptor.spoofed_ip}")
            self.ip_label.setStyleSheet("color:#004000; font-family:'Courier New'; font-size:10px;")
        except Exception:
            self.ip_label.setText(f"Real: unknown  →  Spoofed: {self.interceptor.spoofed_ip}")

    # ════════════════════════════════════════════════════════════
    #  SETTINGS DIALOG
    # ════════════════════════════════════════════════════════════
    def show_settings(self):
        s=self.settings
        dlg=QDialog(self); dlg.setWindowTitle("Privacy & Security Settings")
        dlg.resize(660, 700)

        # Scrollable content
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        inner=QWidget(); layout=QFormLayout(inner)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        scroll.setWidget(inner)

        outer=QVBoxLayout(dlg); outer.addWidget(scroll)

        layout.addRow(QLabel("╔════ SWORDFISH v16.3 SETTINGS ════╗"))
        layout.addRow(QLabel("  All changes apply immediately on Save.\n"
                             "  Reload open tabs to pick up JS changes."))
        layout.addRow(QLabel(""))

        # ── OS Spoofing ──────────────────────────────────────────
        layout.addRow(QLabel("── OS SPOOFING ──────────────────────"))
        chk_os=QCheckBox("Spoof OS to Linux (hide Windows)"); chk_os.setChecked(s["spoof_os"])
        layout.addRow("OS Spoof",chk_os)

        # UA combo-box with editable custom field
        ua_combo=QComboBox(); ua_combo.setEditable(False)
        for label,_ in UA_PRESETS:
            ua_combo.addItem(label)
        # Select the combo entry matching current UA, default to custom
        current_ua=s["user_agent"]
        combo_idx=len(UA_PRESETS)-1  # default to "Custom"
        for i,(lbl,val) in enumerate(UA_PRESETS):
            if val==current_ua:
                combo_idx=i; break
        ua_combo.setCurrentIndex(combo_idx)

        ua_custom=QLineEdit(current_ua); ua_custom.setMinimumWidth(420)
        ua_custom.setPlaceholderText("Type or paste a custom User-Agent string here…")

        def _on_preset_changed(idx):
            _,val=UA_PRESETS[idx]
            if val:  # not the "Custom" entry
                ua_custom.setText(val)
                ua_custom.setEnabled(False)
            else:
                ua_custom.setEnabled(True)
                ua_custom.setFocus()

        ua_combo.currentIndexChanged.connect(_on_preset_changed)
        # Set initial state
        _on_preset_changed(combo_idx)

        layout.addRow("UA Preset:",ua_combo)
        layout.addRow("User-Agent:",ua_custom)

        # ── IP Spoofing ──────────────────────────────────────────
        layout.addRow(QLabel("")); layout.addRow(QLabel("── IP SPOOFING ──────────────────────"))
        chk_ip=QCheckBox("Send spoofed IP in request headers"); chk_ip.setChecked(s["spoof_ip"])
        layout.addRow("IP Spoof",chk_ip)
        ip_edit=QLineEdit(s["spoofed_ip_value"])
        layout.addRow("Spoof IP value:",ip_edit)

        # ── WebRTC & Privacy ─────────────────────────────────────
        layout.addRow(QLabel("")); layout.addRow(QLabel("── WEBRTC & PRIVACY ─────────────────"))
        chk_webrtc=QCheckBox("Block WebRTC (prevents real IP leak)"); chk_webrtc.setChecked(s["block_webrtc"])
        layout.addRow("WebRTC",chk_webrtc)
        chk_geo=QCheckBox("Block/spoof geolocation → London"); chk_geo.setChecked(s["spoof_geo"])
        layout.addRow("Geolocation",chk_geo)
        chk_notif=QCheckBox("Block Notification API"); chk_notif.setChecked(s["block_notif"])
        layout.addRow("Notifications",chk_notif)

        # ── Tracker Blocking ─────────────────────────────────────
        layout.addRow(QLabel("")); layout.addRow(QLabel("── TRACKER BLOCKING ─────────────────"))
        chk_tr=QCheckBox("Block tracking pixels & beacons"); chk_tr.setChecked(s["block_trackers"])
        layout.addRow("Trackers",chk_tr)
        chk_an=QCheckBox("Block Google Analytics / Tag Manager"); chk_an.setChecked(s["block_analytics"])
        layout.addRow("Analytics",chk_an)
        chk_ads=QCheckBox("Block ad networks"); chk_ads.setChecked(s["block_ads"])
        layout.addRow("Ads",chk_ads)

        # Show manually-blocked hosts
        if self.interceptor.extra_blocked:
            blocked_str=", ".join(sorted(self.interceptor.extra_blocked))
            lbl_bl=QLabel(f"Manually blocked: {blocked_str}")
            lbl_bl.setWordWrap(True)
            lbl_bl.setStyleSheet("color:#880000; font-size:10px;")
            btn_clr_bl=QPushButton("Clear manual blocks")
            btn_clr_bl.clicked.connect(lambda: (
                self.interceptor.extra_blocked.clear(),
                self.log_signal.emit("[SETTINGS] Manual block list cleared")
            ))
            layout.addRow(lbl_bl); layout.addRow(btn_clr_bl)

        # ── Fingerprinting ───────────────────────────────────────
        layout.addRow(QLabel("")); layout.addRow(QLabel("── FINGERPRINTING PROTECTION ────────"))
        chk_cv=QCheckBox("Add random noise to canvas readouts"); chk_cv.setChecked(s["poison_canvas"])
        layout.addRow("Canvas FP",chk_cv)
        chk_wg=QCheckBox("Spoof WebGL vendor/renderer"); chk_wg.setChecked(s["poison_webgl"])
        layout.addRow("WebGL FP",chk_wg)

        # ── Display ──────────────────────────────────────────────
        layout.addRow(QLabel("")); layout.addRow(QLabel("── DISPLAY ──────────────────────────"))
        chk_net=QCheckBox("Show Network / Bandwidth bar"); chk_net.setChecked(s["show_net"])
        layout.addRow("Network bar",chk_net)
        chk_log=QCheckBox("Show Traffic Log panel"); chk_log.setChecked(s["show_log"])
        layout.addRow("Traffic log",chk_log)

        # ── Stats ────────────────────────────────────────────────
        layout.addRow(QLabel("")); layout.addRow(QLabel("── SESSION STATS ────────────────────"))
        layout.addRow("Trackers Blocked",QLabel(str(self.blocked_count)))
        layout.addRow("Data Downloaded", QLabel(f"{self.total_bytes/1e6:.2f} MB"))
        layout.addRow("Fake Cookies",    QLabel(str(len(self.fake_cookies))))
        layout.addRow(QLabel(""))

        # ── Buttons ──────────────────────────────────────────────
        btn_row=QHBoxLayout()

        def _collect()->dict:
            # UA: if custom entry is selected and enabled, use that text
            if ua_combo.currentIndex()==len(UA_PRESETS)-1 or ua_custom.isEnabled():
                chosen_ua=ua_custom.text().strip() or _LINUX_UA
            else:
                _,chosen_ua=UA_PRESETS[ua_combo.currentIndex()]
            return {
                "spoof_os":         chk_os.isChecked(),
                "user_agent":       chosen_ua,
                "spoof_ip":         chk_ip.isChecked(),
                "spoofed_ip_value": ip_edit.text().strip(),
                "block_webrtc":     chk_webrtc.isChecked(),
                "spoof_geo":        chk_geo.isChecked(),
                "block_notif":      chk_notif.isChecked(),
                "block_trackers":   chk_tr.isChecked(),
                "block_analytics":  chk_an.isChecked(),
                "block_ads":        chk_ads.isChecked(),
                "poison_canvas":    chk_cv.isChecked(),
                "poison_webgl":     chk_wg.isChecked(),
                "show_net":         chk_net.isChecked(),
                "show_log":         chk_log.isChecked(),
            }

        def _save():
            self._apply_settings(_collect()); dlg.close()

        def _reset():
            dlg.close(); self._apply_settings(dict(DEFAULT_SETTINGS)); self.show_settings()

        btn_save =QPushButton("✔  Save Settings");    btn_save.clicked.connect(_save)
        btn_reset=QPushButton("↺  Reset to Defaults"); btn_reset.clicked.connect(_reset)
        btn_close=QPushButton("✖  Cancel");            btn_close.clicked.connect(dlg.close)
        btn_row.addWidget(btn_save); btn_row.addWidget(btn_reset); btn_row.addWidget(btn_close)
        outer.addLayout(btn_row)

        dlg.exec()

    def _apply_settings(self,new_s:dict):
        self.settings.update(new_s); s=self.settings

        # 1. Privacy JS
        self._inject_privacy_script(build_privacy_js(s))
        self.log_signal.emit("[SETTINGS] Privacy JS rebuilt and re-injected")

        # 2. User-Agent
        self.profile.setHttpUserAgent(s["user_agent"])
        self.log_signal.emit(f"[SETTINGS] UA → {s['user_agent'][:70]}")

        # 3. IP spoofing
        self.interceptor.spoof_enabled=s["spoof_ip"]
        ip_val=s.get("spoofed_ip_value","").strip()
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",ip_val):
            self.interceptor.spoofed_ip=ip_val
            self.ip_edit.setText(ip_val)
        self.chk_spoof_ip.blockSignals(True)
        self.chk_spoof_ip.setChecked(s["spoof_ip"])
        self.chk_spoof_ip.blockSignals(False)
        self.ip_edit.setEnabled(s["spoof_ip"])

        # 4. Blocklist flags
        self.interceptor.block_trackers =s["block_trackers"]
        self.interceptor.block_analytics=s["block_analytics"]
        self.interceptor.block_ads      =s["block_ads"]

        # 5. Display toggles
        self.stats_widget.setVisible(s["show_net"])
        self.log_widget.setVisible(s["show_log"])

        self.log_signal.emit(
            f"[SETTINGS] Applied — Net:{s['show_net']} Log:{s['show_log']} "
            f"OS:{s['spoof_os']} WebRTC:{s['block_webrtc']} "
            f"Canvas:{s['poison_canvas']} WebGL:{s['poison_webgl']}")
        self.log_signal.emit("[SETTINGS] Reload open tabs for JS changes to take effect.")

    # ════════════════════════════════════════════════════════════
    #  COOKIE MANAGER  (no more duplicates)
    # ════════════════════════════════════════════════════════════
    def show_cookies(self):
        dlg=QDialog(self); dlg.setWindowTitle("Cookie Manager"); dlg.resize(760,500)
        lay=QVBoxLayout()

        # ── Real cookies ─────────────────────────────────────────
        lbl_r=QLabel("REAL COOKIES (from websites) — snapshot at open time:")
        lbl_r.setStyleSheet("font-weight:bold; color:#008800;")
        real_tbl=QTableWidget(0,5)
        real_tbl.setHorizontalHeaderLabels(["Domain","Name","Value","Expires","Secure"])
        real_tbl.horizontalHeader().setStretchLastSection(True)
        real_tbl.setAlternatingRowColors(True)
        lay.addWidget(lbl_r); lay.addWidget(real_tbl)

        # One-shot load: collect all cookies then populate table once.
        # We use a local set so the signal only fires during this dialog's lifetime.
        _loaded:set = set()

        def _add_cookie_once(cookie):
            if "__done__" in _loaded: return  # window closed
            try:
                # QNetworkCookie.name()/value() return QByteArray in PyQt6
                def _ba(v):
                    if hasattr(v, "toStdString"): return v.toStdString()
                    if hasattr(v, "data"):        return bytes(v).decode("utf-8", errors="replace")
                    return str(v)
                domain = cookie.domain()
                name   = _ba(cookie.name())
                key    = (domain, name)
                if key in _loaded: return
                _loaded.add(key)
                row = real_tbl.rowCount()
                real_tbl.insertRow(row)
                value   = _ba(cookie.value())[:60]
                expires = cookie.expirationDate().toString("yyyy-MM-dd") if cookie.expirationDate().isValid() else "session"
                secure  = "✔" if cookie.isSecure() else ""
                real_tbl.setItem(row, 0, QTableWidgetItem(domain))
                real_tbl.setItem(row, 1, QTableWidgetItem(name))
                real_tbl.setItem(row, 2, QTableWidgetItem(value))
                real_tbl.setItem(row, 3, QTableWidgetItem(expires))
                real_tbl.setItem(row, 4, QTableWidgetItem(secure))
            except Exception:
                pass

        store=self.profile.cookieStore()
        # Connect, capture the connection object for safe disconnect later
        _conn = store.cookieAdded.connect(_add_cookie_once)
        store.loadAllCookies()
        # Use a flag to stop processing after the dialog load window — safest approach
        # because PyQt6 disconnect(callable) is unreliable across versions
        def _stop(): _loaded.add("__done__")
        QTimer.singleShot(600, _stop)

        # ── Fake cookies ─────────────────────────────────────────
        lbl_f=QLabel("FAKE COOKIES (for testing):")
        lbl_f.setStyleSheet("font-weight:bold; color:#880000;")
        fake_tbl=QTableWidget(len(self.fake_cookies),4)
        fake_tbl.setHorizontalHeaderLabels(["Domain","Name","Value","Type"])
        fake_tbl.setAlternatingRowColors(True)
        for i,c in enumerate(self.fake_cookies):
            fake_tbl.setItem(i,0,QTableWidgetItem(c["domain"]))
            fake_tbl.setItem(i,1,QTableWidgetItem(c["name"]))
            fake_tbl.setItem(i,2,QTableWidgetItem(c["value"][:40]))
            fake_tbl.setItem(i,3,QTableWidgetItem("FAKE"))
        lay.addWidget(lbl_f); lay.addWidget(fake_tbl)

        # ── Buttons ──────────────────────────────────────────────
        br=QHBoxLayout()
        ba=QPushButton("Add Fake Cookie")
        ba.clicked.connect(lambda: self._add_fake_cookie_dialog(dlg))
        bc=QPushButton("Clear All Real Cookies")
        bc.clicked.connect(lambda: (store.deleteAllCookies(),
                                    self._seen_cookies.clear(),
                                    self.log_signal.emit("[COOKIES] All real cookies cleared")))
        bx=QPushButton("Close"); bx.clicked.connect(dlg.close)
        br.addWidget(ba); br.addWidget(bc); br.addWidget(bx)
        lay.addLayout(br); dlg.setLayout(lay); dlg.exec()

    def _add_fake_cookie_dialog(self,parent):
        dlg=QDialog(parent); dlg.setWindowTitle("Add Fake Cookie"); dlg.resize(400,200)
        lay=QFormLayout()
        dom=QLineEdit("example.com"); nam=QLineEdit("session_id"); val=QLineEdit("abc123xyz789")
        lay.addRow("Domain:",dom); lay.addRow("Name:",nam); lay.addRow("Value:",val)
        def _save():
            if dom.text() and nam.text():
                self.fake_cookies.append({"domain":dom.text(),"name":nam.text(),"value":val.text()})
                dlg.close()
                self.log_signal.emit(f"[COOKIE] Added fake: {dom.text()}/{nam.text()}")
        b=QPushButton("Save"); b.clicked.connect(_save); lay.addRow(b)
        dlg.setLayout(lay); dlg.exec()

    def closeEvent(self,event):
        self.profile.clearHttpCache()
        self.profile.cookieStore().deleteAllCookies()
        print("[Swordfish] GHOST EXIT — session data wiped")
        event.accept()


# ════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════
def main():
    import contextlib
    app=QApplication(sys.argv)
    app.setApplicationName("Swordfish")
    app.setStyleSheet(THEME)
    with open(os.devnull,"w") as f:
        with contextlib.redirect_stderr(f):
            win=Swordfish()
            win.show()
            sys.exit(app.exec())

if __name__=="__main__":
    main()

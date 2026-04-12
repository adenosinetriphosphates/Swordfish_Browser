#!/usr/bin/env python3
import sys, os, json, re, random, urllib.request, threading
from datetime import datetime
from pathlib import Path

APP_DIR        = Path(os.path.dirname(os.path.abspath(__file__)))
BLOCKLIST_PATH = APP_DIR / "swordfish_blocklist.txt"
SETTINGS_PATH  = APP_DIR / "swordfish_settings.json"

os.environ["QT_LOGGING_RULES"]            = "*=false"
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
os.environ["PYTHONWARNINGS"]              = "ignore"

_LINUX_UA  = "Mozilla/5.0 (X11; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0"
_CHROME_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
_SAFARI_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
_MOBILE_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36"
_BOT_UA    = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

UA_PRESETS = [
    ("Firefox 138 · Linux x86_64 (default)", _LINUX_UA),
    ("Chrome 124 · Linux x86_64",            _CHROME_UA),
    ("Safari 17 · macOS Sonoma",             _SAFARI_UA),
    ("Chrome 124 · Android 14 · Pixel 8",   _MOBILE_UA),
    ("Googlebot 2.1",                        _BOT_UA),
    ("Custom — type or paste below",         ""),
]

SCREEN_PRESETS = [
    ("1920×1080  Full HD",     1920, 1080),
    ("1366×768   Laptop",      1366,  768),
    ("1536×864   HD+ laptop",  1536,  864),
    ("1440×900   MacBook 13",  1440,  900),
    ("1280×800   Older Screen",1280,  800),
    ("2560×1440  2K",          2560, 1440),
]

GPU_PRESETS = [
    ("Generic GPU (Linux) — Mesa",      "Generic GPU (Linux)",     "Mesa 23.1 on llvmpipe"),
    ("Intel UHD 620 — Mesa",            "Intel",                   "Mesa Intel UHD Graphics 620 (KBL GT2)"),
    ("AMD Radeon RX 580 — Mesa",        "AMD",                     "ANGLE (AMD, AMD Radeon RX 580, OpenGL 4.6)"),
    ("NVIDIA GTX 1060 — ANGLE",         "NVIDIA Corporation",      "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB, OpenGL 4.6.0)"),
    ("Apple M1 — Metal",                "Apple",                   "ANGLE (Apple, ANGLE Metal Renderer: Apple M1, Unspecified Version)"),
    ("Google SwiftShader",              "Google Inc. (Google)",    "ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device), SwiftShader driver)"),
    ("Custom",                          "",                        ""),
]

GEO_PRESETS = [
    ("London, UK",         51.5074, -0.1278),
    ("Paris, France",      48.8566,  2.3522),
    ("Berlin, Germany",    52.5200, 13.4050),
    ("Tokyo, Japan",       35.6762, 139.6503),
    ("New York, USA",      40.7128, -74.0060),
    ("Sydney, Australia", -33.8688, 151.2093),
    ("São Paulo, Brazil", -23.5505, -46.6333),
    ("Mumbai, India",      19.0760,  72.8777),
    ("Delhi, India",       28.7041,  77.1025),
    ("Cairo, Egypt",       30.0444,  31.2357),
    ("Dubai, UAE",         25.2048,  55.2708),
    ("Moscow, Russia",     55.7558,  37.6173),
    ("Beijing, China",      39.9042, 116.4074),
    ("Los Angeles, USA",   34.0522, -118.2437),
    ("Toronto, Canada",     43.6532, -79.3832),
    ("Mexico City, Mexico", 19.4326, -99.1332),
    ("Johannesburg, South Africa", -26.2041, 28.0473),
    ("Singapore, Singapore",  1.3521, 103.8198),
    ("Pyongyang, North Korea", 39.0392, 125.7625),
    ("Custom",                 0.0,     0.0),
]

TZ_PRESETS = [
    "Europe/London","Europe/Paris","Europe/Berlin",
    "America/New_York","America/Chicago","America/Los_Angeles",
    "Asia/Tokyo","Asia/Shanghai","Australia/Sydney","America/Sao_Paulo",
]

FONT_POOLS = {
    "Linux generic":   ["DejaVu Sans","Liberation Sans","Noto Sans","Ubuntu","FreeSans","Nimbus Sans"],
    "macOS":           ["Helvetica Neue","San Francisco","Arial","Georgia","Times New Roman","Menlo"],
    "Windows generic": ["Segoe UI","Arial","Calibri","Tahoma","Verdana","Consolas"],
    "Minimal (3)":     ["Arial","sans-serif","monospace"],
}

# Tracking query params to strip from URLs
TRACKING_PARAMS = [
    "utm_source","utm_medium","utm_campaign","utm_term","utm_content",
    "fbclid","gclid","msclkid","dclid","twclid","igshid","mc_eid",
    "ref","source","_hsenc","_hsmi","mkt_tok","yclid","gbraid","wbraid",
    "__s","vero_id","oly_enc_id","oly_anon_id","_openstat","zanpid",
    "origin_ui","share_source","share_medium",
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
    QTabWidget, QDialog, QFormLayout, QCheckBox, QComboBox, QSpinBox,
    QDoubleSpinBox, QSlider, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea, QAbstractItemView,
    QTextEdit, QProgressBar, QGroupBox,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineUrlRequestInterceptor, QWebEngineProfile,
    QWebEnginePage, QWebEngineScript, QWebEngineSettings,
)
from PyQt6.QtCore  import QUrl, pyqtSignal, Qt, QTimer, QByteArray
from PyQt6.QtGui   import QColor, QPainter, QPen, QFont, QIcon
from PyQt6.QtNetwork import QNetworkCookie


# ════════════════════════════════════════════════════════════════
#  FINGERPRINT PROFILE
# ════════════════════════════════════════════════════════════════
class FingerprintProfile:
    def __init__(self, seed=None, base: dict = None):
        self.seed = seed or random.randint(0, 2**32)
        b = base or {}
        self.user_agent      = b.get("user_agent", _LINUX_UA)
        self.spoofed_ip      = b.get("spoofed_ip_value", "192.0.2.1")
        self.screen_w        = b.get("screen_w", 1920)
        self.screen_h        = b.get("screen_h", 1080)
        self.pixel_ratio     = b.get("pixel_ratio", 1.0)
        self.gpu_vendor      = b.get("gpu_vendor", "Generic GPU (Linux)")
        self.gpu_renderer    = b.get("gpu_renderer", "Mesa 23.1 on llvmpipe")
        self.geo_lat         = b.get("geo_lat", 51.5074)
        self.geo_lng         = b.get("geo_lng", -0.1278)
        self.timezone        = b.get("timezone", "Europe/London")
        self.canvas_noise    = b.get("canvas_noise", 3)
        self.audio_freq      = b.get("audio_freq", 440.0)
        self.device_mem      = b.get("device_mem", 8)
        self.cpu_cores       = b.get("cpu_cores", 4)
        self.font_set        = b.get("font_set", "Linux generic")
        self.timing_jitter   = b.get("timing_jitter", 1.0)   # ms max jitter on perf.now
        self.prefers_scheme  = b.get("prefers_scheme", "light")
        self.prefers_motion  = b.get("prefers_motion", "no-preference")
        # Booleans
        self.spoof_os        = b.get("spoof_os", True)
        self.spoof_screen    = b.get("spoof_screen", True)
        self.block_webrtc    = b.get("block_webrtc", True)
        self.spoof_geo       = b.get("spoof_geo", True)
        self.block_notif     = b.get("block_notif", True)
        self.poison_canvas   = b.get("poison_canvas", True)
        self.poison_webgl    = b.get("poison_webgl", True)
        self.block_trackers  = b.get("block_trackers", True)
        self.block_analytics = b.get("block_analytics", True)
        self.block_ads       = b.get("block_ads", True)
        self.strip_utm       = b.get("strip_utm", True)
        self.isolate_storage = b.get("isolate_storage", True)
        self.spoof_rects     = b.get("spoof_rects", True)
        self.spoof_speech    = b.get("spoof_speech", True)
        self.spoof_keyboard  = b.get("spoof_keyboard", True)
        self.clear_plugins   = b.get("clear_plugins", True)
        self.null_opener     = b.get("null_opener", True)
        self.strip_referrer  = b.get("strip_referrer", True)
        self.spoof_history   = b.get("spoof_history", True)
        self.spoof_focus     = b.get("spoof_focus", True)

    def randomise(self, rng: random.Random):
        fp = FingerprintProfile.__new__(FingerprintProfile)
        fp.seed = rng.randint(0, 2**32)
        r = random.Random(fp.seed)
        _, fp.user_agent = r.choice(UA_PRESETS[:5])
        fp.spoofed_ip    = f"192.0.2.{r.randint(1,254)}"
        _, sw, sh        = r.choice(SCREEN_PRESETS)
        fp.screen_w      = sw + r.choice([0,-8,8,-16,16])
        fp.screen_h      = sh + r.choice([0,-6,6,-12,12])
        fp.pixel_ratio   = r.choice([1.0,1.0,1.5,2.0])
        _, fp.gpu_vendor, fp.gpu_renderer = r.choice(GPU_PRESETS[:6])
        fp.geo_lat       = round(51.5074 + r.uniform(-2,2), 4)
        fp.geo_lng       = round(-0.1278 + r.uniform(-3,3), 4)
        fp.timezone      = r.choice(TZ_PRESETS)
        fp.canvas_noise  = r.randint(1,8)
        fp.audio_freq    = round(440.0 + r.uniform(-30,30), 2)
        fp.device_mem    = r.choice([4,8,16])
        fp.cpu_cores     = r.choice([2,4,6,8])
        fp.font_set      = r.choice(list(FONT_POOLS))
        fp.timing_jitter = round(r.uniform(0.5, 2.0), 2)
        fp.prefers_scheme= r.choice(["light","dark"])
        fp.prefers_motion= r.choice(["no-preference","reduce"])
        # All booleans on
        for attr in ["spoof_os","spoof_screen","block_webrtc","spoof_geo","block_notif",
                     "poison_canvas","poison_webgl","block_trackers","block_analytics",
                     "block_ads","strip_utm","isolate_storage","spoof_rects","spoof_speech",
                     "spoof_keyboard","clear_plugins","null_opener","strip_referrer",
                     "spoof_history","spoof_focus"]:
            setattr(fp, attr, True)
        return fp


# ════════════════════════════════════════════════════════════════
#  JS BUILDER  — every fingerprint vector
# ════════════════════════════════════════════════════════════════
def build_privacy_js(fp: FingerprintProfile) -> str:
    ua    = fp.user_agent.replace("\\","\\\\").replace("'","\\'")
    ff    = re.search(r"Firefox/(\d+)", fp.user_agent)
    fv    = ff.group(1) if ff else "138"
    sw,sh = int(fp.screen_w), int(fp.screen_h)
    lat   = float(fp.geo_lat);  lng  = float(fp.geo_lng)
    noise = max(1, min(10, int(fp.canvas_noise)))
    fonts = json.dumps(FONT_POOLS.get(fp.font_set, FONT_POOLS["Linux generic"]))
    gv    = fp.gpu_vendor.replace("'","\\'")
    gr    = fp.gpu_renderer.replace("'","\\'")
    af    = float(fp.audio_freq)
    dm,cc = int(fp.device_mem), int(fp.cpu_cores)
    pr    = float(fp.pixel_ratio)
    tz    = fp.timezone.replace("'","\\'")
    tj    = float(fp.timing_jitter)
    ps    = fp.prefers_scheme.replace("'","\\'")
    pm    = fp.prefers_motion.replace("'","\\'")
    seed  = int(fp.seed) & 0xFFFFFFFF
    strip = json.dumps(TRACKING_PARAMS)

    parts = [f"(function(){{const _SEED={seed};"]

    # ── Seeded PRNG (Mulberry32) ──────────────────────────────────
    parts.append("""
function _prng(s){let x=s^0xdeadbeef;return function(){x=Math.imul(x^x>>>17,0x45d9f3b);x=Math.imul(x^x>>>12,0xb55a4f09);x^=x>>>16;return(x>>>0)/4294967296;};}
const _rng=_prng(_SEED);
""")

    # ── WebRTC ────────────────────────────────────────────────────
    if fp.block_webrtc:
        parts.append("""
const _rtcB=()=>{throw new Error('WebRTC disabled');};
['RTCPeerConnection','webkitRTCPeerConnection','mozRTCPeerConnection','RTCDataChannel'].forEach(k=>{try{window[k]=_rtcB;}catch(e){}});
if(navigator.mediaDevices){
  navigator.mediaDevices.getUserMedia=()=>Promise.reject(new Error('Blocked'));
  navigator.mediaDevices.enumerateDevices=()=>Promise.resolve([]);
}
""")

    # ── UA + userAgentData ────────────────────────────────────────
    if fp.spoof_os:
        parts.append(f"""
const _ua='{ua}',_fv='{fv}';
[['userAgent',_ua],['appVersion','5.0 (X11)'],['platform','Linux x86_64'],['oscpu','Linux x86_64']].forEach(([k,v])=>{{
  try{{Object.defineProperty(navigator,k,{{value:v,writable:false,configurable:false}});}}catch(e){{}}
}});
if(navigator.userAgentData){{
  const _brands=[{{brand:'Not/A)Brand',version:'8'}},{{brand:'Firefox',version:_fv}}];
  const _uad={{brands:_brands,mobile:false,platform:'Linux',
    getHighEntropyValues(h){{
      const m={{platform:'Linux',platformVersion:'6.5.0',architecture:'x86',bitness:'64',
        model:'',mobile:false,brands:_brands,fullVersionList:_brands,uaFullVersion:_fv+'.0',wow64:false}};
      const r={{}};h.forEach(k=>{{if(k in m)r[k]=m[k];}});return Promise.resolve(r);
    }},
    toJSON(){{return{{brands:_brands,mobile:false,platform:'Linux'}};}}
  }};
  try{{Object.defineProperty(navigator,'userAgentData',{{value:_uad,writable:false,configurable:false}});}}catch(e){{}}
}}
// Remove browser-sniffing objects
try{{delete window.chrome;}}catch(e){{}}
try{{Object.defineProperty(window,'chrome',{{get:()=>undefined,configurable:false}});}}catch(e){{}}
try{{delete window.opr;}}catch(e){{}}
// GPC + DNT
try{{Object.defineProperty(navigator,'doNotTrack',{{value:'1',configurable:false}});}}catch(e){{}}
try{{Object.defineProperty(navigator,'globalPrivacyControl',{{value:true,configurable:false}});}}catch(e){{}}
try{{Object.defineProperty(navigator,'pdfViewerEnabled',{{value:false,configurable:false}});}}catch(e){{}}
""")

    # ── Screen + window + matchMedia + CSS media features ─────────
    if fp.spoof_screen:
        parts.append(f"""
const _sw={sw},_sh={sh},_sa={sh}-40,_pr={pr};
[['width',_sw],['height',_sh],['availWidth',_sw],['availHeight',_sa],['colorDepth',24],['pixelDepth',24]].forEach(([p,v])=>{{
  try{{Object.defineProperty(screen,p,{{get:()=>v,configurable:false}});}}catch(e){{}}
}});
try{{Object.defineProperty(window,'outerWidth',{{get:()=>_sw,configurable:false}});}}catch(e){{}}
try{{Object.defineProperty(window,'outerHeight',{{get:()=>_sh,configurable:false}});}}catch(e){{}}
try{{Object.defineProperty(window,'innerWidth',{{get:()=>_sw,configurable:false}});}}catch(e){{}}
try{{Object.defineProperty(window,'innerHeight',{{get:()=>_sh-80,configurable:false}});}}catch(e){{}}
try{{Object.defineProperty(window,'devicePixelRatio',{{get:()=>_pr,configurable:false}});}}catch(e){{}}
// matchMedia — intercept size + preference queries
(function(){{
  const _omm=window.matchMedia.bind(window);
  const _prefs={{'prefers-color-scheme':'{ps}','prefers-reduced-motion':'{pm}',
    'pointer':'fine','hover':'hover','any-pointer':'fine','any-hover':'hover',
    'color-gamut':'srgb','forced-colors':'none','prefers-contrast':'no-preference',
    'prefers-reduced-data':'no-preference','display-mode':'browser'}};
  window.matchMedia=function(q){{
    // Preference queries
    for(const [feat,val] of Object.entries(_prefs)){{
      const m=new RegExp('\\\\('+feat+'(?::\\\\s*([^)]+))?\\\\)','i').exec(q);
      if(m){{
        const matches=m[1]?m[1].trim()===val:true;
        return{{matches,media:q,onchange:null,addListener:()=>{{}},removeListener:()=>{{}},
          addEventListener:()=>{{}},removeEventListener:()=>{{}},dispatchEvent:()=>false}};
      }}
    }}
    // Size queries
    const r=/\\((?:max|min)-(?:device-)?(width|height):\\s*(\\d+)px\\)/i.exec(q);
    if(r){{
      const dim=r[1].toLowerCase()==='height'?_sh:_sw,val=parseInt(r[2]);
      const matches=q.includes('max-')?(dim<=val):(dim>=val);
      return{{matches,media:q,onchange:null,addListener:()=>{{}},removeListener:()=>{{}},
        addEventListener:()=>{{}},removeEventListener:()=>{{}},dispatchEvent:()=>false}};
    }}
    try{{return _omm(q);}}catch(e){{return{{matches:false,media:q,onchange:null,addListener:()=>{{}},removeListener:()=>{{}}}};}}
  }};
}})();
""")

    # ── Timing jitter (performance.now + Date.now) ────────────────
    parts.append(f"""
// Reduce timing precision to defend against side-channel + timing fingerprint
const _tj={tj};
(function(){{
  const _opn=performance.now.bind(performance);
  performance.now=function(){{return Math.floor(_opn()/_tj)*_tj+_rng()*_tj*0.5;}};
  const _odn=Date.now.bind(Date);
  Date.now=function(){{return Math.floor(_odn()/100)*100;}};  // 100ms precision
  // performance.getEntries leaks resource timing — clear it
  if(performance.clearResourceTimings)performance.clearResourceTimings();
  if(performance.clearMarks)performance.clearMarks();
  if(performance.clearMeasures)performance.clearMeasures();
  const _noop=()=>[];
  ['getEntries','getEntriesByName','getEntriesByType'].forEach(m=>{{
    try{{performance[m]=_noop;}}catch(e){{}}
  }});
  // SharedArrayBuffer — timing attack vector
  if(window.SharedArrayBuffer){{
    try{{delete window.SharedArrayBuffer;}}catch(e){{}}
    try{{Object.defineProperty(window,'SharedArrayBuffer',{{get:()=>undefined,configurable:false}});}}catch(e){{}}
  }}
}})();
""")

    # ── Geolocation ───────────────────────────────────────────────
    if fp.spoof_geo:
        parts.append(f"""
if(navigator.geolocation){{
  const _pos={{coords:{{latitude:{lat},longitude:{lng},accuracy:25+_rng()*50,
    altitude:null,altitudeAccuracy:null,heading:null,speed:null}},timestamp:Date.now()}};
  navigator.geolocation.getCurrentPosition=cb=>setTimeout(()=>cb(_pos),80+_rng()*120);
  navigator.geolocation.watchPosition=cb=>{{setTimeout(()=>cb(_pos),80);return 0;}};
  navigator.geolocation.clearWatch=()=>{{}};
}}
""")

    # ── Timezone ──────────────────────────────────────────────────
    parts.append(f"""
try{{
  const _tz='{tz}';
  const _origDTF=Intl.DateTimeFormat;
  Intl.DateTimeFormat=function(locale,opts){{
    opts=Object.assign({{}},opts,{{timeZone:opts&&opts.timeZone?opts.timeZone:_tz}});
    return new _origDTF(locale,opts);
  }};
  Object.assign(Intl.DateTimeFormat,_origDTF);
  const _origRI=Intl.DateTimeFormat.prototype.resolvedOptions;
  Intl.DateTimeFormat.prototype.resolvedOptions=function(){{const r=_origRI.call(this);r.timeZone=_tz;return r;}};
  // Intl locale normalise — prevent locale leakage
  ['NumberFormat','Collator','PluralRules','RelativeTimeFormat'].forEach(cls=>{{
    if(!Intl[cls])return;
    const _oc=Intl[cls];
    Intl[cls]=function(locale,opts){{return new _oc('en-US',opts);}};
    Object.assign(Intl[cls],_oc);
  }});
}}catch(e){{}}
""")

    # ── Notifications ─────────────────────────────────────────────
    if fp.block_notif:
        parts.append("""
window.Notification=class{
  constructor(){throw new Error('Blocked');}
  static requestPermission(){return Promise.resolve('denied');}
  static get permission(){return 'denied';}
};
""")

    # ── Permissions API ───────────────────────────────────────────
    parts.append("""
if(navigator.permissions&&navigator.permissions.query){
  const _opq=navigator.permissions.query.bind(navigator.permissions);
  navigator.permissions.query=function(desc){
    const name=(desc&&desc.name)||'';
    const denied=['geolocation','notifications','camera','microphone',
      'persistent-storage','payment-handler','idle-detection','screen-wake-lock',
      'nfc','bluetooth','accelerometer','gyroscope','magnetometer'];
    if(denied.includes(name))return Promise.resolve({state:'denied',onchange:null});
    return _opq(desc).catch(()=>Promise.resolve({state:'prompt',onchange:null}));
  };
}
""")

    # ── sendBeacon ────────────────────────────────────────────────
    parts.append("if(navigator.sendBeacon){navigator.sendBeacon=function(){return false;};}\n")

    # ── Speech synthesis ──────────────────────────────────────────
    if fp.spoof_speech:
        parts.append("""
try{
  if(window.speechSynthesis){
    const _ogv=window.speechSynthesis.getVoices.bind(window.speechSynthesis);
    window.speechSynthesis.getVoices=function(){return [];};
    window.speechSynthesis.speak=function(){};
    window.speechSynthesis.cancel=function(){};
  }
  if(window.SpeechSynthesisUtterance){
    // Allow construction but suppress actual synthesis
    const _oSSU=window.SpeechSynthesisUtterance;
    window.SpeechSynthesisUtterance=function(t){return new _oSSU(t);};
  }
}catch(e){}
""")

    # ── Keyboard layout ───────────────────────────────────────────
    if fp.spoof_keyboard:
        parts.append("""
try{
  if(navigator.keyboard&&navigator.keyboard.getLayoutMap){
    navigator.keyboard.getLayoutMap=function(){
      // Return a minimal en-US QWERTY layout map
      const m=new Map([['KeyQ','q'],['KeyW','w'],['KeyE','e'],['KeyR','r'],
        ['KeyT','t'],['KeyY','y'],['KeyU','u'],['KeyI','i'],['KeyO','o'],['KeyP','p']]);
      m.size=m.size; return Promise.resolve(m);
    };
  }
}catch(e){}
""")

    # ── Plugins + MimeTypes cleared ───────────────────────────────
    if fp.clear_plugins:
        parts.append("""
try{
  // Plugins list is a fingerprint source — return empty
  Object.defineProperty(navigator,'plugins',{
    get:()=>Object.create(PluginArray.prototype),configurable:false});
  Object.defineProperty(navigator,'mimeTypes',{
    get:()=>Object.create(MimeTypeArray.prototype),configurable:false});
}catch(e){}
""")

    # ── Canvas fingerprint noise ──────────────────────────────────
    if fp.poison_canvas:
        parts.append(f"""
const _cnoise={noise};
const _origTDU=HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL=function(type,q){{
  const ctx=this.getContext('2d');
  if(ctx){{
    for(let i=0;i<_cnoise;i++){{
      ctx.fillStyle='rgba('+Math.floor(_rng()*4)+','+Math.floor(_rng()*4)+','+Math.floor(_rng()*4)+',0.003)';
      ctx.fillRect(Math.floor(_rng()*this.width),Math.floor(_rng()*this.height),1,1);
    }}
  }}
  return _origTDU.call(this,type,q);
}};
const _origGID=CanvasRenderingContext2D.prototype.getImageData;
CanvasRenderingContext2D.prototype.getImageData=function(x,y,w,h){{
  const d=_origGID.call(this,x,y,w,h);
  for(let i=0;i<d.data.length;i+=4){{d.data[i]^=Math.floor(_rng()*_cnoise);}}
  return d;
}};
""")

    # ── Element.getBoundingClientRect — pixel rounding ────────────
    if fp.spoof_rects:
        parts.append("""
// Sub-pixel font metric fingerprinting via getBoundingClientRect / getClientRects
// Round all values to nearest pixel to prevent cross-font identification
(function(){
  const _r=v=>Math.round(v);
  const _wrapDOMRect=r=>{
    if(!r)return r;
    return{top:_r(r.top),bottom:_r(r.bottom),left:_r(r.left),right:_r(r.right),
      width:_r(r.width),height:_r(r.height),x:_r(r.x),y:_r(r.y),
      toJSON:()=>({top:_r(r.top),bottom:_r(r.bottom),left:_r(r.left),right:_r(r.right),
        width:_r(r.width),height:_r(r.height),x:_r(r.x),y:_r(r.y)})};
  };
  const _oBBCR=Element.prototype.getBoundingClientRect;
  Element.prototype.getBoundingClientRect=function(){return _wrapDOMRect(_oBBCR.call(this));};
  const _oGCR=Element.prototype.getClientRects;
  Element.prototype.getClientRects=function(){
    return Array.from(_oGCR.call(this)).map(_wrapDOMRect);
  };
  // Range.getBoundingClientRect
  if(Range&&Range.prototype.getBoundingClientRect){
    const _oRBR=Range.prototype.getBoundingClientRect;
    Range.prototype.getBoundingClientRect=function(){return _wrapDOMRect(_oRBR.call(this));};
  }
  if(Range&&Range.prototype.getClientRects){
    const _oRCR=Range.prototype.getClientRects;
    Range.prototype.getClientRects=function(){return Array.from(_oRCR.call(this)).map(_wrapDOMRect);};
  }
})();
""")

    # ── WebGL GPU spoofing ────────────────────────────────────────
    if fp.poison_webgl:
        parts.append(f"""
[window.WebGLRenderingContext,window.WebGL2RenderingContext].forEach(ctx=>{{
  if(!ctx)return;
  const _ogp=ctx.prototype.getParameter;
  ctx.prototype.getParameter=function(p){{
    if(p===37445)return'{gv}';
    if(p===37446)return'{gr}';
    // Normalise other potentially identifying params
    if(p===7938)return'WebGL 1.0';   // VERSION
    if(p===35724)return'WebGL GLSL ES 1.0'; // SHADING_LANGUAGE_VERSION
    return _ogp.call(this,p);
  }};
  const _oge=ctx.prototype.getExtension;
  ctx.prototype.getExtension=function(name){{
    if(name==='WEBGL_debug_renderer_info')return null;
    return _oge.call(this,name);
  }};
  const _osp=ctx.prototype.getSupportedExtensions;
  ctx.prototype.getSupportedExtensions=function(){{
    return(_osp.call(this)||[]).filter(e=>e!=='WEBGL_debug_renderer_info');
  }};
}});
""")

    # ── Audio fingerprint ─────────────────────────────────────────
    parts.append(f"""
try{{
  const _AudioCtx=window.AudioContext||window.webkitAudioContext;
  if(_AudioCtx){{
    const _origCA=_AudioCtx.prototype.createAnalyser;
    _AudioCtx.prototype.createAnalyser=function(){{
      const n=_origCA.call(this);
      const _ogFF=n.getFloatFrequencyData.bind(n);
      const _ogBF=n.getByteFrequencyData.bind(n);
      const _ogFT=n.getFloatTimeDomainData?n.getFloatTimeDomainData.bind(n):null;
      n.getFloatFrequencyData=arr=>{{_ogFF(arr);for(let i=0;i<arr.length;i++)arr[i]+=(_rng()-0.5)*0.0001;}};
      n.getByteFrequencyData=arr=>{{_ogBF(arr);for(let i=0;i<arr.length;i++)arr[i]=Math.max(0,Math.min(255,arr[i]+Math.floor((_rng()-0.5)*2)));}}
      if(_ogFT)n.getFloatTimeDomainData=arr=>{{_ogFT(arr);for(let i=0;i<arr.length;i++)arr[i]+=(_rng()-0.5)*0.00005;}};
      return n;
    }};
    // OscillatorNode frequency jitter
    const _origCO=_AudioCtx.prototype.createOscillator;
    _AudioCtx.prototype.createOscillator=function(){{
      const o=_origCO.call(this);
      const _osf=o.frequency.setValueAtTime.bind(o.frequency);
      o.frequency.setValueAtTime=function(v,t){{return _osf(v+(_rng()-0.5)*0.01,t);}};
      return o;
    }};
  }}
}}catch(e){{}}
""")

    # ── Font enumeration ──────────────────────────────────────────
    parts.append(f"""
try{{
  const _fonts={fonts};
  if(document.fonts){{
    const _origFC=document.fonts.check.bind(document.fonts);
    document.fonts.check=function(font,text){{
      const fam=(font.match(/['"]([^'"]+)['"])||[,''])[1];
      if(fam&&!_fonts.some(f=>f.toLowerCase()===fam.toLowerCase()))return false;
      return _origFC(font,text);
    }};
    // FontFaceSet.load — return empty for unknown fonts
    const _origFL=document.fonts.load.bind(document.fonts);
    document.fonts.load=function(font,text){{
      const fam=(font.match(/['"]([^'"]+)['"])||[,''])[1];
      if(fam&&!_fonts.some(f=>f.toLowerCase()===fam.toLowerCase()))return Promise.resolve([]);
      return _origFL(font,text);
    }};
  }}
}}catch(e){{}}
""")

    # ── Hardware / navigator props ────────────────────────────────
    parts.append(f"""
[['language','en-US'],['languages',['en-US','en']],['deviceMemory',{dm}],
 ['hardwareConcurrency',{cc}],['cookieEnabled',true],['onLine',true]].forEach(([k,v])=>{{
  try{{Object.defineProperty(navigator,k,{{value:v,writable:false,configurable:false}});}}catch(e){{}}
}});
if(navigator.getBattery)navigator.getBattery=()=>Promise.resolve({{level:0.75,charging:true,chargingTime:0,dischargingTime:Infinity}});
try{{Object.defineProperty(navigator,'connection',{{
  value:{{effectiveType:'4g',rtt:50,downlink:10,saveData:false,type:'wifi',downlinkMax:Infinity}},
  writable:false,configurable:false}});}}catch(e){{}}
try{{Object.defineProperty(navigator,'maxTouchPoints',{{value:0,writable:false,configurable:false}});}}catch(e){{}}
""")

    # ── window.name clear on navigation (cross-site tracker) ──────
    if fp.null_opener:
        parts.append("""
// window.name persists across navigations and is used for cross-site tracking
try{window.name='';}catch(e){}
// window.opener leaks origin of the tab that opened this one
try{if(window.opener)window.opener=null;}catch(e){}
// document.domain hardening
try{Object.defineProperty(document,'domain',{get:()=>location.hostname,configurable:false});}catch(e){}
""")

    # ── Referrer stripping ────────────────────────────────────────
    if fp.strip_referrer:
        parts.append("""
// Spoof document.referrer to empty for cross-origin loads
try{
  const _curOrigin=location.origin;
  const _origRef=Object.getOwnPropertyDescriptor(Document.prototype,'referrer')
    ||Object.getOwnPropertyDescriptor(document,'referrer');
  if(_origRef){
    Object.defineProperty(document,'referrer',{
      get:function(){
        const r=_origRef.get?_origRef.get.call(document):_origRef.value||'';
        // Only return referrer if same-origin
        try{if(new URL(r).origin===_curOrigin)return r;}catch(e){}
        return '';
      },configurable:false
    });
  }
}catch(e){}
""")

    # ── history.length hardened ───────────────────────────────────
    if fp.spoof_history:
        parts.append("""
try{Object.defineProperty(history,'length',{get:()=>1,configurable:false});}catch(e){}
""")

    # ── document.hasFocus / visibilityState ───────────────────────
    if fp.spoof_focus:
        parts.append("""
try{document.hasFocus=function(){return true;};}catch(e){}
try{Object.defineProperty(document,'visibilityState',{get:()=>'visible',configurable:false});}catch(e){}
try{Object.defineProperty(document,'hidden',{get:()=>false,configurable:false});}catch(e){}
""")

    # ── Storage isolation (tab namespace wrapper) ─────────────────
    if fp.isolate_storage:
        parts.append(f"""
// Wrap localStorage/sessionStorage with a per-tab namespace so tabs
// can't read each other's storage even on the same origin
(function(){{
  const _ns='_sf_{seed}_';
  function _wrap(store){{
    return new Proxy(store,{{
      get(t,k){{
        if(k==='getItem')return n=>t.getItem(_ns+n);
        if(k==='setItem')return(n,v)=>t.setItem(_ns+n,v);
        if(k==='removeItem')return n=>t.removeItem(_ns+n);
        if(k==='key')return i=>{{const keys=Object.keys(t).filter(k=>k.startsWith(_ns));return keys[i]?keys[i].slice(_ns.length):null;}};
        if(k==='length')return Object.keys(t).filter(k=>k.startsWith(_ns)).length;
        if(k==='clear')return()=>Object.keys(t).filter(k=>k.startsWith(_ns)).forEach(k=>t.removeItem(k));
        if(typeof t[k]==='function')return t[k].bind(t);
        return t[k];
      }},
      set(t,k,v){{t[k]=v;return true;}}
    }});
  }}
  try{{Object.defineProperty(window,'localStorage',{{get:()=>_wrap(window.localStorage.__proto__!==Storage.prototype?localStorage:localStorage),configurable:false}});}}catch(e){{}}
}})();
""")

    # ── UTM / tracking param stripping ───────────────────────────
    if fp.strip_utm:
        parts.append(f"""
// Strip tracking parameters from the current URL and intercept link clicks
(function(){{
  const _params={strip};
  function _strip(url){{
    try{{
      const u=new URL(url,location.href);
      let changed=false;
      _params.forEach(p=>{{if(u.searchParams.has(p)){{u.searchParams.delete(p);changed=true;}}}});
      return changed?u.toString():url;
    }}catch(e){{return url;}}
  }}
  // Strip from current URL silently
  try{{
    const clean=_strip(location.href);
    if(clean!==location.href)history.replaceState(null,'',clean);
  }}catch(e){{}}
  // Intercept future navigations via link clicks
  document.addEventListener('click',function(e){{
    const a=e.target.closest('a[href]');
    if(!a)return;
    const cleaned=_strip(a.href);
    if(cleaned!==a.href){{a.href=cleaned;}}
  }},true);
  // Intercept fetch + XHR to strip tracking params from API calls
  const _origFetch=window.fetch;
  window.fetch=function(input,init){{
    if(typeof input==='string')input=_strip(input);
    else if(input instanceof Request){{
      const c=_strip(input.url);
      if(c!==input.url)input=new Request(c,input);
    }}
    return _origFetch.call(this,input,init);
  }};
}}
)();
""")

    # ── Tracker globals ───────────────────────────────────────────
    if fp.block_trackers or fp.block_analytics:
        parts.append("""
['_gaq','ga','gtag','__gaTracker','_paq','fbq','mixpanel','_fbq','dataLayer',
 '_hsq','heap','amplitude','AnalyticsWebInterface','_ym_uid','Klaviyo',
 'FS','_loq','hj','_hjSettings','intercomSettings','Intercom',
 'twttr','twq','snaptr','ttq','pintrk','criteo_q'].forEach(t=>{
  try{delete window[t];Object.defineProperty(window,t,{get:()=>undefined,set:()=>{},configurable:false});}catch(e){}
});
""")

    parts.append(f"console.log('[SWORDFISH v16.6] Active — seed:{seed} tz:{tz} geo:{lat:.3f},{lng:.3f}');\n}})();")
    return "\n".join(parts)


# ════════════════════════════════════════════════════════════════
#  BLOCKLIST
# ════════════════════════════════════════════════════════════════
BLOCKLIST_URL = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"

class BlocklistManager:
    _BUILTIN = {
        "doubleclick.net","google-analytics.com","facebook.com","fb.com",
        "connect.facebook.net","googleadservices.com","googlesyndication.com",
        "pagead2.googlesyndication.com","ads.google.com","adclick.g.doubleclick.net",
        "advertising.com","hotjar.com","clarity.ms","segment.io","segment.com",
        "mixpanel.com","amplitude.com","fullstory.com","logrocket.io",
        "mouseflow.com","inspectlet.com","quantserve.com","scorecardresearch.com",
        "outbrain.com","taboola.com","pubmatic.com","rubiconproject.com",
        "openx.net","appnexus.com","criteo.com","adsrvr.org","moatads.com",
        "adsafeprotected.com","2mdn.net","admob.com","googletagmanager.com",
        "googletagservices.com","analytics.google.com","stats.g.doubleclick.net",
        "dc.services.visualstudio.com","browser.sentry-cdn.com","api.mixpanel.com",
        "static.ads-twitter.com","analytics.twitter.com","ads.twitter.com",
        "tiktokv.com","ads.tiktok.com","analytics.tiktok.com",
        "snap.licdn.com","ads.linkedin.com","px.ads.linkedin.com",
        "ib.adnxs.com","secure.adnxs.com","ads.yahoo.com",
    }

    def __init__(self):
        self._lock=threading.Lock(); self._hosts=set(self._BUILTIN)
        self._custom=set(); self._removed=set(); self._load()

    def _load(self):
        if BLOCKLIST_PATH.exists():
            try:
                d=json.loads(BLOCKLIST_PATH.read_text())
                self._hosts.update(d.get("hosts",[])); self._custom.update(d.get("custom",[]))
                self._removed.update(d.get("removed",[])); self._hosts-=self._removed
            except Exception: pass

    def save(self):
        try: BLOCKLIST_PATH.write_text(json.dumps({"hosts":list(self._hosts),"custom":list(self._custom),"removed":list(self._removed)},indent=2))
        except Exception: pass

    def blocked_domains(self):
        with self._lock: return frozenset(self._hosts)

    def add(self,d):
        d=d.strip().lstrip(".")
        with self._lock: self._hosts.add(d); self._custom.add(d); self._removed.discard(d)
        self.save()

    def remove(self,d):
        with self._lock: self._hosts.discard(d); self._removed.add(d)
        self.save()

    def count(self):
        with self._lock: return len(self._hosts)

    def load_from_url(self,url,progress_fn=None):
        added=0
        try:
            req=urllib.request.urlopen(url,timeout=30); new_hosts=set(); total=0
            for raw in req:
                line=raw.decode("utf-8","replace").strip()
                if line.startswith("#") or not line: continue
                parts=line.split()
                if len(parts)>=2 and parts[0] in ("0.0.0.0","127.0.0.1"):
                    h=parts[1].lower()
                    if h not in ("localhost","broadcasthost","0.0.0.0","127.0.0.1","::1"):
                        new_hosts.add(h)
                total+=1
                if progress_fn and total%5000==0: progress_fn(total)
            with self._lock:
                before=len(self._hosts); self._hosts.update(new_hosts-self._removed); added=len(self._hosts)-before
            self.save()
        except Exception as e:
            if progress_fn: progress_fn(-1,str(e))
        return added

BLOCKLIST = BlocklistManager()


# ════════════════════════════════════════════════════════════════
#  DEFAULT SETTINGS
# ════════════════════════════════════════════════════════════════
DEFAULT_SETTINGS = {
    "spoof_os":True,"user_agent":_LINUX_UA,
    "spoof_ip":True,"spoofed_ip_value":"192.0.2.1",
    "block_webrtc":True,"spoof_geo":True,"block_notif":True,
    "block_trackers":True,"block_analytics":True,"block_ads":True,
    "poison_canvas":True,"poison_webgl":True,"canvas_noise":3,
    "spoof_screen":True,"screen_w":1920,"screen_h":1080,"pixel_ratio":1.0,
    "gpu_vendor":"Generic GPU (Linux)","gpu_renderer":"Mesa 23.1 on llvmpipe",
    "geo_lat":51.5074,"geo_lng":-0.1278,"timezone":"Europe/London",
    "audio_freq":440.0,"device_mem":8,"cpu_cores":4,"font_set":"Linux generic",
    "timing_jitter":1.0,"prefers_scheme":"light","prefers_motion":"no-preference",
    "tab_isolation":False,"show_net":True,"show_log":True,
    "strip_utm":True,"isolate_storage":True,"spoof_rects":True,
    "spoof_speech":True,"spoof_keyboard":True,"clear_plugins":True,
    "null_opener":True,"strip_referrer":True,"spoof_history":True,"spoof_focus":True,
}

def settings_to_fp(s):
    return FingerprintProfile(base=s)


# ════════════════════════════════════════════════════════════════
#  THEME
# ════════════════════════════════════════════════════════════════
THEME = """
* { font-family: Tahoma, "Segoe UI", Arial, sans-serif; font-size: 11px; color: #000; }
QMainWindow, QWidget { background: #d4d0c8; }
QDialog { background: #d4d0c8; }
QScrollArea { background: #d4d0c8; border: none; }
QGroupBox { border: 1px solid #909090; margin-top: 8px; padding: 4px; background: #d4d0c8; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; background: #d4d0c8; font-weight: bold; }
QWidget#toolbar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #eeeade,stop:0.45 #d8d4c8,stop:0.46 #c4c0b4,stop:1 #b8b4a8); border-bottom:2px solid #808080; padding:2px 4px; }
QPushButton#navbtn { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #f0ede4,stop:1 #c8c4b8); border-top:1px solid #fff;border-left:1px solid #fff;border-right:1px solid #606060;border-bottom:1px solid #606060; border-radius:3px;padding:3px 8px;min-width:28px;min-height:22px;font-weight:bold;font-size:12px; }
QPushButton#navbtn:pressed { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #b0aca0,stop:1 #d0ccc0); border-top:1px solid #606060;border-left:1px solid #606060; }
QPushButton#isolbtn_on  { background:#316ac5;color:#fff;font-weight:bold;border:2px solid #1a4a9c;border-radius:3px;padding:3px 8px;min-height:22px; }
QPushButton#isolbtn_off { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #f0ede4,stop:1 #c8c4b8);border-top:1px solid #fff;border-left:1px solid #fff;border-right:1px solid #606060;border-bottom:1px solid #606060;border-radius:3px;padding:3px 8px;min-height:22px; }
QPushButton { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #f0ede4,stop:1 #c8c4b8); border-top:1px solid #fff;border-left:1px solid #fff;border-right:1px solid #606060;border-bottom:1px solid #606060; border-radius:2px;padding:3px 10px;min-height:20px; }
QPushButton:hover { border-color:#316ac5 #1a4a9c #1a4a9c #316ac5; }
QPushButton:pressed { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #b0aca0,stop:1 #d0ccc0); border-top:1px solid #606060;border-left:1px solid #606060; }
QPushButton:disabled { color:#909090; }
QLineEdit#urlbar { background:#fff;color:#000080;border-top:2px solid #808080;border-left:2px solid #808080;border-right:2px solid #d4d0c8;border-bottom:2px solid #d4d0c8;padding:2px 6px;font-size:12px; }
QLineEdit { background:#fff;color:#000;border-top:2px solid #808080;border-left:2px solid #808080;border-right:2px solid #d4d0c8;border-bottom:2px solid #d4d0c8;padding:2px 4px; }
QLineEdit:focus { border-top:2px solid #316ac5;border-left:2px solid #316ac5; }
QComboBox { background:#fff;color:#000;border-top:2px solid #808080;border-left:2px solid #808080;border-right:2px solid #d4d0c8;border-bottom:2px solid #d4d0c8;padding:2px 4px; }
QComboBox QAbstractItemView { background:#fff;selection-background-color:#316ac5;selection-color:#fff; }
QSpinBox,QDoubleSpinBox { background:#fff;color:#000;border-top:2px solid #808080;border-left:2px solid #808080;border-right:2px solid #d4d0c8;border-bottom:2px solid #d4d0c8;padding:2px 4px; }
QTabWidget#pagetabs::pane { border:2px solid #808080;border-top:none;background:#fff; }
QTabBar#pagetabbar::tab { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #c8c4b8,stop:1 #b0aca0); color:#444;border:1px solid #808080;border-bottom:none;padding:3px 14px 4px;margin-right:2px;border-top-left-radius:4px;border-top-right-radius:4px;min-width:80px;max-width:220px; }
QTabBar#pagetabbar::tab:selected { background:#d4d0c8;color:#000;font-weight:bold; }
QListWidget#trafficlog { background:#e8e0c8;color:#1a1a1a;border-top:2px solid #808080;border-left:2px solid #808080;border-right:2px solid #d4d0c8;border-bottom:2px solid #d4d0c8;font-family:"Courier New",Courier,monospace;font-size:10px; }
QListWidget#trafficlog::item { padding:0 2px;border-bottom:1px solid #d4c890; }
QListWidget#trafficlog::item:selected { background:#316ac5;color:#fff; }
QTableWidget { background:#fff;color:#000;border-top:2px solid #808080;border-left:2px solid #808080;border-right:2px solid #d4d0c8;border-bottom:2px solid #d4d0c8;gridline-color:#d0ccc0;alternate-background-color:#f0eee8;selection-background-color:#316ac5;selection-color:#fff; }
QHeaderView::section { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #e8e4dc,stop:1 #ccc8bc);color:#000;border:none;border-right:1px solid #909090;border-bottom:2px solid #808080;padding:3px 6px;font-weight:bold; }
QWidget#statsbar { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #d4d0c8,stop:1 #c0bcb0);border-top:2px solid #808080;padding:1px 6px; }
QLabel#statslabel { color:#000;font-family:"Courier New",Courier,monospace;font-size:10px; }
QLabel#blockedlabel { color:#880000;font-family:"Courier New",Courier,monospace;font-size:10px;font-weight:bold; }
QLabel#iplabel { color:#004000;font-family:"Courier New",Courier,monospace;font-size:10px; }
QCheckBox { color:#000;spacing:5px; }
QCheckBox::indicator { width:13px;height:13px;border-top:2px solid #808080;border-left:2px solid #808080;border-right:2px solid #d4d0c8;border-bottom:2px solid #d4d0c8;background:#fff; }
QCheckBox::indicator:checked { background:#316ac5; }
QSlider::groove:horizontal { height:4px;background:#c0bcb0;border:1px solid #808080; }
QSlider::handle:horizontal { background:#316ac5;border:1px solid #1a4a9c;width:12px;margin:-4px 0;border-radius:6px; }
QProgressBar { border:1px solid #808080;background:#fff;text-align:center; }
QProgressBar::chunk { background:#316ac5; }
QScrollBar:vertical { background:#d4d0c8;width:16px;border:1px solid #808080; }
QScrollBar::handle:vertical { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #e8e4dc,stop:1 #b8b4a8);border-top:1px solid #fff;border-left:1px solid #fff;border-right:1px solid #606060;border-bottom:1px solid #606060;min-height:20px; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #e8e4dc,stop:1 #c8c4b8);border:1px solid #808080;height:16px;subcontrol-origin:margin; }
"""


# ════════════════════════════════════════════════════════════════
#  BANDWIDTH GRAPH
# ════════════════════════════════════════════════════════════════
class BandwidthGraph(QFrame):
    def __init__(self):
        super().__init__(); self.setFixedSize(240,46); self.data=[0.0]*150
        self.setStyleSheet("background:#e8e0c8;border-top:1px solid #808080;border-left:1px solid #808080;border-right:1px solid #d4d0c8;border-bottom:1px solid #d4d0c8;")
    def add_data(self,v): self.data.append(float(v));self.data.pop(0);self.update()
    def paintEvent(self,_):
        from PyQt6.QtGui import QPolygonF,QLinearGradient,QBrush
        from PyQt6.QtCore import QPointF
        p=QPainter(self);w,h=self.width(),self.height()
        p.fillRect(0,0,w,h,QColor(0xe8,0xe0,0xc8))
        p.setPen(QPen(QColor(0x80,0x80,0x80),1));p.drawRect(0,0,w-1,h-1)
        p.setPen(QPen(QColor(0xd4,0xc8,0x90),1))
        for i in range(0,w,40):p.drawLine(i,0,i,h)
        for i in range(0,h,20):p.drawLine(0,i,w,i)
        rec=self.data[-8:];mv=max(max(rec),2.0)*1.15;n=len(self.data)
        pts=[QPointF(0.0,float(h))]
        for i,v in enumerate(self.data):pts.append(QPointF(i*(w/max(n-1,1)),h-12-(v/mv)*(h-22)))
        pts.append(QPointF(float(w),float(h)))
        g=QLinearGradient(0,0,0,h);g.setColorAt(0.0,QColor(0,120,0,120));g.setColorAt(1.0,QColor(0,120,0,20))
        p.setPen(QPen(Qt.PenStyle.NoPen));p.setBrush(QBrush(g));p.drawPolygon(QPolygonF(pts))
        p.setPen(QPen(QColor(0,122,0),2))
        for i in range(n-1):
            x1=i*(w/max(n-1,1));x2=(i+1)*(w/max(n-1,1))
            y1=h-12-(self.data[i]/mv)*(h-22);y2=h-12-(self.data[i+1]/mv)*(h-22)
            p.drawLine(int(x1),int(y1),int(x2),int(y2))
        p.setPen(QPen(QColor(0,0,0),1));p.setFont(QFont("Courier New",8))
        p.drawText(4,11,f"Now:{self.data[-1]:.1f}KB/s");p.drawText(4,h-3,f"Pk:{max(self.data):.0f}KB/s")


# ════════════════════════════════════════════════════════════════
#  INTERCEPTOR
# ════════════════════════════════════════════════════════════════
class URLInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self,log_fn,blocked_fn):
        super().__init__(); self.log=log_fn; self.on_blocked=blocked_fn
        self.spoofed_ip="192.0.2.1"; self.spoof_enabled=True; self.extra_blocked=set()

    def interceptRequest(self,info):
        url=info.requestUrl().toString(); host=info.requestUrl().host().lower()
        self.log(f"[REQUEST] {url[:120]}")
        bl=BLOCKLIST.blocked_domains()|self.extra_blocked
        if host in bl or any(host.endswith("."+b) for b in bl) or any(b in url.lower() for b in bl):
            self.log(f"[BLOCKED] {host}"); self.on_blocked(host,url); info.block(True); return
        if self.spoof_enabled:
            try:
                ip_b=self.spoofed_ip.encode()
                for h in [b"X-Forwarded-For",b"Client-IP",b"X-Real-IP",b"CF-Connecting-IP",b"True-Client-IP"]:
                    info.setHttpHeader(h,ip_b)
                info.setHttpHeader(b"Accept-Language",b"en-US,en;q=0.9")
            except Exception: pass
        self.log(f"[ALLOW] {host}")


# ════════════════════════════════════════════════════════════════
#  CUSTOM PAGE
# ════════════════════════════════════════════════════════════════
class SwordfishPage(QWebEnginePage):
    def javaScriptConsoleMessage(self,*a): pass
    def __init__(self,profile,parent=None):
        super().__init__(profile,parent)
        try: self.permissionRequested.connect(lambda p:p.deny())
        except AttributeError: pass
    def featurePermissionRequested(self,url,feature):
        try: self.setFeaturePermission(url,feature,QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)
        except Exception: pass
    def createWindow(self,_):
        view=QWebEngineView(); page=SwordfishPage(self.profile(),view); view.setPage(page)
        v=self.view()
        if v:
            mw=v.window()
            if hasattr(mw,"_adopt_tab"): mw._adopt_tab(view)
        return page


# ════════════════════════════════════════════════════════════════
#  TRAFFIC LOG
# ════════════════════════════════════════════════════════════════
class TrafficLog(QListWidget):
    open_url=pyqtSignal(str); block_host=pyqtSignal(str)
    def __init__(self):
        super().__init__(); self.setObjectName("trafficlog"); self.setFixedHeight(100); self.setUniformItemSizes(True)
        self._t=QTimer(); self._t.setSingleShot(True); self._t.timeout.connect(self._go)
        self._n=0; self._it=None; self.itemClicked.connect(self._click)
    def _click(self,i): self._it=i;self._n+=1;self._t.stop();self._t.start(350)
    def _go(self):
        n,it=self._n,self._it;self._n=0;self._it=None
        if not it: return
        t=it.text()
        if n>=3:
            m=re.search(r"\[(?:REQUEST|ALLOW|BLOCKED)\]\s+(\S+)",t)
            if m: self.block_host.emit(re.sub(r"^https?://","",m.group(1)).split("/")[0])
        elif n==2:
            m=re.search(r"(https?://\S+)",t)
            if m: self.open_url.emit(m.group(1))


# ════════════════════════════════════════════════════════════════
#  TAB INFO
# ════════════════════════════════════════════════════════════════
class TabInfo:
    def __init__(self,view,fp,isolated): self.view=view;self.fp=fp;self.isolated=isolated


# ════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ════════════════════════════════════════════════════════════════
class Swordfish(QMainWindow):
    log_signal=pyqtSignal(str)

    def __init__(self):
        super().__init__(); self.setWindowTitle("Swordfish - Privacy Browser"); self.resize(1500,960)
        try:
            ip=os.path.join(os.path.dirname(os.path.abspath(__file__)),"download.png")
            if os.path.exists(ip): self.setWindowIcon(QIcon(ip))
        except Exception: pass
        self.settings=self._load_settings(); self.blocked_log=[]; self.fake_cookies=[]
        self._tab_info={}; self._iso_rng=random.Random()
        self.profile=QWebEngineProfile()
        self.profile.setHttpUserAgent(self.settings["user_agent"])
        self.profile.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled,True)
        self.interceptor=URLInterceptor(self.log_signal.emit,self._on_blocked)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        self._global_fp=settings_to_fp(self.settings)
        self._inject_script(self.profile,build_privacy_js(self._global_fp))
        self.log_signal.connect(self._on_log)
        self.total_bytes=self.tick_bytes=self.blocked_count=0
        self._build_ui()
        self.timer=QTimer(); self.timer.timeout.connect(self._tick); self.timer.start(1000)
        threading.Thread(target=self._detect_ip,daemon=True).start()
        self.new_tab()

    def _load_settings(self):
        if SETTINGS_PATH.exists():
            try: s=json.loads(SETTINGS_PATH.read_text()); m=dict(DEFAULT_SETTINGS); m.update(s); return m
            except Exception: pass
        return dict(DEFAULT_SETTINGS)

    def _save_settings(self):
        try: SETTINGS_PATH.write_text(json.dumps(self.settings,indent=2))
        except Exception: pass

    def _inject_script(self,profile,js):
        scripts=profile.scripts()
        for sc in scripts.toList():
            if sc.name()=="swordfish_privacy": scripts.remove(sc)
        sc=QWebEngineScript(); sc.setName("swordfish_privacy"); sc.setSourceCode(js)
        sc.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        sc.setWorldId(0); scripts.insert(sc)

    def _on_blocked(self,host,url): self.blocked_log.append((host,url))

    def _build_ui(self):
        root=QVBoxLayout(); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        tb=QWidget(); tb.setObjectName("toolbar"); tb.setFixedHeight(40)
        tl=QHBoxLayout(tb); tl.setContentsMargins(4,3,4,3); tl.setSpacing(3)
        for attr,lbl,slot in [("btn_back","◄",self._nav_back),("btn_forward","►",self._nav_forward),("btn_reload","↺",self._nav_reload)]:
            b=QPushButton(lbl); b.setObjectName("navbtn"); b.setFixedSize(28,26); b.clicked.connect(slot); setattr(self,attr,b); tl.addWidget(b)
        tl.addSpacing(4)
        self.url_bar=QLineEdit(); self.url_bar.setObjectName("urlbar"); self.url_bar.setPlaceholderText("Enter address or search…")
        self.url_bar.returnPressed.connect(self.navigate); tl.addWidget(self.url_bar,1); tl.addSpacing(4)
        self.btn_iso=QPushButton("⬡ Isolation: OFF"); self.btn_iso.setObjectName("isolbtn_off")
        self.btn_iso.setFixedHeight(26); self.btn_iso.clicked.connect(self._toggle_iso); tl.addWidget(self.btn_iso); tl.addSpacing(4)
        for lbl,slot in [("Home",lambda:self.navigate_to("https://duckduckgo.com")),
                          ("New Tab",self.new_tab),("Cookies",self.show_cookies),
                          ("Trackers",self.show_trackers),("Blocklist",self.show_blocklist),
                          ("DevTools",self._open_devtools),("Settings",self.show_settings)]:
            b=QPushButton(lbl); b.setFixedHeight(24); b.clicked.connect(slot); tl.addWidget(b)
        root.addWidget(tb)
        sep=QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setFixedHeight(2); sep.setStyleSheet("background:#808080;"); root.addWidget(sep)
        self.tabs=QTabWidget(); self.tabs.setObjectName("pagetabs"); self.tabs.tabBar().setObjectName("pagetabbar")
        self.tabs.setTabsClosable(True); self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed); root.addWidget(self.tabs,1)
        self.stats_widget=QWidget(); self.stats_widget.setObjectName("statsbar"); self.stats_widget.setFixedHeight(52)
        sl=QHBoxLayout(self.stats_widget); sl.setContentsMargins(6,2,6,2); sl.setSpacing(8)
        self.stats_label=QLabel("0.00 MB | 0 KB/s"); self.stats_label.setObjectName("statslabel")
        self.blocked_label=QLabel("Blocked:0"); self.blocked_label.setObjectName("blockedlabel")
        self.ip_label=QLabel("Detecting…"); self.ip_label.setObjectName("iplabel")
        self.fp_label=QLabel("FP:global"); self.fp_label.setObjectName("statslabel")
        def _vs(): f=QFrame();f.setFrameShape(QFrame.Shape.VLine);f.setStyleSheet("color:#909090;");return f
        lsi=QLabel("IP:"); lsi.setObjectName("statslabel")
        self.ip_edit=QLineEdit(self.settings["spoofed_ip_value"]); self.ip_edit.setFixedWidth(110)
        self.ip_edit.setStyleSheet("font-family:'Courier New';font-size:10px;padding:1px 4px;border-top:1px solid #808080;border-left:1px solid #808080;border-right:1px solid #d4d0c8;border-bottom:1px solid #d4d0c8;")
        bai=QPushButton("Apply"); bai.setFixedSize(42,22); bai.setStyleSheet("font-size:9px;padding:0;")
        bai.clicked.connect(self._apply_ip); self.ip_edit.returnPressed.connect(self._apply_ip)
        self.chk_ip=QCheckBox("Spoof"); self.chk_ip.setChecked(True); self.chk_ip.setStyleSheet("font-size:10px;")
        self.chk_ip.stateChanged.connect(lambda s:(setattr(self.interceptor,'spoof_enabled',bool(s)),self.ip_edit.setEnabled(bool(s))))
        self.bw=BandwidthGraph()
        for w in [self.stats_label,_vs(),self.blocked_label,_vs(),self.ip_label,_vs(),self.fp_label,_vs(),lsi,self.ip_edit,bai,self.chk_ip]:
            sl.addWidget(w)
        sl.addStretch(); sl.addWidget(self.bw); root.addWidget(self.stats_widget)
        lh=QWidget(); lh.setFixedHeight(18); lh.setStyleSheet("background:#c0bcb0;border-top:1px solid #808080;")
        lhl=QHBoxLayout(lh); lhl.setContentsMargins(6,0,6,0)
        ll=QLabel("Traffic  [dbl=open · triple=block]"); ll.setStyleSheet("font-size:10px;font-weight:bold;color:#1a1a1a;")
        bc=QPushButton("Clear"); bc.setFixedSize(40,16); bc.setStyleSheet("font-size:9px;padding:0;")
        lhl.addWidget(ll); lhl.addStretch(); lhl.addWidget(bc)
        self.traffic_log=TrafficLog(); self.traffic_log.open_url.connect(self._open_url_tab)
        self.traffic_log.block_host.connect(self._block_from_log); bc.clicked.connect(self.traffic_log.clear)
        self.log_widget=QWidget(); lw=QVBoxLayout(self.log_widget); lw.setContentsMargins(0,0,0,0); lw.setSpacing(0)
        lw.addWidget(lh); lw.addWidget(self.traffic_log); root.addWidget(self.log_widget)
        self.stats_widget.setVisible(self.settings.get("show_net",True))
        self.log_widget.setVisible(self.settings.get("show_log",True))
        c=QWidget(); c.setLayout(root); self.setCentralWidget(c)

    def _toggle_iso(self):
        self.settings["tab_isolation"]=not self.settings.get("tab_isolation",False)
        on=self.settings["tab_isolation"]
        self.btn_iso.setObjectName("isolbtn_on" if on else "isolbtn_off")
        self.btn_iso.setText("Isolation: ON" if on else "Isolation: OFF")
        self.btn_iso.style().unpolish(self.btn_iso); self.btn_iso.style().polish(self.btn_iso)
        self.log_signal.emit(f"[ISOLATION] {'ON — new tabs randomised' if on else 'OFF — shared profile'}")

    def new_tab(self,url=None):
        url=url or "https://duckduckgo.com"
        iso=self.settings.get("tab_isolation",False)
        if iso:
            fp=FingerprintProfile().randomise(self._iso_rng)
            pro=QWebEngineProfile(); pro.setHttpUserAgent(fp.user_agent)
            pro.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled,True)
            pro.setUrlRequestInterceptor(self.interceptor)
            self._inject_script(pro,build_privacy_js(fp))
        else:
            fp=self._global_fp; pro=self.profile
        view=QWebEngineView(); page=SwordfishPage(pro,view); view.setPage(page); view.load(QUrl(url))
        view.urlChanged.connect(lambda u,v=view:self._on_url_changed(u,v))
        view.titleChanged.connect(lambda t,v=view:self._on_title_changed(t,v))
        idx=self.tabs.addTab(view,"New Tab")
        if iso:
            self.tabs.tabBar().setTabToolTip(idx,
                f"ISOLATED\nSeed:{fp.seed&0xFFFF:04X}\nUA:{fp.user_agent[:35]}\n"
                f"Screen:{fp.screen_w}×{fp.screen_h}\nGPU:{fp.gpu_renderer[:28]}\n"
                f"IP:{fp.spoofed_ip}\nGeo:{fp.geo_lat:.3f},{fp.geo_lng:.3f}\n"
                f"TZ:{fp.timezone}\nCanvas noise:{fp.canvas_noise}\nAudio:{fp.audio_freq:.1f}Hz")
        self._tab_info[id(view)]=TabInfo(view,fp,iso); self.tabs.setCurrentIndex(idx)

    def _adopt_tab(self,view):
        view.urlChanged.connect(lambda u,v=view:self._on_url_changed(u,v))
        view.titleChanged.connect(lambda t,v=view:self._on_title_changed(t,v))
        idx=self.tabs.addTab(view,"New Tab"); self.tabs.setCurrentIndex(idx)
        if id(view) not in self._tab_info: self._tab_info[id(view)]=TabInfo(view,self._global_fp,False)

    def _open_url_tab(self,url):
        if not url.startswith(("http://","https://")): url="https://"+url
        self.new_tab(url)

    def _block_from_log(self,host):
        if host: BLOCKLIST.add(host); self.interceptor.extra_blocked.add(host); self.log_signal.emit(f"[BLOCKED MANUAL] {host}")

    def _open_devtools(self):
        cur=self.tabs.currentWidget()
        if not cur: return
        dev=QWebEngineView(); dev.setWindowTitle("DevTools"); dev.resize(1100,650)
        cur.page().setDevToolsPage(dev.page()); dev.show(); self._devtools=dev

    def _on_url_changed(self,url,view):
        if view is self.tabs.currentWidget(): self.url_bar.setText(url.toString()); self._upd_fp()

    def _on_title_changed(self,title,view):
        idx=self.tabs.indexOf(view)
        if idx>=0: self.tabs.setTabText(idx,(title[:18]+"…") if len(title)>20 else (title or "New Tab"))

    def _close_tab(self,idx):
        if self.tabs.count()>1:
            v=self.tabs.widget(idx)
            if v and id(v) in self._tab_info: del self._tab_info[id(v)]
            self.tabs.removeTab(idx)

    def _on_tab_changed(self,idx):
        v=self.tabs.widget(idx)
        if v: self.url_bar.setText(v.url().toString()); self._upd_fp()

    def _upd_fp(self):
        cur=self.tabs.currentWidget()
        if not cur: return
        info=self._tab_info.get(id(cur))
        if info and info.isolated:
            self.fp_label.setText(f"FP:iso {info.fp.seed&0xFFFF:04X}"); self.fp_label.setStyleSheet("color:#004080;font-family:'Courier New';font-size:10px;font-weight:bold;")
        else:
            self.fp_label.setText("FP:global"); self.fp_label.setStyleSheet("color:#000;font-family:'Courier New';font-size:10px;")

    def navigate(self):
        url=self.url_bar.text().strip()
        if not url: return
        if not url.startswith(("http://","https://")): url="https://"+url
        cur=self.tabs.currentWidget()
        if cur: cur.load(QUrl(url))

    def navigate_to(self,url): self.url_bar.setText(url); cur=self.tabs.currentWidget(); cur and cur.load(QUrl(url))
    def _nav_back(self): c=self.tabs.currentWidget(); c and c.back()
    def _nav_forward(self): c=self.tabs.currentWidget(); c and c.forward()
    def _nav_reload(self): c=self.tabs.currentWidget(); c and c.reload()

    def _on_log(self,msg):
        ts=datetime.now().strftime("%H:%M:%S"); item=QListWidgetItem(f"[{ts}] {msg}")
        if "[BLOCKED" in msg: item.setForeground(QColor("#880000")); self.blocked_count+=1; self.blocked_label.setText(f"Blocked:{self.blocked_count}")
        elif "[ALLOW]" in msg: item.setForeground(QColor("#005000"))
        elif "[REQUEST]" in msg: item.setForeground(QColor("#1a1a1a"))
        elif "[ISOLATION]" in msg: item.setForeground(QColor("#004080"))
        else: item.setForeground(QColor("#2a3a7a"))
        self.traffic_log.addItem(item)
        if self.traffic_log.count()>1000: self.traffic_log.takeItem(0)
        self.traffic_log.scrollToBottom(); self.tick_bytes+=1500

    def _tick(self):
        kb=self.tick_bytes/1024; self.stats_label.setText(f"{self.total_bytes/1e6:.2f}MB|{kb:.1f}KB/s")
        self.bw.add_data(kb); self.total_bytes+=self.tick_bytes; self.tick_bytes=0

    def _apply_ip(self):
        r=self.ip_edit.text().strip()
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",r):
            self.interceptor.spoofed_ip=r; self.settings["spoofed_ip_value"]=r; self.ip_label.setText(f"Spoof→{r}")

    def _detect_ip(self):
        try:
            r=urllib.request.urlopen("https://api.ipify.org?format=json",timeout=5)
            ip=json.loads(r.read()).get("ip","?")
            self.ip_label.setText(f"Real:{ip}"); self.ip_label.setStyleSheet("color:#004000;font-family:'Courier New';font-size:10px;")
        except: self.ip_label.setText("Real:?")

    # ── Tracker panel ────────────────────────────────────────────
    def show_trackers(self):
        dlg=QDialog(self); dlg.setWindowTitle("Blocked Trackers"); dlg.resize(820,500)
        lay=QVBoxLayout(dlg); lay.addWidget(QLabel(f"<b>{len(self.blocked_log)} blocks this session</b>"))
        tbl=QTableWidget(len(self.blocked_log),2); tbl.setHorizontalHeaderLabels(["Host","URL"])
        tbl.horizontalHeader().setStretchLastSection(True); tbl.setAlternatingRowColors(True)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        for i,(h,u) in enumerate(self.blocked_log): tbl.setItem(i,0,QTableWidgetItem(h)); tbl.setItem(i,1,QTableWidgetItem(u[:100]))
        lay.addWidget(tbl); br=QHBoxLayout()
        bc=QPushButton("Clear"); bc.clicked.connect(lambda:(self.blocked_log.clear(),dlg.close()))
        bx=QPushButton("Close"); bx.clicked.connect(dlg.close)
        br.addWidget(bc); br.addWidget(bx); lay.addLayout(br); dlg.exec()

    # ── Blocklist panel ──────────────────────────────────────────
    def show_blocklist(self):
        dlg=QDialog(self); dlg.setWindowTitle("Blocklist Manager"); dlg.resize(860,580)
        lay=QVBoxLayout(dlg)
        self._bl_st=QLabel(f"Domains: {BLOCKLIST.count()}"); self._bl_st.setStyleSheet("font-weight:bold;color:#004000;"); lay.addWidget(self._bl_st)
        dlr=QHBoxLayout(); ue=QLineEdit(BLOCKLIST_URL); ue.setMinimumWidth(440)
        bd=QPushButton("⬇ Download Steven Black / Pi-hole list"); self._bl_pr=QProgressBar(); self._bl_pr.setVisible(False); self._bl_pr.setRange(0,0)
        dlr.addWidget(QLabel("URL:")); dlr.addWidget(ue); dlr.addWidget(bd); lay.addLayout(dlr); lay.addWidget(self._bl_pr)
        def _dl():
            bd.setEnabled(False); self._bl_pr.setVisible(True); url=ue.text().strip()
            def _w():
                def _p(n,e=None):
                    if e: self.log_signal.emit(f"[BLOCKLIST] Error:{e}")
                    else: self.log_signal.emit(f"[BLOCKLIST] Parsed {n}…")
                added=BLOCKLIST.load_from_url(url,_p)
                self.log_signal.emit(f"[BLOCKLIST] +{added} domains, total {BLOCKLIST.count()}")
                self._bl_st.setText(f"Domains:{BLOCKLIST.count()}"); bd.setEnabled(True); self._bl_pr.setVisible(False); _ref()
            threading.Thread(target=_w,daemon=True).start()
        bd.clicked.connect(_dl)
        se=QLineEdit(); se.setPlaceholderText("Filter…"); lay.addWidget(se)
        lst=QListWidget(); lst.setFont(QFont("Courier New",9)); lay.addWidget(lst)
        _all=[]
        def _ref():
            nonlocal _all; _all=sorted(BLOCKLIST.blocked_domains()); _filt()
        def _filt(): q=se.text().lower(); lst.clear(); [lst.addItem(d) for d in _all if q in d]; lst.scrollToTop()
        se.textChanged.connect(_filt); _ref()
        ar=QHBoxLayout(); ae=QLineEdit(); ae.setPlaceholderText("domain.com")
        ba=QPushButton("Add"); br2=QPushButton("Remove Selected")
        ar.addWidget(ae); ar.addWidget(ba); ar.addWidget(br2); lay.addLayout(ar)
        def _add(): d=ae.text().strip(); d and (BLOCKLIST.add(d),ae.clear(),_ref(),self._bl_st.setText(f"Domains:{BLOCKLIST.count()}"))
        def _rem(): [BLOCKLIST.remove(i.text()) for i in lst.selectedItems()]; _ref(); self._bl_st.setText(f"Domains:{BLOCKLIST.count()}")
        ba.clicked.connect(_add); br2.clicked.connect(_rem)
        bx=QPushButton("Close"); bx.clicked.connect(dlg.close); lay.addWidget(bx); dlg.exec()

    # ── Cookie manager ───────────────────────────────────────────
    def show_cookies(self):
        dlg=QDialog(self); dlg.setWindowTitle("Cookie Manager"); dlg.resize(920,620)
        out=QVBoxLayout(dlg); tabs=QTabWidget(); out.addWidget(tabs)
        store=self.profile.cookieStore()
        # Real cookies tab
        rw=QWidget(); rl=QVBoxLayout(rw)
        rl.addWidget(QLabel("Real cookies. Edit Value/Path inline — changes apply live."))
        rt=QTableWidget(0,6); rt.setHorizontalHeaderLabels(["Domain","Name","Value","Path","Expires","Sec"])
        rt.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        rt.setAlternatingRowColors(True); rt.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        rl.addWidget(rt); _co=[]; _seen=set(); _done=[False]; _ld=[True]
        def _ba(v):
            if isinstance(v,(bytes,bytearray)): return v.decode("utf-8","replace")
            if hasattr(v,"toStdString"): return v.toStdString()
            try:
                if hasattr(v,"__len__") and not isinstance(v,str): return bytes(v).decode("utf-8","replace")
            except: pass
            return str(v)
        def _add(c):
            if _done[0]: return
            try:
                key=(c.domain(),_ba(c.name()))
                if key in _seen: return
                _seen.add(key); row=rt.rowCount(); rt.insertRow(row)
                exp=c.expirationDate().toString("yyyy-MM-dd") if c.expirationDate().isValid() else "session"
                for col,txt in enumerate([c.domain(),_ba(c.name()),_ba(c.value()),c.path(),exp,"✔" if c.isSecure() else ""]):
                    it=QTableWidgetItem(txt)
                    if col not in (2,3): it.setFlags(it.flags()&~Qt.ItemFlag.ItemIsEditable)
                    rt.setItem(row,col,it)
                _co.append(c)
            except: pass
        _conn=store.cookieAdded.connect(_add); store.loadAllCookies()
        QTimer.singleShot(700,lambda:_done.__setitem__(0,True)); QTimer.singleShot(750,lambda:_ld.__setitem__(0,False))
        def _chg(row,col):
            if _ld[0] or row>=len(_co): return
            orig=_co[row]; store.deleteCookie(orig)
            nc=QNetworkCookie(orig.name(),rt.item(row,col).text().encode() if col==2 else orig.value())
            nc.setDomain(orig.domain()); nc.setPath(rt.item(row,3).text() if col==3 else orig.path())
            nc.setSecure(orig.isSecure()); nc.setHttpOnly(orig.isHttpOnly())
            if orig.expirationDate().isValid(): nc.setExpirationDate(orig.expirationDate())
            store.setCookie(nc); _co[row]=nc
        rt.cellChanged.connect(_chg)
        def _del():
            rows=sorted(set(i.row() for i in rt.selectedItems()),reverse=True)
            for r in rows:
                if r<len(_co): store.deleteCookie(_co.pop(r))
                rt.removeRow(r)
        rb=QHBoxLayout()
        for lbl,fn in [("Delete Sel",_del),("Clear ALL",lambda:(store.deleteAllCookies(),_seen.clear(),_co.clear(),rt.setRowCount(0))),
                        ("Refresh",lambda:(_done.__setitem__(0,False),_ld.__setitem__(0,True),_seen.clear(),_co.clear(),rt.setRowCount(0),store.loadAllCookies(),QTimer.singleShot(700,lambda:_done.__setitem__(0,True)),QTimer.singleShot(750,lambda:_ld.__setitem__(0,False))))]:
            b=QPushButton(lbl); b.clicked.connect(fn); rb.addWidget(b)
        rl.addLayout(rb); tabs.addTab(rw,"Real Cookies")
        # Inject tab
        iw=QWidget(); il=QVBoxLayout(iw); il.addWidget(QLabel("Inject a cookie into the browser store."))
        fm=QFormLayout(); fd=QLineEdit(".example.com"); fn2=QLineEdit("session_id"); fv=QLineEdit("abc123"); fp2=QLineEdit("/"); fs=QCheckBox("Secure"); fh=QCheckBox("HttpOnly")
        for lb,w in [("Domain:",fd),("Name:",fn2),("Value:",fv),("Path:",fp2)]: fm.addRow(lb,w)
        fm.addRow("",fs); fm.addRow("",fh); il.addLayout(fm)
        ft=QTableWidget(0,5); ft.setHorizontalHeaderLabels(["Domain","Name","Value","Path","Flags"])
        ft.horizontalHeader().setStretchLastSection(True); ft.setAlternatingRowColors(True)
        ft.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        il.addWidget(QLabel("Injected:")); il.addWidget(ft)
        def _inj():
            d=fd.text().strip(); n=fn2.text().strip(); v=fv.text(); p=fp2.text() or "/"
            if not d or not n: return
            nc=QNetworkCookie(n.encode(),v.encode()); nc.setDomain(d); nc.setPath(p); nc.setSecure(fs.isChecked()); nc.setHttpOnly(fh.isChecked())
            store.setCookie(nc); self.fake_cookies.append({"domain":d,"name":n,"value":v})
            row=ft.rowCount(); ft.insertRow(row); flags=("S" if fs.isChecked() else "")+("H" if fh.isChecked() else "")
            for col,txt in enumerate([d,n,v,p,flags]): ft.setItem(row,col,QTableWidgetItem(txt))
            self.log_signal.emit(f"[COOKIE] Injected! {n} on {d}")
        def _dinj():
            rows=sorted(set(i.row() for i in ft.selectedItems()),reverse=True)
            for r in rows:
                if r<len(self.fake_cookies):
                    c=self.fake_cookies.pop(r); nc=QNetworkCookie(c["name"].encode(),c["value"].encode()); nc.setDomain(c["domain"]); store.deleteCookie(nc)
                ft.removeRow(r)
        ib=QHBoxLayout(); bi=QPushButton("✚ Inject"); bi.clicked.connect(_inj); bd2=QPushButton("Delete Sel"); bd2.clicked.connect(_dinj)
        ib.addWidget(bi); ib.addWidget(bd2); il.addLayout(ib); tabs.addTab(iw,"Inject Cookies")
        bx=QPushButton("Close"); bx.clicked.connect(dlg.close); out.addWidget(bx); dlg.exec()

    # ── Settings / Fingerprint Editor ────────────────────────────
    def show_settings(self):
        s=self.settings; dlg=QDialog(self); dlg.setWindowTitle("Fingerprint Editor — v16.6"); dlg.resize(740,860)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); inner=QWidget(); lay=QFormLayout(inner)
        lay.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        scroll.setWidget(inner); outer=QVBoxLayout(dlg); outer.addWidget(scroll)
        def _s(t): lay.addRow(QLabel("")); lay.addRow(QLabel(f"── {t}"))

        lay.addRow(QLabel("Swordfish Settings"))
        _s("TAB ISOLATION")
        chk_iso=QCheckBox("Randomise all fingerprint values per new tab"); chk_iso.setChecked(s.get("tab_isolation",False)); lay.addRow("Isolation",chk_iso)

        _s("USER-AGENT & OS")
        chk_os=QCheckBox("Spoof UA/OS to Linux?"); chk_os.setChecked(s["spoof_os"]); lay.addRow("OS Spoof",chk_os)
        ua_cb=QComboBox(); [ua_cb.addItem(l) for l,_ in UA_PRESETS]; idx_ua=len(UA_PRESETS)-1
        for i,(_,v) in enumerate(UA_PRESETS):
            if v==s["user_agent"]: idx_ua=i; break
        ua_cb.setCurrentIndex(idx_ua); ua_txt=QLineEdit(s["user_agent"]); ua_txt.setMinimumWidth(460)
        def _uap(i): _,v=UA_PRESETS[i]; ua_txt.setText(v) if v else None; ua_txt.setEnabled(not v)
        ua_cb.currentIndexChanged.connect(_uap); _uap(idx_ua); lay.addRow("UA Preset",ua_cb); lay.addRow("User-Agent",ua_txt)

        _s("SCREEN & WINDOW"); chk_scr=QCheckBox("Spoof screen/window/matchMedia?"); chk_scr.setChecked(s["spoof_screen"]); lay.addRow("Screen",chk_scr)
        sc_cb=QComboBox(); [sc_cb.addItem(l) for l,_,_ in SCREEN_PRESETS]; idx_s=0
        for i,(_,sw,sh) in enumerate(SCREEN_PRESETS):
            if sw==s["screen_w"] and sh==s["screen_h"]: idx_s=i; break
        sc_cb.setCurrentIndex(idx_s); sw_sp=QSpinBox(); sw_sp.setRange(800,7680); sw_sp.setValue(s["screen_w"])
        sh_sp=QSpinBox(); sh_sp.setRange(600,4320); sh_sp.setValue(s["screen_h"])
        def _scp(i): _,sw2,sh2=SCREEN_PRESETS[i]; sw_sp.setValue(sw2); sh_sp.setValue(sh2)
        sc_cb.currentIndexChanged.connect(_scp); lay.addRow("Preset",sc_cb)
        wh=QWidget(); whl=QHBoxLayout(wh); whl.setContentsMargins(0,0,0,0)
        whl.addWidget(QLabel("W:")); whl.addWidget(sw_sp); whl.addWidget(QLabel("H:")); whl.addWidget(sh_sp); whl.addStretch()
        lay.addRow("W×H",wh)
        dpr=QDoubleSpinBox(); dpr.setRange(0.5,4.0); dpr.setSingleStep(0.25); dpr.setValue(s.get("pixel_ratio",1.0)); lay.addRow("DPR",dpr)

        _s("TIMING & SIDE-CHANNEL")
        tj_sp=QDoubleSpinBox(); tj_sp.setRange(0.1,10.0); tj_sp.setSingleStep(0.1); tj_sp.setValue(s.get("timing_jitter",1.0)); tj_sp.setSuffix(" ms")
        lay.addRow("performance.now jitter",tj_sp); lay.addRow(QLabel("Reduces timing precision — defends against side-channel attacks"))

        _s("GPU / WEBGL"); chk_wgl=QCheckBox("Spoof WebGL GPU"); chk_wgl.setChecked(s["poison_webgl"]); lay.addRow("WebGL",chk_wgl)
        gp_cb=QComboBox(); [gp_cb.addItem(l) for l,_,_ in GPU_PRESETS]
        gv_txt=QLineEdit(s.get("gpu_vendor","")); gv_txt.setMinimumWidth(340)
        gr_txt=QLineEdit(s.get("gpu_renderer","")); gr_txt.setMinimumWidth(340)
        def _gpp(i): _,v,r=GPU_PRESETS[i]; (gv_txt.setText(v),gr_txt.setText(r),gv_txt.setEnabled(False),gr_txt.setEnabled(False)) if v else (gv_txt.setEnabled(True),gr_txt.setEnabled(True))
        idx_g=len(GPU_PRESETS)-1
        for i,(_,v,_) in enumerate(GPU_PRESETS):
            if v==s.get("gpu_vendor",""): idx_g=i; break
        gp_cb.setCurrentIndex(idx_g); gp_cb.currentIndexChanged.connect(_gpp); _gpp(idx_g)
        lay.addRow("GPU Preset",gp_cb); lay.addRow("Vendor",gv_txt); lay.addRow("Renderer",gr_txt)

        _s("CANVAS"); chk_cv=QCheckBox("Poison canvas"); chk_cv.setChecked(s["poison_canvas"]); lay.addRow("Canvas",chk_cv)
        n_sl=QSlider(Qt.Orientation.Horizontal); n_sl.setRange(1,10); n_sl.setValue(s.get("canvas_noise",3))
        n_lb=QLabel(f"Intensity:{n_sl.value()}/10"); n_sl.valueChanged.connect(lambda v:n_lb.setText(f"Intensity:{v}/10")); lay.addRow(n_lb,n_sl)
        chk_rct=QCheckBox("Round getBoundingClientRect (font metric FP)"); chk_rct.setChecked(s.get("spoof_rects",True)); lay.addRow("Rect rounding",chk_rct)

        _s("AUDIO"); af_sp=QDoubleSpinBox(); af_sp.setRange(20,20000); af_sp.setSingleStep(1); af_sp.setValue(s.get("audio_freq",440)); af_sp.setSuffix(" Hz"); lay.addRow("Audio probe freq",af_sp)

        _s("GEOLOCATION"); chk_geo=QCheckBox("Spoof location"); chk_geo.setChecked(s["spoof_geo"]); lay.addRow("Geo",chk_geo)
        ge_cb=QComboBox(); [ge_cb.addItem(l) for l,_,_ in GEO_PRESETS]
        la_sp=QDoubleSpinBox(); la_sp.setRange(-90,90); la_sp.setDecimals(4); la_sp.setValue(s.get("geo_lat",51.5074))
        lo_sp=QDoubleSpinBox(); lo_sp.setRange(-180,180); lo_sp.setDecimals(4); lo_sp.setValue(s.get("geo_lng",-0.1278))
        def _gep(i): _,la,lo=GEO_PRESETS[i]; i<len(GEO_PRESETS)-1 and (la_sp.setValue(la),lo_sp.setValue(lo))
        ge_cb.currentIndexChanged.connect(_gep); lay.addRow("Preset",ge_cb)
        ll=QWidget(); lll=QHBoxLayout(ll); lll.setContentsMargins(0,0,0,0)
        lll.addWidget(QLabel("Lat:")); lll.addWidget(la_sp); lll.addWidget(QLabel("Lng:")); lll.addWidget(lo_sp); lll.addStretch(); lay.addRow("Coords",ll)

        _s("TIMEZONE"); tz_cb=QComboBox(); [tz_cb.addItem(t) for t in TZ_PRESETS]
        ct=s.get("timezone","Europe/London"); tz_cb.setCurrentIndex(TZ_PRESETS.index(ct) if ct in TZ_PRESETS else 0); lay.addRow("Timezone",tz_cb)

        _s("FONTS"); fo_cb=QComboBox(); [fo_cb.addItem(k) for k in FONT_POOLS]
        fs2=s.get("font_set","Linux generic"); fo_cb.setCurrentIndex(list(FONT_POOLS).index(fs2) if fs2 in FONT_POOLS else 0); lay.addRow("Font set",fo_cb)

        _s("HARDWARE"); mem_cb=QComboBox(); [mem_cb.addItem(f"{m} GB",m) for m in [2,4,8,16,32]]
        mem_cb.setCurrentIndex([2,4,8,16,32].index(s.get("device_mem",8)) if s.get("device_mem",8) in [2,4,8,16,32] else 2); lay.addRow("Device Memory",mem_cb)
        cpu_cb=QComboBox(); cvs=[1,2,4,6,8,12,16]; [cpu_cb.addItem(f"{c} cores",c) for c in cvs]
        cpu_cb.setCurrentIndex(cvs.index(s.get("cpu_cores",4)) if s.get("cpu_cores",4) in cvs else 2); lay.addRow("CPU cores",cpu_cb)

        _s("CSS MEDIA FEATURES")
        sch_cb=QComboBox(); sch_cb.addItems(["light","dark"])
        sch_cb.setCurrentIndex(0 if s.get("prefers_scheme","light")=="light" else 1); lay.addRow("prefers-color-scheme",sch_cb)
        mot_cb=QComboBox(); mot_cb.addItems(["no-preference","reduce"])
        mot_cb.setCurrentIndex(0 if s.get("prefers_motion","no-preference")=="no-preference" else 1); lay.addRow("prefers-reduced-motion",mot_cb)

        _s("ADVANCED PRIVACY")
        chk_sp=QCheckBox("Clear speech synthesis voices"); chk_sp.setChecked(s.get("spoof_speech",True)); lay.addRow("Speech",chk_sp)
        chk_kb=QCheckBox("Spoof keyboard layout map"); chk_kb.setChecked(s.get("spoof_keyboard",True)); lay.addRow("Keyboard",chk_kb)
        chk_pl=QCheckBox("Clear plugin / MimeType lists"); chk_pl.setChecked(s.get("clear_plugins",True)); lay.addRow("Plugins",chk_pl)
        chk_op=QCheckBox("Null window.opener + clear window.name"); chk_op.setChecked(s.get("null_opener",True)); lay.addRow("Opener/Name",chk_op)
        chk_rf=QCheckBox("Strip cross-origin referrer"); chk_rf.setChecked(s.get("strip_referrer",True)); lay.addRow("Referrer",chk_rf)
        chk_hi=QCheckBox("Spoof history.length to 1"); chk_hi.setChecked(s.get("spoof_history",True)); lay.addRow("History",chk_hi)
        chk_fc=QCheckBox("Always report document as focused/visible"); chk_fc.setChecked(s.get("spoof_focus",True)); lay.addRow("Focus/Visibility",chk_fc)
        chk_ut=QCheckBox("Strip UTM / tracking URL parameters"); chk_ut.setChecked(s.get("strip_utm",True)); lay.addRow("UTM stripping",chk_ut)
        chk_st=QCheckBox("Partition localStorage/sessionStorage per tab (isolation mode)"); chk_st.setChecked(s.get("isolate_storage",True)); lay.addRow("Storage isolation",chk_st)
        chk_rtc=QCheckBox("Block WebRTC"); chk_rtc.setChecked(s["block_webrtc"]); lay.addRow("WebRTC",chk_rtc)
        chk_nt=QCheckBox("Block Notifications"); chk_nt.setChecked(s["block_notif"]); lay.addRow("Notifications",chk_nt)
        chk_tr=QCheckBox("Block Trackers"); chk_tr.setChecked(s["block_trackers"]); lay.addRow("Trackers",chk_tr)
        chk_an=QCheckBox("Block Analytics"); chk_an.setChecked(s["block_analytics"]); lay.addRow("Analytics",chk_an)
        chk_ad=QCheckBox("Block Ads"); chk_ad.setChecked(s["block_ads"]); lay.addRow("Ads",chk_ad)

        _s("IP"); chk_ip=QCheckBox("Send spoofed IP headers"); chk_ip.setChecked(s["spoof_ip"]); lay.addRow("IP Spoof",chk_ip)
        ip_ed=QLineEdit(s["spoofed_ip_value"]); lay.addRow("Spoof IP",ip_ed)

        _s("DISPLAY"); chk_net=QCheckBox("Network bar"); chk_net.setChecked(s.get("show_net",True)); lay.addRow("Net bar",chk_net)
        chk_log=QCheckBox("Traffic log"); chk_log.setChecked(s.get("show_log",True)); lay.addRow("Log",chk_log)
        lay.addRow(QLabel(""))

        def _collect():
            if ua_cb.currentIndex()==len(UA_PRESETS)-1 or ua_txt.isEnabled(): chosen_ua=ua_txt.text().strip() or _LINUX_UA
            else: _,chosen_ua=UA_PRESETS[ua_cb.currentIndex()]
            _,gv,gr=GPU_PRESETS[gp_cb.currentIndex()]
            if not gv: gv=gv_txt.text(); gr=gr_txt.text()
            return {
                "tab_isolation":chk_iso.isChecked(),"spoof_os":chk_os.isChecked(),"user_agent":chosen_ua,
                "spoof_screen":chk_scr.isChecked(),"screen_w":max(800,sw_sp.value()),"screen_h":max(600,sh_sp.value()),"pixel_ratio":dpr.value(),
                "timing_jitter":tj_sp.value(),
                "poison_webgl":chk_wgl.isChecked(),"gpu_vendor":gv,"gpu_renderer":gr,
                "poison_canvas":chk_cv.isChecked(),"canvas_noise":n_sl.value(),"spoof_rects":chk_rct.isChecked(),
                "audio_freq":af_sp.value(),
                "spoof_geo":chk_geo.isChecked(),"geo_lat":la_sp.value(),"geo_lng":lo_sp.value(),
                "timezone":tz_cb.currentText(),"font_set":fo_cb.currentText(),
                "device_mem":mem_cb.currentData(),"cpu_cores":cpu_cb.currentData(),
                "prefers_scheme":sch_cb.currentText(),"prefers_motion":mot_cb.currentText(),
                "spoof_speech":chk_sp.isChecked(),"spoof_keyboard":chk_kb.isChecked(),"clear_plugins":chk_pl.isChecked(),
                "null_opener":chk_op.isChecked(),"strip_referrer":chk_rf.isChecked(),
                "spoof_history":chk_hi.isChecked(),"spoof_focus":chk_fc.isChecked(),
                "strip_utm":chk_ut.isChecked(),"isolate_storage":chk_st.isChecked(),
                "block_webrtc":chk_rtc.isChecked(),"block_notif":chk_nt.isChecked(),
                "block_trackers":chk_tr.isChecked(),"block_analytics":chk_an.isChecked(),"block_ads":chk_ad.isChecked(),
                "spoof_ip":chk_ip.isChecked(),"spoofed_ip_value":ip_ed.text().strip(),
                "show_net":chk_net.isChecked(),"show_log":chk_log.isChecked(),
            }
        br=QHBoxLayout()
        bs=QPushButton("Save"); bs.clicked.connect(lambda:(self._apply_settings(_collect()),dlg.close()))
        brs=QPushButton("Reset"); brs.clicked.connect(lambda:(dlg.close(),self._apply_settings(dict(DEFAULT_SETTINGS)),self.show_settings()))
        bc=QPushButton("Cancel"); bc.clicked.connect(dlg.close)
        for b in [bs,brs,bc]: br.addWidget(b)
        outer.addLayout(br); dlg.exec()

    def _apply_settings(self,ns):
        self.settings.update(ns); s=self.settings
        self._global_fp=settings_to_fp(s); js=build_privacy_js(self._global_fp)
        self._inject_script(self.profile,js); self.profile.setHttpUserAgent(s["user_agent"])
        self.interceptor.spoof_enabled=s["spoof_ip"]
        ip=s.get("spoofed_ip_value","").strip()
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",ip): self.interceptor.spoofed_ip=ip; self.ip_edit.setText(ip)
        self.chk_ip.blockSignals(True); self.chk_ip.setChecked(s["spoof_ip"]); self.chk_ip.blockSignals(False); self.ip_edit.setEnabled(s["spoof_ip"])
        self.stats_widget.setVisible(s.get("show_net",True)); self.log_widget.setVisible(s.get("show_log",True))
        on=s.get("tab_isolation",False); self.btn_iso.setObjectName("isolbtn_on" if on else "isolbtn_off")
        self.btn_iso.setText(" Tab Isolation: ON" if on else " Tab Isolation: OFF")
        self.btn_iso.style().unpolish(self.btn_iso); self.btn_iso.style().polish(self.btn_iso)
        self._save_settings()
        self.log_signal.emit(f"[SETTINGS] Applied v16.6 — {len(DEFAULT_SETTINGS)} fingerprint parameters active")

    def closeEvent(self,e):
        self.profile.clearHttpCache(); self.profile.cookieStore().deleteAllCookies()
        BLOCKLIST.save(); self._save_settings(); print("[Swordfish] EXIT"); e.accept()


def main():
    import contextlib
    app=QApplication(sys.argv); app.setApplicationName("Swordfish"); app.setStyleSheet(THEME)
    with open(os.devnull,"w") as f:
        with contextlib.redirect_stderr(f):
            win=Swordfish(); win.show(); sys.exit(app.exec())

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""
True 3D Sound-Reactive Volumetric Smoke - ModernGL
CLEAN SHADER - Each function defined EXACTLY ONCE
"""

import moderngl
import numpy as np
import librosa
from pathlib import Path
import zlib
import subprocess
import shutil
import struct

AUDIO_PATH = r"C:\Users\clint\Desktop\LET_EM_WONDER_MOW.mp3"
OUTPUT_DIR = Path(r"C:\Users\clint\Desktop\SMOKE_4D_RENDER")
WIDTH, HEIGHT, FPS, CRF = 1920, 1080, 30, 18

# ============================================================
# CLEAN SHADER - EACH FUNCTION DEFINED EXACTLY ONCE
# ============================================================

RAYMARCH_VERTEX = """
#version 330
in vec2 in_pos; in vec2 in_uv; out vec2 v_uv;
void main() { v_uv = in_uv; gl_Position = vec4(in_pos, 0.0, 1.0); }
"""

SMOKE_FRAGMENT = """#version 330
uniform float u_time; uniform vec2 u_resolution;
uniform float u_audio_rms; uniform float u_audio_bass; uniform float u_audio_mid; uniform float u_audio_treble;
uniform int u_beat; uniform int u_onset;
uniform float u_chroma_0; uniform float u_chroma_1; uniform float u_chroma_2; uniform float u_chroma_3;
in vec2 v_uv; out vec4 f_color;

// === ALL FUNCTIONS DEFINED EXACTLY ONCE ===
vec3 H33(vec3 p){ p=fract(p*.1031); p*=p+33.33; p*=p+p.yzx; return fract((p.xxy+p.yxx)*p.zyx); }
float NSE(vec3 p){ vec3 i=floor(p); vec3 w=fract(p); w=w*w*(3.-2.*w);
vec3 a=H33(i),b=H33(i+vec3(1,0,0)),c=H33(i+vec3(0,1,0)),d=H33(i+vec3(1,1,0));
vec3 e=H33(i+vec3(0,0,1)),f=H33(i+vec3(1,0,1)),g=H33(i+vec3(0,1,1)),h=H33(i+vec3(1,1,1));
return mix(mix(mix(a.x,b.x,w.x),mix(c.x,d.x,w.x),w.y),mix(mix(e.x,f.x,w.x),mix(g.x,h.x,w.x),w.y),w.z); }
float FBM(vec3 p,int oct){ float v=0.,a=.5,f=1.; for(int i=0;i<oct;i++){v+=a*NSE(p*f);f*=2.;a*=.5;} return v; }

mat4 R4D(float a,int pl){ mat4 r=mat4(1.); float c=cos(a),s=sin(a);
if(pl==0){r[0][0]=c;r[0][1]=-s;r[1][0]=s;r[1][1]=c;}
else if(pl==1){r[0][0]=c;r[0][2]=-s;r[2][0]=s;r[2][2]=c;}
else if(pl==2){r[0][0]=c;r[0][3]=-s;r[3][0]=s;r[3][3]=c;}
else if(pl==3){r[1][1]=c;r[1][2]=-s;r[2][1]=s;r[2][2]=c;}
else if(pl==4){r[1][1]=c;r[1][3]=-s;r[3][1]=s;r[3][3]=c;}
else{r[2][2]=c;r[2][3]=-s;r[3][2]=s;r[3][3]=c;} return r; }
vec3 PRJ4D(vec4 p){ float s=1./(1.-p.w); return p.xyz*s; }

float SMKDEN(vec3 p,float t,float bass,float mid,float treble,float rms,int beat){
    vec4 p4=vec4(p,sin(t*.3+bass));
    mat4 r=R4D(t*.15+mid*.3,2)*R4D(t*.12+treble*.2,5)*R4D(t*.1+bass*.2,1)*R4D(t*.08,4);
    vec3 q=PRJ4D(r*vec4(p,sin(t*.3+bass)));
    
    float d=0.;
    d+=FBM(q*(.8+bass*.5)+vec3(t*.05,t*.03,t*.02),5)*.5;
    d+=FBM(q*(2.+mid*2.)+vec3(t*.15,-t*.1,t*.07),4)*.3;
    d+=FBM(q*(5.+treble*5.)+vec3(t*.3,t*.2,t*.15),3)*.2;
    
    vec3 CRL=normalize(cross(vec3(NSE(q*2.+t*.1),NSE(q*2.+t*.1+1.),NSE(q*2.+t*.1+2.)),vec3(0.,1.,0.)));
    d+=FBM(q*3.+CRL*.5+t*.2,3)*.15;
    
    if(beat>0) d*=1.5;
    
    if(u_onset>0){
        vec3 TD=normalize(vec3(sin(t*5.),cos(t*3.),sin(t*7.)));
        float TDRIL=1.-smoothstep(0.,.3,abs(dot(q,TD))-length(q)*.7);
        d+=TDRIL*.8*u_audio_treble;
    }
    return max(0.,d);
}

vec3 GETNRM(vec3 p){ vec2 e=vec2(.005,0.); float d=SMKDEN(p,u_time,u_audio_bass,u_audio_mid,u_audio_treble,u_audio_rms,u_beat);
return normalize(vec3(SMKDEN(p+vec3(e.x,0,0),u_time,u_audio_bass,u_audio_mid,u_audio_treble,u_audio_rms,u_beat)-d,
SMKDEN(p+vec3(0,e.x,0),u_time,u_audio_bass,u_audio_mid,u_audio_treble,u_audio_rms,u_beat)-d,
SMKDEN(p+vec3(0,0,e.x),u_time,u_audio_bass,u_audio_mid,u_audio_treble,u_audio_rms,u_beat)-d)/e.x); }

vec3 HSV2RGB(vec3 c){ vec4 K=vec4(1.,2./3.,1./3.,3.); vec3 p=abs(fract(c.xxx+K.xyz)*6.-K.www); return c.z*mix(K.xxx,clamp(p-K.xxx,0.,1.),c.y); }

vec3 GETSMKCOL(vec3 p,float d,float t,float bass,float mid,float treble,float rms,int beat,int onset){
    float hue=atan(p.z,p.x)*.159+t*.08+bass*.6+mid*.3+treble*.2+p.y*.2;
    if(u_beat>0)hue+=.25; if(u_onset>0)hue+=.35;
    hue+=u_chroma_0*.2+u_chroma_1*.1+u_chroma_2*.05+u_chroma_3*.03;
    float sat=.6+.4*d, val=d*(.3+.7*u_audio_rms);
    if(u_beat>0){val=min(1.,val+.4);sat=min(1.,sat+.3);}
    if(u_onset>0){val=min(1.,val+.5);sat=min(1.,sat+.4);}
    hue=fract(hue+.55); return HSV2RGB(vec3(hue,sat,val)); }

void main(){
 vec2 uv=(gl_FragCoord.xy-.5*u_resolution)/min(u_resolution.x,u_resolution.y); uv+=v_uv*sin(u_time*.001)*.001;
 vec3 ro=vec3(0.,0.,4.); vec3 rd=normalize(vec3(uv,-1.5));
 float ca=cos(u_time*.08+u_audio_mid*.3),sa=sin(u_time*.08+u_audio_mid*.3); ro.xz*=mat2(ca,-sa,sa,ca); rd.xz*=mat2(ca,-sa,sa,ca);
 ro.y+=sin(u_time*.05)*.5+u_audio_bass*.5;
 if(u_beat>0){ ro+=vec3(sin(u_time*80.)*.2*u_audio_bass,cos(u_time*60.)*.15*u_audio_mid,sin(u_time*100.)*.1*u_audio_treble); rd.xy+=vec2(sin(u_time*120.),cos(u_time*90.))*.1*u_audio_rms; }
 if(u_onset>0){ ro.z-=.3; rd.xy*=1.1; }
 float t=0.; vec3 col=vec3(0.); float trns=1.;
 float bass=u_audio_bass,mid=u_audio_mid,treble=u_audio_treble,rms=u_audio_rms;
 for(int i=0;i<64;i++){ if(t>25.||trns<.01)break;
 vec3 pos=ro+rd*t; float d=SMKDEN(pos,u_time,u_audio_bass,u_audio_mid,u_audio_treble,u_audio_rms,u_beat);
 if(d>.01){
  vec3 n=GETNRM(pos); vec3 l=normalize(vec3(sin(u_time*.3)+bass*.5,1.+mid*.5,cos(u_time*.3)+treble*.5));
  vec3 v=-rd; float diff=max(dot(n,l),0.); float spec=pow(max(dot(reflect(-l,n),v),0.),32.);
  vec3 c=GETSMKCOL(pos,d,u_time,bass,mid,treble,rms,u_beat,u_onset);
  vec3 lit=c*(.2+diff*.6)+vec3(1.,.9,.7)*spec*.3;
  lit+=d*rms*vec3(1.,.8,.6)*.5+d*bass*vec3(1.,.4,.2)*.8+d*mid*vec3(.3,1.,.4)*.6+d*treble*vec3(.4,.5,1.)*.7;
  if(u_beat>0)lit+=vec3(1.,.7,.3)*d*.8; if(u_onset>0)lit+=vec3(1.,1.,.6)*d*.6;
  float a=d*.15*(1.+rms); if(u_beat>0)a*=2.; if(u_onset>0)a*=1.5;
  col+=lit*a*trns; trns*=1.-a; }
 float stp=.05+.1*(1.-SMKDEN(ro+rd*t,u_time,u_audio_bass,u_audio_mid,u_audio_treble,u_audio_rms,u_beat));
 t+=stp; if(t>30.)break; }
 vec3 bg=vec3(.005,.005,.015)+vec3(.002,.001,.005)*sin(u_time*.5)+vec3(.003,.001,.008)*u_audio_bass;
 vec3 fin=col+bg*trns;
 if(u_beat>0||u_onset>0){float wob=sin(u_time*40.)*.01; f_color=vec4(fin.r+wob,fin.g,fin.b-wob,1.);}
 else f_color=vec4(fin,1.);
}
"""

WIDTH, HEIGHT, FPS, CRF = 1920, 1080, 30, 18
OUTPUT_DIR = Path(r"C:\Users\clint\Desktop\SMOKE_4D_RENDER")

def load_audio():
    y, sr = librosa.load(AUDIO_PATH, sr=None)
    duration = len(y) / sr
    stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    stft_times = librosa.frames_to_time(np.arange(stft.shape[1]), sr=sr, hop_length=512)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=512)
    tempo_val = float(tempo.item()) if hasattr(tempo, 'item') else float(tempo)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=512)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=512)[0]
    cent_times = librosa.frames_to_time(np.arange(len(cent)), sr=sr, hop_length=512)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=512)[0]
    rolloff_times = librosa.frames_to_time(np.arange(len(rolloff)), sr=sr, hop_length=512)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=512)
    chroma_times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=512)
    n_bands = 16
    band_edges = np.logspace(np.log10(20), np.log10(sr/2), n_bands + 1)
    band_indices = []
    for i in range(n_bands):
        low = np.searchsorted(freqs, band_edges[i])
        high = np.searchsorted(freqs, band_edges[i+1])
        band_indices.append((low, high))
    return {
        "duration": duration, "tempo": tempo_val,
        "stft": stft, "freqs": freqs, "stft_times": stft_times,
        "beat_times": beat_times, "onset_times": onset_times,
        "rms": rms, "rms_times": rms_times,
        "centroid": cent, "centroid_times": cent_times,
        "rolloff": rolloff, "rolloff_times": rolloff_times,
        "chroma": chroma, "chroma_times": chroma_times,
        "band_indices": band_indices,
    }

def get_val(times, values, t):
    if len(times) == 0: return 0.0
    idx = np.searchsorted(times, t)
    if idx == 0: return float(values[0])
    if idx >= len(times): return float(values[-1])
    tt = (t - times[idx-1]) / (times[idx] - times[idx-1] + 1e-10)
    return float(values[idx-1] + tt * (values[idx] - values[idx-1]))

def get_beat(t, beat_times):
    return any(abs(t - bt) < 0.08 for bt in beat_times)

def get_onset(t, onset_times):
    return any(abs(t - ot) < 0.05 for ot in onset_times)

RAYMARCH_VERTEX = """
#version 330
in vec2 in_pos; in vec2 in_uv; out vec2 v_uv;
void main() { v_uv = in_uv; gl_Position = vec4(in_pos, 0.0, 1.0); }
"""

WIDTH, HEIGHT, FPS, CRF = 1920, 1080, 30, 18
OUTPUT_DIR = Path(r"C:\Users\clint\Desktop\SMOKE_4D_RENDER")

def load_audio():
    y, sr = librosa.load(AUDIO_PATH, sr=None)
    duration = len(y) / sr
    stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    stft_times = librosa.frames_to_time(np.arange(stft.shape[1]), sr=sr, hop_length=512)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=512)
    tempo_val = float(tempo.item()) if hasattr(tempo, 'item') else float(tempo)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=512)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=512)[0]
    cent_times = librosa.frames_to_time(np.arange(len(cent)), sr=sr, hop_length=512)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=512)[0]
    rolloff_times = librosa.frames_to_time(np.arange(len(rolloff)), sr=sr, hop_length=512)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=512)
    chroma_times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=512)
    n_bands = 16
    band_edges = np.logspace(np.log10(20), np.log10(sr/2), n_bands + 1)
    band_indices = []
    for i in range(n_bands):
        low = np.searchsorted(freqs, band_edges[i])
        high = np.searchsorted(freqs, band_edges[i+1])
        band_indices.append((low, high))
    return {
        "duration": duration, "tempo": tempo_val,
        "stft": stft, "freqs": freqs, "stft_times": stft_times,
        "beat_times": beat_times, "onset_times": onset_times,
        "rms": rms, "rms_times": rms_times,
        "centroid": cent, "centroid_times": cent_times,
        "rolloff": rolloff, "rolloff_times": rolloff_times,
        "chroma": chroma, "chroma_times": chroma_times,
        "band_indices": band_indices,
    }

def get_val(times, values, t):
    if len(times) == 0: return 0.0
    idx = np.searchsorted(times, t)
    if idx == 0: return float(values[0])
    if idx >= len(times): return float(values[-1])
    tt = (t - times[idx-1]) / (times[idx] - times[idx-1] + 1e-10)
    return float(values[idx-1] + tt * (values[idx] - values[idx-1]))

def get_beat(t, beat_times):
    return any(abs(t - bt) < 0.08 for bt in beat_times)

def get_onset(t, onset_times):
    return any(abs(t - ot) < 0.05 for ot in onset_times)

RAYMARCH_VERTEX = """
#version 330
in vec2 in_pos; in vec2 in_uv; out vec2 v_uv;
void main() { v_uv = in_uv; gl_Position = vec4(in_pos, 0.0, 1.0); }
"""

WIDTH, HEIGHT, FPS, CRF = 1920, 1080, 30, 18
OUTPUT_DIR = Path(r"C:\Users\clint\Desktop\SMOKE_4D_RENDER")

def load_audio():
    y, sr = librosa.load(AUDIO_PATH, sr=None)
    duration = len(y) / sr
    stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    stft_times = librosa.frames_to_time(np.arange(stft.shape[1]), sr=sr, hop_length=512)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=512)
    tempo_val = float(tempo.item()) if hasattr(tempo, 'item') else float(tempo)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=512)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=512)[0]
    cent_times = librosa.frames_to_time(np.arange(len(cent)), sr=sr, hop_length=512)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=512)[0]
    rolloff_times = librosa.frames_to_time(np.arange(len(rolloff)), sr=sr, hop_length=512)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=512)
    chroma_times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=512)
    n_bands = 16
    band_edges = np.logspace(np.log10(20), np.log10(sr/2), n_bands + 1)
    band_indices = []
    for i in range(n_bands):
        low = np.searchsorted(freqs, band_edges[i])
        high = np.searchsorted(freqs, band_edges[i+1])
        band_indices.append((low, high))
    return {
        "duration": duration, "tempo": tempo_val,
        "stft": stft, "freqs": freqs, "stft_times": stft_times,
        "beat_times": beat_times, "onset_times": onset_times,
        "rms": rms, "rms_times": rms_times,
        "centroid": cent, "centroid_times": cent_times,
        "rolloff": rolloff, "rolloff_times": rolloff_times,
        "chroma": chroma, "chroma_times": chroma_times,
        "band_indices": band_indices,
    }

def get_val(times, values, t):
    if len(times) == 0: return 0.0
    idx = np.searchsorted(times, t)
    if idx == 0: return float(values[0])
    if idx >= len(times): return float(values[-1])
    tt = (t - times[idx-1]) / (times[idx] - times[idx-1] + 1e-10)
    return float(values[idx-1] + tt * (values[idx] - values[idx-1]))

def get_beat(t, beat_times):
    return any(abs(t - bt) < 0.08 for bt in beat_times)

def get_onset(t, onset_times):
    return any(abs(t - ot) < 0.05 for ot in onset_times)

RAYMARCH_VERTEX = """
#version 330
in vec2 in_pos; in vec2 in_uv; out vec2 v_uv;
void main() { v_uv = in_uv; gl_Position = vec4(in_pos, 0.0, 1.0); }
"""

WIDTH, HEIGHT, FPS, CRF = 1920, 1080, 30, 18
OUTPUT_DIR = Path(r"C:\Users\clint\Desktop\SMOKE_4D_RENDER")

def load_audio():
    y, sr = librosa.load(AUDIO_PATH, sr=None)
    duration = len(y) / sr
    stft = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    stft_times = librosa.frames_to_time(np.arange(stft.shape[1]), sr=sr, hop_length=512)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=512)
    tempo_val = float(tempo.item()) if hasattr(tempo, 'item') else float(tempo)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=512)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=512)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=512)[0]
    cent_times = librosa.frames_to_time(np.arange(len(cent)), sr=sr, hop_length=512)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=512)[0]
    rolloff_times = librosa.frames_to_time(np.arange(len(rolloff)), sr=sr, hop_length=512)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=512)
    chroma_times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=512)
    n_bands = 16
    band_edges = np.logspace(np.log10(20), np.log10(sr/2), n_bands + 1)
    band_indices = []
    for i in range(n_bands):
        low = np.searchsorted(freqs, band_edges[i])
        high = np.searchsorted(freqs, band_edges[i+1])
        band_indices.append((low, high))
    return {
        "duration": duration, "tempo": tempo_val,
        "stft": stft, "freqs": freqs, "stft_times": stft_times,
        "beat_times": beat_times, "onset_times": onset_times,
        "rms": rms, "rms_times": rms_times,
        "centroid": cent, "centroid_times": cent_times,
        "rolloff": rolloff, "rolloff_times": rolloff_times,
        "chroma": chroma, "chroma_times": chroma_times,
        "band_indices": band_indices,
    }

def get_val(times, values, t):
    if len(times) == 0: return 0.0
    idx = np.searchsorted(times, t)
    if idx == 0: return float(values[0])
    if idx >= len(times): return float(values[-1])
    tt = (t - times[idx-1]) / (times[idx] - times[idx-1] + 1e-10)
    return float(values[idx-1] + tt * (values[idx] - values[idx-1]))

def get_beat(t, beat_times):
    return any(abs(t - bt) < 0.08 for bt in beat_times)

def get_onset(t, onset_times):
    return any(abs(t - ot) < 0.05 for ot in onset_times)

def png_ok(path):
    """Structural PNG check (magic + IEND trailer): stdlib only, detects truncation."""
    try:
        with open(path, "rb") as fh:
            if fh.read(8) != b"\x89PNG\r\n\x1a\n":
                return False
            fh.seek(-8, 2)
            tail = fh.read(8)
    except (OSError, ValueError) as exc:
        print("  png_ok: unreadable %s (%s)" % (path, exc))
        return False
    return tail == b"IEND\xae\x42\x60\x82"


def save_png_rgb(path, arr):
    """Write an HxWx3 uint8 array as PNG - stdlib zlib only."""
    arr = np.ascontiguousarray(arr)
    h, w, _ = arr.shape
    raw = b"".join(b"\x00" + arr[y].tobytes() for y in range(h))
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    blob = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 1))
            + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(blob)


def generate():
    audio = load_audio()
    duration = audio["duration"]
    total_frames = int(duration * FPS)
    
    output_path = OUTPUT_DIR / "LET_EM_WONDER_4D_SMOKE_TRUE3D.mp4"
    frame_dir = OUTPUT_DIR / "frames" / "smoke_4d"
    frame_dir.mkdir(parents=True, exist_ok=True)
    
    audio_data = load_audio()
    duration = audio_data["duration"]
    total_frames = int(duration * FPS)
    
    n_bands = 16
    band_data = []
    print("Pre-computing audio features...")
    for i in range(total_frames):
        t = i / FPS
        bass = mid = treble = 0.0
        for bi, (low, high) in enumerate(audio["band_indices"]):
            if low < high and low < audio["stft"].shape[0]:
                idx = np.searchsorted(audio["stft_times"], min(t, audio["stft_times"][-1]))
                if idx >= audio["stft"].shape[1]: idx = audio["stft"].shape[1] - 1
                mag = np.mean(audio["stft"][low:high, idx])
                mag_norm = min(mag / (np.max(audio["stft"]) + 1e-10), 1.0)
                if bi < 5: bass += mag_norm
                elif bi < 10: mid += mag_norm
                else: treble += mag_norm
        bass = min(bass / 5.0, 1.0)
        mid = min(mid / 5.0, 1.0)
        treble = min(treble / 6.0, 1.0)
        rms = get_val(audio["rms_times"], audio["rms"], t)
        rms_norm = min(rms / 0.3, 1.0)
        is_beat = get_beat(t, audio["beat_times"])
        is_onset = get_onset(t, audio["onset_times"])
        chroma = [get_val(audio["chroma_times"], audio["chroma"][c, :], t) for c in range(4)]
        band_data.append({
            't': t, 'bass': bass, 'mid': mid, 'treble': treble,
            'rms': rms_norm, 'beat': is_beat, 'onset': is_onset,
            'chroma': chroma
        })
        if i % 2000 == 0: print(f"  Pre-compute: {t:.1f}s / {duration:.1f}s")
    
    print(f"Rendering {total_frames} frames...")
    
    ctx = moderngl.create_context(require=330, standalone=True)
    ctx.enable(moderngl.DEPTH_TEST)
    ctx.viewport = (0, 0, WIDTH, HEIGHT)
    
    color_tex = ctx.texture((WIDTH, HEIGHT), 4)
    depth_tex = ctx.depth_texture((WIDTH, HEIGHT))
    fbo = ctx.framebuffer(color_attachments=[color_tex], depth_attachment=depth_tex)
    fbo.use()
    
    verts = np.array([-1,-1,0,0, 1,-1,1,0, -1,1,0,1, 1,1,1,1], dtype=np.float32)
    vbo = ctx.buffer(verts.tobytes())
    prog = ctx.program(vertex_shader=RAYMARCH_VERTEX, fragment_shader=SMOKE_FRAGMENT)
    vao = ctx.vertex_array(prog, [(vbo, '2f 2f', 'in_pos', 'in_uv')])
    
    color_tex = ctx.texture((WIDTH, HEIGHT), 4)
    depth_tex = ctx.depth_texture((WIDTH, HEIGHT))
    fbo = ctx.framebuffer(color_attachments=[color_tex], depth_attachment=depth_tex)
    fbo.use()
    
    frame_dir = OUTPUT_DIR / "frames" / "smoke_4d"
    frame_dir.mkdir(parents=True, exist_ok=True)
    
    total_frames = int(audio["duration"] * FPS)
    skipped = 0
    
    for frame_num in range(total_frames):
        out_png = frame_dir / f"frame_{frame_num:06d}.png"
        if out_png.exists():
            if png_ok(out_png):
                skipped += 1
                continue
            print(f"  incomplete frame {out_png.name} -> re-rendering")
            out_png.unlink(missing_ok=True)
        bd = band_data[frame_num]
        t = bd['t']
        
        fbo.use()
        ctx.clear(0.005, 0.005, 0.015, 1.0)
        
        prog['u_time'].write(struct.pack('f', t))
        prog['u_resolution'].write(struct.pack('ff', WIDTH, HEIGHT))
        prog['u_audio_rms'].write(struct.pack('f', bd['rms']))
        prog['u_audio_bass'].write(struct.pack('f', bd['bass']))
        prog['u_audio_mid'].write(struct.pack('f', bd['mid']))
        prog['u_audio_treble'].write(struct.pack('f', bd['treble']))
        prog['u_beat'].write(struct.pack('i', 1 if bd['beat'] else 0))
        prog['u_onset'].write(struct.pack('i', 1 if bd['onset'] else 0))
        prog['u_chroma_0'].write(struct.pack('f', bd['chroma'][0]))
        prog['u_chroma_1'].write(struct.pack('f', bd['chroma'][1]))
        prog['u_chroma_2'].write(struct.pack('f', bd['chroma'][2]))
        prog['u_chroma_3'].write(struct.pack('f', bd['chroma'][3]))
        
        vao.render(moderngl.TRIANGLE_STRIP)
        
        frame = np.frombuffer(color_tex.read(), dtype=np.uint8).reshape(HEIGHT, WIDTH, 4)[:,:,:3]
        save_png_rgb(frame_dir / f"frame_{frame_num:06d}.png", frame)
        
        if frame_num % (FPS * 30) == 0:
            print(f"  {t:.1f}s / {duration:.1f}s ({frame_num}/{total_frames})")
    
    print(f"Resume: {skipped} frames skipped (already on disk), {total_frames - skipped} rendered")
    print("Encoding...")
    subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",str(frame_dir/"frame_%06d.png"),
        "-i",AUDIO_PATH,"-c:v","libx264","-preset","medium","-crf",str(CRF),
        "-pix_fmt","yuv420p","-c:a","aac","-b:a","320k","-shortest",
        str(OUTPUT_DIR/"LET_EM_WONDER_4D_SMOKE_TRUE3D.mp4")], timeout=7200)
    
    try:
        shutil.rmtree(frame_dir)
    except Exception as exc:
        print(f"  frame cleanup failed (mp4 already encoded): {exc}")
    print("✓ 4D Smoke done")

def get_val(times, values, t):
    if len(times) == 0: return 0.0
    idx = np.searchsorted(times, t)
    if idx == 0: return float(values[0])
    if idx >= len(times): return float(values[-1])
    tt = (t - times[idx-1]) / (times[idx] - times[idx-1] + 1e-10)
    return float(values[idx-1] + tt * (values[idx] - values[idx-1]))

def get_beat(t, beat_times):
    return any(abs(t - bt) < 0.08 for bt in beat_times)

def get_onset(t, onset_times):
    return any(abs(t - ot) < 0.05 for ot in onset_times)

if __name__ == "__main__":
    print("Starting 4D Smoke generation...")
    generate()
    print("DONE")
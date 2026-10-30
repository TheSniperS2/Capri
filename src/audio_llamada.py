"""Canal telefónico y envolvente medidos sobre el audio que se va a reproducir."""
import tempfile
import wave
from pathlib import Path

PASO=.02

def factor_mascara(mascara):return {'ardilla':1.2,'villana':.84}.get(mascara,1.)

def preparar(archivo,conectar=False,mascara=None):
    import av
    import numpy as np
    resampler=av.AudioResampler(format='s16',layout='mono',rate=16000)
    trozos=[]
    with av.open(str(archivo)) as entrada:
        for frame in entrada.decode(audio=0):
            for mono in resampler.resample(frame):trozos.append(mono.to_ndarray().reshape(-1))
        for mono in resampler.resample(None):trozos.append(mono.to_ndarray().reshape(-1))
    if not trozos:raise ValueError('Audio de llamada vacío.')
    muestras=np.concatenate(trozos).astype(np.float64)/32768.
    factor=factor_mascara(mascara)
    if factor!=1:
        muestras=np.interp(np.arange(0,len(muestras),factor),np.arange(len(muestras)),muestras)
    if mascara=='robot':
        muestras*=.65+.35*np.sin(2*np.pi*65*np.arange(len(muestras))/16000)
    # Banda de telefonía, compresión suave y un fondo mínimo solo durante habla.
    margen=4096;extendidas=np.pad(muestras,(margen,margen))
    frecuencias=np.fft.rfftfreq(len(extendidas),1/16000)
    mascara=(1-np.exp(-(frecuencias/280)**4))*np.exp(-(frecuencias/3350)**8)
    filtrado=np.fft.irfft(np.fft.rfft(extendidas)*mascara,n=len(extendidas))[margen:margen+len(muestras)]
    filtrado=np.tanh(filtrado*1.5)*.8
    filtrado+=np.random.default_rng(42).normal(0,.0008,len(filtrado))*(np.abs(filtrado)>.006)
    adelanto=.18 if conectar else 0.
    if conectar:
        cabecera=np.zeros(round(adelanto*16000))
        for inicio,hz in ((.015,980),(.075,1380)):
            n=640;t=np.arange(n)/16000
            tono=np.sin(2*np.pi*hz*t)*np.hanning(n)*.035
            pos=round(inicio*16000);cabecera[pos:pos+n]+=tono
        filtrado=np.concatenate((cabecera,filtrado))
    pcm=np.rint(np.clip(filtrado,-.99,.99)*32767).astype('<i2')
    n=round(PASO*16000);acolchado=np.pad(filtrado,(0,(-len(filtrado))%n))
    niveles=np.minimum(1,np.sqrt(np.mean(acolchado.reshape(-1,n)**2,axis=1))*6).tolist()
    with tempfile.NamedTemporaryFile(suffix='.wav',delete=False) as f:salida=Path(f.name)
    try:
        with wave.open(str(salida),'wb') as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000);wav.writeframes(pcm.tobytes())
    except Exception:
        salida.unlink(missing_ok=True);raise
    return salida,niveles,adelanto


def barras(niveles,segundos,cantidad=28):
    indice=int(max(0,segundos)/PASO)
    return tuple(niveles[i] if 0<=i<len(niveles) else 0. for i in range(indice-cantidad+1,indice+1))


def sonido_colgado(volumen=100):
    """Dos tonos descendentes suaves, como la desconexión de un enlace."""
    import io,math
    from array import array
    volumen=max(0,min(100,float(volumen)))/100
    if not volumen:return b''
    frecuencia=22050;muestras=array('h')
    for i in range(round(.24*frecuencia)):
        t=i/frecuencia;valor=0.
        for inicio,duracion,agudo,grave in ((0.,.075,740,520),(.105,.105,520,350)):
            u=t-inicio
            if 0<=u<duracion:
                envolvente=math.sin(math.pi*u/duracion)**2
                valor+=(math.sin(2*math.pi*agudo*u)+math.sin(2*math.pi*grave*u))*.05*envolvente
        muestras.append(round(valor*volumen*32767))
    salida=io.BytesIO()
    with wave.open(salida,'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(frecuencia);wav.writeframes(muestras.tobytes())
    return salida.getvalue()

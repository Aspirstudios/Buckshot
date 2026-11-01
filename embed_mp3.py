#!/usr/bin/env python3
"""Incrusta un mp3 dentro de buckshot.py (base64) para que el juego siga siendo un solo script.
Opcionalmente le aplica un efecto bitcrusher antes de incrustarlo (necesita ffmpeg, solo aqui,
el juego y el .exe NO lo necesitan).

  python embed_mp3.py                    -> usa el unico .mp3 de la carpeta, con bitcrush 50%
  python embed_mp3.py musica.mp3         -> usa ese mp3
  python embed_mp3.py musica.mp3 --crush 50   (0 = sin efecto, 100 = destruido)
  python embed_mp3.py --clear            -> quita el mp3 incrustado
"""
import argparse
import base64
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
START, END = '# --- SPLASH MP3 START ---', '# --- SPLASH MP3 END ---'


def find_ffmpeg():
    for cand in (shutil.which('ffmpeg'), os.path.join(HERE, 'ffmpeg.exe'), os.path.join(HERE, 'ffmpeg')):
        if cand and os.path.isfile(cand):
            return cand
    return None


def crush(path, pct, bitrate):
    """Bitcrusher: reduce bit depth and sample rate (grit). pct 0-100. Returns the new mp3 as bytes."""
    ff = find_ffmpeg()
    if not ff:
        print('\nNo encuentro ffmpeg, hace falta para aplicar el bitcrush.')
        print('  Windows: abre una terminal y ejecuta  winget install Gyan.FFmpeg  (y reabre la terminal)')
        print('  o descarga ffmpeg.exe y ponlo en esta misma carpeta.')
        if input('Incrustar el mp3 SIN efecto? [s/N] ').strip().lower() in ('s', 'si', 'y', 'yes'):
            return open(path, 'rb').read()
        sys.exit(1)
    c = pct / 100.0
    bits = round(16 - 10 * c)          # 30% -> 13 bits, 100% -> 6 bits
    samples = round(1 + 7 * c)         # 30% -> x3 downsampling, 100% -> x8
    out = os.path.join(tempfile.mkdtemp(prefix='bs_'), 'crushed.mp3')
    cmd = [ff, '-y', '-loglevel', 'error', '-i', path,
           '-af', 'acrusher=bits=%d:samples=%d:mix=1:mode=lin:aa=0,alimiter=limit=0.9' % (bits, samples),
           '-codec:a', 'libmp3lame', '-b:a', bitrate, out]
    try:
        subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, OSError) as e:
        print('ffmpeg fallo:', e)
        sys.exit(1)
    data = open(out, 'rb').read()
    shutil.rmtree(os.path.dirname(out), ignore_errors=True)
    print('Bitcrush %d%% aplicado (%d bits, muestreo /%d).' % (pct, bits, samples))
    return data


def main():
    ap = argparse.ArgumentParser(description='Incrusta un mp3 en buckshot.py')
    ap.add_argument('mp3', nargs='?', help='archivo mp3 (si se omite, usa el unico .mp3 de la carpeta)')
    ap.add_argument('--target', default=os.path.join(HERE, 'buckshot.py'), help='script destino')
    ap.add_argument('--crush', type=float, default=50, help='bitcrush 0-100 (por defecto 50)')
    ap.add_argument('--bitrate', default='128k', help='bitrate del mp3 final (por defecto 128k)')
    ap.add_argument('--clear', action='store_true', help='quitar el mp3 incrustado')
    a = ap.parse_args()

    if a.clear:
        b64 = ''
    else:
        mp3 = a.mp3
        if not mp3:
            found = glob.glob(os.path.join(HERE, '*.mp3')) or glob.glob('*.mp3')
            if len(found) != 1:
                print('Pon UN solo .mp3 en la carpeta o indica cual: python embed_mp3.py musica.mp3'
                      if found else 'No hay ningun .mp3 en la carpeta.')
                return 1
            mp3 = found[0]
            print('Usando', os.path.basename(mp3))
        if not os.path.isfile(mp3):
            print('No existe', mp3)
            return 1
        data = crush(mp3, max(0, min(100, a.crush)), a.bitrate) if a.crush > 0 else open(mp3, 'rb').read()
        if len(data) > 1_500_000:
            print('Aviso: el mp3 pesa %.1f MB; el script quedara muy grande (recomendado < 1 MB).' % (len(data) / 1e6))
        b64 = base64.b64encode(data).decode()

    src = open(a.target, encoding='utf-8').read()
    if START not in src or END not in src:
        print('No encuentro los marcadores en', a.target)
        return 1
    if b64:
        lines = [b64[i:i + 100] for i in range(0, len(b64), 100)]
        body = "SPLASH_MP3 = '''\n" + '\n'.join(lines) + "\n'''"
    else:
        body = "SPLASH_MP3 = ''"
    new = re.sub(re.escape(START) + r'.*?' + re.escape(END),
                 lambda m: START + '\n' + body + '\n' + END, src, flags=re.S)
    with open(a.target, 'w', encoding='utf-8') as f:
        f.write(new)
    print('Listo: %s (%s)' % (os.path.basename(a.target),
                              'mp3 incrustado, %d KB' % (len(b64) * 3 // 4 // 1024) if b64 else 'mp3 eliminado'))
    return 0


if __name__ == '__main__':
    sys.exit(main())

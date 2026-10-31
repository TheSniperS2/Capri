"""Ejecuta toda la suite aislando el estado nativo de Tk entre pruebas gráficas.

Sin argumentos descubre los mismos archivos test*.py de tests/. Se pueden pasar
nombres de módulos para una comprobación focal. No omite ni reintenta fallos.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import unittest


def casos_de(suite):
    for caso in suite:
        if isinstance(caso,unittest.TestSuite):yield from casos_de(caso)
        else:yield caso


def planificar(modulo):
    casos=list(casos_de(unittest.defaultTestLoader.loadTestsFromName(modulo)))
    if any(type(c).__name__=='_FailedTest' for c in casos):return [[modulo]]
    graficos=[];normales=[]
    for caso in casos:
        if any(base.__name__=='PruebasTk' for base in type(caso).__mro__):graficos.append([caso.id()])
        else:normales.append(caso.id())
    return ([normales] if normales else [])+graficos


def main():
    base=Path(__file__).resolve().parents[1];carpeta=base/'tests'
    disponibles={'.'.join(p.relative_to(carpeta).with_suffix('').parts) for p in carpeta.rglob('test*.py')}
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('modulos',nargs='*');args=parser.parse_args()
    modulos=args.modulos or sorted(disponibles)
    if set(modulos)-disponibles:parser.error('Módulo de pruebas desconocido.')
    env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join([str(carpeta),str(base/'src'),env.get('PYTHONPATH','')])
    env.update(PYTHONFAULTHANDLER='1',PYTHONUNBUFFERED='1',PYTHONUTF8='1')
    sys.path[:0]=[str(carpeta),str(base/'src')]
    fallos=[];ejecuciones=0
    for modulo in modulos:
        for seleccion in planificar(modulo):
            etiqueta=seleccion[0] if len(seleccion)==1 else modulo+' (sin Tk)'
            print(f'::group::{etiqueta}',flush=True);ejecuciones+=1
            resultado=subprocess.run([sys.executable,'-m','unittest',*seleccion,'-v'],cwd=base,env=env)
            print('::endgroup::',flush=True)
            if resultado.returncode:fallos.append((etiqueta,resultado.returncode))
    print(f'{len(modulos)} módulos; {ejecuciones} procesos; {len(fallos)} con fallos.',flush=True)
    for modulo,codigo in fallos:print(f'FALLO: {modulo} (código {codigo})',flush=True)
    return int(bool(fallos))


if __name__=='__main__':sys.exit(main())

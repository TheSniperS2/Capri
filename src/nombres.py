"""Nombres de aplicaciones. Las equivalencias se aplican solo al abrir una app."""
import unicodedata

VOCABULARIO='Spotify, YouTube, Opera GX, Google, Windows, Discord, Steam, Cyberpunk, Capri'
ALIAS={
    'spotify':('spotify','spotifai','espotifai','es potifai','espoti fai','es poti fai','spot ifai','spoty fi','spot i fi','es potify','es por ti','es por ti fai'),
    'youtube':('youtube','you tube','yutub','yu tub','yutube'),
}

def nombre_aplicacion(texto):
    nombre=''.join(c for c in unicodedata.normalize('NFD',texto.casefold()) if unicodedata.category(c)!='Mn')
    nombre=' '.join(nombre.split())
    for canonico,variantes in ALIAS.items():
        if nombre in variantes:return canonico
    return nombre

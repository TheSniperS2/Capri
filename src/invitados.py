"""Llamadas ficticias y perfiles sintéticos propios inspirados en Edgerunners 2."""
import random

NOMBRES={'king':'King','d':'D','roman':'Roman','talia':'Talia'}
VOCES={
    'king':({'es':'es-MX-JorgeNeural','en':'en-US-GuyNeural','pt':'pt-BR-AntonioNeural','ja':'ja-JP-KeitaNeural'},'-18Hz','-6%'),
    'd':({'es':'es-MX-JorgeNeural','en':'en-US-AndrewMultilingualNeural','pt':'pt-BR-AntonioNeural','ja':'ja-JP-KeitaNeural'},'-4Hz','+1%'),
    'roman':({'es':'es-MX-DaliaNeural','en':'en-US-EricNeural','pt':'pt-BR-AntonioNeural','ja':'ja-JP-KeitaNeural'},'+24Hz','+10%'),
    'talia':({'es':'es-MX-DaliaNeural','en':'en-US-JennyNeural','pt':'pt-BR-FranciscaNeural','ja':'ja-JP-NanamiNeural'},'+2Hz','+9%'),
}
BROMAS={
    'king':[
        ('King al aparato. Un veterano sabe cuándo retirarse. Yo me retiré del gimnasio cuando la cinta empezó a perseguirme. Decisión táctica. Fin de la llamada.',
         'King acaba de perder una pelea contra una cinta de correr. Ni siquiera estaba en modo difícil.'),
        ('Habla King. He cambiado mis implantes por experiencia. Ahora las rodillas me hacen el sonido de inicio de Windows. Cuelgo antes de que pidan actualizarse.',
         'Vale, el chiste de las rodillas me hizo gracia. No se lo digas a King o lo repite durante seis meses.'),
    ],
    'd':[
        ('Soy D. He encontrado al responsable de la caída de la red. Era el cable. Lo interrogué. No soltó una palabra. Investigación cerrada.',
         'D acaba de interrogar a un cable. Ese es oficialmente el peor chiste que he escuchado esta noche.'),
        ('D en línea. Entré en una red supuestamente impenetrable. La contraseña era impenetrable. Un trabajo exigente para el ego. Cambio y fuera.',
         'Un aplauso para D, que ha derrotado al enemigo más peligroso: una contraseña escrita en una nota adhesiva.'),
    ],
    'roman':[
        ('Roman al habla. Rodé una película de suspense sobre una carpeta vacía. No pasa nada durante dos horas. La crítica dice que el archivo tiene profundidad. Corte. Cuelgo.',
         'Roman ha inventado el cine sin película. Me enfada muchísimo que eso pueda ganar un premio.'),
        ('Soy Roman. Mi documental sobre una tostadora tiene un final quemado. La secuela está en producción, pero el protagonista exige mantequilla. Esto merece un primer plano.',
         'Lo admito: pagaría por ver esa tostadora. Roman, como cobres la entrada en criptomonedas, te muerdo el objetivo.'),
    ],
    'talia':[
        ('Talia aquí. Le puse cromo a una cuchara. Ahora la sopa necesita mantenimiento y la cuchara me cobra suscripción. Gran avance tecnológico. Ya puedes colgar.',
         'Talia ha logrado que hasta la sopa tenga gastos mensuales. Arasaka estará tomando notas, seguro.'),
        ('Habla Talia. Mi nuevo brazo tiene tanta potencia que abrí un tarro y también una pequeña crisis diplomática. El pepinillo está bien. Yo estoy espectacular. Fin.',
         'Talia contra un tarro de pepinillos. Por fin una pelea con consecuencias geopolíticas. Me encanta este desastre.'),
    ],
}
_ultimas={}

def elegir():return random.choice((None,None,None,'king','d','roman','talia'))

def guion(nombre):
    opciones=[p for p in BROMAS[nombre] if p!=_ultimas.get(nombre)] or BROMAS[nombre]
    resultado=random.choice(opciones);_ultimas[nombre]=resultado;return resultado

def voz(nombre,idioma):
    voces,tono,ritmo=VOCES[nombre]
    if idioma=='es' and nombre in ('d','roman'):
        tono,ritmo={'d':('-8Hz','-2%'),'roman':('+18Hz','+4%')}[nombre]
    return voces.get(idioma,voces['es']),tono,ritmo

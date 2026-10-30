"""Cadencia de conversación, asomos y bromas de ventana optativas."""
import random
import time


class Travesuras:
    def __init__(self,reloj=None):
        self.reloj=reloj or time.monotonic;self.proxima=self.reloj()+900;self.ultima_frase=None;self.bolsas={}

    def programar(self,minutos=15):
        self.proxima=self.reloj()+max(3,min(60,float(minutos)))*60*random.uniform(.85,1.15)

    def tick(self,llamadas,ocupada,asomos=False,minimizar=False,personaje=False,minutos=15):
        if ocupada or self.reloj()<self.proxima:return None
        opciones=[]
        if llamadas:opciones.extend(('llamada','llamada'))
        if personaje and asomos:opciones.append('asomar')
        if minimizar:opciones.append('minimizar')
        if not opciones:return None
        self.programar(minutos);return random.choice(opciones)

    def frase(self,tipo='llamada'):
        frases={
            'saludo':[
                'Aló. Capri al aparato. Esto es una llamada de importancia ridículamente baja.',
                'Choom, soy Capri. Interrumpo esta realidad para emitir una tontería.',
                'Buenas, habla Capri. Esta llamada podría empeorar tu sentido del humor.',
                'Capri en línea. Comunicado urgente y completamente innecesario.',
            ],
            'llamada':[
                'Llama el departamento de tornillos sueltos. El mío acaba de ascender a director. Comunicado terminado.',
                'Toc, toc. Soy tu antivirus. Mentira, soy yo con una olla en la cabeza. Cuelgo antes de que me contraten.',
                'He vendido mi silencio por tres píxeles y una empanada imaginaria. La empanada estaba corrupta. Pésimo negocio.',
                'Acabo de declarar este rincón república independiente. El himno dura medio segundo: pi. Ya está.',
                'Una migaja ha tomado el control del teclado. He iniciado negociaciones. Exige mantequilla.',
                'Servicio técnico de ardillas. Hemos encontrado una bellota en su sistema. Procedo a comérmela. Ñam. Reparado.',
                'Habla la villana del escritorio. Iba a dominar el mundo, pero me he enredado con el cable del ratón. Retirada táctica.',
                'Unidad Capri cero cero uno. Error: exceso de dramatismo. Reiniciando dignidad. Dignidad no encontrada. Bip. Cuelgo.',
                'Aló, pizzería dimensional. Su pizza salió por un agujero negro. Sigue caliente, pero llegará el martes del año pasado.',
                'He intentado poner cara de persona responsable. Me ha dado un error de compatibilidad. Vuelvo a ser un peligro decorativo.',
                'Toc, toc. No abras, que soy yo otra vez. Solo vine a anunciar que el suelo es lava y yo hago trampas flotando.',
                'Llamo para informar que un calcetín perdido ha sido elegido alcalde del cesto. Promete acabar con las parejas.',
                'Acabo de ganar una discusión contra una carpeta vacía. Rival durísimo. No dijo ni una palabra.',
                'Tu cursor y yo hemos terminado. Se iba con cualquiera que tuviera un enlace. No quiero hablar del tema. Cuelgo dramáticamente.',
                'Emergencia de mentira: el pato de goma está fuera de control. Cuac. Ya lo he detenido. Cuac. Se ha fugado.',
                'Servicio técnico de ardillas. Su garantía cubre mordiscos emocionales y cables imaginarios. La factura son cuatro bellotas. Hasta nunca.',
                'Habla la villana del escritorio. He secuestrado un píxel. Pido como rescate otro píxel. El negocio está creciendo fatal.',
                'Unidad Capri cero cero uno. Analizando caos. Resultado: yo. Caso resuelto. Autodestrucción cancelada por pereza.',
                'He fundado una secta de cucharas. Solo tenemos un tenedor infiltrado y demasiadas tensiones internas. Fin del informe.',
                'Llamada equivocada. Buscaba al director de las nubes. Tengo una reclamación: ayer una tenía forma de brócoli. Imperdonable.',
                'Buenas, inspección de monstruos debajo de la cama. Todo correcto, solo había un cargador muy enfadado. Le puse una multa imaginaria.',
                'He abierto una academia para enseñar a los fantasmas a asustar. Primera lección: bu. Segunda lección: facturar. Cierro por éxito.',
                'Transmisión pirata: este escritorio pertenece ahora a una tostadora con delirios de grandeza. Soy su ministra del pan. Cambio y fuera.',
                'Me he puesto una corbata invisible para dar este comunicado: bla. Gracias por asistir a mi caída profesional. Cuelgo.',
            ],
            'asomar':[
                'Operación espía diminuta. He llegado a la esquina sin que nadie me vea. Excepto tú. Y todo el mundo. Misión impecable.',
                'Este rincón queda confiscado por exceso de esquina. Lo devuelvo cuando termine mi investigación imaginaria.',
                'Me he convertido en gárgola de escritorio. Protejo este lugar de las palomas digitales. Cobro en caos.',
                'Inspección de polvo digital. He encontrado tres pelusas y les he dado nombres de villanos. Ya están conspirando.',
                'No estoy espiando. Soy una decoración sospechosamente informada. Continúa con tus actividades totalmente normales.',
                'Informe desde la esquina: el horizonte es plano y el monitor también. Estoy rodeada de pruebas. Cuelgo antes de pensar más.',
            ],
            'minimizar':[
                'He secuestrado tu ventana. El rescate era una carcajada, pero me dio pereza negociar. Ya la devolví. Criminal pésima, yo.',
                'Tu ventana acaba de hacer una sentadilla. De nada. Soy entrenadora de rectángulos y no tengo licencia.',
                'Ta-da. He hecho desaparecer una ventana y volver a aparecer mi ego. La ventana ya está de vuelta. Mi ego nunca se fue.',
                'He mandado tu ventana de excursión a la barra de tareas. Volvió sin recuerdos y con un imán de nevera imaginario.',
                'Control de calidad: la ventana baja. La ventana sube. Mi carrera como científica está despegando peligrosamente.',
            ],
        }.get(tipo,[])
        if not self.bolsas.get(tipo):self.bolsas[tipo]=list(frases)
        opciones=[f for f in self.bolsas[tipo] if f!=self.ultima_frase] or self.bolsas[tipo]
        self.ultima_frase=random.choice(opciones);self.bolsas[tipo].remove(self.ultima_frase);return self.ultima_frase

    def disfraz(self,frase):
        for prefijo,voz in (('Servicio técnico de ardillas.','ardilla'),('Habla la villana del escritorio.','villana'),('Unidad Capri cero cero uno.','robot')):
            if frase.startswith(prefijo):return voz
        return None

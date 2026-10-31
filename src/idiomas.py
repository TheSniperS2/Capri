"""Idiomas de la interfaz, respuestas y voces. No altera los datos del usuario."""
import json
import re
import tkinter as tk
from pathlib import Path
from functools import lru_cache

_actual='es'
_catalogo=None

def activar(idioma):
    global _actual
    _actual=codigo(idioma)

def idioma_actual():return _actual

def catalogo():
    global _catalogo
    if _catalogo is None:
        try:_catalogo=json.loads(Path(__file__).with_name('traducciones.json').read_text(encoding='utf8'))
        except (OSError,ValueError):_catalogo={}
        _catalogo.update(UI_FIJOS)
    return _catalogo

@lru_cache(maxsize=2048)
def _traducir_ui(original,idioma):
    if idioma=='es' or not original:return original
    if original in ('Español','English','Português','日本語'):return original
    indice=('en','pt','ja').index(idioma);datos=catalogo()
    if original in datos:return datos[original][indice]
    if original.startswith('CAPRI // '):return 'CAPRI // '+_traducir_ui(original[9:],idioma)
    atajo=re.fullmatch(r'((?:(?:Ctrl|Alt|Shift|Win)\+)*(?:F\d{1,2}|[A-Za-z0-9]+))( para hablar.*)',original)
    if atajo:return atajo[1]+_traducir_ui(atajo[2],idioma)
    for prefijo in ('DI «CAPRI»  //  ','F8','F9','F10','F11','F12'):
        if original.startswith(prefijo) and original!=prefijo:
            return _traducir_ui(prefijo,idioma)+_traducir_ui(original[len(prefijo):],idioma)
    for plantilla in _plantillas():
        expresion,origen,numeros=plantilla
        m=expresion.fullmatch(original)
        if m:
            valores=dict(zip(numeros,m.groups()));salida=datos[origen][indice]
            return re.sub(r'\{(\d+)\}',lambda t:valores.get(t[1],t[0]),salida)
    for prefijo in ('Oyendo: ','Guardado: ','No disponible: ','Seleccionado: ','Di «Capri» o pulsa ',
                    'No te escuché. Pulsa ','No entendí la frase. Acércate al micrófono y pulsa ',
                    'No pude mantener la escucha de «Capri». Puedes usar Hablar. ',
                    'No pude completar la prueba: ','No pude usar el micrófono. ',
                    'No se pudo inicializar el audio de Windows: ','Vinculada. Puedes decir «Capri, pon mi playlist '):
        if original.startswith(prefijo) and len(original)>len(prefijo):
            return _traducir_ui(prefijo,idioma)+_traducir_ui(original[len(prefijo):],idioma)
    if original.endswith(' para repetir.'):
        return _traducir_ui(original[:-len(' para repetir.')],idioma)+_traducir_ui(' para repetir.',idioma)
    return original

@lru_cache(maxsize=1)
def _plantillas():
    resultado=[]
    for origen in sorted(catalogo(),key=len,reverse=True):
        numeros=re.findall(r'\{(\d+)\}',origen)
        if numeros:
            patron=re.escape(origen)
            for numero in numeros:patron=patron.replace(re.escape('{'+numero+'}'),r'(.+?)',1)
            resultado.append((re.compile(patron,re.S),origen,numeros))
    return resultado

def ui(original,idioma=None):
    return _traducir_ui(str(original),codigo(idioma or _actual))

def frase_despedida(idioma=None):
    return {'es':'Cuídate mucho, choom.','en':"I'll see you around, choom.",
            'pt':'Até mais, choom.','ja':'またね、choom。'}[codigo(idioma or _actual)]

class Lienzo(tk.Canvas):
    """Traduce al dibujar sin cambiar los valores internos de los controles."""
    def __init__(self,*args,**kw):
        self._textos_ui={}
        super().__init__(*args,**kw)
    def create_text(self,*args,**kw):
        original=kw.get('text','');fuente_original=kw.get('font')
        kw['text']=ui(original)
        if _actual=='ja' and isinstance(fuente_original,tuple):kw['font']=('Yu Gothic UI',)+fuente_original[1:]
        item=super().create_text(*args,**kw);self._textos_ui[item]=(original,fuente_original)
        return item
    def delete(self,*args):
        if 'all' in args:self._textos_ui.clear()
        else:
            for tag in args:
                for item in self.find_withtag(tag):self._textos_ui.pop(item,None)
        return super().delete(*args)
    def itemconfigure(self,item,cnf=None,**kw):
        if 'text' in kw:
            original=kw['text'];kw['text']=ui(original)
            for identificador in self.find_withtag(item):
                anterior=self._textos_ui.get(identificador,('',None));self._textos_ui[identificador]=(original,kw.get('font',anterior[1]))
        return super().itemconfigure(item,cnf,**kw)
    itemconfig=itemconfigure
    def retraducir(self):
        for item,(original,fuente_original) in self._textos_ui.items():
            kw={'text':ui(original)}
            if isinstance(fuente_original,tuple):kw['font']=(('Yu Gothic UI',)+fuente_original[1:]) if _actual=='ja' else fuente_original
            super().itemconfigure(item,**kw)

def localizar_widgets(raiz,forzar=False):
    """Localiza textos visibles; selectores, modelos y rutas conservan su identidad."""
    def recorrer(w):
        if isinstance(w,(tk.Label,tk.Button,tk.Checkbutton,tk.LabelFrame)):
            try:
                variable=w.cget('textvariable') if 'textvariable' in w.keys() else ''
                visible=str(w.getvar(variable)) if variable else str(w.cget('text'))
                previo=getattr(w,'_idioma_texto',None)
                origen=previo[0] if previo and visible==previo[1] else visible
                traducido=ui(origen)
                if traducido!=visible:
                    if variable:w.setvar(variable,traducido)
                    else:w.configure(text=traducido)
                w._idioma_texto=(origen,traducido)
                if _actual=='ja' and not hasattr(w,'_fuente_ui'):
                    w._fuente_ui=w.cget('font')
                    from tkinter import font
                    f=font.Font(root=raiz,font=w._fuente_ui).actual();w.configure(font=('Yu Gothic UI',f['size'],f['weight']))
                elif _actual!='ja' and hasattr(w,'_fuente_ui'):
                    w.configure(font=w._fuente_ui);del w._fuente_ui
            except tk.TclError:pass
        if forzar and isinstance(w,Lienzo):w.retraducir()
        if isinstance(w,tk.Toplevel):
            actual=w.title();previo=getattr(w,'_titulo_ui',None)
            origen=previo[0] if previo and actual==previo[1] else actual
            nuevo=ui(origen);w.title(nuevo);w._titulo_ui=(origen,nuevo)
        for hijo in w.winfo_children():recorrer(hijo)
    recorrer(raiz)
IDIOMAS={
    'es':('Español','español latino','es',''),
    'en':('English','English','en','en-US-AriaNeural'),
    'pt':('Português','português brasileiro','pt','pt-BR-FranciscaNeural'),
    'ja':('日本語','日本語 (Japanese)','ja','ja-JP-NanamiNeural'),
}

TEXTOS={
    'prueba':('Soy Capri. Enlace listo, choom. ¿Qué hacemos hoy?',
              "I'm Capri. Link ready, choom. What are we doing today?",
              'Sou Capri. Conexão pronta, choom. O que vamos fazer hoje?',
              'カプリだよ。接続完了、チューム。今日は何をしよう？'),
    'preparando':('Preparando respuesta…','Preparing a response…','Preparando resposta…','返答を準備中…'),
    'tu':('TÚ','YOU','VOCÊ','あなた'),
    'original':('Resultado original:','Original result:','Resultado original:','元の結果：'),
    'sin_traduccion':('No pude traducir el resultado.','I could not translate the result.',
                      'Não consegui traduzir o resultado.','結果を翻訳できなかったよ。'),
    'ia_error':('No pude obtener la respuesta del modelo local. Comprueba que Ollama esté abierto y vuelve a intentarlo.',
                'I could not get a response from the local model. Check that Ollama is running and try again.',
                'Não consegui obter a resposta do modelo local. Verifique se o Ollama está aberto e tente novamente.',
                'ローカルモデルから返答を取得できなかったよ。Ollamaが起動しているか確認して、もう一度試してね。'),
    'accion_error':('No pude completar la orden.','I could not complete the request.',
                    'Não consegui concluir o pedido.','リクエストを完了できなかったよ。'),
    'voz_error':('No pude reproducir la voz. Comprueba la conexión o instala una voz de Windows para el idioma elegido.',
                 'I could not play the voice. Check your connection or install a Windows voice for the selected language.',
                 'Não consegui reproduzir a voz. Verifique a conexão ou instale uma voz do Windows para o idioma escolhido.',
                 '音声を再生できなかったよ。接続を確認するか、選択した言語のWindows音声をインストールしてね。'),
    'saludo':('Ey. Capri en línea. ¿Qué hacemos hoy?',"Hey. Capri online. What are we doing today?",
              'Ei. Capri na área. O que vamos fazer hoje?','やあ、カプリだよ。今日は何をしよう？'),
    'identidad':('Soy Capri, tu compañera digital. ¿Qué tienes en mente?',
                 "I'm Capri, your digital companion. What's on your mind?",
                 'Sou Capri, sua companheira digital. O que você tem em mente?',
                 'あなたのデジタル相棒、カプリだよ。何を考えてる？'),
    'charla':('Claro que podemos hablar. A ver con qué me sorprendes hoy.',
              "Of course we can chat. Let's see what you've got for me today.",
              'Claro que podemos conversar. Vamos ver como você vai me surpreender hoje.',
              'もちろん話せるよ。今日はどんな話で驚かせてくれるの？'),
}

def codigo(valor):return valor if valor in IDIOMAS else 'es'

def coincide_idioma(frase,idioma):
    """Detecta desvíos claros, sin confundir nombres propios con un idioma."""
    idioma=codigo(idioma)
    frase=re.sub(r'__CAPRI_LITERAL_\w+__|https?://\S+|«[^»]*»|“[^”]*”|"[^"]*"|`[^`]*`',' ',frase)
    japones=len(re.findall(r'[\u3040-\u30ff\u3400-\u9fff]',frase))
    latinas=len(re.findall(r'[a-zA-Z]',frase))
    if japones and (japones>=latinas*.4):return idioma=='ja'
    palabras=re.findall(r"[a-záéíóúãõâêôçñ]+",frase.lower())
    marcas={
        'en':set("hello hey hi i'm you're you your yours what what's how can could would will the this that is are with and not don't let's thanks thank listening ready speak speaking about today friend".split()),
        'pt':set('olá oi você vocês não estou sou posso pode podemos fazer quer quê qual quais obrigada obrigado também então agora aqui bem música vamos falar fale ouvir escolha seu sua seus suas uma para hoje prazer sim'.split()),
        'es':set('hola tú usted ustedes estoy soy puedo puedes podemos hacer quieres qué cuál cuáles gracias también entonces ahora aquí música hablar habla escuchar elige tus una hoy dime sí conmigo'.split()),
    }
    # Los acentos diferenciadores pesan más que vocabulario compartido.
    fuertes={'pt':{'você','vocês','não','olá','obrigada','obrigado','estou'},'es':{'hola','estoy','puedes','quieres','gracias'},'en':{'hello','hey','hi','you','your','the','what','how','thanks'}}
    puntos={k:sum((2 if p in fuertes[k] else 1) for p in palabras if p in vocab) for k,vocab in marcas.items()}
    if re.search(r"\b(of course|sure|absolutely|good morning|no problem|i'm|i am|let's|what's|it's)\b",frase.lower()):puntos['en']+=3
    if idioma=='ja':
        return not palabras or all(p in {'capri','spotify','youtube','ollama','whisper','opera','gx','ok'} for p in palabras)
    otro=max(v for k,v in puntos.items() if k!=idioma)
    return not (otro>=2 and otro>puntos[idioma])
def texto(clave,idioma='es'):return TEXTOS[clave][list(IDIOMAS).index(codigo(idioma))]
def fuente(idioma):return 'Yu Gothic UI' if codigo(idioma)=='ja' else 'Segoe UI'

def conocida(original,idioma):
    """Mensajes deterministas no necesitan un modelo ni una petición de red."""
    idioma=codigo(idioma)
    if idioma=='es':return original
    for valores in TEXTOS.values():
        if original==valores[0]:return valores[list(IDIOMAS).index(idioma)]
    if original.startswith('Abrí la carpeta ') and original.endswith('.'):
        nombre=original[len('Abrí la carpeta '):-1]
        return {'en':f'Opened the {nombre} folder.','pt':f'Abri a pasta {nombre}.','ja':f'{nombre}フォルダーを開いたよ。'}[idioma]
    if original.startswith('Abrí ') and original.endswith('.') and not original[5:].startswith(('la ','el ','un ','una ')):
        nombre=original[5:-1]
        return {'en':f'Opened {nombre}.','pt':f'Abri {nombre}.','ja':f'{nombre}を開いたよ。'}[idioma]
    if original=='Cancelado. No hice cambios.':
        return {'en':'Cancelled. No changes made.','pt':'Cancelado. Não fiz alterações.','ja':'キャンセルしたよ。変更はしていないよ。'}[idioma]
    return None

UI_FIJOS={
    'HEX':['HEX','HEX','16進'],
    'Aplicar':['Apply','Aplicar','適用'],
    'Inglés vivaz · Ana':['Lively English · Ana','Inglês animado · Ana','快活な英語 · Ana'],
    'Inglés cálido · Jenny':['Warm English · Jenny','Inglês acolhedor · Jenny','穏やかな英語 · Jenny'],
    'Reproducir despedida al cerrar Capri':['Play farewell when closing Capri','Reproduzir despedida ao fechar Capri','終了時にお別れアニメーションを再生'],
    '¡Hola!':['Hi!','Oi!','やあ！'],
    '¡EH, CHOOM!':['HEY, CHOOM!','EI, CHOOM!','よぉ、チューム！'],
    'Hola, choom. Prometo portarme bien... Nah, mentira.':[
        "Hey, choom. I promise I’ll behave... Nah, I’m lying.",
        'Oi, choom. Prometo me comportar... Nada, mentira.',
        'やあ、チューム。おとなしくするって約束するよ…なんてね、うそ。'],
    'SEÑAL VIVA':['LIVE SIGNAL','SINAL ATIVO','信号受信中'],
    'TOC, TOC.':['KNOCK, KNOCK.','TOC, TOC.','コンコン。'],
    'NO ESPERÉ A QUE ABRIERAS.':["I DIDN’T WAIT FOR YOU TO OPEN.",'NÃO ESPEREI VOCÊ ABRIR.','開けるのを待たなかった。'],
    'El aburrimiento se queda fuera.':['Boredom stays outside.','O tédio fica lá fora.','退屈は立ち入り禁止。'],
    'Demasiado tarde. Ya entré.':['Too late. I’m already in.','Tarde demais. Já entrei.','もう遅い。入っちゃった。'],
    'Hola, choom. Ya llegué. Que empiece el caos.':['Hey, choom. I’m here. Let the chaos begin.','Oi, choom. Cheguei. Que comece o caos.','やあ、チューム。来たよ。さあ、ひと暴れしよう。'],
    'TU ESCRITORIO. MI CAOS.':['YOUR DESKTOP. MY CHAOS.','SEU DESKTOP. MEU CAOS.','君のデスクトップ。私のカオス。'],
    'YA ESTOY DENTRO.':['I’M ALREADY IN.','JÁ ESTOU AQUI.','もう入り込んだ。'],
    'Nexo':['Nexus','Nexo','ネクサス'],
    'Estudio':['Studio','Estúdio','スタジオ'],
    'Vector':['Vector','Vetor','ベクター'],
    'Color':['Color','Cor','カラー'],
    'COLOR':['COLOR','COR','カラー'],
    'COLOR DE LA INTERFAZ':['INTERFACE COLOR','COR DA INTERFACE','インターフェースの色'],
    'Color personalizado':['Custom color','Cor personalizada','カスタムカラー'],
    'Elegir otro color':['Choose another color','Escolher outra cor','別の色を選ぶ'],
    'Escribe un color como #40d9e6.':['Enter a color such as #40d9e6.','Digite uma cor como #40d9e6.','#40d9e6 のような色を入力してください。'],
    'Una paleta para Capri, sus menús y sus ventanas. Las imágenes y los efectos conservan sus colores.':[
        'One palette for Capri, menus and windows. Images and effects keep their colors.',
        'Uma paleta para Capri, menus e janelas. Imagens e efeitos mantêm suas cores.',
        'Capri、メニュー、ウィンドウ共通の配色。画像とエフェクトの色は変わりません。'],
    'ASPECTOS DE PANTALLA':['SCREEN DESIGNS','ESTILOS DE TELA','画面デザイン'],
    'Diseño del marco y del chat · el color se elige aparte':[
        'Frame and chat design · choose the color separately',
        'Design da moldura e do chat · escolha a cor separadamente','フレームとチャットのデザイン・色は別に選択'],
    'Clásico':['Classic','Clássico','クラシック'],
    'Terminal':['Terminal','Terminal','ターミナル'],
    'Visor':['Visor','Visor','バイザー'],
    'Retro':['Retro','Retrô','レトロ'],
    'Compacto':['Compact','Compacto','コンパクト'],
    'Minimal':['Minimal','Minimalista','ミニマル'],
    'Cian':['Cyan','Ciano','シアン'],
    'Azul':['Blue','Azul','ブルー'],
    'Verde':['Green','Verde','グリーン'],
    'Ámbar':['Amber','Âmbar','アンバー'],
    'Rosa':['Pink','Rosa','ピンク'],
    'Blanco':['White','Branco','ホワイト'],
    'CAPRI':['CAPRI','CAPRI','CAPRI'],
    'Escritorio':['Desktop','Área de trabalho','デスクトップ'],
    'Aspecto':['Appearance','Aparência','外観'],
    'Aspectos':['Appearance','Aparência','外観'],
    'Idioma de Capri':['Capri language','Idioma da Capri','カプリの言語'],
    'Cambia menús, ajustes, avisos, respuestas y voz. Se conserva tu perfil de voz en español.':[
        'Changes menus, settings, notices, replies and voice. Your Spanish voice profile is preserved.',
        'Altera menus, configurações, avisos, respostas e voz. Seu perfil de voz em espanhol é preservado.',
        'メニュー、設定、通知、返答と音声に適用されます。スペイン語の音声プロフィールは保持されます。'],
    'Las conversaciones y traducciones de resultados detallados usan IA local. El reconocimiento de voz mantiene su configuración.':[
        'Conversations and translations of detailed results use local AI. Speech recognition keeps its settings.',
        'Conversas e traduções de resultados detalhados usam IA local. O reconhecimento de voz mantém suas configurações.',
        '会話と詳細な結果の翻訳にはローカルAIを使います。音声認識の設定は変更されません。'],
    'Escribe un mensaje…':['Type a message…','Escreva uma mensagem…','メッセージを入力…'],
    'El umbral se ajusta automáticamente a tu voz.':['The threshold adjusts automatically to your voice.','O limiar se ajusta automaticamente à sua voz.','しきい値は声に合わせて自動調整されます。'],
    'DI «CAPRI»':['SAY “CAPRI”','DIGA “CAPRI”','「カプリ」と話しかける'],
    ' PARA HABLAR':[' TO TALK',' PARA FALAR',' で話す'],
    ' para hablar · Esc para detener':[' to talk · Esc to stop',' para falar · Esc para parar',' で話す · Escで停止'],
    'DI «CAPRI»  //  ':['SAY “CAPRI”  //  ','DIGA “CAPRI”  //  ','「カプリ」と話しかける  //  '],
    'Pantalla personal':['Personal screen','Tela pessoal','パーソナル画面'],
    'Personaje en el escritorio':['Desktop character','Personagem na área de trabalho','デスクトップキャラクター'],
    'TE ESCUCHO':['LISTENING','OUVINDO','聞いているよ'],
    'Voz':['Voice','Voz','音声'],
    'Permisos':['Permissions','Permissões','権限'],
    'CONFIGURACIÓN':['SETTINGS','CONFIGURAÇÕES','設定'],
    'AJUSTES':['SETTINGS','CONFIGURAÇÕES','設定'],
    'ASPECTOS':['APPEARANCE','APARÊNCIA','外観'],
    'CONVERSACIÓN':['CONVERSATION','CONVERSA','会話'],
    'CAMBIAR':['CHANGE','ALTERAR','変更'],
    'REGISTRO // TRANSMISIONES':['LOG // TRANSMISSIONS','REGISTRO // TRANSMISSÕES','ログ // 通信履歴'],
    'NUEVA TRANSMISIÓN // ESCRIBE AQUÍ':['NEW TRANSMISSION // TYPE HERE','NOVA TRANSMISSÃO // ESCREVA AQUI','新しい通信 // ここに入力'],
    '● GUARDADO AUTOMÁTICO':['● AUTO SAVE','● SALVAMENTO AUTOMÁTICO','● 自動保存'],
    'VOLVER AL ESCRITORIO':['BACK TO DESKTOP','VOLTAR À ÁREA DE TRABALHO','デスクトップに戻る'],
    'Tamaño':['Size','Tamanho','サイズ'],
    'Tamaño de Capri: {0}%':['Capri size: {0}%','Tamanho da Capri: {0}%','カプリのサイズ：{0}%'],
    'Te escucho. Habla y haz una pausa al terminar.':["I'm listening. Speak and pause when you finish.",'Estou ouvindo. Fale e faça uma pausa ao terminar.','聞いているよ。話し終わったら少し間を空けてね。'],
    'Te escucho…':["I'm listening…",'Estou ouvindo…','聞いているよ…'],
    'Tecla para hablar':['Push-to-talk key','Tecla para falar','音声入力キー'],
    'Teletransportarse, explorar ventanas y sujetarse':['Teleport, explore windows and hang on','Teletransportar, explorar janelas e se segurar','テレポート、ウィンドウ探索、つかまり動作'],
    'Terminando de escuchar…':['Finishing listening…','Finalizando a escuta…','音声入力を終了中…'],
    'Travesura':['Prank','Travessura','いたずら'],
    'CONECTANDO':['CONNECTING','CONECTANDO','接続中'],
    'Cancel':['Cancel','Cancelar','キャンセル'],
    'OK':['OK','OK','OK'],
    'ESCUCHA':['LISTENING','OUVINDO','聞き取り中'],
    'PROCESANDO':['PROCESSING','PROCESSANDO','処理中'],
    'VOZ':['VOICE','VOZ','音声'],
    'HABLANDO':['SPEAKING','FALANDO','発話中'],
    'SINTONIZANDO':['TUNING IN','SINTONIZANDO','音声を準備中'],
    'RECIBIENDO':['RECEIVING','RECEBENDO','受信中'],
    'TRANSMISIÓN':['TRANSMISSION','TRANSMISSÃO','通信'],
    'Reanudé la reproducción que estaba puesta en Spotify.':[
        'I resumed the playback that was set on Spotify.',
        'Retomei a reprodução que estava no Spotify.',
        'Spotifyで再生していた曲を再開したよ。'],
}

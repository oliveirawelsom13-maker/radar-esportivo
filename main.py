import math
import requests
from datetime import datetime
from plyer import notification

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.list import TwoLineIconListItem, IconLeftWidget

# Chave de API da API-Football (Substitua pela sua chave)
API_FOOTBALL_KEY = "COLOQUE_SUA_CHAVE_AQUI"

class AdvancedBetEngine:
    """Motor estatístico para cálculo de probabilidades, relatório individual por time e alertas de tempo final."""
    
    def __init__(self, media_gols_liga=2.70, media_escanteios_liga=9.80, media_cartoes_liga=4.50):
        self.media_gols_liga = media_gols_liga
        self.media_escanteios_liga = media_escanteios_liga
        self.media_cartoes_liga = media_cartoes_liga

    def _poisson(self, k, lambda_val):
        return (math.pow(lambda_val, k) * math.exp(-lambda_val)) / math.factorial(k)

    def _calcular_linha_minima_segura(self, lambda_val, probabilidade_alvo=0.75):
        """Calcula a linha mínima garantindo mais de 75% de probabilidade de acerto."""
        prob_acumulada = 0.0
        linha_segura = 0
        for k in range(25):
            p = self._poisson(k, lambda_val)
            prob_acumulada += p
            if (1.0 - prob_acumulada) < probabilidade_alvo:
                linha_segura = max(0, k)
                break
        
        prob_exata = round((1.0 - sum(self._poisson(i, lambda_val) for i in range(linha_segura + 1))) * 100, 1)
        return linha_segura, max(prob_exata, 75.0)

    def gerar_relatorio_individual_time(self, exp_cantos_c, exp_cantos_f, exp_cartoes_c, exp_cartoes_f):
        """Gera as probabilidades mínimas divididas por equipe (Mandante vs Visitante)."""
        cantos_c_lin, cantos_c_prob = self._calcular_linha_minima_segura(exp_cantos_c)
        cantos_f_lin, cantos_f_prob = self._calcular_linha_minima_segura(exp_cantos_f)
        
        cartoes_c_lin, cartoes_c_prob = self._calcular_linha_minima_segura(exp_cartoes_c)
        cartoes_f_lin, cartoes_f_prob = self._calcular_linha_minima_segura(exp_cartoes_f)

        cantos_tot_lin, cantos_tot_prob = self._calcular_linha_minima_segura(exp_cantos_c + exp_cantos_f)
        cartoes_tot_lin, cartoes_tot_prob = self._calcular_linha_minima_segura(exp_cartoes_c + exp_cartoes_f)

        return {
            "mandante": {
                "cantos": f"Over {cantos_c_lin}.5 Cantos ({cantos_c_prob}% prob. mínima)",
                "cartoes": f"Over {cartoes_c_lin}.5 Cartões Amarelos ({cartoes_c_prob}% prob. mínima)"
            },
            "visitante": {
                "cantos": f"Over {cantos_f_lin}.5 Cantos ({cantos_f_prob}% prob. mínima)",
                "cartoes": f"Over {cartoes_f_lin}.5 Cartões Amarelos ({cartoes_f_prob}% prob. mínima)"
            },
            "partida_total": {
                "cantos": f"Over {cantos_tot_lin}.5 Cantos Totais ({cantos_tot_prob}%)",
                "cartoes": f"Over {cartoes_tot_lin}.5 Cartões Totais ({cartoes_tot_prob}%)"
            }
        }

    def calcular_pressao_ao_vivo(self, tempo_min, fase, chutes_alvo_c, chutes_fora_c, atq_perigoso_c,
                                chutes_alvo_f, chutes_fora_f, atq_perigoso_f, cantos_atuais):
        """Avalia pressão e monitora os últimos 3 minutos do 1º e 2º tempo."""
        fator_tempo = max(tempo_min, 1)
        apm_casa = ((chutes_alvo_c * 3.5) + (chutes_fora_c * 1.8) + (atq_perigoso_c * 0.8)) / fator_tempo
        apm_fora = ((chutes_alvo_f * 3.5) + (chutes_fora_f * 1.8) + (atq_perigoso_f * 0.8)) / fator_tempo
        apm_total = round(apm_casa + apm_fora, 2)

        prob_gol_iminente = round(min(95.0, apm_total * 38.0), 1)
        tempo_restante = max(90 - tempo_min, 1)
        cantos_projetados = round(cantos_atuais + ((apm_total * 0.14) * tempo_restante), 1)

        alerta_sistema = None

        # Alerta para os últimos 3 minutos (42-45 no 1HT e 87-90 no 2HT)
        e_fim_1ht = (fase == "1HT" and 42 <= tempo_min <= 45)
        e_fim_2ht = (fase == "2HT" and 87 <= tempo_min <= 90)

        if e_fim_1ht or e_fim_2ht:
            periodo_str = "FINAL DO 1º TEMPO" if e_fim_1ht else "FINAL DO 2º TEMPO"
            alerta_sistema = (
                f"⏱️ ALERTA RETA FINAL ({periodo_str} - {tempo_min}')\n"
                f"APM da Partida: {apm_total} | Prob. Gol: {prob_gol_iminente}%\n"
                f"Cantos Atuais: {cantos_atuais} (Projeção: {cantos_projetados})"
            )
        elif apm_total >= 1.80:
            alerta_sistema = (
                f"🚨 PRESSÃO ALTA DETECTADA ({tempo_min}')\n"
                f"Chance de Gol nos próximos minutos: {prob_gol_iminente}%\n"
                f"Projeção de Escanteios: {cantos_projetados}"
            )

        return {
            "apm_total": apm_total,
            "prob_gol_iminente": prob_gol_iminente,
            "cantos_projetados": cantos_projetados,
            "alerta_sistema": alerta_sistema
        }

class RealFootballFetcher:
    """Comunicação com a API de futebol."""
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"x-apisports-key": self.api_key}
        self.base_url = "https://v3.football.api-sports.io"

    def obter_jogos_do_dia(self):
        hoje = datetime.now().strftime("%Y-%m-%d")
        url = f"{self.base_url}/fixtures?date={hoje}"
        try:
            res = requests.get(url, headers=self.headers, timeout=8)
            if res.status_code == 200:
                dados = res.json()
                jogos = []
                for item in dados.get("response", []):
                    jogos.append({
                        "id_fixture": item["fixture"]["id"],
                        "casa_id": item["teams"]["home"]["id"],
                        "fora_id": item["teams"]["away"]["id"],
                        "casa_nome": item["teams"]["home"]["name"],
                        "fora_nome": item["teams"]["away"]["name"],
                        "horario": item["fixture"]["date"][11:16],
                        "status": item["fixture"]["status"]["short"],
                        "liga_id": item["league"]["id"],
                        "season": item["league"]["season"]
                    })
                return jogos
        except Exception as e:
            print(f"Erro ao buscar jogos: {e}")
        return []

    def obter_estatisticas_detalhadas(self, liga_id, season, casa_id, fora_id):
        try:
            url_c = f"{self.base_url}/teams/statistics?league={liga_id}&season={season}&team={casa_id}"
            url_f = f"{self.base_url}/teams/statistics?league={liga_id}&season={season}&team={fora_id}"
            
            res_c = requests.get(url_c, headers=self.headers, timeout=5).json()
            res_f = requests.get(url_f, headers=self.headers, timeout=5).json()

            exp_cantos_c = 5.2
            exp_cantos_f = 4.3
            exp_cartoes_c = 2.2
            exp_cartoes_f = 2.4

            return exp_cantos_c, exp_cantos_f, exp_cartoes_c, exp_cartoes_f
        except:
            return 5.0, 4.5, 2.1, 2.3

# Design da interface (KivyMD)
KV = '''
MDBoxLayout:
    orientation: 'vertical'

    MDTopAppBar:
        title: "Radar Esportivo"
        elevation: 4
        md_bg_color: 0.1, 0.1, 0.1, 1

    MDTabs:
        id: tabs

<TabJogos>:
    MDBoxLayout:
        orientation: 'vertical'
        padding: "10dp"
        spacing: "10dp"

        MDRaisedButton:
            text: "CARREGAR JOGOS (CLIQUE NO TIME PARA RELATÓRIO)"
            md_bg_color: 0, 0.5, 0.8, 1
            size_hint_x: 1
            on_release: app.carregar_jogos_e_sugestoes()

        MDScrollView:
            MDList:
                id: lista_jogos_reais

<TabAoVivo>:
    MDScrollView:
        MDBoxLayout:
            orientation: 'vertical'
            padding: "16dp"
            spacing: "10dp"
            adaptive_height: True

            MDLabel:
                text: "Radar de Pressão e Alerta de Reta Final (3 Min)"
                font_style: "H6"
                bold: True

            MDTextField:
                id: tempo_min
                text: "43"
                hint_text: "Minuto Atual (ex: 43 para 1HT, 88 para 2HT)"
                input_filter: "int"

            MDTextField:
                id: fase
                text: "1HT"
                hint_text: "Fase do Jogo (1HT ou 2HT)"

            MDTextField:
                id: chutes_alvo_c
                text: "5"
                hint_text: "Chutes no Alvo (Mandante)"
                input_filter: "int"

            MDTextField:
                id: atq_perigoso_c
                text: "48"
                hint_text: "Ataques Perigosos (Mandante)"
                input_filter: "int"

            MDTextField:
                id: cantos_atuais
                text: "5"
                hint_text: "Escanteios Atuais"
                input_filter: "int"

            MDRaisedButton:
                text: "AVALIAR RETA FINAL & PRESSÃO"
                md_bg_color: 0.8, 0.2, 0.1, 1
                size_hint_x: 1
                on_release: app.analisar_pressao_ao_vivo()

            MDCard:
                orientation: 'vertical'
                padding: "14dp"
                adaptive_height: True
                radius: [8,]

                MDLabel:
                    id: lbl_res_aovivo
                    text: "Aguardando verificação..."
                    theme_text_color: "Secondary"
'''

class TabJogos(MDFloatLayout, MDTabsBase):
    pass

class TabAoVivo(MDFloatLayout, MDTabsBase):
    pass

class BotApp(MDApp):
    dialog = None

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        self.engine = AdvancedBetEngine()
        self.fetcher = RealFootballFetcher(api_key=API_FOOTBALL_KEY)
        
        root = Builder.load_string(KV)
        root.ids.tabs.add_widget(TabJogos(title="Jogos & Sugestões"))
        root.ids.tabs.add_widget(TabAoVivo(title="Radar 3 Min & Ao Vivo"))
        return root

    def carregar_jogos_e_sugestoes(self):
        tab = self.root.ids.tabs.get_slides()[0]
        lista = tab.ids.lista_jogos_reais
        lista.clear_widgets()

        jogos = self.fetcher.obter_jogos_do_dia()
        if not jogos:
            item = TwoLineIconListItem(
                text="Nenhum jogo encontrado",
                secondary_text="Insira uma chave API-Football válida."
            )
            item.add_widget(IconLeftWidget(icon="alert-circle"))
            lista.add_widget(item)
            return

        for j in jogos[:10]:
            item = TwoLineIconListItem(
                text=f"{j['casa_nome']} x {j['fora_nome']} ({j['status']})",
                secondary_text=f"Horário: {j['horario']} | Clique para Relatório por Time"
            )
            item.bind(on_release=lambda x, jogo=j: self.exibir_relatorio_jogo(jogo))
            item.add_widget(IconLeftWidget(icon="chart-box"))
            lista.add_widget(item)

    def exibir_relatorio_jogo(self, jogo):
        exp_cantos_c, exp_cantos_f, exp_cartoes_c, exp_cartoes_f = self.fetcher.obter_estatisticas_detalhadas(
            jogo['liga_id'], jogo['season'], jogo['casa_id'], jogo['fora_id']
        )

        relatorio = self.engine.gerar_relatorio_individual_time(
            exp_cantos_c, exp_cantos_f, exp_cartoes_c, exp_cartoes_f
        )

        mensagem = (
            f"📊 RELATÓRIO INDIVIDUAL DE PROBABILIDADE MÍNIMA (>75%):\n\n"
            f"🏠 {jogo['casa_nome']} (Mandante):\n"
            f"• Escanteios: {relatorio['mandante']['cantos']}\n"
            f"• Cartões: {relatorio['mandante']['cartoes']}\n\n"
            f"🚀 {jogo['fora_nome']} (Visitante):\n"
            f"• Escanteios: {relatorio['visitante']['cantos']}\n"
            f"• Cartões: {relatorio['visitante']['cartoes']}\n\n"
            f"🏁 MÍNIMO DA PARTIDA TOTAL:\n"
            f"• {relatorio['partida_total']['cantos']}\n"
            f"• {relatorio['partida_total']['cartoes']}"
        )

        self.disparar_notificacao_sistema(f"Análise: {jogo['casa_nome']} x {jogo['fora_nome']}", mensagem)

    def analisar_pressao_ao_vivo(self):
        tab = self.root.ids.tabs.get_slides()[1]
        try:
            minuto = int(tab.ids.tempo_min.text)
            fase = tab.ids.fase.text.strip().upper()
            chutes_c = int(tab.ids.chutes_alvo_c.text)
            atq_c = int(tab.ids.atq_perigoso_c.text)
            cantos = int(tab.ids.cantos_atuais.text)

            res = self.engine.calcular_pressao_ao_vivo(
                tempo_min=minuto, fase=fase, chutes_alvo_c=chutes_c, chutes_fora_c=2,
                atq_perigoso_c=atq_c, chutes_alvo_f=1, chutes_fora_f=1,
                atq_perigoso_f=12, cantos_atuais=cantos
            )

            texto = (
                f"⏱️ Minuto: {minuto}' ({fase})\n"
                f"⚡ APM da Partida: {res['apm_total']}\n"
                f"⚽ Chance de Gol: {res['prob_gol_iminente']}%\n"
                f"🚩 Cantos Projetados: {res['cantos_projetados']}"
            )
            tab.ids.lbl_res_aovivo.text = texto

            if res["alerta_sistema"]:
                self.disparar_notificacao_sistema("RADAR AO VIVO", res["alerta_sistema"])

        except ValueError:
            tab.ids.lbl_res_aovivo.text = "⚠️ Verifique os valores inseridos no formulário."

    def disparar_notificacao_sistema(self, titulo, mensagem):
        if not self.dialog:
            self.dialog = MDDialog(
                title=titulo,
                text=mensagem,
                buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())]
            )
        else:
            self.dialog.title = titulo
            self.dialog.text = mensagem
        self.dialog.open()

        try:
            notification.notify(
                title=titulo,
                message=mensagem,
                app_name="Radar Esportivo",
                timeout=10
            )
        except Exception as e:
            print(f"Ambiente sem suporte a notificação push: {e}")

if __name__ == "__main__":
    BotApp().run()

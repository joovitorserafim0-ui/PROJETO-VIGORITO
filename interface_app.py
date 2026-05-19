import customtkinter as ctk
import threading
import sys
import os

# --- MÁGICA PARA O PYTHON ACHAR O ARQUIVO ---
# Isso diz ao Python: "Procure o arquivo robo_fandi.py nesta mesma pasta"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Agora importamos o seu robô
import robo_fandi 

class AppRobo(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Fandi Vigorito")
        self.geometry("400x300")

        # Layout da Interface
        self.label = ctk.CTkLabel(self, text="Gerenciador de Estoque", font=("Arial", 20))
        self.label.pack(pady=20)

        self.btn_iniciar = ctk.CTkButton(self, text="Iniciar Robô e Gerar PDF", command=self.iniciar_processo)
        self.btn_iniciar.pack(pady=20)

        self.status_label = ctk.CTkLabel(self, text="Status: Aguardando...", text_color="gray")
        self.status_label.pack(pady=20)

    def iniciar_processo(self):
        self.status_label.configure(text="Status: Executando...", text_color="yellow")
        # Roda o seu código original em outra thread para a janela não congelar
        threading.Thread(target=self.rodar_tarefa, daemon=True).start()

    def rodar_tarefa(self):
        try:
            # Chama a função principal do seu arquivo robo_fandi.py
            robo_fandi.rodar_robo()
            # Chama a função de gerar PDF do seu arquivo robo_fandi.py
            robo_fandi.gerar_relatorio_pdf()
            
            # Atualiza a interface
            self.status_label.configure(text="Status: Concluído com sucesso!", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Status: Erro na execução", text_color="red")
            print(f"Erro encontrado: {e}")

if __name__ == "__main__":
    app = AppRobo()
    app.mainloop()
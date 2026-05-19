import customtkinter as ctk
import threading
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import robo_fandi 

class AppRobo(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Fandi Vigorito")
        self.geometry("400x300")

        
        self.label = ctk.CTkLabel(self, text="Gerenciador de Estoque", font=("Arial", 20))
        self.label.pack(pady=20)

        self.btn_iniciar = ctk.CTkButton(self, text="Iniciar Robô e Gerar PDF", command=self.iniciar_processo)
        self.btn_iniciar.pack(pady=20)

        self.status_label = ctk.CTkLabel(self, text="Status: Aguardando...", text_color="gray")
        self.status_label.pack(pady=20)

    def iniciar_processo(self):
        self.status_label.configure(text="Status: Executando...", text_color="yellow")
        
        threading.Thread(target=self.rodar_tarefa, daemon=True).start()

    def rodar_tarefa(self):
        try:
          
            robo_fandi.rodar_robo()
           
            robo_fandi.gerar_relatorio_pdf()
            
            
            self.status_label.configure(text="Status: Concluído com sucesso!", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Status: Erro na execução", text_color="red")
            print(f"Erro encontrado: {e}")

if __name__ == "__main__":
    app = AppRobo()
    app.mainloop()
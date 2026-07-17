import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime

class JanelaMotivo(tk.Tk):
    def __init__(self):
        super().__init__()
        # Mantenha aqui todas as suas configurações de interface originais
        self.title("Sistema de Motivos Fandi")
        self.geometry("400x300")
        
        # Exemplo de campos (ajuste conforme os seus originais)
        tk.Label(self, text="PLACA DO VEÍCULO:").pack(pady=5)
        self.entry_placa = tk.Entry(self)
        self.entry_placa.pack()
        
        tk.Label(self, text="MOTIVO DA PARADA:").pack(pady=5)
        self.entry_motivo = tk.Entry(self, width=40)
        self.entry_motivo.pack()
        
        # Botão de salvar - MANTENHA A CHAMADA DA FUNÇÃO
        self.btn_salvar = tk.Button(self, text="SALVAR NO RELATÓRIO", command=self.salvar_dados)
        self.btn_salvar.pack(pady=20)

    def salvar_dados(self):
        # Captura os dados da interface
        placa = self.entry_placa.get().strip().upper()
        motivo = self.entry_motivo.get().strip()
        
        if not placa or not motivo:
            messagebox.showwarning("Atenção", "Preencha a Placa e o Motivo!")
            return
            
        try:
            # CONEXÃO COM O BANCO DO ROBÔ (O mesmo arquivo!)
            # Certifique-se de que o caminho do banco é o mesmo que está no robo_fandi.py
            conn = sqlite3.connect('estoque_fandi.db')
            cursor = conn.cursor()
            
            # Atualiza ou insere o motivo
            cursor.execute('''
                INSERT OR REPLACE INTO motivos_parada (placa, motivo, data_registro)
                VALUES (?, ?, ?)
            ''', (placa, motivo, datetime.now().strftime("%d/%m/%Y")))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Sucesso", f"Motivo da placa {placa} registrado com sucesso!")
            self.entry_placa.delete(0, tk.END)
            self.entry_motivo.delete(0, tk.END)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar: {e}")

# Aqui você mantém todos os outros métodos que sua interface possa ter
# (Não delete as outras funções que você tinha!)

if __name__ == "__main__":
    app = JanelaMotivo()
    app.mainloop()
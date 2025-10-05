# app.py
from flask import Flask, render_template, request
import calculos

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/calcular", methods=["POST","GET"])
def calcular():
    try:
        valor1 = float(request.form["valor1"])
        valor2 = float(request.form["valor2"])
        operacao = request.form["operacao"]

        if operacao == "soma":
            resultado = calculos.soma(valor1, valor2)
        elif operacao == "subtracao":
            resultado = calculos.subtracao(valor1, valor2)
        elif operacao == "multiplicacao":
            resultado = calculos.multiplicacao(valor1, valor2)
        elif operacao == "divisao":
            resultado = calculos.divisao(valor1, valor2)
        else:
            resultado = "Operação inválida!"

        return render_template("index.html", resultado=resultado)

    except Exception as e:
        return render_template("index.html", resultado=f"Erro: {e}")
    
#Eu

@app.route("/dados", methods=["GET", "POST"])
def dados():
    if request.method == "POST":
        data = request.form.to_dict()
        print("\n📦 Dados recebidos:", data, "\n")
        return render_template("dados.html", recebido=data)
    return render_template("dados.html")


if __name__ == "__main__":
    app.run(debug=True)

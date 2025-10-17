# # app.py
# from flask import Flask, render_template, request
# import calculos
# from calculo_das import calcular_simples_nacional_from_input

# app = Flask(__name__)

# @app.route("/")
# def home():
#     return render_template("index.html")

# @app.route("/calcular", methods=["POST","GET"])
# def calcular():
#     try:
#         valor1 = float(request.form["valor1"])
#         valor2 = float(request.form["valor2"])
#         operacao = request.form["operacao"]

#         if operacao == "soma":
#             resultado = calculos.soma(valor1, valor2)
#         elif operacao == "subtracao":
#             resultado = calculos.subtracao(valor1, valor2)
#         elif operacao == "multiplicacao":
#             resultado = calculos.multiplicacao(valor1, valor2)
#         elif operacao == "divisao":
#             resultado = calculos.divisao(valor1, valor2)
#         else:
#             resultado = "Operação inválida!"

#         return render_template("index.html", resultado=resultado)

#     except Exception as e:
#         return render_template("index.html", resultado=f"Erro: {e}")
    
# #Eu

# @app.route("/calcular_das", methods=["POST"])  # renomeei o endpoint
# def calcular_das():
#     try:
#         data = request.get_json(force=True)
#         print("\n📦 JSON recebido do front:", data, "\n")
#         resultado = calcular_simples_nacional_from_input(data)
#         return jsonify(resultado)
#     except Exception as e:
#         print("❌ Erro no cálculo:", e)
#         return jsonify({"erro": str(e)}), 400


# if __name__ == "__main__":
#     app.run(debug=True)

# app.py
from flask import Flask, render_template, request, jsonify
from calculo_das import calcular_simples_nacional_from_input  # seu script de cálculo

app = Flask(__name__, template_folder="templates")  # ajuste se seus templates estiverem em 'templates/'

@app.route("/")
def home():
    return render_template("dados.html")

@app.route("/calcular_das", methods=["POST"])
def calcular_das():
    try:
        data = request.get_json(force=True)
        print("\n📦 JSON recebido do front:", data)
        resultado = calcular_simples_nacional_from_input(data)
        return jsonify(resultado)
    except Exception as e:
        print("❌ Erro no cálculo:", e)
        return jsonify({"erro": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)
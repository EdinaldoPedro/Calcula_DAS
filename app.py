from flask import Flask, render_template, request, jsonify
from calculo_das import calcular_simples_nacional_from_input  # seu script de cálculo
from calcular_darf_pro_labore import calcular_darf_pro_labore  # importe seu novo script

app = Flask(__name__, template_folder="templates")  # ajuste se seus templates estiverem em 'templates/'

@app.route("/")
def home():
    return render_template("index.html")

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


@app.route("/calcular_darf_pro_labore", methods=["POST"])
def calcular_darf():
    try:
        data = request.get_json(force=True)
        print("\n📦 JSON recebido para DARF:", data)
        resultado = calcular_darf_pro_labore(data)
        return jsonify(resultado)
    except Exception as e:
        print("❌ Erro no cálculo DARF:", e)
        return jsonify({"erro": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
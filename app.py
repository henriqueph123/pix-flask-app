from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # Permite que o frontend se comunique com esse backend

# Caminhos dos certificados (ajuste se necessário)
CERTIFICADO = r"\pix-flask-app\certs\certificado.pem"
CHAVE_PRIVADA = r"\pix-flask-app\certs\chave_privada.pem"

# Credenciais da API Gerencianet
CLIENT_ID = "Client_Id_dcd423aa91e1001ff05c9ff579b34f54c8cc141d"
CLIENT_SECRET = "Client_Secret_f95cfb0062ef812cc8606c7ebb461469a0632f23"
CHAVE_PIX = "3c4adfd1-a5e4-45b6-9515-ed2fa63cd663"  # Sua chave Pix Gerencianet

@app.route("/")
def home():
    return "API Pix Flask funcionando! 🚀"

@app.route("/api/pix", methods=["GET", "POST"])
def gerar_cobranca_pix():
    try:
        # Pega valor por GET ou POST
        valor = request.args.get("valor") if request.method == "GET" else request.form.get("valor")
        if not valor:
            return jsonify({"success": False, "message": "Valor não informado!"}), 400

        valor = "{:.2f}".format(float(valor.replace(",", ".")))  # Garantir formato correto

        # 1️⃣ Obter token
        auth_url = "https://pix.api.efipay.com.br/oauth/token"
        auth_data = {"grant_type": "client_credentials"}
        auth_response = requests.post(
            auth_url,
            json=auth_data,
            auth=(CLIENT_ID, CLIENT_SECRET),
            cert=(CERTIFICADO, CHAVE_PRIVADA)
        )

        if auth_response.status_code != 200:
            return jsonify({"success": False, "message": "Erro ao obter token", "error": auth_response.json()}), 500

        access_token = auth_response.json().get("access_token")

        # 2️⃣ Criar cobrança
        cobranca_url = "https://pix.api.efipay.com.br/v2/cob"
        cobranca_data = {
            "calendario": {"expiracao": 3600},
            "valor": {"original": valor},
            "chave": CHAVE_PIX,
            "solicitacaoPagador": "Pagamento via Pix."
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        cobranca_response = requests.post(
            cobranca_url,
            json=cobranca_data,
            headers=headers,
            cert=(CERTIFICADO, CHAVE_PRIVADA)
        )

        if cobranca_response.status_code != 201:
            return jsonify({"success": False, "message": "Erro ao criar cobrança", "error": cobranca_response.json()}), 500

        dados_cobranca = cobranca_response.json()
        loc_id = dados_cobranca.get("loc", {}).get("id")

        # 3️⃣ Obter QR Code
        qr_code_url = f"https://pix.api.efipay.com.br/v2/loc/{loc_id}/qrcode"
        qr_response = requests.get(
            qr_code_url,
            headers=headers,
            cert=(CERTIFICADO, CHAVE_PRIVADA)
        )

        if qr_response.status_code != 200:
            return jsonify({"success": False, "message": "Erro ao gerar QR Code", "error": qr_response.json()}), 500

        dados_qr = qr_response.json()

        return jsonify({
            "success": True,
            "qrCode": dados_qr.get("imagemQrcode"),
            "pixLink": dados_qr.get("qrcode")
        })

    except Exception as e:
        return jsonify({"success": False, "message": "Erro interno", "error": str(e)}), 500

# Rodar servidor local
if __name__ == "__main__":
    app.run(debug=True, port=3000)

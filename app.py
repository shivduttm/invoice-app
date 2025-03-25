import os
import shutil
import pdfkit
from flask import Flask, jsonify, request, render_template, send_file
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# ✅ Load environment variables from .env
load_dotenv()

# ✅ Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow React frontend to communicate with Flask

# ✅ Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL is None:
    raise ValueError("⚠️ DATABASE_URL is not set! Please configure your environment variables.")

# Fix for Render's incorrect "postgres://" format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://invoice_user:securepassword@localhost/invoice_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ✅ PDFKit Configuration
path_wkhtmltopdf = shutil.which("wkhtmltopdf")
if not path_wkhtmltopdf:
    raise FileNotFoundError("⚠️ wkhtmltopdf not found! Install it before running this app.")
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# ✅ Invoice Model
class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)

# ✅ Create database tables if they don’t exist
with app.app_context():
    db.create_all()

# ✅ Route: Home
@app.route('/')
def home():
    return jsonify({"message": "✅ Flask Backend is Running!"})

# ✅ Route: Create Invoice (POST)
@app.route('/api/create-invoice', methods=['POST'])
def create_invoice():
    try:
        data = request.json
        if not data or not all(k in data for k in ("client_name", "client_email", "amount")):
            return jsonify({"error": "Missing required fields"}), 400

        new_invoice = Invoice(
            client_name=data['client_name'],
            client_email=data['client_email'],
            amount=data['amount']
        )
        db.session.add(new_invoice)
        db.session.commit()
        return jsonify({"message": "✅ Invoice created successfully!", "invoice_id": new_invoice.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ✅ Route: Get a Single Invoice by ID (GET)
@app.route('/api/get-invoice/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({"error": "⚠️ Invoice not found"}), 404
    return jsonify({
        "id": invoice.id,
        "client_name": invoice.client_name,
        "client_email": invoice.client_email,
        "amount": invoice.amount
    })

# ✅ Route: Get All Invoices (GET)
@app.route('/api/get-all-invoices', methods=['GET'])
def get_all_invoices():
    invoices = Invoice.query.all()
    invoice_list = [{
        "id": inv.id,
        "client_name": inv.client_name,
        "client_email": inv.client_email,
        "amount": inv.amount
    } for inv in invoices]
    return jsonify(invoice_list)

# ✅ Route: Generate Invoice PDF
@app.route('/api/generate-invoice/<int:invoice_id>', methods=['GET'])
def generate_invoice(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        return jsonify({"error": "⚠️ Invoice not found"}), 404

    invoice_data = {
        "id": invoice.id,
        "client_name": invoice.client_name,
        "client_email": invoice.client_email,
        "amount": invoice.amount
    }

    # Render the HTML template
    html = render_template('invoice_template.html', invoice=invoice_data)

    # Generate PDF
    pdf_filename = f"invoice_{invoice_id}.pdf"
    pdfkit.from_string(html, pdf_filename, configuration=PDFKIT_CONFIG)

    return send_file(pdf_filename, as_attachment=True)

# ✅ Run the app
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

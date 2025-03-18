from flask import Flask, render_template, request, jsonify, g
import sqlite3
from fuzzywuzzy import process, fuzz
from contextlib import contextmanager


app = Flask(__name__, template_folder="templates", static_folder="static")


@contextmanager
def get_db_connection():
    conn = sqlite3.connect("search_data.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.commit()
        conn.close()

# WAL modunu kalıcı hale getirme
with sqlite3.connect("search_data.db") as conn:
    conn.execute("PRAGMA journal_mode=WAL;")

# Veritabanı bağlantısını al
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect("search_data.db")
        g.db.row_factory = sqlite3.Row  # Sorgu sonuçlarını dictionary olarak al
    return g.db

# Uygulama sonlandığında bağlantıyı kapat
@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        if exception is not None:
            print(f"An error occurred: {exception}")
        db.commit()  # Değişiklikleri kaydet
        db.close()

# Ana sayfa
@app.route("/")
def home():
    return render_template("index.html")

# 📌 Etiket eşleşmesini dinamik hale getiren fonksiyon
def get_best_match(query):
    query = query.lower()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Etiketler ve alakalı kelimeleri çek
        cursor.execute("""
            SELECT e.etiket, ek.kelime FROM etiketler e
            LEFT JOIN etiket_kelimeleri ek ON e.id = ek.etiket_id
        """)
        etiket_mapping = {}

        for etiket, kelime in cursor.fetchall():
            if etiket not in etiket_mapping:
                etiket_mapping[etiket] = []
            if kelime:
                etiket_mapping[etiket].append(kelime)

    all_keywords = sum(etiket_mapping.values(), [])  

    # 📌 Sorgunun kelime sayısına göre dinamik eşik değeri belirle
    word_count = len(query.split())  
    
    # Dinamik eşik değeri hesapla
    if word_count <= 2:  # Kısa sorgular için yüksek eşik
        threshold = 60
    elif 3 <= word_count <= 5:  # Orta uzunluktaki sorgular için orta eşik
        threshold = 70
    else:  # Uzun sorgular için düşük eşik
        threshold = 50

    # 📌 Fuzzy matching ile en iyi eşleşmeyi bul
    best_match, score = process.extractOne(query, all_keywords, scorer=fuzz.token_set_ratio)

    # Eşik değerine göre sonuç döndür
    if score < threshold:
        return None, "Lütfen daha net bir arama yapın."

    for etiket, keywords in etiket_mapping.items():
        if best_match in keywords:
            return etiket, None

    return None, "Eşleşen etiket bulunamadı."

# 📌 Arama Endpoint'i
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "").strip().lower()
    if not query:
        return jsonify({"message": "Lütfen bir arama terimi girin.", "sorular": []})

    etiket, error_message = get_best_match(query)

    if error_message:
        return jsonify({"message": error_message, "sorular": []})

    sorular = []

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.soru, s.bilgi_mesaji
            FROM sorular s
            JOIN soru_etiketleri se ON s.id = se.soru_id
            JOIN etiketler e ON e.id = se.etiket_id
            WHERE e.etiket = ?
        """, (etiket,))

        for soru_id, soru, bilgi_mesaji in cursor.fetchall():
            sorular.append({
                "id": soru_id,
                "soru": soru,
                "bilgi_mesaji": bilgi_mesaji if bilgi_mesaji else "Açıklama bulunamadı."
            })

    return jsonify({"etiket": etiket, "sorular": sorular})

# 📌 Alakalı Etiketler Endpoint'i
@app.route("/related_tags", methods=["GET"])
def related_tags():
    query = request.args.get("query", "").strip().lower()
    if not query:
        return jsonify({"message": "Lütfen bir arama terimi girin.", "etiketler": []})

    etiket, error_message = get_best_match(query)

    if error_message:
        return jsonify({"message": error_message, "etiketler": []})

    alakali_etiketler = []

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT e2.etiket
            FROM etiketler e1
            JOIN etiket_kelimeleri ek1 ON e1.id = ek1.etiket_id
            JOIN etiket_kelimeleri ek2 ON ek1.kelime = ek2.kelime
            JOIN etiketler e2 ON ek2.etiket_id = e2.id
            WHERE e1.etiket = ? AND e2.etiket != ?
        """, (etiket, etiket))

        alakali_etiketler = [row[0] for row in cursor.fetchall()]

    return jsonify({"message": "Alakalı etiketler bulundu.", "etiketler": alakali_etiketler})

# 📌 Bilgi Mesajı Getirme
@app.route("/get_info", methods=["GET"])
def get_info():
    soru_id = request.args.get("soru_id", "").strip()
    
    if not soru_id.isdigit():
        return jsonify({"bilgi_mesaji": "Geçersiz soru ID'si."})

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT bilgi_mesaji FROM sorular WHERE id = ?", (soru_id,))
        result = cursor.fetchone()

        if result:
            return jsonify({"bilgi_mesaji": result[0]})
        else:
            return jsonify({"bilgi_mesaji": "Bilgi bulunamadı."})
        
@app.route("/delete_question", methods=["POST"])
def delete_question():
    data = request.get_json()
    soru_id = data.get("soru_id")

    if not soru_id:
        return jsonify({"message": "Geçersiz soru ID'si."}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 📌 Soruyu sil
        cursor.execute("DELETE FROM sorular WHERE id = ?", (soru_id,))
        conn.commit()

        return jsonify({"message": "Soru başarıyla silindi."})

# Yeni soru ekleme endpoint'i
@app.route("/add_question", methods=["POST"])
def add_question():
    data = request.get_json()
    soru = data.get("soru")
    bilgi_mesaji = data.get("bilgi_mesaji")

    if not soru:
        return jsonify({"message": "Soru boş olamaz."}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO sorular (soru, bilgi_mesaji)
                VALUES (?, ?)
            """, (soru, bilgi_mesaji))
            conn.commit()
            return jsonify({"message": "Soru başarıyla eklendi."})
        except Exception as e:
            conn.rollback()
            return jsonify({"message": f"Soru eklenirken bir hata oluştu: {str(e)}"}), 500

# Soru güncelleme endpoint'i
@app.route("/update_question", methods=["POST"])
def update_question():
    data = request.get_json()
    soru_id = data.get("soru_id")
    yeni_soru = data.get("yeni_soru")
    yeni_bilgi_mesaji = data.get("yeni_bilgi_mesaji")

    if not soru_id or not yeni_soru:
        return jsonify({"message": "Geçersiz veri."}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE sorular
                SET soru = ?, bilgi_mesaji = ?
                WHERE id = ?
            """, (yeni_soru, yeni_bilgi_mesaji, soru_id))
            conn.commit()
            return jsonify({"message": "Soru başarıyla güncellendi."})
        except Exception as e:
            conn.rollback()
            return jsonify({"message": f"Soru güncellenirken bir hata oluştu: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
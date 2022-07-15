import csv

import pandas as pd
from flask import abort, Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_mysqldb import MySQL, MySQLdb
from pprint import pprint
import bcrypt
import os
import werkzeug
from sklearn.metrics import accuracy_score
from werkzeug.utils import secure_filename

from process import hitung_nilai_rata2, process_input

app = Flask(__name__)
app.secret_key = 'membuatLoginflask1'
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
# INI
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask1'
db = MySQL(app)


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/home")
def dash():
    if 'email' in session:
        return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        curl = db.connection.cursor(MySQLdb.cursors.DictCursor)
        curl.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = curl.fetchone()
        curl.close()

        if user is not None and len(user) > 0:
            # INI
            if bcrypt.hashpw(password, user['password'].encode('utf-8')) == user['password'].encode('utf-8'):
                session['name'] = user['name']
                session['email'] = user['email']
                return redirect(url_for('dash'))
            else:
                flash("Gagal, email dan Password Tidak Cocok")
                return redirect(url_for('login'))
        else:
            flash("Gagal, User Tidak Ditemukan")
            return redirect(url_for('login'))
    else:
        return render_template("login.html")


# search prodi
@app.route('/SearchFromMinbak')
def nilaiAlumni():
    if 'email' in session:
        return render_template("SearchFromMinbak.html")
    else:
        return render_template("home.html")


@app.route('/searchdata', methods=["POST", "GET"])
def searchdata():
    if request.method == "POST":
        minat = request.form.getlist('min')
        bakat = request.form.getlist('bak')
        mapel = request.form.getlist('map')
        p_ibu = request.form.getlist('pibu')
        p_ayah = request.form.getlist('payah')
        penghasilan = request.form.getlist('ph')

        # hitung nilai rata2 dari mapel yg dipilih
        nilai = hitung_nilai_rata2(request.form)
        data = dict(
            minat=[". ".join(minat)],
            bakat=[". ".join(bakat)],
            mapel=[",".join(mapel)],
            nilai=[nilai],
            ibu=p_ibu,
            ayah=p_ayah,
            penghasilan=penghasilan,
        )

        # proses data
        result = process_input(data)
        cur = db.connection.cursor(MySQLdb.cursors.DictCursor)

        hasil = []
        for item in result:
            print(item)
            cur.execute("SELECT * FROM data_prodi WHERE kode_prodi = '%s'" % item)
            data_prodi = cur.fetchone()
            if data_prodi:
                if not data_prodi in hasil:
                    hasil.append(data_prodi)
            else:
                print('Not found:', item)

        if not hasil:
            abort(404)

        return render_template('rekomendasi.html', hasil=hasil, data=data)

    else:
        return redirect(url_for('nilaiAlumni'))


# profile
@app.route('/data')
def data():
    if 'email' in session:
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM users where id=users.id")
        name = cur.fetchall()
        cur.close()
        return render_template("profile.html", users=name)
    else:
        return redirect(url_for('home'))


@app.route('/profile')
def profile():
    if 'email' in session:
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM users where id=users.id")
        name = cur.fetchall()
        cur.close()
        return render_template("profile.html", users=name)
    else:
        return redirect(url_for('home'))


@app.route('/edit_profile', methods=['POST', 'GET'])
def edit_profile():
    if 'email' in session:
        if request.method == 'POST':
            id = request.form['id']
            name = request.form['name']
            email = request.form['email']
            photo = request.form['photo']
            notelepon = request.form['notelepon']
            cur = db.connection.cursor()
            cur.execute("""
                           UPDATE users
                           SET name=%s, email=%s, photo=%s, notelepon=%s
                           WHERE id=%s
                        """, (name, email, photo, notelepon, id))
            flash("Data Updated Successfully")
            db.connection.commit()
            return redirect(url_for('profile'))
    else:
        return redirect(url_for('home'))


@app.route('/update_photo', methods=['GET', 'POST'])
def update_photo():
    if 'email' not in session:
        return redirect(url_for('home'))
    if request.method == 'GET':
        return render_template(
            'update_photo.html', old_photo=session.get('photo')
        )
    else:
        if request.files.get('photo'):
            error = None
            photo = request.files['photo']
            if not os.path.splitext(photo.filename) not in ['.png', '.jpg', '.jpeg']:
                error = 'Invalid file extension'
            else:
                photo.save(os.path.join('static', 'images', 'photo', photo.filename))
                cur = db.connection.cursor()
                query = f'UPDATE users SET photo = %s where email = %s'
                cur.execute(query, (photo.filename, session['email']))
                db.connection.commit()
                session['photo'] = photo.filename
        else:
            error = 'Invalid photo'
        return render_template(
            'update_photo.html', old_photo=session.get('photo'), error=error
        )


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# data_alumni
@app.route('/data_alumni')
def data_alumni():
    if 'email' in session:
        cur = db.connection.cursor()
        cur.execute("SELECT "
                    "data_alumni.id_alumni, "
                    "data_alumni.nama_alumni, "
                    "data_prodi.nama_prodi as 'nama_prodi', "
                    "data_alumni.minat, "
                    "data_alumni.bakat, "
                    "data_alumni.mapel, "
                    "data_alumni.nilai, "
                    "data_alumni.ibu, "
                    "data_alumni.ayah, "
                    "data_alumni.penghasilan "
                    "FROM data_alumni "
                    "INNER JOIN data_prodi on data_alumni.nama_prodi = data_prodi.kode_prodi ")
        prodi = cur.fetchall()
        cur.execute("SELECT * FROM data_prodi")
        data_prodi = cur.fetchall()
        cur.close()
        return render_template("data_alumni.html", data=prodi, dp=data_prodi)
    else:
        return redirect(url_for('home'))


@app.route('/download_form')  # this is a job for GET, not POST
def download_form():
    return send_file(
        'data/Format_input_data_alumni.csv',
        mimetype='text/csv',
        download_name='Format_input_data_alumni.csv',
        as_attachment=True
    )


@app.route('/upload', methods=["GET", "POST"])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        file_name = secure_filename(file.filename)
        file_path = 'upload/' + file_name
        file.save(file_path)

        parseCSV(file_path)
        return redirect(url_for('data_alumni'))


def parseCSV(filePath):
    # CSV Column Names
    col_name = ['nama',
                'prodi',
                'minat',
                'bakat',
                'mapel',
                'nilai',
                'ibu',
                'ayah',
                'penghasilan']

    # use pandas to parse the CSV file
    cur = db.connection.cursor()
    cur.execute("SELECT COUNT(data_alumni.id_alumni) FROM data_alumni")
    count = cur.fetchone()[0] + 1

    # Use Pandas to parse the CSV file
    csvData = pd.read_csv(filePath, names=col_name, skiprows=1, sep=";|,", header=None)
    # Loop through the Rows

    file_excel = pd.read_excel("train.xlsx")

    for i, row in csvData.iterrows():
        sql = "INSERT INTO data_alumni " \
              "(nama_alumni, nama_prodi, minat, bakat, mapel, nilai, ibu, ayah, penghasilan) " \
              "VALUES (%s, %s, %s, %s, %s, %s,%s, %s, %s) " \

        value = (row['nama'],
                 row['prodi'],
                 row['minat'],
                 row['bakat'],
                 row['mapel'],
                 row['nilai'],
                 row['ibu'],
                 row['ayah'],
                 row['penghasilan'])

        cur.execute(sql, value)
        db.connection.commit()

        new_value_excel = pd.DataFrame({
            'no': [count],
            'nama': [row['nama']],
            'prodi': [row['prodi']],
            'minat': [row['minat']],
            'bakat': [row['bakat']],
            'mapel': [row['mapel']],
            'nilai': [row['nilai']],
            'ibu': [row['ibu']],
            'ayah': [row['ayah']],
            'penghasilan': [row['penghasilan']]
        })

        new_file_excel = pd.concat([file_excel, new_value_excel])
        count += 1

    cur.close()
    new_file_excel.to_excel("train.xlsx", index=False)

    return redirect(url_for('data_alumni'))


@app.route('/detail_data/<int:id_alumni>', methods=['POST', 'GET'])
def detail_data(id_alumni):
    if 'email' in session:
        cur = db.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT "
                    "data_alumni.id_alumni, "
                    "data_alumni.nama_alumni, "
                    "data_prodi.nama_prodi as 'nama_prodi', "
                    "data_alumni.minat, "
                    "data_alumni.bakat, "
                    "data_alumni.mapel, "
                    "data_alumni.nilai, "
                    "data_alumni.ibu, "
                    "data_alumni.ayah, "
                    "data_alumni.penghasilan "
                    "FROM data_alumni "
                    "INNER JOIN data_prodi on data_alumni.nama_prodi = data_prodi.kode_prodi "
                    "WHERE id_alumni = %s", [id_alumni])
        data_alumni = cur.fetchone()
        cur.close()
        return render_template("detail_alumni.html", data=data_alumni)
    else:
        return redirect(url_for('home'))


@app.route('/hapusdata/<string:id_alumni>', methods=["GET"])
def hapusdata(id_alumni):
    if 'email' in session:
        cur = db.connection.cursor()
        cur.execute("DELETE FROM data_alumni WHERE id_alumni=%s", (id_alumni,))
        db.connection.commit()
        return redirect(url_for('data_alumni'))
    else:
        return redirect(url_for('home'))


@app.route('/edit_data', methods=['GET', 'POST'])
def edit_data():
    if 'email' in session:
        if request.method == 'POST':
            id_alumni = request.form['id_alumni']
            nama_alumni = request.form['nama_alumni']
            nama_prodi = request.form['nama_prodi']
            minat = request.form['minat']
            bakat = request.form['bakat']
            mapel = request.form['mapel']
            nilai = request.form['nilai']
            ibu = request.form['ibu']
            ayah = request.form['ayah']
            penghasilan = request.form['penghasilan']
            cur = db.connection.cursor()
            cur.execute("""
                       UPDATE data_alumni
                       SET nama_alumni=%s, nama_prodi=%s, minat=%s, bakat=%s, mapel=%s, nilai=%s,
                       ibu=%s, ayah=%s, penghasilan=%s
                       WHERE id_alumni=%s
                    """, (nama_alumni, nama_prodi, minat, bakat, mapel, nilai, ibu, ayah, penghasilan, id_alumni))
            flash("Data Updated Successfully")
            db.connection.commit()
        return redirect(url_for('data_alumni'))
    else:
        return redirect(url_for('home'))


# prodi
@app.route('/prodi')
def prodi():
    if 'email' in session:
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM data_prodi")
        prodi = cur.fetchall()
        cur.close()
        return render_template("prodi.html", data=prodi)
    else:
        return redirect(url_for('home'))


@app.route('/simpan_prodi', methods=["POST"])
def simpan_prodi():
    if 'email' in session:
        kode_prodi = request.form['kode_prodi']
        nama_prodi = request.form['nama_prodi']
        keterangan = request.form['keterangan']
        keahlian = request.form['keahlian']
        output = request.form['output']
        cur = db.connection.cursor()
        cur.execute(
            "INSERT INTO data_prodi(kode_prodi,nama_prodi,keterangan,keahlian,output) VALUES(%s,%s,%s,%s,%s)",
            (kode_prodi, nama_prodi, keterangan, keahlian, output)
        )
        flash("Data Updated Successfully")
        db.connection.commit()
        cur.close()
        return redirect(url_for('prodi'))
    else:
        return redirect(url_for('home'))


@app.route('/formtambahdataprodi')
def formtambahdataprodi():
    if 'email' in session:
        return render_template("tambah_prodi.html")
    else:
        return redirect(url_for('home'))


@app.route('/detail_prodi/<kode_prodi>', methods=['POST', 'GET'])
def detail_prodi(kode_prodi):
    if 'email' in session:
        cur = db.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM data_prodi WHERE kode_prodi = '%s'" % kode_prodi)
        data_prodi = cur.fetchone()
        cur.close()
        daftar_keahlian = [x.strip() for x in data_prodi.get('keahlian', '').split(',')]
        daftar_output = [x.strip() for x in data_prodi.get('output', '').split(',')]
        data_prodi['keahlian'] = daftar_keahlian
        data_prodi['output'] = daftar_output
        print(data_prodi)
        return render_template("detail_prodi.html", data=data_prodi)
    else:
        return redirect(url_for('home'))


@app.route('/edit_prodi', methods=['POST', 'GET'])
def edit_prodi():
    if 'email' in session:
        if request.method == 'POST':
            kode_prodi = request.form['kode_prodi']
            nama_prodi = request.form['nama_prodi']
            keterangan = request.form['keterangan']
            keahlian = request.form['keahlian']
            output = request.form['output']
            cur = db.connection.cursor()
            cur.execute("""
                       UPDATE data_prodi
                       SET nama_prodi=%s, keterangan=%s, keahlian=%s, output=%s
                       WHERE kode_prodi=%s
                    """, (nama_prodi, keterangan, keahlian, output, kode_prodi))
            flash("Data Updated Successfully")
            db.connection.commit()
            return redirect(url_for('prodi'))
    else:
        return redirect(url_for('home'))


@app.route('/hapusdataprodi/<kode_prodi>', methods=["GET"])
def hapusdataprodi(kode_prodi):
    if 'email' in session:
        cur = db.connection.cursor()
        cur.execute("DELETE FROM data_prodi WHERE kode_prodi = %s", [kode_prodi])
        db.connection.commit()
        return redirect(url_for('prodi'))
    else:
        return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)

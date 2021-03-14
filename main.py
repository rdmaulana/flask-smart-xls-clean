import pandas as pd
import numpy as np
import io
import time
import uuid

from flask import Flask, render_template, request, redirect, url_for, Response, session, send_file, make_response, send_from_directory
from os.path import join, dirname, realpath
from werkzeug.wsgi import FileWrapper

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["UPLOAD_FOLDER"] = 'media/dataset'
app.config["EXPORT_FOLDER_CSV"] = 'media/result'
app.config["SECRET_KEY"] = 'DBA2823#*@$&bdaiuwgdbi8238XBxjzhx@$@'
app.config['SESSION_TYPE'] = 'filesystem'

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/", methods=['POST'])
def uploadExcel():
    start_id = request.form['id']
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        file_path = join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        uploaded_file.save(file_path)

        cleanExcel(file_path, start_id)

        csv_name = session['csv_name']

        return redirect(url_for('success', file_id=csv_name))
    else:
        return redirect(url_for('index'))

@app.route('/export/<file_id>', methods=['GET','POST'])
def success(file_id):
    filename = session['csv_name'] if "csv_name" in session else ""
    return render_template('success.html', filename=file_id)

@app.route('/downloads/<path:filename>', methods=['GET','POST'])
def download(filename):
    uploads = join(app.root_path, app.config['EXPORT_FOLDER_CSV'])
    return send_from_directory(directory=uploads, filename=filename)

def cleanExcel(file_path, start_id):
    xls = pd.read_excel(file_path)
    xls.replace(to_replace=[r"\\t|\\n|\\r", "\t|\n|\r"], value=["",""], regex=True)

    xls.rename(columns = {
        'NIK':'nik',
        'NAMA':'nama',
        'JENIS_KELAMIN':'jkel',
        'TANGGAL_LAHIR':'tgl_lahir',
        'NO_HP':'telp', 
        'INSTANSI_PEKERJAAN':'instansi',
        'ALAMAT KTP': 'alamat',
        'ALAMAT_KTP': 'alamat',
        'KODE_KAB_KOTA_TEMPAT_KERJA': 'kab_id',
        'KODE_KATEGORI': 'kategori'
    }, inplace = True)

    xls['nik'] = xls['nik'].astype(str) 

    xls.insert(0, 'id', range(int(start_id), int(start_id) + len(xls)))
    xls.insert(2, 'nama_ktp', xls['nama'])
    xls.insert(6, 'status', 0)

    del xls['NO']
    del xls['UMUR']
    del xls['JENIS_PEKERJAAN']

    xls.drop(xls[xls['tgl_lahir'].isnull()].index, inplace = True)
    xls.drop(xls[xls['nik'].isnull()].index, inplace = True)
    xls.drop(xls[xls['nik'].str.len() > 16].index, inplace = True)
    xls.drop(xls[xls['nik'].str.len() < 16].index, inplace = True)
    xls.drop(xls[xls.duplicated(['nik'])].index, inplace = True)

    if xls['telp'].dtypes == 'float64':
        xls['telp'] = xls['telp'].astype(str)
        xls['telp'] = xls['telp'].str.split('.').str[0]
        xls['telp'] = xls['telp'].replace('nan',np.NaN)
        xls['telp'] =  '0' + xls['telp']

    if xls['telp'].dtypes == 'object':
        xls['telp'] = xls['telp'].str.split('/').str[0]

    if xls['kab_id'].dtypes == 'float64':
        xls['kab_id'] = xls['kab_id'].astype(str)
        xls['kab_id'] = xls['kab_id'].str.split('.').str[0]
        xls['kab_id'] = xls['kab_id'].replace('nan',np.NaN)

    if xls['kategori'].dtypes == 'int64':
        xls['kategori'] = xls['kategori'].astype(str)
        xls['kategori'] =  '0' + xls['kategori']

    xls['alamat'] = xls['alamat'].replace(';','')
    
    uid = str(uuid.uuid4())[:4]
    path_file = 'media/result/'
    outfile_name = '{0}{1}'.format(time.strftime("%Y%m%d-%H%M%S-"),uid)
    session['csv_name'] = f'{outfile_name}'
    xls.to_csv(f'{path_file}{outfile_name}.csv', index=False, header=True, encoding="utf-8")
                 
if __name__ == '__main__': 
    app.run(debug=True)
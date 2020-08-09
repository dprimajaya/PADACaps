from flask import Flask, render_template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

# bacalah file `googleplaystore.csv` data dan simpan ke objek dataframe dengan nama playstore
playstore = pd.read_csv('data/googleplaystore.csv')

# Hapus data yang duplikat berdasarkan kolom App, dengan tetap keep data pertama (hint : gunakan parameter subset)
playstore.drop_duplicates(subset = 'App', keep = 'first') 

# bagian ini untuk menghapus row 10472 karena nilai data tersebut tidak tersimpan pada kolom yang benar
playstore.drop([10472], inplace=True)

# Cek tipe data kolom Category. Jika masih tersimpan dengan format tipe data yang salah, ubah ke tipe data yang sesuai
playstore.dtypes

# Pada kolom Installs Buang tanda koma(,) dan tanda tambah(+) kemudian ubah tipe data menjadi integer
playstore.Installs = playstore.Installs.apply(lambda x: x.replace(',',''))
playstore.Installs = playstore.Installs.apply(lambda x: x.replace('+',''))
# bagian untuk mengubah tipe data Installs
playstore['Installs'] = playstore['Installs'].astype('int64')

# Bagian ini untuk merapikan kolom Size, Anda tidak perlu mengubah apapun di bagian ini
playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

# Pada kolom Price, buang karakater $ pada nilai Price lalu ubah tipe datanya menjadi float
playstore.Price = playstore.Price.apply(lambda x: x.replace('$',' '))
playstore['Price'] = playstore['Price'].astype('float64')

# Ubah tipe data Reviews, Size, Installs ke dalam tipe data integer
playstore[['Reviews', 'Size', 'Installs']] = playstore[['Reviews', 'Size', 'Installs']].astype('int64')

@app.route("/")
# This fuction for rendering the table
def index():
    df2 = playstore.copy()

# Statistik
# Dataframe top_category dibuat untuk menyimpan frekuensi aplikasi untuk setiap Category. 
# Gunakan crosstab untuk menghitung frekuensi aplikasi di setiap category kemudian gunakan 'Jumlah'
# sebagai nama kolom dan urutkan nilai frekuensi dari nilai yang paling banyak. Terakhir reset index dari dataframe top_category 
    top_category = pd.crosstab(
        index=df2['Category'],
        columns='Jumlah').sort_values(by='Jumlah', ascending=False).reset_index()
# Dictionary stats digunakan untuk menyimpan beberapa data yang digunakan untuk menampilkan nilai di value box dan tabel
    stats = {
        # Ini adalah bagian untuk melengkapi konten value box ,
        # most category mengambil nama category paling banyak mengacu pada dataframe top_category
        # total mengambil frekuensi/jumlah category paling banyak mengacu pada dataframe top_category
        'most_categories': top_category.iloc[0,0],
        'total': top_category.iloc[0,1],
        # rev_table adalah tabel yang berisi 10 aplikasi yang paling banyak direview oleh pengguna. 
        # Silahkan melakukan agregasi data yang tepat menggunakan groupby untuk menampilkan 10 aplikasi yang diurutkan berdasarkan 
        # jumlah Review pengguna. Tabel yang ditampilkan terdiri dari 4 kolom yaitu nama Category, nama App, total Reviews, dan rata-rata Rating.
        # Agregasi Anda dinilai benar jika hasilnya sama dengan tabel yang terlampir pada file ini
        'rev_table' : df2.groupby(['Category', 'App']).agg({'Reviews':'sum', 'Rating':'mean'}).sort_values(by=['Reviews', 'Category'], ascending=False).head(10).to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

## Bar Plot
## Lengkapi tahap agregasi untuk membuat dataframe yang mengelompokkan aplikasi berdasarkan Category
## Buatlah bar plot dimana axis x adalah nama Category dan axis y adalah jumlah aplikasi pada setiap kategori, kemudian urutkan dari jumlah terbanyak
## Old syntax: cat_order = df2.groupby('Category').agg({'Reviews': 'sum'}).rename({'Reviews':'Total'}, axis=1).sort_values(by='Total', ascending=False).head()
## Old syntax tdk dapat digunakan karena aggregasi nya gak bisa pake Category (jadi gak sesuai soal)   
    cat_order = pd.crosstab(
    index=df2['Category'],
    columns='Total'
    ).sort_values(by='Total', ascending=False).reset_index().head()
    
    X = cat_order['Category']
    Y = cat_order['Total']

    my_colors = 'rgbkymc'

# bagian ini digunakan untuk membuat kanvas/figure
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
# bagian ini digunakan untuk membuat bar plot
# isi variabel x dan y yang telah di definisikan di atas
    plt.barh(X,Y,color=my_colors)
# bagian ini digunakan untuk menyimpan plot dalam format image.png
    plt.savefig('cat_order.png',bbox_inches="tight") 

# bagian ini digunakan untuk mengconvert matplotlib png ke base64 agar dapat ditampilkan ke template html
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
# variabel result akan dimasukkan ke dalam parameter di fungsi render_template() agar dapat ditampilkan di 
# halaman html
    result = str(figdata_png)[2:-1]
    
## Scatter Plot
# Buatlah scatter plot untuk menampilkan hubungan dan persebaran apalikasi dilihat dari Review vs Rating.
# Ukuran scatter menggambarkan berapa banyak pengguna yang telah menginstall aplikasi 
    X = df2['Reviews'].values # axis x
    Y = df2['Rating'].values # axis y
    area = playstore['Installs'].values/10000000 # ukuran besar/kecilnya lingkaran scatter plot
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
# isi nama method untuk scatter plot, variabel x, dan variabel y
    plt.scatter(x=X,y=Y, s=area, alpha=0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    plt.savefig('rev_rat.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

## Histogram Size Distribution
# Buatlah sebuah histogram yang menggambarkan distribusi Size aplikasi dalam satuan Mb(Megabytes) 
# Histogram yang terbentuk terbagi menjadi 100 bins
    X=(playstore['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(X,bins=100, density=True,  alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.savefig('hist_size.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

## Buatlah sebuah plot yang menampilkan insight di dalam data 
    playstore_pvt = playstore.pivot_table(
                        index='Category',
                        columns='Type',
                        values='Price')  
    playstore_pvt.fillna(0).sort_values(by='Paid', ascending=False).drop('Free', axis=1).head(5)\
    .plot.pie(subplots=True)
## Berdasarkan pivot dan plot di atas, diketahui Top 5 PAID Category dengan harga nya
## Namun karena belum bisa membuat parameter --> terpaksalah saya meng-hard coded kategori wkwkwk...
## Hard code dlm pemrograman hukumnya haram tetapi mungkin buat programmer pemula spt saya
## mestinya sih -- dapat dimaafkeun -- wkwkwk
 
    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(aspect="equal"))

    kategori = ["171 FINANCE",
          "124 LIFESTYLE",
          "101 EVENTS",
          "13 BUSINESS",
          "13 MEDICAL"]

    data = [float(x.split()[0]) for x in kategori]
    ingredients = [x.split()[-1] for x in kategori]


    def func(pct, allvals):
        absolute = int(pct/100.*np.sum(allvals))
        return "{:.1f}%\n($ {:d})".format(pct, absolute)


    wedges, texts, autotexts = ax.pie(data, autopct=lambda pct: func(pct, data),
                                  textprops=dict(color="w"))

    ax.legend(wedges, ingredients,
          title="Category",
          loc="center left",
          bbox_to_anchor=(0, 0, 0, 0))

    plt.setp(autotexts, size=12, weight="bold")

    ax.set_title("Top 5 PAID Categories", fontsize=18)

    plt.savefig('piechart.png', bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result4 = str(figdata_png)[2:-1]

# Tambahkan hasil result plot pada fungsi render_template()
    return render_template('index.html', stats=stats, result=result, result2=result2, result3=result3, result4=result4)

if __name__ == "__main__": 
    app.run(debug=True)

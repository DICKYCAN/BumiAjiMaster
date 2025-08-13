from django.urls import path
from . import views

urlpatterns = [
    path('',views.loginview, name='login'),
    path('performlogin',views.performlogin,name="performlogin"),
    path('performlogout',views.performlogout,name="performlogout"),
    path('base', views.base,name='base'),
    # path('sidebar', views.sidebar,name='sidebar'),
    # path('navbar', views.navbar,name='navbar'),
    # path('errors', views.errors,name='errors'),
    # CRUD MITRA
    path('create_mitra', views.create_mitra,name='create_mitra'),
    path('readmitra', views.read_mitra,name='readmitra'),
    path('update_mitra/<str:id>', views.update_mitra,name='update_mitra'),
    path('delete_mitra/<str:id>', views.delete_mitra,name='delete_mitra'),
    # CRUD PENJUALAN
    path('create_penjualan', views.create_penjualan,name='create_penjualan'),
    path('read_penjualan', views.read_penjualan,name='read_penjualan'),
    path('update_penjualan/<str:id>', views.update_penjualan,name='update_penjualan'),
    path('delete_penjualan/<str:id>', views.delete_penjualan,name='delete_penjualan'),
    # CUD DETAIL PENJUALAN
    path('update_detail_penjualan/<str:id>', views.update_detail_penjualan,name='update_detail_penjualan'),
    path('delete_detail_penjualan/<str:id>', views.delete_detail_penjualan,name='delete_detail_penjualan'),
    path('create_detail_penjualan/<str:id>', views.create_detail_penjualan,name='create_detail_penjualan'),
    # CRUD PRODUK
    path('create_produk', views.create_produk,name='create_produk'),
    path('read_produk', views.read_produk,name='read_produk'),
    path('update_produk/<str:id>', views.update_produk,name='update_produk'),
    path('delete_produk/<str:id>', views.delete_produk,name='delete_produk'),
    # CRUD KOMODITAS
    path('create_komoditas', views.create_komoditas,name='create_komoditas'),
    path('read_komoditas', views.read_komoditas,name='read_komoditas'),
    path('update_komoditas/<str:id>', views.update_komoditas,name='update_komoditas'),
    path('delete_komoditas/<str:id>', views.delete_komoditas,name='delete_komoditas'),
    # CRUD GRADE
    path('create_grade', views.create_grade,name='create_grade'),
    path('read_grade',views.read_grade,name='read_grade'),
    path('update_grade/<str:id>', views.update_grade,name='update_grade'),
    path('delete_grade/<str:id>', views.delete_grade,name='delete_grade'),
    # CRUD PASAR
    path('create_pasar', views.create_pasar,name='create_pasar'),
    path('read_pasar', views.read_pasar,name='read_pasar'),
    path('update_pasar/<str:id>', views.update_pasar,name='update_pasar'),
    path('delete_pasar/<str:id>', views.delete_pasar,name='delete_pasar'),
     # CRUD PANEN
    path('create_panenmitra', views.create_panenmitra,name='create_panenmitra'),
    path('read_panenmitra', views.read_panenmitra,name='read_panenmitra'),
    path('update_panenmitra/<str:id>', views.update_panenmitra,name='update_panenmitra'),
    path('delete_panenmitra/<str:id>', views.delete_panenmitra,name='delete_panenmitra'),
    
    path('create_panenlokal', views.create_panenlokal,name='create_panenlokal'),
    path('read_panenlokal', views.read_panenlokal,name='read_panenlokal'),
    path('update_panenlokal/<str:id>', views.update_panenlokal,name='update_panenlokal'),
    path('delete_panenlokal/<str:id>', views.delete_panenlokal,name='delete_panenlokal'),

    path('read_penimbanganmitra', views.read_penimbanganmitra,name='read_penimbanganmitra'),
    path('read_penimbanganlokal', views.read_penimbanganlokal,name='read_penimbanganlokal'),

    # CRUD BIAYA
    path('create_jenisbiaya', views.create_jenisbiaya,name='create_jenisbiaya'),
    path('read_jenisbiaya', views.read_jenisbiaya,name='read_jenisbiaya'),
    path('update_jenisbiaya/<str:id>', views.update_jenisbiaya,name='update_jenisbiaya'),
    path('delete_jenisbiaya/<str:id>', views.delete_jenisbiaya,name='delete_jenisbiaya'),
    
    path('create_detailbiaya', views.create_detailbiaya,name='create_detailbiaya'),
    path('read_detailbiaya', views.read_detailbiaya,name='read_detailbiaya'),
    path('update_detailbiaya/<str:id>', views.update_detailbiaya,name='update_detailbiaya'),
    path('delete_detailbiaya/<str:id>', views.delete_detailbiaya,name='delete_detailbiaya'),

    # CRUD PRODUKSI
    path('create_produksi', views.create_produksi,name='create_produksi'),
    path('read_produksi', views.read_produksi,name='read_produksi'),
    path('update_produksi/<str:id>', views.update_produksi,name='update_produksi'),
    path('delete_produksi/<str:id>', views.delete_produksi,name='delete_produksi'),

    # Laporan
    path('laporan_penjualan', views.laporan_penjualan,name='laporan_penjualan'),
    path('laporanpanen', views.laporan_panen,name='laporanpanen'),
    path('laporan_labarugi', views.laporan_labarugi,name='laporan_labarugi'),
    path('laporanlabarugi_pdf<str:bulan>', views.laporanlabarugi_pdf,name='laporanlabarugi_pdf'),

    path('total_komoditas/', views.total_komoditas, name='total_komoditas'),
    path('rekap_panen/', views.rekap_panen_bulanan, name='rekap-panen'),
    path('log_aktivitas/', views.log_aktivitas, name='log_aktivitas')


]
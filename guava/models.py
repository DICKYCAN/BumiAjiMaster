from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class mitra(models.Model) :
    id_mitra = models.AutoField(primary_key=True)
    nama_mitra = models.CharField(max_length=100)
    alamat_mitra = models.TextField(blank=True,null=True)
    nohp_mitra = models.PositiveBigIntegerField()
    tanggalawal_mitra = models.DateField()
    durasi_kontrak = models.PositiveIntegerField()
    luas_lahan = models.PositiveIntegerField(null=True)
    status_mitra = models.BooleanField(default=None, null=True)
    minimal_kuantitas = models.PositiveIntegerField()
    email = models.EmailField()

    def __str__(self) :
        return str(self.nama_mitra)

class grade(models.Model) :
    id_grade = models.AutoField(primary_key=True)
    nama_grade = models.CharField(max_length=100)
    deskripsi_grade = models.TextField(blank=True,null=True)

    def __str__(self) :
        return str(self.nama_grade)
    
class komoditas(models.Model) :
    id_komoditas = models.AutoField(primary_key=True)
    id_grade = models.ForeignKey(grade,on_delete=models.CASCADE)
    nama_komoditas = models.CharField(max_length=100)
    harga_beli = models.IntegerField()
    harga_jual = models.IntegerField()

    def __str__(self):
        return f"{self.nama_komoditas} - {self.id_grade.nama_grade}"

class produk(models.Model) :
    id_produk = models.AutoField(primary_key=True)
    nama_produk = models.CharField(max_length=100)
    satuan_produk = models.CharField(max_length=100)
    harga_produk = models.PositiveIntegerField()
    
    def __str__(self) :
        return str(self.nama_produk)

class panenmitra(models.Model) :
    idpanen_mitra = models.AutoField(primary_key=True)
    id_mitra = models.ForeignKey(mitra,on_delete=models.CASCADE)
    tanggal_panen = models.DateField()
    
    def __str__(self) :
        return str(self.id_mitra.nama_mitra)

class detailpanenmitra(models.Model) :
    iddetailpanen_mitra = models.AutoField(primary_key=True)
    idpanen_mitra = models.ForeignKey(panenmitra,on_delete=models.CASCADE)
    id_komoditas = models.ForeignKey(komoditas, on_delete=models.CASCADE)
    batch = models.PositiveIntegerField()
    tanggal_kadaluwarsa = models.DateField()
    kuantitas = models.PositiveIntegerField()

    def __str__(self) :
        return "{} - {}".format(self.idpanen_mitra,self.batch)
    
class panenlokal(models.Model) :
    idpanen_lokal = models.AutoField(primary_key=True)
    tanggal_panen = models.DateField()
    
    def __str__(self) :
        return str(self.idpanen_lokal)
   
class detailpanenlokal(models.Model) :
    iddetailpanen_lokal = models.AutoField(primary_key=True)
    idpanen_lokal = models.ForeignKey(panenlokal,on_delete=models.CASCADE)
    id_komoditas = models.ForeignKey(komoditas, on_delete=models.CASCADE)
    batch = models.PositiveIntegerField()
    tanggal_kadaluwarsa = models.DateField()
    kuantitas = models.PositiveIntegerField(null=True)

    def __str__(self) :
        return "{} - {}".format(self.idpanen_lokal,self.batch)

class pasar(models.Model) :
    id_pasar = models.AutoField(primary_key=True)
    nama_pasar = models.CharField(max_length=100)
    alamat_pasar = models.TextField(null=True,blank=True)

    def __str__(self) :
        return str(self.nama_pasar)
    
class penjualan(models.Model) :
    id_penjualan = models.AutoField(primary_key=True)
    id_pasar = models.ForeignKey(pasar,on_delete=models.CASCADE)
    tanggal = models.DateField()

    def __str__(self) :
        return str(self.id_pasar)

class detailpenjualan(models.Model):
    iddetail_penjualan = models.AutoField(primary_key=True)
    id_penjualan = models.ForeignKey(penjualan,on_delete=models.CASCADE)
    id_produk = models.ForeignKey(produk,null=True,on_delete=models.CASCADE)
    id_komoditas = models.ForeignKey(komoditas,null=True,on_delete=models.CASCADE)
    kuantitas_komoditas = models.PositiveIntegerField(null=True)
    kuantitas_produk = models.PositiveIntegerField(null=True)

    def __str__(self) :
        return str(self.id_penjualan)

class produksi(models.Model) :
    id_produksi = models.AutoField(primary_key=True)
    tanggal = models.DateField()
    

    def __str__(self) :
        return str(self.tanggal)

class detailproduksi(models.Model):
    iddetail_produksi = models.AutoField(primary_key=True)
    id_produk = models.ForeignKey(produk,on_delete=models.CASCADE)
    id_produksi = models.ForeignKey(produksi, on_delete=models.CASCADE)
    kuantitas_produk = models.PositiveIntegerField()
    status_produk = models.CharField(max_length=100,null=True)
    def __str__(self) :
        return "{} - {}".format(self.id_produk,self.status_produk)
    
class jenisbiaya(models.Model) :
    idjenisbiaya = models.AutoField(primary_key=True)
    jenis_biaya = models.CharField(max_length=100)

    def __str__(self) :
        return str(self.jenis_biaya)
    
class biaya(models.Model) :
    idbiaya = models.AutoField(primary_key=True)
    idjenisbiaya = models.ForeignKey(jenisbiaya,on_delete=models.CASCADE)
    tanggal = models.DateField()
    nama_biaya = models.CharField(max_length=100)
    nominal_biaya = models.PositiveIntegerField()

    def __str__(self) :
        return "{} - {}".format(self.idjenisbiaya,self.nama_biaya)

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
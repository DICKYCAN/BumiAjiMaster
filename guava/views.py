from django.shortcuts import render, redirect
from . import models
from datetime import datetime
import calendar
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login , logout, authenticate
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.forms import DateInput
from django.db.models import F,Q,Sum,Value
import math
from weasyprint import HTML
from django.template.loader import render_to_string
import tempfile
from django.urls import reverse
import qrcode
from io import BytesIO
from django.utils.timezone import now
from django.shortcuts import render
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings


# Create your views here.
konversi_produk_to_komoditas = {'Pastry':('Jambu Kristal',0.33),
            'Teh Bunga Telang' :('Bunga Telang',0.1),
            'Lemon Kering' :('Lemon',0.2),
            'Keripik Cale' :('Cale',0.25),
            'Rujak Jambu Kristal' : ('Jambu Kristal', 0.4)
            }
bulan_indo = {
    'January': 'Januari',
    'February': 'Februari',
    'March': 'Maret',
    'April': 'April',
    'May': 'Mei',
    'June': 'Juni',
    'July': 'Juli',
    'August': 'Agustus',
    'September': 'September',
    'October': 'Oktober',
    'November': 'November',
    'December': 'Desember'
    }

def loginview(request):
    if request.user.is_authenticated:
        group = None
        if request.user.groups.exists():
            group = request.user.groups.all()[0].name

        if group == 'inspeksi':
            return redirect('readmitra')
        elif group in ['admin', 'owner']:
            return redirect('base')
        else :
            return redirect('read_produksi')
    else:
        return render(request,"base/login.html")
    
def performlogin(request):
    if request.method != "POST":
        return HttpResponse("Method not Allowed")
    else:
        username_login = request.POST['username']
        password_login = request.POST['password']
        userobj = authenticate(request, username=username_login,password=password_login)
        if userobj is not None:
            login(request, userobj)
            messages.success(request,"Login success")
            if userobj.groups.filter(name='admin').exists() or userobj.groups.filter(name='owner').exists():
                return redirect("base")
            elif userobj.groups.filter(name='inspeksi').exists() :
                return redirect("readmitra")
            elif  userobj.groups.filter(name='produksi').exists() :
                return redirect('read_produksi')
            else:
                return redirect('login')
        else:
            messages.error(request,"Username atau Password salah !!!")
            return redirect("login")


@login_required(login_url="login")
def logoutview(request):
    logout(request)
    messages.info(request,"Berhasil Logout")
    return redirect('login')

@login_required(login_url="login")
def performlogout(request):
    logout(request)
    return redirect("login")

@login_required(login_url="login")
@role_required(["owner", 'admin'])  
def base(request):
    penjualanobj = models.detailpenjualan.objects.all()
    detailpanenlokal = models.detailpanenlokal.objects.all()
    detailpanenmitra = models.detailpanenmitra.objects.all()
    komoditasobj = models.komoditas.objects.all()
    komoditas_dict = {i : 0 for i in komoditasobj}

    for panenlokal in detailpanenlokal:
        komoditas_nama = panenlokal.id_komoditas
        if komoditas_nama in komoditas_dict:
            komoditas_dict[komoditas_nama] += panenlokal.kuantitas
        else:
            komoditas_dict[komoditas_nama] = panenlokal.kuantitas

    for panenmitra in detailpanenmitra:
        komoditas_nama = panenmitra.id_komoditas
        if komoditas_nama in komoditas_dict:
            komoditas_dict[komoditas_nama] += panenmitra.kuantitas
        else:
            komoditas_dict[komoditas_nama] = panenmitra.kuantitas

    print(komoditas_dict)

    listkomoditas = list(komoditas_dict.keys())
    listkuantitaskomoditas = list(komoditas_dict.values())

    if request.method == 'GET':
        return render(request, 'base/dashboard.html', {
            'listkomoditas' : listkomoditas,
            'listkuantitaskomoditas' : listkuantitaskomoditas,
        })
    
    else :
        inp = request.POST['grafik']

        listpasar = []
        listkuantitas = []
        if inp == 'Produk' :
            for i in penjualanobj :
                if i.id_penjualan.id_pasar is not None and i.kuantitas_komoditas :
                    listpasar.append(i.id_penjualan.id_pasar.nama_pasar)
                    listkuantitas.append(i.kuantitas_komoditas)

            dict_pasar = {}
            for a,b in zip(listpasar,listkuantitas) :
                if a in dict_pasar :
                    dict_pasar[a] += b
                else :
                    dict_pasar[a] = b

            listpasarakhir = list(dict_pasar.keys())
            listkuantitasakhir = list(dict_pasar.values())
                
            
            return render(request, 'base/dashboard.html', {
                'listkomoditas' : listkomoditas,
                'listkuantitaskomoditas' : listkuantitaskomoditas,
                'listpasar' : listpasarakhir,
                'listkuantitas' : listkuantitasakhir,
            })

        elif inp == 'Komoditas' :
            for i in penjualanobj :
                if i.id_penjualan.id_pasar is not None and i.kuantitas_produk :
                    listpasar.append(i.id_penjualan.id_pasar.nama_pasar)
                    listkuantitas.append(i.kuantitas_produk)

            dict_pasar = {}
            for a,b in zip(listpasar,listkuantitas) :
                if a in dict_pasar :
                    dict_pasar[a] += b
                else :
                    dict_pasar[a] = b
            
            listpasarakhir = list(dict_pasar.keys())
            listkuantitasakhir = list(dict_pasar.values())
            
            return render(request, 'base/dashboard.html', {
                'listkomoditas' : listkomoditas,
                'listkuantitaskomoditas' : listkuantitaskomoditas,
                'listpasar' : listpasarakhir,
                'listkuantitas' : listkuantitasakhir,
            })
        
    

# CRUD MITRA
@login_required(login_url="login")
@role_required(["owner", 'admin','inspeksi']) 
def read_mitra(request) :
    allmitra = models.mitra.objects.all().order_by('tanggalawal_mitra')
    if not allmitra.exists():
        messages.error(request, "Data Mitra Tidak Ditemukan!")
    return render(request,
                  'mitra/read_mitra.html',
                  {
                      'allmitra': allmitra
                  })

@login_required(login_url="login")
@role_required(["owner", 'admin']) 
def create_mitra(request) :
    
    if request.method == "GET" :
        return render(request, 
                      'mitra/create_mitra.html')
    else :
        namamitra = request.POST["nama_mitra"]
        namamitra = namamitra.lower()
        mitraobj = models.mitra.objects.filter(nama_mitra=namamitra)
        
        if len(mitraobj) >0:
            messages.error(request,"Nama Mitra Sudah Ada")
            return redirect("create_mitra")
        else :
            alamatmitra = request.POST["alamat_mitra"]
            nohpmitra = request.POST["nohp_mitra"]
            tanggalawalmitra = request.POST["tanggalawal_mitra"]
            durasikontrakmitra = request.POST["durasi_kontrak"]
            luaslahan = request.POST["luas_lahan"]
            luaslahan = int(luaslahan)
            print('luaslahan',luaslahan,"type",type(luaslahan))
            minimal_kuantitas = request.POST['minimal_kuantitas']
            status = request.POST["status_mitra"]
            if status.lower() == "aktif" :
                statusmitra = True
            else :
                statusmitra = False
            if luaslahan<100 :
                messages.error(request,"Luas lahan harus lebih dari 100 m^2")
                return redirect("create_mitra")
            else :
                pass
            data = models.mitra(
                nama_mitra = namamitra,
                alamat_mitra = alamatmitra,
                nohp_mitra = nohpmitra,
                tanggalawal_mitra = tanggalawalmitra,
                durasi_kontrak = durasikontrakmitra,
                luas_lahan = luaslahan,
                minimal_kuantitas = minimal_kuantitas,
                status_mitra = statusmitra
            )
            data.save()
            
            models.ActivityLog(
                user=request.user,
                action="Tambah Mitra",
                description=f"Menambahkan mitra baru: {data.nama_mitra} dengan luas {data.luas_lahan} m², kontrak {data.durasi_kontrak} bulan.",
            ).save()

            messages.success(request,"Data Mitra Berhasil Ditambahkan!")
        return redirect("readmitra")
            

@login_required(login_url="login")
@role_required(["owner", 'admin']) 
def update_mitra(request, id):
    try:
        getmitraobj = models.mitra.objects.get(id_mitra=id)
    except models.mitra.DoesNotExist:
        messages.error(request, "Mitra tidak ditemukan!")
        return redirect('readmitra')

    tanggal = getmitraobj.tanggalawal_mitra.strftime('%Y-%m-%d')  # Format tanggal
    statusmitra = 'Aktif' if getmitraobj.status_mitra else 'Tidak Aktif'
    if request.method == "GET":
        return render(request, 'mitra/update_mitra.html', {
            'getmitraobj': getmitraobj,
            'statusmitra': statusmitra,
            'tanggal': tanggal
        })
    else:
        namamitra = request.POST["nama_mitra"]
        namamitra = namamitra.lower()
        if models.mitra.objects.filter(nama_mitra=namamitra).exclude(id_mitra=id).exists():
            messages.error(request, "Nama Mitra Sudah Ada!")
            return render(request, 'mitra/update_mitra.html', {
            'getmitraobj': getmitraobj,
            'statusmitra': statusmitra,
            'tanggal': tanggal
        })
        luaslahan = request.POST["luas_lahan"]
        luaslahan = int(luaslahan)
        print('luaslahan',luaslahan,"type",type(luaslahan))
        if luaslahan<100 :
            messages.error(request,"Luas lahan harus lebih dari 100 m^2")
            return render(request, 'mitra/update_mitra.html', {
            'getmitraobj': getmitraobj,
            'statusmitra': statusmitra,
            'tanggal': tanggal})
        else :
            pass
        
        status_lama = getmitraobj.status_mitra
        
        getmitraobj.nama_mitra = namamitra
        getmitraobj.alamat_mitra = request.POST["alamat_mitra"]
        getmitraobj.nohp_mitra = request.POST["nohp_mitra"]
        getmitraobj.tanggalawal_mitra = request.POST["tanggalawal_mitra"]
        getmitraobj.durasi_kontrak = request.POST["durasi_kontrak"]
        getmitraobj.luas_lahan = luaslahan
        getmitraobj.status_mitra = request.POST["status_mitra"].lower() == "aktif"
        getmitraobj.save()
        
        models.ActivityLog.objects.create(
            user=request.user,
            action="Update Mitra",
            description=(
                f"Memperbarui data mitra: {getmitraobj.nama_mitra},\n "
                f"Alamat: {getmitraobj.alamat_mitra},\n "
                f"Status: {status_lama} menjadi {'Aktif' if getmitraobj.status_mitra else 'Tidak Aktif'}.\n"
            )
        )
        messages.success(request, "Mitra berhasil diperbarui!")
        return redirect('readmitra')
            
@login_required(login_url="login")
@role_required(["owner"])     
def delete_mitra(request, id):
    getmitraobj = models.mitra.objects.get(id_mitra=id)
    nama = getmitraobj.nama_mitra
    alamat = getmitraobj.alamat_mitra
    nohp = getmitraobj.nohp_mitra

    models.ActivityLog(
        user=request.user,
        action="Hapus Mitra",
        description=f"Menghapus mitra: {nama}, Alamat: {alamat}, No HP: {nohp}."
    ).save()

    getmitraobj.delete()
    messages.success(request, "Data berhasil dihapus!")
    return redirect('readmitra')

'''CRUD PENJUALAN'''
# @login_required(login_url='login')
# @role_required(['owner', 'admin'])
# def create_penjualan(request) :
#     #Data yang harus diambil sebelum masuk ke 'get'/'post'
#     # detailpanenlobj = 
#     pasarobj = models.pasar.objects.all()
#     produkobj = models.produk.objects.all()
#     komoditasobj = models.komoditas.objects.all()
#     if request.method == 'GET' :
#         return render(request, 'penjualan/create_penjualan.html',{
#             'pasarobj' : pasarobj,
#             'produkobj' : produkobj,
#             'komoditasobj' : komoditasobj,
#         })
    
#     else :
#         #Mengambil data yang ingin di 'post' dari input html
#         pasar = request.POST['pasar']
#         tanggal = request.POST['tanggal']
#         kuantitasp = request.POST.getlist('kuantitasp')
#         kuantitask = request.POST.getlist('kuantitask')
#         produk = request.POST.getlist('produk')
#         komoditas = request.POST.getlist('komoditas')

#         print(kuantitasp)
#         print(kuantitask)
#         print(produk)
#         print(komoditas)
#         #request.POST.getlist
#         #for a,b,c,d in zip(a,b,c,d)


#         penjualan = models.penjualan(
#             id_pasar = models.pasar.objects.get(id_pasar = pasar),
#             tanggal = tanggal,
#         )
#         penjualan.save()

#         id = penjualan.id_penjualan
#         iddetail = []

#         for produk,komoditas,kuantitasp,kuantitask in zip(produk,komoditas,kuantitasp,kuantitask) :
#             if komoditas != '' and produk != '' and kuantitasp != '' and kuantitask != '' :
#                 detail = models.detailpenjualan(
#                     id_penjualan = models.penjualan.objects.get(id_penjualan = id),
#                     id_produk = models.produk.objects.get(id_produk = produk),
#                     id_komoditas = models.komoditas.objects.get(id_komoditas = komoditas),
#                     kuantitas_produk = kuantitasp,
#                     kuantitas_komoditas = kuantitask,
#                 )
#                 detail.save()
#                 iddetail.append(detail.iddetail_penjualan)


#             elif komoditas != '' and produk == '' and kuantitasp == '' and kuantitask != '' :
#                 detail = models.detailpenjualan(
#                     id_penjualan = models.penjualan.objects.get(id_penjualan = id),
#                     id_produk = None,
#                     id_komoditas = models.komoditas.objects.get(id_komoditas = komoditas),
#                     kuantitas_produk = None,
#                     kuantitas_komoditas = kuantitask,
#                 )
#                 detail.save()
#                 iddetail.append(detail.iddetail_penjualan)
            
#             elif komoditas == '' and produk != '' and kuantitasp != '' and kuantitask == '' :
#                 detail = models.detailpenjualan(
#                     id_penjualan = models.penjualan.objects.get(id_penjualan = id),
#                     id_produk = models.produk.objects.get(id_produk = produk),
#                     id_komoditas = None,
#                     kuantitas_produk = kuantitasp,
#                     kuantitas_komoditas = None,
#                 )
#                 detail.save()
#                 iddetail.append(detail.iddetail_penjualan)

#             else :
#                 getpenjualan = models.penjualan.objects.get(id_penjualan = id)
#                 getdetailpenjualan = models.detailpenjualan.objects.filter(iddetail_penjualan__in = iddetail)
#                 getpenjualan.delete()
#                 getdetailpenjualan.delete()
#                 messages.error(request, 'Data Penjualan minimal memiliki produk/komoditas dan kuantitas yang sesuai, Coba Ulang Kembali!')
#                 return redirect('create_penjualan')
#         messages.success(request, 'Data Penjualan Berhasil Ditambahkan!')
#         return redirect('read_penjualan')


@login_required(login_url='login')
@role_required(['owner', 'admin'])
def create_penjualan(request):
    pasarobj = models.pasar.objects.all()
    produkobj = models.produk.objects.all()
    komoditasobj = models.komoditas.objects.all()

    qr_data = {
        'qr_komoditas': request.GET.get('qr_komoditas', ''),  # sekarang harus ID
        'qr_kadaluarsa': request.GET.get('qr_kadaluarsa', ''),
        'qr_kuantitas': request.GET.get('qr_kuantitas', ''),
    }

    if request.method == 'GET':
        return render(request, 'penjualan/create_penjualan.html', {
            'pasarobj': pasarobj,
            'produkobj': produkobj,
            'komoditasobj': komoditasobj,
            'qr_data': qr_data,
        })

    else:
        pasar = request.POST.get('pasar')
        tanggal = request.POST.get('tanggal')

        kuantitasp = request.POST.getlist('kuantitasp')
        kuantitask = request.POST.getlist('kuantitask')
        produk = request.POST.getlist('produk')
        komoditas = request.POST.getlist('komoditas')

        qr_komoditas = request.POST.getlist('qr_komoditas')  # ID Komoditas dari QR
        qr_kadaluarsa = request.POST.getlist('qr_kadaluarsa')
        qr_kuantitas = request.POST.getlist('qr_kuantitas')

        penjualan = models.penjualan(
            id_pasar=models.pasar.objects.get(id_pasar=pasar),
            tanggal=tanggal,
        )
        penjualan.save()
        iddetail = []

        # Penjualan dari form manual
        for p, k, qp, qk in zip(produk, komoditas, kuantitasp, kuantitask):
            if k and p and qp and qk:
                detail = models.detailpenjualan(
                    id_penjualan=penjualan,
                    id_produk=models.produk.objects.get(id_produk=p),
                    id_komoditas=models.komoditas.objects.get(id_komoditas=k),
                    kuantitas_produk=qp,
                    kuantitas_komoditas=qk,
                )
            elif k and not p and not qp and qk:
                detail = models.detailpenjualan(
                    id_penjualan=penjualan,
                    id_produk=None,
                    id_komoditas=models.komoditas.objects.get(id_komoditas=k),
                    kuantitas_produk=None,
                    kuantitas_komoditas=qk,
                )
            elif not k and p and qp and not qk:
                detail = models.detailpenjualan(
                    id_penjualan=penjualan,
                    id_produk=models.produk.objects.get(id_produk=p),
                    id_komoditas=None,
                    kuantitas_produk=qp,
                    kuantitas_komoditas=None,
                )
            else:
                continue  
            detail.save()
            iddetail.append(detail.iddetail_penjualan)

        # Penjualan dari QR (dengan ID komoditas)
        for komoditas, kadaluwarsa, kuantitas in zip(qr_komoditas, qr_kadaluarsa, qr_kuantitas):
            if not komoditas or not kuantitas:
                continue  

            try:
                komoditas_obj = models.komoditas.objects.get(id_komoditas=komoditas)

                detail = models.detailpenjualan(
                    id_penjualan=penjualan,
                    id_produk=None,
                    id_komoditas=komoditas_obj,
                    kuantitas_produk=None,
                    kuantitas_komoditas=kuantitas,
                )
                detail.save()
                iddetail.append(detail.iddetail_penjualan)

            except models.komoditas.DoesNotExist:
                messages.error(request, f"Komoditas dengan ID {komoditas} tidak ditemukan.")
                penjualan.delete()
                return redirect('create_penjualan')

        if not iddetail:
            messages.error(request, 'Tidak ada data penjualan yang valid disimpan.')
            penjualan.delete()
            return redirect('create_penjualan')

        pasar_name = models.pasar.objects.get(id_pasar=pasar).nama_pasar
        
        models.ActivityLog.objects.create(
            user=request.user,
            action="Tambah Penjualan",
            description=f"Menambahkan penjualan baru di {pasar_name} pada tanggal {tanggal}"
        )

        messages.success(request, 'Data Penjualan Berhasil Ditambahkan!')
        return redirect('read_penjualan')

@login_required(login_url='login')
@role_required(['owner', 'admin'])
def read_penjualan(request) : 
    penjualanobj = models.penjualan.objects.all()
    detailpenjualanobj = models.detailpenjualan.objects.all()
    if not penjualanobj.exists():
        messages.error(request, "Data Penjualan Tidak Ditemukan!")
    return render(request,
                  'penjualan/read_penjualan.html',
                  {
                      'penjualanobj': penjualanobj,
                      'detailpenjualanobj' : detailpenjualanobj,
                  })

@login_required(login_url='login')
@role_required(['owner', 'admin'])
def update_penjualan(request, id) :
    pasarobj = models.pasar.objects.all()
    produkobj = models.produk.objects.all()
    komoditasobj = models.komoditas.objects.all()

    getpenjualan = models.penjualan.objects.get(id_penjualan = id)
    tanggal_penjualan = datetime.strftime(getpenjualan.tanggal, '%Y-%m-%d')
    id_pasar = getpenjualan.id_pasar.nama_pasar
    print(id_pasar)
    print(getpenjualan.tanggal)
    print(tanggal_penjualan)
    if request.method == 'GET' :
        return render (request, 'penjualan/update_penjualan.html', {
            'tanggalpenjualan' : tanggal_penjualan,
            'id_pasar' : id_pasar,
            'getpenjualan' : getpenjualan,
            'pasarobj' : pasarobj,
            'produkobj' : produkobj,
            'komoditasobj' : komoditasobj,
            'id' : id,
        })
    
    else :
        pasar = request.POST['pasar']
        tanggal = request.POST['tanggal']
        

        old_pasar = getpenjualan.id_pasar.nama_pasar
        old_tanggal = getpenjualan.tanggal

        getpenjualan.id_penjualan = getpenjualan.id_penjualan
        getpenjualan.id_pasar = models.pasar.objects.get(id_pasar = pasar)
        getpenjualan.tanggal = tanggal

        getpenjualan.save()
        
        models.ActivityLog(
            user=request.user,
            action="Update Penjualan",
            description=f"Memperbarui data penjualan ID: {getpenjualan.id_penjualan}. "
                        f"pada Pasar: {old_pasar},\n"
                        f"pada Tanggal penjualan: {old_tanggal}\n"
        ).save()
        
        messages.success(request, "Data Penjualan berhasil diperbarui!")
        return redirect('read_penjualan')

@login_required(login_url='login')
@role_required(['owner'])
def delete_penjualan(request, id) :
    getpenjualan = models.penjualan.objects.get(id_penjualan = id)
    
    pasar_name = getpenjualan.id_pasar.nama_pasar
    tanggal = getpenjualan.tanggal
    
    models.ActivityLog(
        user=request.user,
        action="Hapus Penjualan",
        description=f"Menghapus data penjualan dengan ID penjualan: {id} di pasar {pasar_name} pada tanggal penjualan {tanggal}"
    ).save()
    
    getpenjualan.delete()
    messages.error(request, "Data Penjualan berhasil dihapus!")
    return redirect('read_penjualan')


'''CUD DETAIL PENJUALAN'''
@login_required(login_url='login')
@role_required(['owner', 'admin'])
def create_detail_penjualan(request, id) :
    komoditasobj = models.komoditas.objects.all()
    produkobj = models.produk.objects.all()
    if request.method == 'GET' :
        return render (request, 'penjualan/create_detail_penjualan.html', {
            'komoditasobj' : komoditasobj,
            'produkobj' : produkobj,
        })
    
    else :
        kuantitasp = request.POST.getlist('kuantitasp')
        kuantitask = request.POST.getlist('kuantitask')
        produk = request.POST.getlist('produk')
        komoditas = request.POST.getlist('komoditas')

        iddetail = []

        for produk,komoditas,kuantitasp,kuantitask in zip(produk,komoditas,kuantitasp,kuantitask) :
            if komoditas != '' and produk != '' and kuantitasp != '' and kuantitask != '' :
                detail = models.detailpenjualan(
                    id_penjualan = models.penjualan.objects.get(id_penjualan = id),
                    id_produk = models.produk.objects.get(id_produk = produk),
                    id_komoditas = models.komoditas.objects.get(id_komoditas = komoditas),
                    kuantitas_produk = kuantitasp,
                    kuantitas_komoditas = kuantitask,
                )
                detail.save()
                iddetail.append(detail.iddetail_penjualan)

                print('kondisi 1')


            elif komoditas != '' and produk == '' and kuantitasp == '' and kuantitask != '' :
                detail = models.detailpenjualan(
                    id_penjualan = models.penjualan.objects.get(id_penjualan = id),
                    id_produk = None,
                    id_komoditas = models.komoditas.objects.get(id_komoditas = komoditas),
                    kuantitas_produk = None,
                    kuantitas_komoditas = kuantitask,
                )
                detail.save()
                iddetail.append(detail.iddetail_penjualan)
                print('kondisi 2')
            
            elif komoditas == '' and produk != '' and kuantitasp != '' and kuantitask == '' :
                detail = models.detailpenjualan(
                    id_penjualan = models.penjualan.objects.get(id_penjualan = id),
                    id_produk = models.produk.objects.get(id_produk = produk),
                    id_komoditas = None,
                    kuantitas_produk = kuantitasp,
                    kuantitas_komoditas = None,
                )
                detail.save()
                iddetail.append(detail.iddetail_penjualan)
                print('kondisi 3')

            else :
                getdetailpenjualan = models.detailpenjualan.objects.filter(iddetail_penjualan__in = iddetail)
                getdetailpenjualan.delete()
                print('kondisi 4')
                messages.error(request, 'Data Detail Penjualan minimal memiliki produk/komoditas dan kuantitas yang sesuai, Coba Ulang Kembali!')
                return redirect(reverse('create_detail_penjualan', args =[id]))
            
        messages.success(request, 'Data Detail Penjualan Berhasil Ditambahkan!')
        return redirect('read_penjualan')
    
@login_required(login_url='login')
@role_required(['owner', 'admin'])
def update_detail_penjualan(request, id) :
    komoditas = models.komoditas.objects.all()
    produk = models.produk.objects.all()
    getpenjualan = models.penjualan.objects.all()
    getdetailpenjualan = models.detailpenjualan.objects.get(iddetail_penjualan = id)
    id_penjualan = getdetailpenjualan.id_penjualan.id_penjualan

    if getdetailpenjualan.id_produk is None :
        id_komoditas = getdetailpenjualan.id_komoditas.id_komoditas
        kuantitask = getdetailpenjualan.kuantitas_komoditas
        if request.method == 'GET' :
            return render (request, 'penjualan/update_detail_penjualan.html', {
                'kuantitask' : kuantitask,
                'id_komoditas' : id_komoditas,
                'komoditas' : komoditas,
                'produk' : produk,
                'id_penjualan' : id_penjualan,
                'getdetailpenjualan' : getdetailpenjualan,
                'getpenjualan' : getpenjualan,
                'id' : id

            })

    if getdetailpenjualan.id_komoditas is None :
        id_produk = getdetailpenjualan.id_produk.id_produk
        kuantitasp = getdetailpenjualan.kuantitas_produk
        if request.method == 'GET' :
            return render (request, 'penjualan/update_detail_penjualan.html', {
                'kuantitasp' : kuantitasp,
                'id_produk' : id_produk,
                'komoditas' : komoditas,
                'produk' : produk,
                'id_penjualan' : id_penjualan,
                'getdetailpenjualan' : getdetailpenjualan,
                'getpenjualan' : getpenjualan,
                'id' : id
            })
        
    else :
        id_komoditas = getdetailpenjualan.id_komoditas.id_komoditas
        kuantitask = getdetailpenjualan.kuantitas_komoditas
        id_produk = getdetailpenjualan.id_produk.id_produk
        kuantitasp = getdetailpenjualan.kuantitas_produk
        if request.method == 'GET' :
            return render (request, 'penjualan/update_detail_penjualan.html', {
                'id_komoditas' : id_komoditas,
                'kuantitask' : kuantitask,
                'kuantitasp' : kuantitasp,
                'id_produk' : id_produk,
                'komoditas' : komoditas,
                'produk' : produk,
                'id_penjualan' : id_penjualan,
                'getdetailpenjualan' : getdetailpenjualan,
                'getpenjualan' : getpenjualan,
                'id' : id
            })

        
    idpenjualan = request.POST['idpenjualan']
    kuantitasp = request.POST['kuantitasp']
    kuantitask = request.POST['kuantitask']
    produk = request.POST['produk']
    komoditas = request.POST['komoditas']

    print('ini komoditas',kuantitask)
    print(kuantitasp)

    if komoditas != '' and produk != '' and kuantitasp != '' and kuantitask != '' :
        getdetailpenjualan.iddetail_penjualan = getdetailpenjualan.iddetail_penjualan
        getdetailpenjualan.id_penjualan = models.penjualan.objects.get(id_penjualan = idpenjualan)
        getdetailpenjualan.id_produk = models.produk.objects.get(id_produk = produk)
        getdetailpenjualan.id_komoditas = models.komoditas.objects.get(id_komoditas = komoditas)
        getdetailpenjualan.kuantitas_produk = kuantitasp
        getdetailpenjualan.kuantitas_komoditas = kuantitask

        getdetailpenjualan.save()

        print('kondisi 1')


    elif komoditas != '' and produk == '' and kuantitasp == '' and kuantitask != '' :
        getdetailpenjualan.iddetail_penjualan = getdetailpenjualan.iddetail_penjualan
        getdetailpenjualan.id_penjualan = models.penjualan.objects.get(id_penjualan = idpenjualan)
        getdetailpenjualan.id_produk = None
        getdetailpenjualan.id_komoditas = models.komoditas.objects.get(id_komoditas = komoditas)
        getdetailpenjualan.kuantitas_produk = None
        getdetailpenjualan.kuantitas_komoditas = kuantitask

        getdetailpenjualan.save()

        print('kondisi 2')
    
    elif komoditas == '' and produk != '' and kuantitasp != '' and kuantitask == '' :
        getdetailpenjualan.iddetail_penjualan = getdetailpenjualan.iddetail_penjualan
        getdetailpenjualan.id_penjualan = models.penjualan.objects.get(id_penjualan = idpenjualan)
        getdetailpenjualan.id_produk = models.produk.objects.get(id_produk = produk)
        getdetailpenjualan.id_komoditas = None
        getdetailpenjualan.kuantitas_produk = kuantitasp
        getdetailpenjualan.kuantitas_komoditas = None

        getdetailpenjualan.save()

        print('kondisi 3')

    else :
        print('sayaaaaaa')
        messages.error(request, 'Data Detail Penjualan minimal memiliki produk/komoditas dan kuantitas yang sesuai, Coba Ulang Kembali!')
        return redirect(reverse('update_detail_penjualan', args =[id]))


    messages.success(request, "Data Detail Penjualan berhasil diperbarui!")
    return redirect('read_penjualan')
    
@login_required(login_url='login')
@role_required(['owner'])
def delete_detail_penjualan(request, id) :
    getdetailpenjualan = models.detailpenjualan.objects.get(iddetail_penjualan = id)
    getdetailpenjualan.delete()
    messages.error(request, "Data Penjualan berhasil dihapus!")
    return redirect('read_penjualan')

'''CRUD PRODUK'''
@login_required(login_url='login')
@role_required(['owner'])
def create_produk(request) :
    if request.method == 'GET' :
        return render(request, 'produk/create_produk.html')
    
    else :
        nama_produk = request.POST['nama_produk']
        satuan_produk = request.POST['satuan_produk']
        harga_produk = request.POST['harga_produk']

        produkobj = models.produk.objects.filter(nama_produk = nama_produk)
        if produkobj.exists() :
            messages.error(request, 'Nama Produk sudah ada!')
            return redirect('create_produk')

        
        data = models.produk(
            nama_produk = nama_produk,
            satuan_produk = satuan_produk,
            harga_produk = harga_produk,
        )
        data.save()
        
        models.ActivityLog(
            user=request.user,
            action="Tambah Produk",
            description=f"Menambahkan produk baru: {data.nama_produk} dengan satuan '{data.satuan_produk}' dan harga Rp {data.harga_produk}."
        ).save()

        messages.success(request, 'Data Produk Berhasil Ditambahkan!')
        return redirect('read_produk')

@login_required(login_url='login')
@role_required(['owner', 'admin', 'produksi'])
def read_produk(request) :
    produkobj = models.produk.objects.all()
    if not produkobj.exists():
        messages.error(request, "Data Produk Tidak Ditemukan!")

    return render(request, 'produk/read_produk.html', {
        'produkobj' : produkobj
    })

@login_required(login_url='login')
@role_required(['owner'])
def update_produk(request, id) :
    getproduk = models.produk.objects.get(id_produk = id)
    if request.method == 'GET' :
        return render(request, 'produk/update_produk.html', {
            'getproduk' : getproduk,
            'id' : id
        })
    
    else :
        nama_produk = request.POST['nama_produk']
        satuan_produk = request.POST['satuan_produk']
        harga_produk = request.POST['harga_produk']

        produkobj = models.produk.objects.filter(nama_produk = nama_produk)
        if produkobj.exists() and getproduk.nama_produk != nama_produk:
            messages.error(request, 'Data Produk sudah ada!')
            return redirect('update_produk', id)
        
        old_nama = getproduk.nama_produk
        old_satuan = getproduk.satuan_produk
        old_harga = getproduk.harga_produk

        getproduk.id_produk = getproduk.id_produk
        getproduk.nama_produk = nama_produk
        getproduk.satuan_produk = satuan_produk
        getproduk.harga_produk = harga_produk

        getproduk.save()
        
        models.ActivityLog(
            user=request.user,
            action="Update Produk",
            description=(
                f"Memperbarui produk ID {id}:\n "
                f"Nama '{old_nama}' menjadi '{nama_produk}',\n "
                f"Satuan '{old_satuan}' menjadi '{satuan_produk}',\n "
                f"Harga Rp {old_harga} menjadi Rp {harga_produk}.\n"
            )
        ).save()

        messages.success(request, "Data Produk berhasil diperbarui!")
        return redirect('read_produk')

@login_required(login_url='login')
@role_required(['owner'])
def delete_produk(request, id) :
    getproduk = models.produk.objects.get(id_produk = id)
    nama_produk = getproduk.nama_produk
    harga_produk = getproduk.harga_produk

    getproduk.delete()

    models.ActivityLog(
        user=request.user,
        action="Hapus Produk",
        description=(
            f"Menghapus produk: {nama_produk} dengan harga Rp {harga_produk} "
        )
    ).save()

    messages.error(request, "Data Produk berhasil dihapus!")
    return redirect('read_produk')

'''CRUD KOMODITAS'''
@login_required(login_url='login')
@role_required(['owner'])
def create_komoditas(request):
    gradeobj = models.grade.objects.all()
    
    if request.method == 'GET':
        return render(request, 'komoditas/create_komoditas.html', {
            'gradeobj': gradeobj
        })
    
    else:
        nama_grade = request.POST['nama_grade']
        nama_komoditas = request.POST['nama_komoditas']
        harga_beli = request.POST['harga_beli']
        harga_jual = request.POST['harga_jual']

        komoditasobj = models.komoditas.objects.filter(
            nama_komoditas=nama_komoditas,
            id_grade__nama_grade=nama_grade
        )

        if komoditasobj.exists():
            messages.error(request, 'Nama Komoditas sudah ada!')
        
        else:
            grade_instance = models.grade.objects.get(nama_grade=nama_grade)
            data = models.komoditas(
                id_grade=grade_instance,
                nama_komoditas=nama_komoditas,
                harga_beli=harga_beli,
                harga_jual=harga_jual,
            )
            data.save()

            models.ActivityLog(
                user=request.user,
                action="Tambah Komoditas",
                description=(
                    f"Menambahkan komoditas baru: {data.nama_komoditas} "
                    f"dengan grade {data.id_grade.nama_grade},"
                    f"harga beli Rp {data.harga_beli}, "
                    f"harga jual Rp {data.harga_jual}."
                )
            ).save()

            messages.success(request, 'Data Komoditas Berhasil Ditambahkan!')

        return redirect('read_komoditas')


@login_required(login_url='login')
@role_required(['owner', 'admin', 'inspeksi'])
def read_komoditas(request) :
    komoditasobj = models.komoditas.objects.all()
    if not komoditasobj.exists():
        messages.error(request, "Data Komoditas Tidak Ditemukan!")

    return render(request, 'komoditas/read_komoditas.html', {
        'komoditasobj' : komoditasobj
    })

@login_required(login_url='login')
@role_required(['owner'])
def update_komoditas(request, id):
    gradeobj = models.grade.objects.all()
    getkomoditas = models.komoditas.objects.get(id_komoditas=id)
    nama_grade = getkomoditas.id_grade.nama_grade

    if request.method == 'GET':
        return render(request, 'komoditas/update_komoditas.html', {
            'getkomoditas': getkomoditas,
            'nama_grade': nama_grade,
            'gradeobj': gradeobj,
            'id': id,
        })

    else:
        nama_grade_baru = request.POST['nama_grade']
        nama_komoditas_baru = request.POST['nama_komoditas']
        harga_beli_baru = request.POST['harga_beli']
        harga_jual_baru = request.POST['harga_jual']

        komoditasobj = models.komoditas.objects.filter(nama_komoditas=nama_komoditas_baru,id_grade__nama_grade=nama_grade_baru)
        if komoditasobj.exists() and (getkomoditas.nama_komoditas != nama_komoditas_baru or getkomoditas.id_grade.nama_grade != nama_grade_baru):
            messages.error(request, 'Data Komoditas sudah ada!')
            return redirect('update_komoditas', id)

        nama_komoditas_lama = getkomoditas.nama_komoditas
        grade_lama = getkomoditas.id_grade.nama_grade
        harga_beli_lama = getkomoditas.harga_beli
        harga_jual_lama = getkomoditas.harga_jual

        getkomoditas.id_grade = models.grade.objects.get(nama_grade=nama_grade_baru)
        getkomoditas.nama_komoditas = nama_komoditas_baru
        getkomoditas.harga_beli = harga_beli_baru
        getkomoditas.harga_jual = harga_jual_baru
        getkomoditas.save()

        models.ActivityLog(
            user=request.user,
            action="Update Komoditas",
            description=(
                f"Memperbarui komoditas ID {getkomoditas.id_komoditas}.\n "
                f"Dari: {nama_komoditas_lama} (Grade: {grade_lama}, Beli: Rp{harga_beli_lama}, Jual: Rp{harga_jual_lama})\n "
                f"Menjadi: {nama_komoditas_baru} (Grade: {nama_grade_baru}, Beli: Rp{harga_beli_baru}, Jual: Rp{harga_jual_baru})\n"
            )
        ).save()

        messages.success(request, 'Data Komoditas berhasil diperbarui!')
        return redirect('read_komoditas')


@login_required(login_url='login')
@role_required(['owner'])
def delete_komoditas(request, id):
    getkomoditas = models.komoditas.objects.get(id_komoditas=id)
    nama_komoditas = getkomoditas.nama_komoditas
    nama_grade = getkomoditas.id_grade.nama_grade

    models.ActivityLog(
        user=request.user,
        action="Hapus Komoditas",
        description=(
            f"Menghapus komoditas: {nama_komoditas} (Grade: {nama_grade}) "
        )
    ).save()
    getkomoditas.delete()
    messages.error(request, "Data komoditas berhasil dihapus!")
    return redirect('read_komoditas')


'''CRUD GRADE'''
@login_required(login_url='login')
@role_required(['owner','admin','inspeksi'])
def read_grade(request) :
    gradeobj = models.grade.objects.all()
    return render(request, 'grade/read_grade.html', {'gradeobj': gradeobj})

@login_required(login_url='login')
@role_required(['owner'])
def create_grade(request) :
    if request.method == "GET" :
        return render(request, 
                      'grade/create_grade.html')
    else :
        namagrade = request.POST["nama_grade"]
        gradeobj = models.grade.objects.filter(nama_grade=namagrade)
        
        if len(gradeobj) >0:
            messages.error(request,"Nama Grade Sudah Ada")
            return redirect("create_mitra")
        else :
            deskripsi = request.POST["deskripsi"]
    
            data = models.grade(
                nama_grade = namagrade,
                deskripsi_grade = deskripsi,
            )
            data.save()
            messages.success(request,"Data Grade Berhasil Ditambahkan!")
            
        models.ActivityLog(
            user=request.user,
            action="Tambah Grade",
            description=f"Menambahkan grade baru: {data.nama_grade} - {data.deskripsi_grade}."
        ).save()
        
        return redirect("read_grade")

@login_required(login_url='login')
@role_required(['owner'])
def update_grade(request,id) :
    try:
        getgradeobj = models.grade.objects.get(id_grade=id)
    except models.grade.DoesNotExist:
        messages.error(request, "Grade tidak ditemukan!")
        return redirect('read_grade')


    if request.method == "GET":
        return render(request, 'grade/update_grade.html', {
            'getgradeobj': getgradeobj,
        })
    else:
        namagrade = request.POST["nama_grade"]
        if models.grade.objects.filter(nama_grade=namagrade).exclude(id_grade = id).exists() :
            messages.error(request,"Nama grade sudah ada!")
            return render(request, 'grade/update_grade.html', {
            'getgradeobj': getgradeobj,
            }) 
            
        old_nama = getgradeobj.nama_grade
        old_desc = getgradeobj.deskripsi_grade

        getgradeobj.nama_grade = request.POST["nama_grade"]
        getgradeobj.deskripsi_grade = request.POST["deskripsi_grade"]
        getgradeobj.save()

        models.ActivityLog(
            user=request.user,
            action="Update Grade",
            description=f"Memperbarui grade dari '{old_nama} - {old_desc}' \n menjadi '{getgradeobj.nama_grade} - {getgradeobj.deskripsi_grade}'."
        ).save()
        messages.success(request, "Grade berhasil diperbarui!")
        return redirect('read_grade')

@login_required(login_url='login')
@role_required(['owner'])   
def delete_grade(request,id) :
    getgrade = models.grade.objects.get(id_grade=id)
    nama_grade = getgrade.nama_grade
    deskripsi_grade = getgrade.deskripsi_grade

    getgrade.delete()

    models.ActivityLog(
        user=request.user,
        action="Hapus Grade",
        description=f"Menghapus grade: {nama_grade} - {deskripsi_grade}."
    ).save()
    messages.success(request, "Grade berhasil dihapus!")
    return redirect('read_grade')

'''CRUD PASAR'''
@login_required(login_url='login')
@role_required(['owner'])
def create_pasar(request) :
    if request.method == 'GET' :
        return render(request, 'pasar/create_pasar.html')
    
    else :
        nama_pasar = request.POST['nama_pasar']
        alamat_pasar = request.POST['alamat_pasar']

        pasarobj = models.pasar.objects.filter(nama_pasar = nama_pasar)
        if pasarobj.exists() :
            messages.error(request, 'Nama Pasar sudah ada!')

        else :
            data = models.pasar(
                nama_pasar = nama_pasar,
                alamat_pasar = alamat_pasar,
            )
            data.save()
            
            models.ActivityLog(
                user=request.user,
                action="Tambah Pasar",
                description=f"Menambahkan pasar baru: {data.nama_pasar}, beralamat di {data.alamat_pasar}."
            ).save()
            messages.success(request, 'Data Pasar Berhasil Ditambahkan!')

        return redirect('read_pasar')

@login_required(login_url='login')
@role_required(['owner', 'admin'])
def read_pasar(request) :
    pasarobj = models.pasar.objects.all()
    if not pasarobj.exists():
        messages.error(request, "Data Pasar Tidak Ditemukan!")

    return render(request, 'pasar/read_pasar.html', {
        'pasarobj' : pasarobj
    })

def update_pasar(request, id) :
    getpasar = models.pasar.objects.get(id_pasar = id)
    if request.method == 'GET' :
        return render(request, 'pasar/update_pasar.html', {
            'getpasar' : getpasar,
            'id' : id
        })
    
    else :
        nama_pasar = request.POST['nama_pasar']
        alamat_pasar = request.POST['alamat_pasar']
        
        pasarobj = models.pasar.objects.filter(nama_pasar = nama_pasar)
        if pasarobj.exists() and getpasar.nama_pasar != nama_pasar:
            messages.error(request, 'Nama Pasar sudah ada!')
            return redirect('update_pasar', id)

        nama_lama = getpasar.nama_pasar
        alamat_lama = getpasar.alamat_pasar

        getpasar.nama_pasar = nama_pasar
        getpasar.alamat_pasar = alamat_pasar
        getpasar.save()

        models.ActivityLog(
            user=request.user,
            action="Update Pasar",
            description=f"Memperbarui pasar dari '{nama_lama} - {alamat_lama}' \n menjadi '{nama_pasar} - {alamat_pasar}'."
        ).save()

        messages.success(request, 'Data Pasar berhasil diperbarui!')
        return redirect('read_pasar')

@login_required(login_url='login')
@role_required(['owner'])
def delete_pasar(request, id) :
    getpasar = models.pasar.objects.get(id_pasar = id)
    nama = getpasar.nama_pasar
    alamat = getpasar.alamat_pasar

    getpasar.delete()

    models.ActivityLog(
        user=request.user,
        action="Hapus Pasar",
        description=f"Menghapus pasar {nama} dengan alamat {alamat}."
    ).save()

    messages.error(request, "Data pasar berhasil dihapus!")
    return redirect('read_pasar')

@login_required(login_url='login')
@role_required(['owner'])
def laporan_penjualan(request) :
    mulai = request.GET.get('mulai')
    akhir = request.GET.get('akhir')

    if mulai and akhir  :
        mulai_date = datetime.strptime(mulai, "%Y-%m-%d")
        akhir_date = datetime.strptime(akhir, "%Y-%m-%d")

        penjualanobj = models.penjualan.objects.filter(tanggal__range = (mulai,akhir)).order_by('tanggal')
        if not penjualanobj.exists() :
            messages.error(request, "Data Penjualan tidak ada!")
            return redirect('laporan_penjualan')
        detailobjlokal = []
        listgrandtotal = []
        for item in penjualanobj :
            listdetail = []
            listhargajual = []
            id_penjualan = item.id_penjualan
        
            detailpenjualanobj = models.detailpenjualan.objects.filter(id_penjualan = id_penjualan)

            if not detailpenjualanobj.exists() :
                continue

            for i in detailpenjualanobj :
                hargapenjualan = (i.id_komoditas.harga_jual * i.kuantitas_komoditas) + (i.id_produk.harga_produk * i.kuantitas_produk)
                listhargajual.append(hargapenjualan)

            totaljual = sum(listhargajual)
            listdetail.append(item)
            listdetail.append(detailpenjualanobj)
            listdetail.append(listhargajual)
            listdetail.append(totaljual)

            listgrandtotal.append(totaljual)
            detailobjlokal.append(listdetail)

        grandtotallokal = sum(listgrandtotal)

        return render(request,'laporan/laporan_penjualan.html',{
        'detailobjlokal' :detailobjlokal,
        'grandtotallokal' :grandtotallokal,
        'mulai' : mulai_date,
        'akhir' :akhir_date,
    })
    else :
        penjualanobj = models.penjualan.objects.all().order_by('tanggal')
        detailobjlokal = []
        listgrandtotal = []
        for item in penjualanobj :
            listdetail = []
            listhargajual = []
            id_penjualan = item.id_penjualan
        
            detailpenjualanobj = models.detailpenjualan.objects.filter(id_penjualan = id_penjualan)

            
            if not detailpenjualanobj.exists() :
                continue

            for i in detailpenjualanobj :
                if i.id_komoditas is not None and i.id_produk is not None :
                    hargapenjualan = (i.id_komoditas.harga_jual * i.kuantitas_komoditas) + (i.id_produk.harga_produk * i.kuantitas_produk)
                    listhargajual.append(hargapenjualan)
                elif i.id_komoditas is None and i.id_produk is not None :
                    hargapenjualan = (i.id_produk.harga_produk * i.kuantitas_produk)
                    listhargajual.append(hargapenjualan)
                elif i.id_komoditas is not None and i.id_produk is None :
                    hargapenjualan = (i.id_komoditas.harga_jual * i.kuantitas_komoditas)
                    listhargajual.append(hargapenjualan)

            totaljual = sum(listhargajual)
            listdetail.append(item)
            listdetail.append(detailpenjualanobj)
            listdetail.append(listhargajual)
            listdetail.append(totaljual)

            listgrandtotal.append(totaljual)
            detailobjlokal.append(listdetail)
        grandtotallokal = sum(listgrandtotal)

        return render(request,'laporan/laporan_penjualan.html',{
        'detailobjlokal' :detailobjlokal,
        'grandtotallokal' :grandtotallokal,
    })

'''PANEN MITRA'''
@login_required(login_url="login")
@role_required(["owner", 'admin','inspeksi']) 
def read_panenmitra(request) :
    panenmitra = models.detailpanenmitra.objects.all().order_by('idpanen_mitra__tanggal_panen')
    if not panenmitra.exists() :
        messages.error(request, 'Data Panen Mitra Tidak Ditemukan!')
        return render(request,'panen/panenmitra/read_panenmitra.html')
    else :

        

        return render(request,'panen/panenmitra/read_panenmitra.html',{
            'panenmitra' : panenmitra,
        })
        
# @login_required(login_url="login")
# @role_required(["owner",'admin']) 
# def create_panenmitra(request) :
#     filtermitra = models.mitra.objects.filter(status_mitra = True)
#     allkomoditas = models.komoditas.objects.all()
#     if request.method == "GET" :
#         return render(request, 
#                       'panen/panenmitra/create_panenmitra.html',{
#                             'filtermitra' : filtermitra,
#                             'allkomoditas' : allkomoditas,
#                       })
#     else :
#         nama_mitra = request.POST["nama_mitra"]
#         tanggal_panen = request.POST["tanggal_panen"]
#         komoditas = request.POST.getlist("komoditas")
#         batch = request.POST.getlist("batch")
#         kadaluwarsa = request.POST.getlist("kadaluwarsa")
#         kuantitas = request.POST.getlist("kuantitas")
       
#         panen_mitra = models.panenmitra(
#             id_mitra = models.mitra.objects.get(id_mitra=nama_mitra),
#             tanggal_panen = tanggal_panen
#         )

#         panen_mitra.save()
       
#         for komoditas,batch,kadaluwarsa,kuantitas in zip(komoditas,batch,kadaluwarsa,kuantitas) :
#             models.detailpanenmitra(
#                 idpanen_mitra = panen_mitra,
#                 id_komoditas = models.komoditas.objects.get(
#                     id_komoditas = komoditas
#                 ),
#                 batch = batch,
#                 tanggal_kadaluwarsa = kadaluwarsa,
#                 kuantitas = kuantitas,
#             ).save()

#         messages.success(request,"Data Panen Mitra Berhasil Ditambahkan!")
#         return redirect("read_panenmitra")
            
@login_required(login_url="login")
@role_required(["owner"])
def create_panenmitra(request):
    allkomoditas = models.komoditas.objects.all()
    allmitra = models.mitra.objects.all()

    if request.method == "GET":
        return render(request, 'panen/panenmitra/create_panenmitra.html', {
            'allkomoditas': allkomoditas,
            'allmitra': allmitra
        })

    else:
        tanggal_panen = request.POST["tanggal_panen"]
        id_mitra = request.POST["nama_mitra"]
        komoditas_list = request.POST.getlist("komoditas")
        batch_list = request.POST.getlist("batch")
        kadaluwarsa_list = request.POST.getlist("kadaluwarsa")
        kuantitas_list = request.POST.getlist("kuantitas")

        panen_mitra = models.panenmitra(
            tanggal_panen=tanggal_panen,
            id_mitra=models.mitra.objects.get(id_mitra=id_mitra)
        )
        panen_mitra.save()

        for komoditas_id, batch, kadaluwarsa, kuantitas in zip(komoditas_list, batch_list, kadaluwarsa_list, kuantitas_list):
            komoditas_obj = models.komoditas.objects.get(id_komoditas=komoditas_id)

            if not qr_already_generated(komoditas_id, kadaluwarsa):
                models.detailpanenmitra(
                    idpanen_mitra=panen_mitra,
                    id_komoditas = models.komoditas.objects.get(
                    id_komoditas = komoditas_id
                 ),
                    batch=batch,
                    tanggal_kadaluwarsa=kadaluwarsa,
                    kuantitas=kuantitas,
                ).save()
                
                komoditas_str = models.komoditas.objects.get(id_komoditas=komoditas_id)
                qr_data = generate_qr_data(
                    str(komoditas_str),
                    kadaluwarsa,
                    kuantitas
                )
                qr_image = generate_qr_image(qr_data)

                response = HttpResponse(qr_image.getvalue(), content_type="image/png")
                response['Content-Disposition'] = f'attachment; filename="qr_{komoditas_obj.nama_komoditas}_{komoditas_obj.id_grade.nama_grade}_{kadaluwarsa}.png"'
                return response
            else:
                models.detailpanenmitra(
                    idpanen_mitra=panen_mitra,
                    id_komoditas = models.komoditas.objects.get(
                     id_komoditas = komoditas_id
                 ),
                    batch=batch,
                    tanggal_kadaluwarsa=kadaluwarsa,
                    kuantitas=kuantitas,
                ).save()
                
            for komoditas_id, batch, kadaluwarsa, kuantitas in zip(komoditas_list, batch_list, kadaluwarsa_list, kuantitas_list):
                komoditas_obj = models.komoditas.objects.get(id_komoditas=komoditas_id)

                models.ActivityLog(
                    user=request.user,
                    action="Tambah Panen Mitra",
                    description=(
                        f"Menambahkan panen mitra dari: {panen_mitra.id_mitra.nama_mitra}"
                        f"dengan tanggal panen: {panen_mitra.tanggal_panen}"
                    )
                ).save()
                
                messages.warning(request, f"QR tidak dibuat karena data {komoditas_id} dengan kadaluarsa {kadaluwarsa} sudah ada.")
    messages.success(request, "Data Panen Mitra Berhasil Ditambahkan!")
    return redirect("total_komoditas")


@login_required(login_url="login")
@role_required(["owner",'admin','inspeksi']) 
def update_panenmitra(request, id):
    try:
        getdetailobj = models.detailpanenmitra.objects.get(iddetailpanen_mitra=id)
        
    except models.detailpanenmitra.DoesNotExist:
        messages.error(request, "Data Panen Mitra tidak ditemukan!")
        return redirect('read_panenmitra')
    filtermitra = models.mitra.objects.filter(status_mitra = True)
    allkomoditas = models.komoditas.objects.all()
  
    if request.method == "GET":
        tanggal_panen = getdetailobj.idpanen_mitra.tanggal_panen.strftime('%Y-%m-%d')  # Format tanggal
        tanggal_kadaluwarsa = getdetailobj.tanggal_kadaluwarsa.strftime('%Y-%m-%d')  # Format tanggal
        return render(request, 'panen/panenmitra/update_panenmitra.html', {
            'getdetailobj': getdetailobj,
            'filtermitra' : filtermitra,
            'allkomoditas' : allkomoditas,
            'tanggal_panen': tanggal_panen,
            'tanggal_kadaluwarsa': tanggal_kadaluwarsa
        })
    else:     
        # Perbarui objek mitra
        getmitra = models.mitra.objects.get(id_mitra=request.POST["nama_mitra"])
        getkomoditas =models.komoditas.objects.get(id_komoditas=request.POST["komoditas"])

        getdetailobj.idpanen_mitra.id_mitra = getmitra
        getdetailobj.idpanen_mitra.tanggal_panen = request.POST["tanggal_panen"]
        getdetailobj.id_komoditas = getkomoditas
        getdetailobj.batch = request.POST["batch"]
        getdetailobj.tanggal_kadaluwarsa = request.POST["kadaluwarsa"]
        getdetailobj.kuantitas = request.POST["kuantitas"]

        getdetailobj.idpanen_mitra.save()
        getdetailobj.save()
        
        models.ActivityLog(
        user=request.user,
        action="Update Panen Mitra",
        description=(
            f"Memperbarui data panen mitra: "
            f"{getmitra.nama_mitra}, tanggal panen {getdetailobj.idpanen_mitra.tanggal_panen}"
            )
        ).save()
                
        messages.success(request, "Data panen mitra berhasil diperbarui!")
        return redirect('read_panenmitra')
            
@login_required(login_url="login")
@role_required(["owner"])    
def delete_panenmitra(request,id) :
    getdetailobj = models.detailpanenmitra.objects.get(iddetailpanen_mitra = id)
    
    nama_mitra = getdetailobj.idpanen_mitra.id_mitra.nama_mitra
    tanggal_panen = getdetailobj.idpanen_mitra.tanggal_panen.strftime('%Y-%m-%d')
    
    models.ActivityLog(
        user=request.user,
        action="Hapus Panen Mitra",
        description=f"Menghapus data panen mitra: {nama_mitra}, tanggal panen {tanggal_panen}"
    ).savea()
    
    getdetailobj.delete()
    messages.success(request, "Data berhasil dihapus!")
    return redirect('read_panenmitra')

'''PANEN LOKAL'''
@login_required(login_url="login")
@role_required(["owner",'admin','inspeksi']) 
def read_panenlokal(request) :
    panenlokal = models.detailpanenlokal.objects.all().order_by('idpanen_lokal__tanggal_panen')
    if not panenlokal.exists() :
        messages.error(request, 'Data Panen lokal Tidak Ditemukan!')
        return render(request,'panen/panenlokal/read_panenlokal.html')
    else :

        return render(request,'panen/panenlokal/read_panenlokal.html',{
            'panenlokal' : panenlokal,
        })
# @login_required(login_url="login")
# @role_required(["owner"]) 
# def create_panenlokal(request) :
    
#     allkomoditas = models.komoditas.objects.all()
#     if request.method == "GET" :
#         return render(request, 
#                       'panen/panenlokal/create_panenlokal.html',{
#                             'allkomoditas' : allkomoditas,
#                       })
#     else :
#         tanggal_panen = request.POST["tanggal_panen"]
#         komoditas = request.POST.getlist("komoditas")
#         batch = request.POST.getlist("batch")
#         kadaluwarsa = request.POST.getlist("kadaluwarsa")
#         kuantitas = request.POST.getlist("kuantitas")
       
#         panen_lokal = models.panenlokal(
#             tanggal_panen = tanggal_panen
#         )

#         panen_lokal.save()

#         for komoditas,batch,kadaluwarsa,kuantitas in zip(komoditas,batch,kadaluwarsa,kuantitas) :
#             models.detailpanenlokal(
#                 idpanen_lokal = panen_lokal,
#                 id_komoditas = models.komoditas.objects.get(
#                     id_komoditas = komoditas
#                 ),
#                 batch = batch,
#                 tanggal_kadaluwarsa = kadaluwarsa,
#                 kuantitas = kuantitas,
#             ).save()

#         messages.success(request,"Data Panen lokal Berhasil Ditambahkan!")
#         return redirect("read_panenlokal")
            
@login_required(login_url="login")
@role_required(["owner"])
def create_panenlokal(request):
    allkomoditas = models.komoditas.objects.all()
    alllokal = models.panenlokal.objects.all()

    if request.method == "GET":
        return render(request, 'panen/panenlokal/create_panenlokal.html', {
            'allkomoditas': allkomoditas,
            'alllokal': alllokal
        })

    else:
        tanggal_panen = request.POST["tanggal_panen"]
        komoditas_list = request.POST.getlist("komoditas")
        batch_list = request.POST.getlist("batch")
        kadaluwarsa_list = request.POST.getlist("kadaluwarsa")
        kuantitas_list = request.POST.getlist("kuantitas")

        panen_lokal = models.panenlokal(
            tanggal_panen=tanggal_panen,
        )
        panen_lokal.save()

        for komoditas_id, batch, kadaluwarsa, kuantitas in zip(komoditas_list, batch_list, kadaluwarsa_list, kuantitas_list):
            komoditas_obj = models.komoditas.objects.get(id_komoditas=komoditas_id)


            if not qr_already_generated(komoditas_id, kadaluwarsa):

                models.detailpanenlokal(
                    idpanen_lokal=panen_lokal,
                    id_komoditas = models.komoditas.objects.get(
                     id_komoditas = komoditas_id
                 ),
                    batch=batch,
                    tanggal_kadaluwarsa=kadaluwarsa,
                    kuantitas=kuantitas,
                ).save()
                
                komoditas_str = models.komoditas.objects.get(id_komoditas=komoditas_id)
                qr_data = generate_qr_data(
                    str(komoditas_str),
                    kadaluwarsa,
                    kuantitas
                )
                qr_image = generate_qr_image(qr_data)

                response = HttpResponse(qr_image.getvalue(), content_type="image/png")
                response['Content-Disposition'] = f'attachment; filename="qr_{komoditas_obj.nama_komoditas}_{komoditas_obj.id_grade.nama_grade}_{kadaluwarsa}.png"'
                return response
            else:
                
                models.detailpanenlokal(
                    idpanen_lokal=panen_lokal,
                    id_komoditas = models.komoditas.objects.get(
                     id_komoditas = komoditas_id
                 ),
                    batch=batch,
                    tanggal_kadaluwarsa=kadaluwarsa,
                    kuantitas=kuantitas,
                ).save()
                messages.warning(request, f"QR tidak dibuat karena data {komoditas_id} dengan kadaluarsa {kadaluwarsa} sudah ada.")
                
            komoditas1 = models.komoditas.objects.get(id_komoditas=komoditas_list[0])
            nama_komoditas1 = komoditas1.nama_komoditas
            nama_grade1 = komoditas1.id_grade.nama_grade

            models.ActivityLog(
                user=request.user,
                action="Tambah Panen Lokal",
                description=f"Menambahkan panen lokal tanggal {tanggal_panen} untuk komoditas {nama_komoditas1} - {nama_grade1}"
            ).save()
            
    messages.success(request, "Data Panen lokal Berhasil Ditambahkan!")
    return redirect("total_komoditas")
    
@login_required(login_url="login")
@role_required(["owner",'inspeksi']) 
def update_panenlokal(request, id):
    try:
        getdetailobj = models.detailpanenlokal.objects.get(iddetailpanen_lokal=id)
        
    except models.detailpanenlokal.DoesNotExist:
        messages.error(request, "Data Panen lokal tidak ditemukan!")
        return redirect('read_panenlokal')
    allkomoditas = models.komoditas.objects.all()
  
    if request.method == "GET":
        tanggal_panen = getdetailobj.idpanen_lokal.tanggal_panen.strftime('%Y-%m-%d')  # Format tanggal
        tanggal_kadaluwarsa = getdetailobj.tanggal_kadaluwarsa.strftime('%Y-%m-%d')  # Format tanggal
        return render(request, 'panen/panenlokal/update_panenlokal.html', {
            'getdetailobj': getdetailobj,
            'allkomoditas' : allkomoditas,
            'tanggal_panen': tanggal_panen,
            'tanggal_kadaluwarsa': tanggal_kadaluwarsa
        })
    else:     
    
        getkomoditas =models.komoditas.objects.get(id_komoditas=request.POST["komoditas"])

        getdetailobj.idpanen_lokal.tanggal_panen = request.POST["tanggal_panen"]
        getdetailobj.id_komoditas = getkomoditas
        getdetailobj.batch = request.POST["batch"]
        getdetailobj.tanggal_kadaluwarsa = request.POST["kadaluwarsa"]
        getdetailobj.kuantitas = request.POST["kuantitas"]

        getdetailobj.idpanen_lokal.save()
        getdetailobj.save()
        
        models.ActivityLog(
            user=request.user,
            action="Update Panen Lokal",
            description=f"Memperbarui panen lokal tanggal {getdetailobj.idpanen_lokal.tanggal_panen} untuk komoditas {getkomoditas.nama_komoditas} (Grade {getkomoditas.id_grade.nama_grade})"
        ).save()
   
        messages.success(request, "Data lokal berhasil diperbarui!")
        return redirect('read_panenlokal')
            
@login_required(login_url="login")
@role_required(["owner"]) 
def delete_panenlokal(request,id) :
    getdetailobj = models.detailpanenlokal.objects.get(iddetailpanen_lokal = id)
    
    models.ActivityLog(
        user=request.user,
        action="Hapus Panen Lokal",
        description=f"Menghapus data panen lokal tanggal {getdetailobj.idpanen_lokal.tanggal_panen} untuk komoditas {getdetailobj.id_komoditas.nama_komoditas} (Grade {getdetailobj.id_komoditas.id_grade.nama_grade})"
    ).save()

    getdetailobj.delete()
    messages.success(request, "Data berhasil dihapus!")
    return redirect('read_panenlokal')


'''READ AKUMULASI PENIMBANGAN'''
@login_required(login_url="login")
@role_required(["owner","admin","inspeksi"]) 
def read_penimbanganmitra(request) :
       
    detailobj = models.detailpanenmitra.objects.values('idpanen_mitra__id_mitra__nama_mitra','id_komoditas__nama_komoditas','id_komoditas__id_grade__nama_grade','idpanen_mitra__tanggal_panen','tanggal_kadaluwarsa').annotate(kuantitas_total = Sum('kuantitas')).order_by('idpanen_mitra__tanggal_panen')
    print("detail obj :" ,detailobj)
    return render(request,'panen/penimbangan/read_penimbanganmitra.html',{
        'penimbangan' : detailobj,
    })
@login_required(login_url="login")
@role_required(["owner","admin","inspeksi"]) 
def read_penimbanganlokal(request) :
   
    detailobj = models.detailpanenlokal.objects.values('id_komoditas__nama_komoditas','id_komoditas__id_grade__nama_grade','idpanen_lokal__tanggal_panen','tanggal_kadaluwarsa').annotate(kuantitas_total = Sum('kuantitas')).order_by('idpanen_lokal__tanggal_panen')

    print(detailobj)
    return render(request,'panen/penimbangan/read_penimbanganlokal.html',{
        'penimbangan' : detailobj,
    })


'''CRUD JENIS BIAYA'''
@login_required(login_url="login")
@role_required(["owner","admin"]) 
def read_jenisbiaya(request) :
    biayaobj = models.jenisbiaya.objects.all()
    if not biayaobj.exists() :
        messages.error(request,"Data Jenis Biaya Tidak Ditemukan")
    
    return render(request,'biaya/jenis/read_jenisbiaya.html',{
        'biayaobj' : biayaobj
    })

@login_required(login_url="login")
@role_required(["owner"]) 
def create_jenisbiaya(request) :
    if request.method == "GET" :
        return render(request, 
                      'biaya/jenis/create_jenisbiaya.html')
    else :
        jenis_biaya = request.POST["jenis_biaya"]
        biayaobj = models.jenisbiaya.objects.filter(jenis_biaya=jenis_biaya)
        
        if len(biayaobj) >0:
            messages.error(request,"Jenis Biaya Sudah Ada")
        else :
            models.jenisbiaya(
                jenis_biaya = jenis_biaya,
            ).save()

            messages.success(request,"Data Biaya Berhasil Ditambahkan!")

        return redirect("read_jenisbiaya")
    
@login_required(login_url="login")
@role_required(["owner"]) 
def update_jenisbiaya(request,id) :
    try :
        getbiayaobj = models.jenisbiaya.objects.get(idjenisbiaya = id)
    except models.jenisbiaya.DoesNotExist :
        messages.error(request,"Jenis Biaya Tidak Ditemukan!")

    if request.method == "GET" :
        return render(request, 
                      'biaya/jenis/update_jenisbiaya.html',{
                          'biayaobj' : getbiayaobj
                      })
    else :
        jenis_biaya = request.POST["jenis_biaya"]
        print("jenis biaya :", jenis_biaya)
        if models.jenisbiaya.objects.filter(jenis_biaya=jenis_biaya).exclude(idjenisbiaya=id).exists():
            messages.error(request, "Nama Biaya Sudah Ada!")
            return redirect('read_jenisbiaya')
        
        getbiayaobj.jenis_biaya = jenis_biaya
        getbiayaobj.save()
        messages.success(request,"Data Biaya Berhasil Ditambahkan!")
        return redirect("read_jenisbiaya")

@login_required(login_url="login")
@role_required(["owner"]) 
def delete_jenisbiaya(request,id) :
    getbiayaobj = models.jenisbiaya.objects.get(idjenisbiaya = id)
    getbiayaobj.delete()
    messages.success(request,"Data Berhasil Dihapus")
    return redirect('read_jenisbiaya')


'''CRUD DETAIL BIAYA'''
@login_required(login_url="login")
@role_required(["owner","admin","produksi"])
def read_detailbiaya(request) :
    biayaobj = models.biaya.objects.all().order_by('tanggal')
    if not biayaobj.exists() :
        messages.error(request,"Data Biaya Tidak Ditemukan!")
    
   
    return render(request,'biaya/detail/read_detailbiaya.html',{
        'biayaobj' : biayaobj
    })

@login_required(login_url="login")
@role_required(["owner","admin","produksi"]) 
def create_detailbiaya(request) :
    alljenisbiaya = models.jenisbiaya.objects.all()
    if request.method == "GET" :
        return render(request,'biaya/detail/create_detailbiaya.html',{
            'alljenisbiaya' : alljenisbiaya
        })
    else :
        jenis_biaya = request.POST["jenis_biaya"]
        tanggal = request.POST['tanggal']
        nama_biaya = request.POST['nama_biaya']
        nominal_biaya = request.POST['nominal_biaya']

        jenisbiaya = models.jenisbiaya.objects.get(jenis_biaya=jenis_biaya)

        models.biaya(
            idjenisbiaya = jenisbiaya,
            tanggal = tanggal,
            nama_biaya = nama_biaya,
            nominal_biaya = nominal_biaya
        ).save()

        messages.success(request,"Data Biaya Berhasil Ditambahkan")
        return redirect("read_detailbiaya")

@login_required(login_url="login")
@role_required(["owner","admin", "produksi"])    
def update_detailbiaya(request, id):
    try:
        getdetailobj = models.biaya.objects.get(idbiaya=id)
        
    except models.biayaa.DoesNotExist:
        messages.error(request, "Data Biaya tidak ditemukan!")
        return redirect('read_detailbiaya')
  
    allbiayaobj = models.jenisbiaya.objects.all()
  
    if request.method == "GET":
        tanggal = getdetailobj.tanggal.strftime('%Y-%m-%d')  # Format tanggal
        return render(request, 'biaya/detail/update_detailbiaya.html', {
            'getdetailobj': getdetailobj,
            'allbiayaobj' : allbiayaobj,
            'tanggal': tanggal,
        })
    else:    
        getjenisbiaya = models.jenisbiaya.objects.get(jenis_biaya=request.POST["jenis_biaya"])
        

        getdetailobj.idjenisbiayaa = getjenisbiaya
        getdetailobj.tanggal = request.POST['tanggal']
        getdetailobj.nama_biaya = request.POST["nama_biaya"]
        getdetailobj.nominal_biaya = request.POST["nominal_biaya"]

        # getdetailobj.idjenisbiaya.jenis_biaya.save()
        getdetailobj.save()
        
        messages.success(request, "Data Detail Biaya berhasil diperbarui!")
        return redirect('read_detailbiaya')
    
@login_required(login_url="login")
@role_required(["owner"])    
def delete_detailbiaya(request,id) :
    getdetailobj = models.biaya.objects.get(idbiaya = id)
    getdetailobj.delete()
    messages.success(request,"Data Berhasil Dihapus!")
    return redirect('read_detailbiaya')


''' CRUD PRODUKSI'''
@login_required(login_url="login")
@role_required(["owner","admin","produksi"]) 
def read_produksi(request) :
    produksiobj = models.detailproduksi.objects.all()
    if not produksiobj.exists() :
        messages.error(request,"Data Produksi Tidak Ditemukan!")

    return render(request,"produksi/read_produksi.html",{
        'produksiobj' : produksiobj
    })

@login_required(login_url="login")
@role_required(["owner","admin","produksi"]) 
def create_produksi(request) :
    produkobj = models.produk.objects.all()
    if request.method == 'GET' :
        return render(request,"produksi/create_produksi.html",{
            'produkobj' : produkobj
        })
        
    else :
        tanggal = request.POST['tanggal']
        status_produk = request.POST.getlist('status_produk')
        produk = request.POST.getlist('produk')
        kuantitas = request.POST.getlist('kuantitas')

        produksi = models.produksi(
            tanggal=tanggal,
        )

        log_produk = []
        log_kuantitas = []
        
        produksi.save()
        for status_produk,produk,kuantitas in zip(status_produk,produk,kuantitas) :
            produk_obj = models.produk.objects.get(id_produk=produk)
            models.detailproduksi(
                id_produk=models.produk.objects.get(id_produk = produk),
                id_produksi = produksi,
                kuantitas_produk = kuantitas,
                status_produk = status_produk
            ).save()
            log_produk.append(f"{produk_obj.nama_produk}")
            log_kuantitas.append(f"{kuantitas}")
        
        log_deskripsi = f"Menambahkan produksi tanggal {tanggal}:\n"
        for produk, kuantitas in zip(log_produk, log_kuantitas):
            log_deskripsi += f"- Produk: {produk}, Kuantitas: {kuantitas}\n"

        models.ActivityLog(
            user=request.user,
            action="Tambah Produksi",
            description=log_deskripsi.strip()
        ).save()
        
        messages.success(request,"Data Status Produk Berhasil Disimpan!")
        return redirect("read_produksi")

@login_required(login_url="login")
@role_required(["owner","admin","produksi"])   
def update_produksi(request,id) :
    getproduksi = models.detailproduksi.objects.get(iddetail_produksi = id)
    produkobj = models.produk.objects.all()
    if request.method == 'GET' :
        tanggal =getproduksi.id_produksi.tanggal.strftime('%Y-%m-%d')
        return render(request,"produksi/update_produksi.html",{
            'getproduksi' : getproduksi,
            'produkobj' : produkobj,
            'tanggal' : tanggal
        })
    else :
        getproduk = models.produk.objects.get(id_produk = request.POST['produk'])
        
        produk_lama = getproduksi.id_produk.nama_produk
        kuantitas_lama = getproduksi.kuantitas_produk
        status_lama = getproduksi.status_produk
        tanggal_lama = getproduksi.id_produksi.tanggal.strftime('%Y-%m-%d')

        tanggal_baru = request.POST['tanggal']
        status_baru = request.POST['status_produk']
        kuantitas_baru = request.POST['kuantitas']

        getproduksi.id_produksi.tanggal = tanggal_baru
        getproduksi.status_produk = status_baru
        getproduksi.id_produk = getproduk
        getproduksi.kuantitas_produk = kuantitas_baru
        
        models.ActivityLog.objects.create(
            user=request.user,
            action="Update Produksi",
            description=(
                f"Memperbarui produksi tanggal {tanggal_lama} menjadi {tanggal_baru}:\n"
                f"- Produk: {produk_lama} menjadi {getproduk.nama_produk}\n"
                f"- Kuantitas: {kuantitas_lama} menjadi {kuantitas_baru}\n"
                f"- Status: {status_lama} menjadi {status_baru}"
            )
        )

        messages.success(request, "Data produksi berhasil diperbarui!")
        return redirect('read_produksi')
    
@login_required(login_url="login")
@role_required(["owner"])      
def delete_produksi(request,id) :
    getproduksi = models.detailproduksi.objects.get(iddetail_produksi = id)
    nama_produk = getproduksi.id_produk.nama_produk
    kuantitas = getproduksi.kuantitas_produk
    tanggal = getproduksi.id_produksi.tanggal.strftime('%Y-%m-%d')

    getproduksi.delete()

    models.ActivityLog.objects.create(
        user=request.user,
        action="Hapus Produksi",
        description=f"Menghapus data produksi tanggal {tanggal} untuk produk {nama_produk} sebanyak {kuantitas} unit."
    )
    messages.success(request, "Data produksi berhasil dihapus!")
    return redirect('read_produksi')


'''LAPORAN PANEN'''
@login_required(login_url="login")
@role_required(["owner"]) 
def laporan_panen(request) :
    mulai = request.GET.get('mulai')
    akhir = request.GET.get('akhir')
    jenis_panen = request.GET.get('jenis_panen')
    if mulai and akhir  :
        mulai_date = datetime.strptime(mulai, "%Y-%m-%d")
        akhir_date = datetime.strptime(akhir, "%Y-%m-%d")
        if jenis_panen == 'panen lokal' :

            panenlokalobj = models.panenlokal.objects.filter(tanggal_panen__range = (mulai,akhir)).order_by('tanggal_panen')
            detailobjlokal = []
            listgrandtotal = []
            for item in panenlokalobj :
                listdetail = []
                listhargabeli = []
                idpanen_lokal = item.idpanen_lokal
            
                filterdetailpanen = models.detailpanenlokal.objects.filter(idpanen_lokal = idpanen_lokal)


                if not filterdetailpanen.exists() :
                    continue

                for i in filterdetailpanen :
                    hargapembelian = i.id_komoditas.harga_beli * i.kuantitas
                    print('harga beli' ,hargapembelian)
                    listhargabeli.append(hargapembelian)
                print(listhargabeli)
                totalbeli = sum(listhargabeli)
                listdetail.append(item)
                listdetail.append(filterdetailpanen)
                listdetail.append(listhargabeli)
                listdetail.append(totalbeli)

                listgrandtotal.append(totalbeli)
                detailobjlokal.append(listdetail)

            grandtotallokal = sum(listgrandtotal)
            print(listgrandtotal)
            print(grandtotallokal)
            print(detailobjlokal)
            return render(request,'laporan/laporan_panen.html',{
            'detailobjlokal' :detailobjlokal,
            'grandtotallokal' :grandtotallokal,
            'mulai' : mulai_date,
            'akhir' :akhir_date,
            'jenis_panen' : jenis_panen
        })
        else :
            panenmitraobj = models.panenmitra.objects.filter(tanggal_panen__range = (mulai,akhir)).order_by('tanggal_panen')
       
            detailobj = []
            listgrandtotal = []
            for item in panenmitraobj :
                listdetail = []
                listhargabeli = []
                idpanen_mitra = item.idpanen_mitra
            
                filterdetailpanen = models.detailpanenmitra.objects.filter(idpanen_mitra = idpanen_mitra)

                
                if not filterdetailpanen.exists() :
                    continue

                for i in filterdetailpanen :
                    hargapembelian = i.id_komoditas.harga_beli * i.kuantitas
                    print('harga beli' ,hargapembelian)
                    listhargabeli.append(hargapembelian)
                print(listhargabeli)
                totalbeli = sum(listhargabeli)
                listdetail.append(item)
                listdetail.append(filterdetailpanen)
                listdetail.append(listhargabeli)
                listdetail.append(totalbeli)

                listgrandtotal.append(totalbeli)
                detailobj.append(listdetail)


            grandtotal = sum(listgrandtotal)
            print(listgrandtotal)
            print(grandtotal)
            print(detailobj)

            return render(request,'laporan/laporan_panen.html',{
            'detailobj' :detailobj,
            'grandtotal' :grandtotal,
            'mulai' : mulai_date,
            'akhir' :akhir_date,
            'jenis_panen' : jenis_panen
        })
            
    else :
        if jenis_panen == 'panen lokal' :
            
            panenlokalobj = models.panenlokal.objects.all().order_by('tanggal_panen')
            detailobjlokal = []
            listgrandtotal = []
            for item in panenlokalobj :
                listdetail = []
                listhargabeli = []
                idpanen_lokal = item.idpanen_lokal
            
                filterdetailpanen = models.detailpanenlokal.objects.filter(idpanen_lokal = idpanen_lokal)

                
                if not filterdetailpanen.exists() :
                    continue

                for i in filterdetailpanen :
                    hargapembelian = i.id_komoditas.harga_beli * i.kuantitas
                    print('harga beli' ,hargapembelian)
                    listhargabeli.append(hargapembelian)
                totalbeli = sum(listhargabeli)
                listdetail.append(item)
                listdetail.append(filterdetailpanen)
                listdetail.append(listhargabeli)
                listdetail.append(totalbeli)

                listgrandtotal.append(totalbeli)
                detailobjlokal.append(listdetail)
            grandtotallokal = sum(listgrandtotal)
            print(listgrandtotal)
            print(grandtotallokal)
            print(detailobjlokal)

            return render(request,'laporan/laporan_panen.html',{
            'detailobjlokal' :detailobjlokal,
            'grandtotallokal' :grandtotallokal,
            'jenis_panen' : jenis_panen,
   
        })
        else :
            jenis_panen = 'panen mitra'
            panenmitraobj = models.panenmitra.objects.all().order_by('tanggal_panen')
         
            detailobj = []
            listgrandtotal = []
            for item in panenmitraobj :
                
                listdetail = []
                listhargabeli = []
                idpanen_mitra = item.idpanen_mitra
                filterdetailpanen = models.detailpanenmitra.objects.filter(idpanen_mitra = idpanen_mitra)

                if not filterdetailpanen.exists() :
                    continue
                
                for i in filterdetailpanen :
                    hargapembelian = i.id_komoditas.harga_beli * i.kuantitas
                    print('harga beli' ,hargapembelian)
                    listhargabeli.append(hargapembelian)
                totalbeli = sum(listhargabeli)
                listdetail.append(item)
                listdetail.append(filterdetailpanen)
                listdetail.append(listhargabeli)
                listdetail.append(totalbeli)

                listgrandtotal.append(totalbeli)
                detailobj.append(listdetail)

            grandtotal = sum(listgrandtotal)
            print(listgrandtotal)
            print(grandtotal)
            print(detailobj)





            return render(request,'laporan/laporan_panen.html',{
                'detailobj' :detailobj,
                'grandtotal' :grandtotal,
                'jenis_panen' : jenis_panen,
     
            })
'''LAPORAN LABA RUGI'''
@login_required(login_url="login")
@role_required(["owner"]) 
def laporan_labarugi(request) :
    if len(request.GET) == 0 :
        return render(request,'laporan/laporan_labarugi.html') 
    else :
        bulan = request.GET['bulan']
        print(bulan)
        year, month = map(int, bulan.split('-'))
        bulanaja = calendar.month_name[month]
        bulan_fix = bulan_indo[bulanaja]
        print('bulan fix',bulan_fix)
        tanggal_mulai = datetime(year, month, 1)
        tanggal_akhir = datetime(year, month, calendar.monthrange(year, month)[1])
        listtotaljual = []
        listhpptemp = []
        wip_awal = {}
        wip_akhir = {}  
        fg_awal = {}
        fg_akhir = {}  

     


        detailpenjualan = models.detailpenjualan.objects.filter(id_penjualan__tanggal__range = (tanggal_mulai,tanggal_akhir))
        print("detail penjualan",detailpenjualan)

        if not detailpenjualan.exists() :
            total = 0
            listtotaljual.append(total)
            # messages.error(request, "Data Penjualan tidak ditemukan!")
            # return redirect('laporan_labarugi')
        else :
            for item in detailpenjualan:
                try:
                    # Pendapatan awal
                    kuantitask = item.kuantitas_komoditas
                    kuantitasp = item.kuantitas_produk
                    hargak = item.id_komoditas.harga_jual
                    hargap = item.id_produk.harga_produk
                    
                    # Periksa apakah salah satu nilai adalah None
                    if kuantitask is None or kuantitasp is None or hargak is None or hargap is None:
                        continue  # Lanjutkan ke iterasi berikutnya jika ada yang None
                    
                    total = kuantitask * hargak + kuantitasp * hargap
                    listtotaljual.append(total)
                
                except AttributeError as e:
                    # Log error atau lakukan tindakan lain jika perlu
                    print(f"Error processing item {item.iddetail_penjualan}: {e}")
                    continue  # Lanjutkan ke iterasi berikutnya jika ada error
        print('list total',listtotaljual)
        # HPP(produksi)
        produkobj = models.produk.objects.all()
        if not produkobj.exists() :
            messages.error(request,"Data Produk Tidak Ditemukan!")
        for i in produkobj :  
            nama_produk = i.nama_produk

            nama_komoditas = konversi_produk_to_komoditas[nama_produk][0]
            
            hargakomoditas = models.komoditas.objects.filter(nama_komoditas=nama_komoditas).filter(id_grade__nama_grade = 'olah').values('harga_beli')

            if not hargakomoditas.exists() :
                hargakomoditas = [{'harga_beli' : 0}]
            else :
                pass
            

            konversiproduk = konversi_produk_to_komoditas[nama_produk][1]
            print(konversiproduk)

            filterfgall = models.detailproduksi.objects.filter(id_produk__nama_produk=nama_produk,status_produk = 'fg')


            for a in filterfgall :
                kuantitasprod = a.kuantitas_produk
                hasilkonv = math.ceil(kuantitasprod*konversiproduk)
            
            filterwipawal = models.detailproduksi.objects.filter(id_produk__nama_produk=nama_produk).filter(status_produk = 'wip').filter(id_produksi__tanggal = tanggal_mulai)

            filterwipakhir = models.detailproduksi.objects.filter(id_produk__nama_produk=nama_produk).filter(status_produk = 'wip').filter(id_produksi__tanggal = tanggal_akhir)

            filterfgawal = models.detailproduksi.objects.filter(id_produk__nama_produk=nama_produk).filter(status_produk = 'fg').filter(id_produksi__tanggal = tanggal_mulai)

            filterfgakhir = models.detailproduksi.objects.filter(id_produk__nama_produk=nama_produk).filter(status_produk = 'fg').filter(id_produksi__tanggal = tanggal_akhir)


            # wip awal
            for b in filterwipawal:
                harga = b.kuantitas_produk * b.id_produk.harga_produk
                nama_produk = b.id_produk.nama_produk
                if nama_produk in wip_awal:
                    wip_awal[nama_produk] += harga
                else:
                    wip_awal[nama_produk] = harga

            # wip akhir
            for b in filterwipakhir:
                harga = b.kuantitas_produk * b.id_produk.harga_produk
                nama_produk = b.id_produk.nama_produk
                if nama_produk in wip_akhir:
                    wip_akhir[nama_produk] += harga
                else:
                    wip_akhir[nama_produk] = harga
        
            # fg awal
            for b in filterfgawal:
                harga = b.kuantitas_produk * b.id_produk.harga_produk
                nama_produk = b.id_produk.nama_produk
                if nama_produk in fg_awal:
                    fg_awal[nama_produk] += harga
                else:
                    fg_awal[nama_produk] = harga

            # fg akhir
            for b in filterfgakhir:
                harga = b.kuantitas_produk * b.id_produk.harga_produk
                nama_produk = b.id_produk.nama_produk
                if nama_produk in fg_akhir:
                    fg_akhir[nama_produk] += harga
                else:
                    fg_akhir[nama_produk] = harga

        

            hargawipawal = wip_awal.get(nama_produk, 0)
            hargawipakhir = wip_akhir.get(nama_produk, 0)

            print("h kom",hargakomoditas)
            hpp_temporary = (hasilkonv * hargakomoditas[0]['harga_beli']) + hargawipawal - hargawipakhir
            listhpptemp.append(hpp_temporary)

        tenagakerja_dan_overhead = models.biaya.objects.filter(
            Q(idjenisbiaya__jenis_biaya='Biaya Tenaga Kerja') | 
            Q(idjenisbiaya__jenis_biaya='Biaya Overhead'),
            tanggal__range=(tanggal_mulai, tanggal_akhir))
        if not tenagakerja_dan_overhead.exists() :
            total_biaya={'total_biaya' : 0}
        else  :
            total_biaya = tenagakerja_dan_overhead.aggregate(total_biaya=Sum('nominal_biaya'))

        print('total biaya',total_biaya)
        hpp_final = sum(listhpptemp) + total_biaya['total_biaya']

        
        listfgawal = []
        for i in fg_awal.values() :
            listfgawal.append(i)

        listfgakhir = []
        for i in fg_akhir.values() :
            listfgakhir.append(i)

        
        filterkom = models.komoditas.objects.exclude(id_grade__nama_grade = 'olah')

        
        listmitra = []
        listlokal = []
        # Harga Beli Komoditas
        for item in filterkom :
            id_kom = item
            print('id komoditas',id_kom)

            detailmitra = models.detailpanenmitra.objects.filter(id_komoditas=id_kom)
            detaillokal = models.detailpanenlokal.objects.filter(id_komoditas=id_kom)

            for a in detailmitra :
                hargakomoditas = a.kuantitas * a.id_komoditas.harga_beli
                listmitra.append(hargakomoditas)

            for b in detaillokal :
                hargakomoditas = b.kuantitas * b.id_komoditas.harga_beli
                listlokal.append(hargakomoditas)

        # HPP Penjualan
        hppembelian = hpp_final+sum(listmitra)+sum(listlokal) + sum(listfgawal) - sum(listfgakhir)

        # Pendapatan Kotor
        totalpendapatanawal = sum(listtotaljual)
        laba_kotor = totalpendapatanawal- hppembelian

        # Pajak Penghasilan
        pajak_penghasilan = (0.5/100) * laba_kotor

       
        bbu = models.biaya.objects.filter(tanggal__range=(tanggal_mulai,tanggal_akhir)).filter(idjenisbiaya__jenis_biaya ='Beban Usaha')
        print('dict',bbu)
        dictbbu = {}
        for item in bbu :
            namabiaya = item.nama_biaya
            if namabiaya in dictbbu :
                dictbbu[namabiaya] += item.nominal_biaya
            else :
                dictbbu[namabiaya] = item.nominal_biaya

    
    

        bbufix = 0
        for item in dictbbu.values():
            bbufix+=item
      
        # Pendapatan bersih
        pendapatan_bersih = laba_kotor-pajak_penghasilan-bbufix

        if pendapatan_bersih<0 :
            messages.warning(request,"Pendapatan bersih menjadi mines!")

        return render(
            request,'laporan/laporan_labarugi.html',{
                'bulan':bulan,
                'month':bulan_fix,
                'tanggal_mulai':tanggal_mulai,
                'tanggal_akhir':tanggal_akhir,
                'pendapatan_awal' :totalpendapatanawal,
                'hpproduksi' : hpp_final,
                'hppenjualan' : hppembelian,
                'laba_kotor' :laba_kotor,
                'pajak_penghasilan' : pajak_penghasilan,
                'dictbbu' : dictbbu,
                'bbufix' : bbufix,
                'pendapatan_bersih' : pendapatan_bersih
            }
        )

def laporanlabarugi_pdf(request,bulan) :
    year, month = map(int, bulan.split('-'))
    bulanaja = calendar.month_name[month]
    bulan_fix = bulan_indo[bulanaja]
    print('bulan fix',bulan_fix)
    tanggal_mulai = datetime(year, month, 1)
    tanggal_akhir = datetime(year, month, calendar.monthrange(year, month)[1])
    listtotaljual = []
    listhpptemp = []
    wip_awal = {}
    wip_akhir = {}  
    fg_awal = {}
    fg_akhir = {}  

    


    detailpenjualan = models.detailpenjualan.objects.filter(id_penjualan__tanggal__range = (tanggal_mulai,tanggal_akhir))
    print("detail penjualan",detailpenjualan)

    if not detailpenjualan.exists() :
        total = 0
        listtotaljual.append(total)
        # messages.error(request, "Data Penjualan tidak ditemukan!")
        # return redirect('laporan_labarugi')
    else :
        for item in detailpenjualan:
            try:
                # Pendapatan awal
                kuantitask = item.kuantitas_komoditas
                kuantitasp = item.kuantitas_produk
                hargak = item.id_komoditas.harga_jual
                hargap = item.id_produk.harga_produk
                
                # Periksa apakah salah satu nilai adalah None
                if kuantitask is None or kuantitasp is None or hargak is None or hargap is None:
                    continue  # Lanjutkan ke iterasi berikutnya jika ada yang None
                
                total = kuantitask * hargak + kuantitasp * hargap
                listtotaljual.append(total)
            
            except AttributeError as e:
                # Log error atau lakukan tindakan lain jika perlu
                print(f"Error processing item {item.iddetail_penjualan}: {e}")
                continue  # Lanjutkan ke iterasi berikutnya jika ada error
    print('list total',listtotaljual)
    # HPP(produksi)
    produkobj = models.produk.objects.all()
    if not produkobj.exists() :
        messages.error(request,"Data Produk Tidak Ditemukan!")
    for i in produkobj :  
        nama_produk = i.nama_produk

        nama_komoditas = konversi_produk_to_komoditas[nama_produk][0]
        
        hargakomoditas = models.komoditas.objects.filter(nama_komoditas=nama_komoditas).filter(id_grade__nama_grade = 'olah').values('harga_beli')

        if not hargakomoditas.exists() :
            hargakomoditas = [{'harga_beli' : 0}]
        else :
            pass
        

        konversiproduk = konversi_produk_to_komoditas[nama_produk][1]
        print(konversiproduk)

        filterfgall = models.detailproduksi.objects.filter(id_produk__nama_produk=nama_produk,status_produk = 'fg')


        for a in filterfgall :
            kuantitasprod = a.kuantitas_produk
            hasilkonv = math.ceil(kuantitasprod*konversiproduk)
        
        filterwipawal = models.detailproduksi.objects.filter(id_produk__nama_produk=nama_produk).filter(status_produk = 'wip').filter(id_produksi__tanggal = tanggal_mulai)

        filterwipakhir = models.detailproduksi.objects.filter(id_produk__nama_produk=nama_produk).filter(status_produk = 'wip').filter(id_produksi__tanggal = tanggal_akhir)

        filterfgawal = models.detailproduksi.objects.filter(id_produk__nama_produk=nama_produk).filter(status_produk = 'fg').filter(id_produksi__tanggal = tanggal_mulai)

        filterfgakhir = models.detailproduksi.objects.filter(id_produk__nama_produk=nama_produk).filter(status_produk = 'fg').filter(id_produksi__tanggal = tanggal_akhir)


        # wip awal
        for b in filterwipawal:
            harga = b.kuantitas_produk * b.id_produk.harga_produk
            nama_produk = b.id_produk.nama_produk
            if nama_produk in wip_awal:
                wip_awal[nama_produk] += harga
            else:
                wip_awal[nama_produk] = harga

        # wip akhir
        for b in filterwipakhir:
            harga = b.kuantitas_produk * b.id_produk.harga_produk
            nama_produk = b.id_produk.nama_produk
            if nama_produk in wip_akhir:
                wip_akhir[nama_produk] += harga
            else:
                wip_akhir[nama_produk] = harga
    
        # fg awal
        for b in filterfgawal:
            harga = b.kuantitas_produk * b.id_produk.harga_produk
            nama_produk = b.id_produk.nama_produk
            if nama_produk in fg_awal:
                fg_awal[nama_produk] += harga
            else:
                fg_awal[nama_produk] = harga

        # fg akhir
        for b in filterfgakhir:
            harga = b.kuantitas_produk * b.id_produk.harga_produk
            nama_produk = b.id_produk.nama_produk
            if nama_produk in fg_akhir:
                fg_akhir[nama_produk] += harga
            else:
                fg_akhir[nama_produk] = harga

    

        hargawipawal = wip_awal.get(nama_produk, 0)
        hargawipakhir = wip_akhir.get(nama_produk, 0)

        print("h kom",hargakomoditas)
        hpp_temporary = (hasilkonv * hargakomoditas[0]['harga_beli']) + hargawipawal - hargawipakhir
        listhpptemp.append(hpp_temporary)

    tenagakerja_dan_overhead = models.biaya.objects.filter(
        Q(idjenisbiaya__jenis_biaya='Biaya Tenaga Kerja') | 
        Q(idjenisbiaya__jenis_biaya='Biaya Overhead'),
        tanggal__range=(tanggal_mulai, tanggal_akhir))
    if not tenagakerja_dan_overhead.exists() :
        total_biaya={'total_biaya' : 0}
    else  :
        total_biaya = tenagakerja_dan_overhead.aggregate(total_biaya=Sum('nominal_biaya'))

    print('total biaya',total_biaya)
    hpp_final = sum(listhpptemp) + total_biaya['total_biaya']

    
    listfgawal = []
    for i in fg_awal.values() :
        listfgawal.append(i)

    listfgakhir = []
    for i in fg_akhir.values() :
        listfgakhir.append(i)

    
    filterkom = models.komoditas.objects.exclude(id_grade__nama_grade = 'olah')

    
    listmitra = []
    listlokal = []
    # Harga Beli Komoditas
    for item in filterkom :
        id_kom = item
        print('id komoditas',id_kom)

        detailmitra = models.detailpanenmitra.objects.filter(id_komoditas=id_kom)
        detaillokal = models.detailpanenlokal.objects.filter(id_komoditas=id_kom)

        for a in detailmitra :
            hargakomoditas = a.kuantitas * a.id_komoditas.harga_beli
            listmitra.append(hargakomoditas)

        for b in detaillokal :
            hargakomoditas = b.kuantitas * b.id_komoditas.harga_beli
            listlokal.append(hargakomoditas)

    # HPP Penjualan
    hppembelian = hpp_final+sum(listmitra)+sum(listlokal) + sum(listfgawal) - sum(listfgakhir)

    # Pendapatan Kotor
    totalpendapatanawal = sum(listtotaljual)
    laba_kotor = totalpendapatanawal- hppembelian

    # Pajak Penghasilan
    pajak_penghasilan = (0.5/100) * laba_kotor

    
    bbu = models.biaya.objects.filter(tanggal__range=(tanggal_mulai,tanggal_akhir)).filter(idjenisbiaya__jenis_biaya ='Beban Usaha')
    print('dict',bbu)
    dictbbu = {}
    for item in bbu :
        namabiaya = item.nama_biaya
        if namabiaya in dictbbu :
            dictbbu[namabiaya] += item.nominal_biaya
        else :
            dictbbu[namabiaya] = item.nominal_biaya




    bbufix = 0
    for item in dictbbu.values():
        bbufix+=item
    
    # Pendapatan bersih
    pendapatan_bersih = laba_kotor-pajak_penghasilan-bbufix

    response = HttpResponse(content_type='application/pdf;')
    response['Content-Disposition'] = 'inline; filename=laporan laba rugi.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    html_string = render_to_string(
        'laporan/laporanlabarugipdf.html',{
            'month':bulan_fix,
            'pendapatan_awal' :totalpendapatanawal,
            'hpproduksi' : hpp_final,
            'hppenjualan' : hppembelian,
            'laba_kotor' :laba_kotor,
            'pajak_penghasilan' : pajak_penghasilan,
            'dictbbu' : dictbbu,
            'bbufix' : bbufix,
            'pendapatan_bersih' : pendapatan_bersih
            })
    
    html = HTML(string=html_string)
    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        output.seek(0)
        response.write(output.read())
    
    render(request, 'laporan/laporanlabarugipdf.html')
    
    return response

@login_required(login_url="login")
@role_required(["owner"])
def rekap_panen_bulanan(request):
    hari_ini = now().date()
    bulan_ini_awal = hari_ini.replace(day=1)

    if hari_ini.month == 12:
        bulan_depan_awal = hari_ini.replace(year=hari_ini.year + 1, month=1, day=1)
    else:
        bulan_depan_awal = hari_ini.replace(month=hari_ini.month + 1, day=1)

    semua_mitra = models.mitra.objects.all()

    for mitra in semua_mitra:
        panen_bulanan = models.panenmitra.objects.filter(
            id_mitra=mitra,
            tanggal_panen__gte=bulan_ini_awal,
            tanggal_panen__lt=bulan_depan_awal
        )

        detail_data = []
        total_kuantitas_semua = 0

        for panen in panen_bulanan:
            detail_items = models.detailpanenmitra.objects.filter(idpanen_mitra=panen).select_related("id_komoditas")
            for detail in detail_items:
                detail_data.append({
                    'tanggal_panen': panen.tanggal_panen,
                    'nama_komoditas': detail.id_komoditas.nama_komoditas,
                    'kuantitas': detail.kuantitas,
                })
                total_kuantitas_semua += detail.kuantitas

        if total_kuantitas_semua < mitra.minimal_kuantitas:
            subject = f"Laporan Panen Bulanan - {mitra.nama_mitra}"
            html_message = render_to_string("email_laporan.html", {
                'nama_mitra': mitra.nama_mitra,
                'detail': detail_data,
                'total': total_kuantitas_semua,
                'kuantitas_minimal': mitra.minimal_kuantitas,
            })

            email = EmailMessage(subject, html_message, settings.EMAIL_HOST_USER, [mitra.email])
            email.content_subtype = "html"
            email.send()

    return render(request, '404.html')  

def total_komoditas(request):
    if request.method == "GET":
        panen_mitra = models.panenmitra.objects.all()
        panen_lokal = models.panenlokal.objects.all()

        hasil = {}
        komoditas_set = set()
        batch_set = set()
        tanggalpanen_set = set()
        tanggalkadaluarsa_set = set()

        def proses_panen(panen_list, dari_mitra=True):
            for panen in panen_list:
                details = (
                    models.detailpanenmitra.objects.filter(idpanen_mitra=panen)
                    if dari_mitra else
                    models.detailpanenlokal.objects.filter(idpanen_lokal=panen)
                )

                for detail in details:
                    komoditas_obj = detail.id_komoditas 
                    komoditas_str = str(komoditas_obj)   
                    batch = detail.batch
                    tanggalpanen = (
                        detail.idpanen_mitra.tanggal_panen
                        if dari_mitra else
                        detail.idpanen_lokal.tanggal_panen
                    )
                    tanggalkadaluarsa = detail.tanggal_kadaluwarsa
                    kuantitas = detail.kuantitas

                    key = (komoditas_str, batch, tanggalpanen, tanggalkadaluarsa)

                    if key not in hasil:
                        data_qr = generate_qr_data(komoditas_str, tanggalkadaluarsa, kuantitas)
                        qr_img = generate_qr_image(data_qr)
                        hasil[key] = {"total": kuantitas, "qr": qr_img}
                    else:
                        hasil[key]["total"] += kuantitas

                    komoditas_set.add(komoditas_str)
                    batch_set.add(batch)
                    tanggalpanen_set.add(tanggalpanen)
                    tanggalkadaluarsa_set.add(tanggalkadaluarsa)

        proses_panen(panen_mitra, dari_mitra=True)
        proses_panen(panen_lokal, dari_mitra=False)

        result = [
            {
                "komoditas": komoditas,
                "batch": batch,
                "tanggal_panen": tanggalpanen.strftime("%Y-%m-%d"),
                "tanggal_kadaluwarsa": tanggalkadaluarsa.strftime("%Y-%m-%d"),
                "total_kuantitas": data["total"],
                "qr": data["qr"]
            }
            for (komoditas, batch, tanggalpanen, tanggalkadaluarsa), data in hasil.items()
        ]

        return render(request, "total_komoditas.html", {
            "list_total": result,
            "komoditas_list": sorted(komoditas_set),
            "batch_list": sorted(batch_set),
            "tanggal_panen_list": sorted(tanggalpanen_set),
            "tanggal_list": sorted(tanggalkadaluarsa_set)
        })

def generate_qr_image(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def generate_qr_data(komoditas_str, kadaluarsa, kuantitas):
    return f"{komoditas_str}|{kadaluarsa}|{kuantitas}"


def qr_already_generated(id_komoditas, kadaluarsa):
    return (
        models.detailpanenlokal.objects.filter(
            id_komoditas_id=id_komoditas,
            tanggal_kadaluwarsa=kadaluarsa
        ).exists()
        or models.detailpanenmitra.objects.filter(
            id_komoditas_id=id_komoditas,
            tanggal_kadaluwarsa=kadaluarsa
        ).exists()
    )

def log_aktivitas(request):
    logs = models.ActivityLog.objects.all().order_by('-timestamp')  # Urutkan terbaru dulu
    return render(request, 'log/activity_log.html', {'logs': logs})
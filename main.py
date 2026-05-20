#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#PROJE: Kütüphane Yönetim Sistemi
#KULLANILAN TEKNOLOJİLER: Python, SQLite3, CustomTkinter, Threading


import os
import sys
import sqlite3
import threading  #Arayüz donmasın diye arka planda işlem yapmak için
from datetime import datetime, timedelta
from tkinter import messagebox, filedialog

#KÜTÜPHANE KONTROLÜ 
#Program çalışırken hata verip kapanmasın diye
try:
    import requests  # İnternetten kapak resmi indirmek için
    import customtkinter as ctk  # Modern arayüz için
    from PIL import Image, ImageTk  # Resim işlemek için
except ImportError as e:
    sys.exit(f"Eksik kütüphane: {e}\nLütfen: pip install customtkinter pillow requests")

# AYARLAR 
APP_NAME = "Kütüphane Yönetim Sistemi"
DB_FILE = "kutuphane.db"
TARIH_FORMATI = "%d.%m.%Y"

RENKLER = {
    "bg": "#0F172A",        "sidebar": "#1E293B",   "kart": "#334155",
    "kart_hover": "#475569","ana": "#6366F1",       "ana_hover": "#4F46E5", 
    "yesil": "#10B981",     "kirmizi": "#EF4444",   "turuncu": "#F59E0B",   
    "mor": "#8B5CF6",       "yazi": "#F8FAFC",      "gri": "#94A3B8",       
    "aktif_cizgi": "#38BDF8","sari": "#FACC15"       
}

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


# VERİTABANI BACKEND
# Veri işleri / SQL sorgusu çalıştırır
class VeritabaniYoneticisi:
    def __init__(self):
        self.db_name = DB_FILE
        self.klasor_profil = "profil_resimleri"
        self.klasor_kapak = "kitap_kapaklari"
        self._klasorleri_hazirla() # Resimlerin kaydedileceği klasörleri oluşturur
        self._tablolari_kur()      # Veritabanı tabloları yoksa oluşturur

    def _klasorleri_hazirla(self):
        # os.path.exists:klasör var mı diye bakar, yoksa oluşturur
        if not os.path.exists(self.klasor_profil): os.makedirs(self.klasor_profil)
        if not os.path.exists(self.klasor_kapak): os.makedirs(self.klasor_kapak)

    def _baglanti_ac(self):
        # SQLite dosyasına bağlandı
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def _tablolari_kur(self):
        conn = self._baglanti_ac()
        cursor = conn.cursor()
        
        # IF NOT EXISTS ile hata alma engellendi
        cursor.execute("CREATE TABLE IF NOT EXISTS kullanicilar (id INTEGER PRIMARY KEY AUTOINCREMENT, kadi TEXT UNIQUE, sifre TEXT, rol TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS kitaplar (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, yazar TEXT, tur TEXT, durum TEXT, sahibi TEXT, teslim_tarihi TEXT, resim_yolu TEXT)")
        # FOREIGN KEY:kitap_id
        cursor.execute("CREATE TABLE IF NOT EXISTS yorumlar (id INTEGER PRIMARY KEY AUTOINCREMENT, kitap_id INTEGER, kadi TEXT, puan INTEGER, yorum TEXT, tarih TEXT, FOREIGN KEY(kitap_id) REFERENCES kitaplar(id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS gecmis_islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, kadi TEXT, kitap_ad TEXT, yazar TEXT, iade_tarihi TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS rezervasyonlar (id INTEGER PRIMARY KEY AUTOINCREMENT, kitap_id INTEGER, kadi TEXT, tarih TEXT, FOREIGN KEY(kitap_id) REFERENCES kitaplar(id))")
        
        # Varsayılan admin hesabı oluşturma
        cursor.execute("SELECT * FROM kullanicilar WHERE kadi = 'admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO kullanicilar (kadi, sifre, rol) VALUES (?, ?, ?)", ('admin', '1234', 'yonetici'))
            
        conn.commit(); conn.close()

    # GENEL SORGU FONKSİYONU
    # Her işlem için ayrı bağlantı aç-kapat yapmamak için bu fonksiyonu yazdık.
    # params: SQL injection saldırılarını önlemek için parametreleri ayrı yollarız.
    def sorgu_calistir(self, sql, params=(), commit=False):
        try:
            conn = self._baglanti_ac(); cursor = conn.cursor()
            cursor.execute(sql, params)
            if commit: 
                conn.commit()             # Veri ekleme silme güncelleme ise kaydeder
                sonuc = cursor.lastrowid  
            else: 
                sonuc = cursor.fetchall() # Veri sadece okunuyor ise döndürür
            conn.close()
            return sonuc
        except sqlite3.Error as e: 
            print(f"DB Hata: {e}")
            return None

    # GOOGLE BOOKS API ENTEGRASYONU
    def google_kapak_indir(self, kitap_adi, yazar):
        try:
            url = "https://www.googleapis.com/books/v1/volumes"
            params = {'q': f"{kitap_adi} {yazar}", 'maxResults': 1}
            # requests.get ile istek atılıyor
            res = requests.get(url, params=params, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            
            if res.status_code == 200:
                data = res.json() # Gelen cevabı JSON formatına çevir
                if "items" in data:
                    img_url = data['items'][0]['volumeInfo']['imageLinks']['thumbnail']
                    img_data = requests.get(img_url).content # Resmin binary verisini indir
                    path = os.path.join(self.klasor_kapak, f"{datetime.now().timestamp()}.jpg")
                    with open(path, 'wb') as f: f.write(img_data) # Dosyayı diske kaydet
                    return path
        except Exception as e:
            print(f"Kapak indirme hatası: {e}")
        return None


# ARAYÜZ FRONTEND
# CustomTkinter
class KutuphaneUygulamasi(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1280x850")
        self.configure(fg_color=RENKLER["bg"])
        self.db = VeritabaniYoneticisi() # Backend sınıfını burada başlatır
        self.aktif_kullanici = None      # Giriş yapan kullanıcıyı tutar
        self.aktif_sayfa_id = None 
        self.kitap_turleri = ["Genel", "Roman", "Bilim", "Tarih", "Eğitim", "Dergi", "Çizgi Roman", "Sanat", "Teknoloji"]
        self.sayfa_giris() # İlk açılışta giriş ekranını çağırır

    # YARDIMCI METOTLAR 
    def widget_temizle(self):
        # Sayfa değiştirirken eski yazılar silinir
        for widget in self.winfo_children(): widget.destroy()

    def resim_getir(self, yol, boyut=(100, 150)):
        # Resmi bulur boyutlandırır ve CTkImage objesine çevirir
        if yol and os.path.exists(yol):
            try: return ctk.CTkImage(Image.open(yol), size=boyut)
            except: pass
        return None

    def yukleniyor_baslat(self):
        # İmleci kum saati şekline çevirir
        self.configure(cursor="watch"); self.update()

    def yukleniyor_bitir(self):
        self.configure(cursor=""); self.update()

    def pencere_on_plan(self, pencere):
        # Açılan pencerelerin ana ekranın altında kalmasını engeller
        pencere.transient(self) 
        pencere.grab_set() 
        pencere.lift()
        pencere.attributes('-topmost', True)

    def ortalama_puan_hesapla(self, kid, sembollu=True):
        # Bir kitabın yorum tablosundaki puanlarının ortalamasını alır.
        rows = self.db.sorgu_calistir("SELECT puan FROM yorumlar WHERE kitap_id=?", (kid,))
        if not rows: return "Yeni" if sembollu else 0
        # List comprehension kullanarak pratik toplama işlemi
        puan = sum(r['puan'] for r in rows)/len(rows)
        return f"⭐ {puan:.1f}" if sembollu else puan

    def ui_buton_olustur(self, master, text, command, renk="ana", genislik=120, yukseklik=35):
        c = RENKLER.get(renk, RENKLER["ana"])
        return ctk.CTkButton(master, text=text, command=command, fg_color=c, hover_color=RENKLER.get("ana_hover"), 
                             width=genislik, height=yukseklik, corner_radius=8, font=("Segoe UI", 12, "bold"))

    def ui_input_olustur(self, master, ph, show=None):
        entry = ctk.CTkEntry(master, placeholder_text=ph, height=40, corner_radius=8, 
                            border_color=RENKLER["ana"], fg_color=RENKLER["sidebar"], font=("Segoe UI", 13))
        if show: entry.configure(show=show)
        return entry

    # SAYFA FONKSİYONLARI
    # Not: Her sayfa fonksiyonu önce widget_temizle() çağırır, sonra kendi elemanlarını çizer.
    
    def sayfa_giris(self):
        self.widget_temizle()
        # Grid sistemi ile ekranı bölüyoruz.
        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=0)
        
        fr = ctk.CTkFrame(self, fg_color=RENKLER["sidebar"], corner_radius=20, border_width=1, border_color=RENKLER["kart"], width=400, height=500)
        fr.place(relx=0.5, rely=0.5, anchor="center") # Ekranın tam ortasına yerleştir
        fr.pack_propagate(False) # Çerçevenin içindekilere göre küçülmesini engelle

        ctk.CTkLabel(fr, text="Hoş Geldiniz", font=("Segoe UI", 32, "bold"), text_color=RENKLER["yazi"]).pack(pady=(60, 10))
        self.giris_kadi = self.ui_input_olustur(fr, "Kullanıcı Adı"); self.giris_kadi.pack(pady=10, padx=40, fill="x")
        self.giris_sifre = self.ui_input_olustur(fr, "Şifre", show="*"); self.giris_sifre.pack(pady=10, padx=40, fill="x")
        
        # Enter tuşuna basınca giriş yapmasını sağla
        self.bind('<Return>', lambda e: self.giris_kontrol())
        self.ui_buton_olustur(fr, "GİRİŞ YAP", self.giris_kontrol, "ana", 250, 45).pack(pady=20)
        ctk.CTkButton(fr, text="Hesap Oluştur", fg_color="transparent", text_color=RENKLER["ana"], hover=False, command=self.sayfa_kayit).pack()

    def sayfa_kayit(self):
        # Kayıt ekranı
        self.widget_temizle()
        fr = ctk.CTkFrame(self, fg_color=RENKLER["sidebar"], corner_radius=20, width=400, height=550)
        fr.place(relx=0.5, rely=0.5, anchor="center")
        fr.pack_propagate(False)

        ctk.CTkLabel(fr, text="Yeni Üyelik", font=("Segoe UI", 32, "bold")).pack(pady=(50, 30))
        u = self.ui_input_olustur(fr, "Kullanıcı Adı"); u.pack(pady=10, padx=40, fill="x")
        p = self.ui_input_olustur(fr, "Şifre", show="*"); p.pack(pady=10, padx=40, fill="x")
        
        v_rol = ctk.StringVar(value="ogrenci")
        rf = ctk.CTkFrame(fr, fg_color="transparent"); rf.pack(pady=15)
        ctk.CTkRadioButton(rf, text="Öğrenci", variable=v_rol, value="ogrenci", fg_color=RENKLER["ana"]).pack(side="left", padx=10)
        ctk.CTkRadioButton(rf, text="Yönetici", variable=v_rol, value="yonetici", fg_color=RENKLER["ana"]).pack(side="left", padx=10)

        def kaydet():
            self.yukleniyor_baslat()
            try:
                self.db.sorgu_calistir("INSERT INTO kullanicilar (kadi, sifre, rol) VALUES (?,?,?)", (u.get(), p.get(), v_rol.get()), True)
                messagebox.showinfo("Başarılı", "Kayıt oldunuz."); self.sayfa_giris()
            except: messagebox.showerror("Hata", "Kullanıcı adı dolu.")
            self.yukleniyor_bitir()
        
        self.ui_buton_olustur(fr, "KAYDOL", kaydet, "yesil", 250, 45).pack(pady=20)
        ctk.CTkButton(fr, text="Geri Dön", fg_color="transparent", text_color=RENKLER["gri"], hover=False, command=self.sayfa_giris).pack()

    def giris_kontrol(self):
        # Giriş doğrulama
        self.yukleniyor_baslat()
        res = self.db.sorgu_calistir("SELECT * FROM kullanicilar WHERE kadi=? AND sifre=?", (self.giris_kadi.get(), self.giris_sifre.get()))
        self.yukleniyor_bitir()
        
        if res:
            self.aktif_kullanici = dict(res[0])
            self.unbind('<Return>') # Enter tuşu bağını kaldır
            self.grid_columnconfigure(0, weight=0); self.grid_columnconfigure(1, weight=1)
            # Role göre yönlendirme
            if self.aktif_kullanici['rol'] == 'yonetici': self.sayfa_yonetici()
            else: self.sayfa_ogrenci("katalog")
        else: messagebox.showerror("Hata", "Yanlış bilgiler.")

    #  YAN MENÜ
    def sidebar_olustur(self, butonlar):
        # Dinamik Sidebar
        self.widget_temizle()
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)

        sb = ctk.CTkFrame(self, fg_color=RENKLER["sidebar"], width=260, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_rowconfigure(10, weight=1)

        # Profil Resmi Alanı
        yol = f"{self.db.klasor_profil}/{self.aktif_kullanici['kadi']}.png"
        img = self.resim_getir(yol, (70, 70))
        pf = ctk.CTkFrame(sb, fg_color="transparent"); pf.pack(pady=(40, 20))
        ctk.CTkLabel(pf, text="", image=img if img else None).pack()
        if not img: ctk.CTkLabel(pf, text="👤", font=("Arial", 50), text_color=RENKLER["ana"]).pack()
        ctk.CTkLabel(pf, text=self.aktif_kullanici['kadi'], font=("Segoe UI", 18, "bold")).pack(pady=(10, 0))
        ctk.CTkLabel(pf, text=self.aktif_kullanici['rol'].capitalize(), font=("Segoe UI", 12), text_color=RENKLER["gri"]).pack()

        # Menü Butonlarını Döngüyle Oluşturma
        for key, txt, cmd in butonlar:
            isActive = (self.aktif_sayfa_id == key)
            btn_color = RENKLER["kart"] if isActive else "transparent"
            text_color = RENKLER["ana"] if isActive else RENKLER["gri"]
            
            btn_fr = ctk.CTkFrame(sb, fg_color=btn_color, corner_radius=8, height=50)
            btn_fr.pack(fill="x", padx=15, pady=5)
            btn_fr.pack_propagate(False)
            
            if isActive: # Aktif sekme için sol tarafa çizgi koy
                ctk.CTkFrame(btn_fr, fg_color=RENKLER["aktif_cizgi"], width=4, height=30).pack(side="left", padx=(10, 5), pady=10)
            
            ctk.CTkButton(btn_fr, text=txt, command=cmd, fg_color="transparent", hover=False, 
                          text_color=text_color, font=("Segoe UI", 14, "bold" if isActive else "normal"), anchor="w").pack(side="left", fill="both", expand=True, padx=10)

        self.ui_buton_olustur(sb, "Profil Ayarları", self.popup_profil, "kart", 200).pack(pady=10)
        self.ui_buton_olustur(sb, "Çıkış Yap", self.sayfa_giris, "kirmizi", 200).pack(side="bottom", pady=40)

        # Ana içerik alanı
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    # ÖĞRENCİ PANELİ 
    def sayfa_ogrenci(self, sayfa):
        self.aktif_sayfa_id = sayfa
        menu = [
            ("katalog", "📚  Kütüphane Kataloğu", lambda: self.sayfa_ogrenci("katalog")),
            ("elimdekiler", "🎒  Elimdekiler", lambda: self.sayfa_ogrenci("elimdekiler")),
            ("gecmis", "🕒  Geçmiş İşlemler", lambda: self.sayfa_ogrenci("gecmis"))
        ]
        self.sidebar_olustur(menu)
        
        basliklar = {"katalog": "Kitap Kataloğu", "elimdekiler": "Okuduğum Kitaplar", "gecmis": "Okuma Geçmişim"}
        ctk.CTkLabel(self.main_area, text=basliklar[sayfa], font=("Segoe UI", 28, "bold"), text_color=RENKLER["yazi"]).pack(anchor="w", pady=(0, 20))

        # Arama ve Filtreleme Alanı
        if sayfa == "katalog":
            top = ctk.CTkFrame(self.main_area, fg_color="transparent"); top.pack(fill="x", pady=10)
            self.cb = ctk.CTkComboBox(top, values=["Tümü"]+self.kitap_turleri, width=150, command=lambda e: self.yenile_ogrenci_liste(sayfa))
            self.cb.set("Tümü"); self.cb.pack(side="left")
            self.ea = self.ui_input_olustur(top, "Kitap veya Yazar Ara..."); self.ea.pack(side="left", padx=10, fill="x", expand=True)
            self.ea.bind("<KeyRelease>", lambda e: self.yenile_ogrenci_liste(sayfa)) # Her tuşa basışta filtreler
        
        self.scroll = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self.yenile_ogrenci_liste(sayfa)

    def yenile_ogrenci_liste(self, sayfa):
        for w in self.scroll.winfo_children(): w.destroy()
        ben = self.aktif_kullanici['kadi']
        
        # KATALOG LİSTELEME
        if sayfa == "katalog":
            ara = self.ea.get(); tur = self.cb.get()
            sql = "SELECT * FROM kitaplar WHERE (ad LIKE ? OR yazar LIKE ?)"; p = [f"%{ara}%", f"%{ara}%"]
            if tur != "Tümü": sql += " AND tur=?"; p.append(tur)
            data = self.db.sorgu_calistir(sql, tuple(p))
            
            for i, k in enumerate(data):
                # Durum kontrolü: rafta başkasında rezerve
                durum_txt = "Mevcut"; durum_renk = "yesil"
                
                if k['durum'] == "Rafta": pass
                elif k['durum'] == "Rezerve":
                    durum_txt = f"{k['sahibi']} adına Rezerve"; durum_renk = "mor"
                    if k['sahibi'] == ben: durum_txt = "Senin İçin Rezerve"
                else:
                    durum_txt = f"{k['sahibi']} okuyor"; durum_renk = "kirmizi"
                    if k['sahibi'] == ben: durum_txt, durum_renk = "Sende", "turuncu"
                
                rez_sayisi = 0
                rows = self.db.sorgu_calistir("SELECT COUNT(*) as sayi FROM rezervasyonlar WHERE kitap_id=?", (k['id'],))
                if rows: rez_sayisi = rows[0]['sayi']

                # Buton fonksiyonları
                def b_fn(f, kit=k, d_renk=durum_renk):
                    self.ui_buton_olustur(f, "İncele & Yorumla", lambda: self.popup_yorum(kit), "kart", 100, 30).pack(fill="x", pady=2)
                    
                    if kit['durum'] == "Rafta":
                        self.ui_buton_olustur(f, "Ödünç Al", lambda: self.islem(kit['id'], "al"), "yesil", 100, 30).pack(fill="x", pady=2)
                    elif kit['sahibi'] != ben:
                         # Rezervasyon mantığı
                         zaten_sirada = self.db.sorgu_calistir("SELECT id FROM rezervasyonlar WHERE kitap_id=? AND kadi=?", (kit['id'], ben))
                         btn_text = f"Sıraya Gir ({rez_sayisi})"
                         state = "normal"; renk = "mor"
                         
                         if zaten_sirada: 
                             btn_text = "Sıradasın ✅"; state = "disabled"; renk = "gri"
                         
                         if state == "normal":
                            self.ui_buton_olustur(f, btn_text, lambda: self.rezervasyon_yap(kit['id']), renk, 100, 30).pack(fill="x", pady=2)
                         else:
                            ctk.CTkLabel(f, text=btn_text, text_color=RENKLER["yesil"], font=("Bold", 12)).pack(pady=5)
                
                self.kart_ciz_grid(self.scroll, k, i, durum_txt, durum_renk, b_fn)

        # ELİMDEKİLER LİSTELEME
        elif sayfa == "elimdekiler":
            data = self.db.sorgu_calistir("SELECT * FROM kitaplar WHERE sahibi=?", (ben,))
            if not data: ctk.CTkLabel(self.scroll, text="Kitap yok.", font=("Arial", 16)).pack(pady=20)
            for i, k in enumerate(data):
                fark = 0; msg = ""; clr = "turuncu"

                if k['durum'] == "Rezerve":
                    msg = "TESLİM ALINMAYI BEKLİYOR"; clr = "mor"
                else:
                    if k['teslim_tarihi']:
                        try: fark = (datetime.strptime(k['teslim_tarihi'], TARIH_FORMATI) - datetime.now()).days
                        except: fark = 0
                    msg = f"{fark} Gün Kaldı" if fark >= 0 else "SÜRESİ DOLDU"; clr = "turuncu" if fark >= 0 else "kirmizi"
                
                def b_fn(f, kit=k):
                    if kit['durum'] == "Rezerve":
                         self.ui_buton_olustur(f, "Teslim Al", lambda: self.islem(kit['id'], "onayla"), "yesil", 100, 30).pack(fill="x", pady=2)
                    else:
                        self.ui_buton_olustur(f, "İade Et", lambda: self.islem(kit['id'], "ver"), "kirmizi", 100, 30).pack(fill="x", pady=2)
                    self.ui_buton_olustur(f, "İncele & Yorumla", lambda: self.popup_yorum(kit), "kart", 100, 30).pack(fill="x", pady=2)
                
                self.kart_ciz_grid(self.scroll, k, i, msg, clr, b_fn)

        # GEÇMİŞ İŞLEMLER
        elif sayfa == "gecmis":
            data = self.db.sorgu_calistir("SELECT * FROM gecmis_islemler WHERE kadi=? ORDER BY id DESC", (ben,))
            if not data: ctk.CTkLabel(self.scroll, text="Geçmiş yok.", font=("Arial", 16)).pack(pady=20)
            for g in data:
                fr = ctk.CTkFrame(self.scroll, fg_color=RENKLER["kart"], corner_radius=10); fr.pack(fill="x", pady=5, padx=5)
                ctk.CTkLabel(fr, text=f"📘 {g['kitap_ad']}", font=("Bold", 14)).pack(side="left", padx=15, pady=10)
                ctk.CTkLabel(fr, text=g['yazar'], text_color="gray").pack(side="left")
                ctk.CTkLabel(fr, text=f"İade: {g['iade_tarihi']}", text_color=RENKLER["yesil"]).pack(side="right", padx=15)

    def rezervasyon_yap(self, kid):
        self.yukleniyor_baslat()
        try:
            self.db.sorgu_calistir("INSERT INTO rezervasyonlar (kitap_id, kadi, tarih) VALUES (?,?,?)", 
                                   (kid, self.aktif_kullanici['kadi'], datetime.now().strftime(TARIH_FORMATI)), True)
            messagebox.showinfo("Başarılı", "Sıraya girdiniz! Kitap iade edildiğinde sizin için rezerve edilecek.")
            self.sayfa_ogrenci("katalog")
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem başarısız: {e}")
        self.yukleniyor_bitir()

    #  KİTAP İŞLEMLERİ ödünç iade onay
    def islem(self, kid, tip):
        self.yukleniyor_baslat()
        if tip == "al": # Normal Ödünç Alma
            tarih = (datetime.now() + timedelta(days=15)).strftime(TARIH_FORMATI)
            self.db.sorgu_calistir("UPDATE kitaplar SET durum='Odunc', sahibi=?, teslim_tarihi=? WHERE id=?", (self.aktif_kullanici['kadi'], tarih, kid), True)
            messagebox.showinfo("Başarılı", "Kitap kütüphanene eklendi!")
            self.sayfa_ogrenci("katalog")
        
        elif tip == "onayla": # Rezerve kitabı teslim alma
            tarih = (datetime.now() + timedelta(days=15)).strftime(TARIH_FORMATI)
            self.db.sorgu_calistir("UPDATE kitaplar SET durum='Odunc', teslim_tarihi=? WHERE id=?", (tarih, kid), True)
            messagebox.showinfo("Başarılı", "Kitabı teslim aldınız. İyi okumalar!")
            self.sayfa_ogrenci("elimdekiler")

        else: # İade etme
            k = self.db.sorgu_calistir("SELECT * FROM kitaplar WHERE id=?", (kid,))[0]
            
            # Geçmişe yaz
            self.db.sorgu_calistir("INSERT INTO gecmis_islemler (kadi, kitap_ad, yazar, iade_tarihi) VALUES (?,?,?,?)", 
                          (self.aktif_kullanici['kadi'], k['ad'], k['yazar'], datetime.now().strftime(TARIH_FORMATI)), True)
            
            # Rezervasyon kontrolü
            siradaki = self.db.sorgu_calistir("SELECT * FROM rezervasyonlar WHERE kitap_id=? ORDER BY id ASC LIMIT 1", (kid,))
            
            if siradaki:
                siradaki_kisi = siradaki[0]
                # Kitabı sıradaki kişiye rezerve et
                self.db.sorgu_calistir("UPDATE kitaplar SET durum='Rezerve', sahibi=?, teslim_tarihi=NULL WHERE id=?", (siradaki_kisi['kadi'], kid), True)
                # Kişiyi sıradan sil
                self.db.sorgu_calistir("DELETE FROM rezervasyonlar WHERE id=?", (siradaki_kisi['id'],), True)
                messagebox.showinfo("Bilgi", f"Kitap iade edildi ve sıradaki kullanıcı ({siradaki_kisi['kadi']}) için rezerve edildi.")
            else:
                # Kimse yoksa rafa kaldır
                self.db.sorgu_calistir("UPDATE kitaplar SET durum='Rafta', sahibi=NULL, teslim_tarihi=NULL WHERE id=?", (kid,), True)
                messagebox.showinfo("Başarılı", "Kitap iade edildi ve rafa kaldırıldı.")
            
            self.sayfa_ogrenci("elimdekiler")
            
        self.yukleniyor_bitir()

    # YÖNETİCİ PANELİ 
    def sayfa_yonetici(self):
        self.aktif_sayfa_id = "yonetim"
        self.sidebar_olustur([("yonetim", "🛠  Kitap Yönetimi", self.sayfa_yonetici)])
        
        ctk.CTkLabel(self.main_area, text="Yönetim Paneli", font=("Segoe UI", 28, "bold")).pack(anchor="w", pady=(0, 20))
        
        add = ctk.CTkFrame(self.main_area, fg_color=RENKLER["kart"]); add.pack(fill="x", pady=10)
        e1 = self.ui_input_olustur(add, "Kitap Adı"); e1.pack(side="left", padx=10, expand=True, fill="x")
        e2 = self.ui_input_olustur(add, "Yazar"); e2.pack(side="left", padx=10, expand=True, fill="x")
        
        cb_tur = ctk.CTkComboBox(add, values=self.kitap_turleri, width=150)
        cb_tur.set("Genel")
        cb_tur.pack(side="left", padx=10)

        # MULTI THREADING
        # Kitap eklerken internetten resim indiriliyor
        # Eğer Thread kullanılmadığında resim inene kadar program donuyor
        def ekle_thread():
            ad, yazar, tur = e1.get(), e2.get(), cb_tur.get()
            if not ad or not yazar: return
            self.btn_ekle.configure(text="İşleniyor...", state="disabled")
            
            # Arka planda indirme
            def islem_yap():
                path = self.db.google_kapak_indir(ad, yazar)
                # GUI güncellemesi ana thread'de olmalı
                self.after(0, lambda: veri_kaydet(path))

            # Veritabanına kaydetme
            def veri_kaydet(path):
                self.db.sorgu_calistir("INSERT INTO kitaplar (ad,yazar,tur,durum,resim_yolu) VALUES (?,?,?,'Rafta',?)", (ad, yazar, tur, path), True)
                e1.delete(0,'end'); e2.delete(0,'end')
                self.yonetici_yenile()
                self.btn_ekle.configure(text="+ Ekle", state="normal")
            
            # Threadı başlatıyor
            threading.Thread(target=islem_yap, daemon=True).start()

        self.btn_ekle = self.ui_buton_olustur(add, "+ Ekle", ekle_thread, "yesil", 80); self.btn_ekle.pack(side="left", padx=10, pady=10)
        self.scroll = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent"); self.scroll.pack(fill="both", expand=True)
        self.yonetici_yenile()

    def yonetici_yenile(self):
        for w in self.scroll.winfo_children(): w.destroy()
        data = self.db.sorgu_calistir("SELECT * FROM kitaplar")
        for i, k in enumerate(data):
            def b_fn(f, kit=k):
                self.ui_buton_olustur(f, "Sil", lambda: self.yonetici_sil(kit['id']), "kirmizi", 100, 30).pack(fill="x", pady=2)
                self.ui_buton_olustur(f, "Düzenle", lambda: self.popup_duzenle(kit), "turuncu", 100, 30).pack(fill="x", pady=2)
            self.kart_ciz_grid(self.scroll, k, i, k['durum'], "gri", b_fn)

    def yonetici_sil(self, kid):
        if messagebox.askyesno("Sil", "Silinsin mi?"):
            self.db.sorgu_calistir("DELETE FROM kitaplar WHERE id=?", (kid,), True)
            self.db.sorgu_calistir("DELETE FROM yorumlar WHERE kitap_id=?", (kid,), True)
            self.db.sorgu_calistir("DELETE FROM rezervasyonlar WHERE kitap_id=?", (kid,), True)
            self.yonetici_yenile()

    #  KART TASARIMI
    def kart_ciz_grid(self, master, k, index, durum_txt, renk, btn_fn):
       
        row = index // 3; col = index % 3
        
        card = ctk.CTkFrame(master, fg_color=RENKLER["kart"], corner_radius=15, border_width=0)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        master.grid_columnconfigure((0,1,2), weight=1)

        # Mouse üzerine gelince renk değiştirme
        def enter(e): card.configure(fg_color=RENKLER["kart_hover"], border_width=1, border_color=RENKLER["ana"])
        def leave(e): card.configure(fg_color=RENKLER["kart"], border_width=0)
        card.bind("<Enter>", enter); card.bind("<Leave>", leave)

        img = self.resim_getir(k['resim_yolu'], (120, 180))
        img_lbl = ctk.CTkLabel(card, text="", image=img) if img else ctk.CTkLabel(card, text="📚", font=("Arial", 60))
        img_lbl.pack(pady=(15, 10))

        puan_txt = self.ortalama_puan_hesapla(k['id'])
        ctk.CTkLabel(card, text=puan_txt, text_color=RENKLER["sari"], font=("Segoe UI", 14, "bold")).pack(pady=2)

        ctk.CTkLabel(card, text=k['ad'][:20] + ("..." if len(k['ad'])>20 else ""), font=("Segoe UI", 16, "bold"), text_color=RENKLER["yazi"]).pack()
        ctk.CTkLabel(card, text=k['yazar'][:25], font=("Segoe UI", 12), text_color=RENKLER["gri"]).pack()
        
        badge = ctk.CTkFrame(card, fg_color="transparent", border_width=1, border_color=RENKLER.get(renk, "white"), corner_radius=20)
        badge.pack(pady=5)
        ctk.CTkLabel(badge, text=durum_txt, font=("Segoe UI", 11), text_color=RENKLER.get(renk, "white")).pack(padx=10, pady=2)

        btn_fr = ctk.CTkFrame(card, fg_color="transparent"); btn_fr.pack(pady=10, fill="x", padx=10)
        btn_fn(btn_fr)

    # POP-UP PENCERELER 
    def popup_duzenle(self, k):
        top = ctk.CTkToplevel(self); top.geometry("350x350"); top.title("Düzenle")
        self.pencere_on_plan(top) 

        ctk.CTkLabel(top, text="Kitap Adı", anchor="w").pack(padx=20, pady=(10,0), fill="x")
        e1 = self.ui_input_olustur(top, "Ad")
        e1.insert(0, k['ad'])
        e1.pack(pady=(0,10), padx=20, fill="x")

        ctk.CTkLabel(top, text="Yazar", anchor="w").pack(padx=20, pady=(5,0), fill="x")
        e2 = self.ui_input_olustur(top, "Yazar")
        e2.insert(0, k['yazar'])
        e2.pack(pady=(0,10), padx=20, fill="x")

        ctk.CTkLabel(top, text="Tür / Kategori", anchor="w").pack(padx=20, pady=(5,0), fill="x")
        cb_tur = ctk.CTkComboBox(top, values=self.kitap_turleri)
        if 'tur' in k and k['tur']: cb_tur.set(k['tur'])
        cb_tur.pack(pady=(0,10), padx=20, fill="x")

        def save(): 
            self.db.sorgu_calistir("UPDATE kitaplar SET ad=?, yazar=?, tur=? WHERE id=?", 
                                   (e1.get(), e2.get(), cb_tur.get(), k['id']), True)
            self.yonetici_yenile(); top.destroy()
        
        self.ui_buton_olustur(top, "Kaydet", save, "yesil").pack(pady=15)

    def popup_yorum(self, k):
        top = ctk.CTkToplevel(self); top.geometry("450x600"); top.title(f"{k['ad']} - İncelemeler")
        self.pencere_on_plan(top)

        info_fr = ctk.CTkFrame(top, fg_color="transparent")
        info_fr.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(info_fr, text=k['ad'], font=("Segoe UI", 20, "bold")).pack()
        ctk.CTkLabel(info_fr, text=f"{k['yazar']} | {self.ortalama_puan_hesapla(k['id'])}", text_color=RENKLER["gri"]).pack()

        ctk.CTkLabel(top, text="Kullanıcı Yorumları", anchor="w", font=("Bold", 14)).pack(fill="x", padx=20, pady=(10,5))
        scroll = ctk.CTkScrollableFrame(top, height=200, fg_color=RENKLER["sidebar"])
        scroll.pack(fill="both", expand=True, padx=20)

        yorumlar = self.db.sorgu_calistir("SELECT * FROM yorumlar WHERE kitap_id=? ORDER BY id DESC", (k['id'],))
        
        if not yorumlar:
            ctk.CTkLabel(scroll, text="Henüz yorum yapılmamış.", text_color="gray").pack(pady=20)
        else:
            for y in yorumlar:
                yf = ctk.CTkFrame(scroll, fg_color=RENKLER["kart"], corner_radius=10)
                yf.pack(fill="x", pady=5)
                
                head = ctk.CTkFrame(yf, fg_color="transparent"); head.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(head, text=y['kadi'], font=("Bold", 12)).pack(side="left")
                ctk.CTkLabel(head, text="★"*y['puan'], text_color=RENKLER["sari"]).pack(side="right")
                
                ctk.CTkLabel(yf, text=y['yorum'], font=("Segoe UI", 12), wraplength=350, justify="left").pack(anchor="w", padx=10, pady=(0,10))
                ctk.CTkLabel(yf, text=y['tarih'], font=("Arial", 10), text_color="gray").pack(anchor="e", padx=10, pady=(0,5))

        ctk.CTkLabel(top, text="Puan Ver & Yorumla", anchor="w", font=("Bold", 14)).pack(fill="x", padx=20, pady=(20,5))
        
        self.secilen_puan = 5
        star_frame = ctk.CTkFrame(top, fg_color="transparent"); star_frame.pack(pady=5)
        yildizlar = []

        def set_puan(p):
            self.secilen_puan = p
            for i, btn in enumerate(yildizlar):
                if i < p: btn.configure(text="★", text_color=RENKLER["sari"])
                else: btn.configure(text="☆", text_color=RENKLER["gri"])
        
        for i in range(1, 6):
            btn = ctk.CTkButton(star_frame, text="★", width=30, font=("Arial", 24), fg_color="transparent", hover=False, 
                                command=lambda p=i: set_puan(p), text_color=RENKLER["sari"])
            btn.pack(side="left")
            yildizlar.append(btn)

        txt_yorum = ctk.CTkTextbox(top, height=80, corner_radius=10, fg_color=RENKLER["sidebar"])
        txt_yorum.pack(padx=20, fill="x", pady=10)

        def send():
            kontrol = self.db.sorgu_calistir("SELECT id FROM yorumlar WHERE kitap_id=? AND kadi=?", (k['id'], self.aktif_kullanici['kadi']))
            if kontrol:
                messagebox.showerror("Hata", "Bu kitaba zaten yorum yaptınız!"); return

            if not txt_yorum.get("1.0", "end-1c").strip():
                messagebox.showwarning("Uyarı", "Lütfen bir yorum yazın."); return
            
            self.db.sorgu_calistir("INSERT INTO yorumlar (kitap_id,kadi,puan,yorum,tarih) VALUES (?,?,?,?,?)", 
                          (k['id'], self.aktif_kullanici['kadi'], self.secilen_puan, txt_yorum.get("1.0", "end-1c"), datetime.now().strftime(TARIH_FORMATI)), True)
            top.destroy()
            messagebox.showinfo("Teşekkürler", "Yorumunuz kaydedildi.")
        
        self.ui_buton_olustur(top, "Yorumu Paylaş", send, "ana").pack(pady=(0, 20))

    def popup_profil(self):
        top = ctk.CTkToplevel(self); top.geometry("600x450"); top.title("Kullanıcı Profili")
        self.pencere_on_plan(top) 
        
        grid_frame = ctk.CTkFrame(top, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        left = ctk.CTkFrame(grid_frame, fg_color=RENKLER["kart"], width=200); left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        
        yol = f"{self.db.klasor_profil}/{self.aktif_kullanici['kadi']}.png"
        img = self.resim_getir(yol, (120, 120))
        ctk.CTkLabel(left, text="", image=img if img else None).pack(pady=(30, 10))
        if not img: ctk.CTkLabel(left, text="👤", font=("Arial", 60)).pack(pady=(30, 10))
        
        ctk.CTkLabel(left, text=self.aktif_kullanici['kadi'], font=("Bold", 20)).pack()
        ctk.CTkLabel(left, text=self.aktif_kullanici['rol'], text_color=RENKLER["gri"]).pack()

        def resim_degis():
            f = filedialog.askopenfilename(filetypes=[("Resim","*.png;*.jpg")])
            if f: 
                Image.open(f).resize((200,200)).save(f"{self.db.klasor_profil}/{self.aktif_kullanici['kadi']}.png")
                messagebox.showinfo("Tamam","Resim güncellendi, tekrar giriş yapın."); top.destroy()
        
        ctk.CTkButton(left, text="Fotoğraf Değiştir", command=resim_degis, fg_color=RENKLER["sidebar"], hover_color=RENKLER["ana"]).pack(pady=20, padx=20)

        right = ctk.CTkFrame(grid_frame, fg_color="transparent"); right.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(right, text="Güvenlik Ayarları", font=("Bold", 18)).pack(anchor="w", pady=(0, 20))
        e_eski = self.ui_input_olustur(right, "Mevcut Şifreniz", show="*"); e_eski.pack(pady=10, fill="x")
        e_yeni = self.ui_input_olustur(right, "Yeni Şifre", show="*"); e_yeni.pack(pady=10, fill="x")
        e_yeni2 = self.ui_input_olustur(right, "Yeni Şifre (Tekrar)", show="*"); e_yeni2.pack(pady=10, fill="x")

        def sifre_kaydet():
            if e_eski.get() != self.aktif_kullanici['sifre']:
                messagebox.showerror("Hata", "Mevcut şifreniz yanlış!"); return
            if e_yeni.get() != e_yeni2.get() or not e_yeni.get():
                messagebox.showerror("Hata", "Yeni şifreler uyuşmuyor veya boş!"); return
            
            self.db.sorgu_calistir("UPDATE kullanicilar SET sifre=? WHERE id=?", (e_yeni.get(), self.aktif_kullanici['id']), True)
            self.aktif_kullanici['sifre'] = e_yeni.get()
            messagebox.showinfo("Başarılı", "Şifreniz güncellendi."); top.destroy()

        self.ui_buton_olustur(right, "Şifreyi Güncelle", sifre_kaydet, "yesil").pack(pady=20, anchor="e")

if __name__ == "__main__":
    app = KutuphaneUygulamasi()
    app.mainloop()
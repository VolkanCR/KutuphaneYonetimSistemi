# Kütüphane Yönetim Sistemi

Python, SQLite ve CustomTkinter ile geliştirilmiş masaüstü kütüphane yönetim sistemi.

Bu proje; kitapları takip etmek, öğrencilerin kitap ödünç almasını sağlamak, iade ve rezervasyon sürecini yönetmek için hazırlanmış sade ama işlevsel bir masaüstü uygulamasıdır. Klasik bir terminal uygulaması yerine modern görünümlü bir arayüz kullanır. Veriler yerel SQLite veritabanında tutulur, bu yüzden kurulumdan sonra ekstra bir sunucuya ihtiyaç duymaz.

<p align="center">
  <img src="assets/screenshots/student-catalog.png" alt="Kütüphane kataloğu ekranı" width="100%">
</p>

## Proje ne yapıyor?

Uygulamada iki temel kullanıcı tipi var: öğrenci ve yönetici.

Öğrenci tarafında kullanıcı kitap kataloğunu görüntüleyebilir, kitap adına veya yazar adına göre arama yapabilir, kitapları türe göre filtreleyebilir. Rafta olan kitaplar ödünç alınabilir. Başka bir kullanıcıda olan kitaplar için rezervasyon sırasına girilebilir. Kullanıcı aldığı kitapları ayrı bir ekranda takip edebilir, iade edebilir ve daha önce okuduğu kitapların geçmişini görebilir.

Yönetici tarafında kitap ekleme, düzenleme ve silme işlemleri yapılır. Kitap eklenirken Google Books üzerinden kapak görseli çekilmeye çalışılır. Bu işlem arayüzü dondurmasın diye ayrı thread içinde çalıştırılır.

Kitaplara yorum ve puan verme sistemi de bulunur. Böylece katalog sadece bir kitap listesi olarak kalmaz; kullanıcıların kitaplar hakkındaki geri bildirimlerini de içerir.

## Ekran görüntüleri

### Giriş ekranı

Kullanıcı adı ve şifre ile oturum açma ekranı.

<p align="center">
  <img src="assets/screenshots/login.png" alt="Giriş ekranı" width="100%">
</p>

### Kayıt ekranı

Yeni kullanıcı oluşturma ekranı. Kullanıcı öğrenci veya yönetici rolüyle kayıt olabilir.

<p align="center">
  <img src="assets/screenshots/register.png" alt="Kayıt ekranı" width="100%">
</p>

### Öğrenci kataloğu

Kitap arama, filtreleme, ödünç alma ve rezervasyon işlemlerinin yapıldığı ana öğrenci ekranı.

<p align="center">
  <img src="assets/screenshots/student-catalog.png" alt="Öğrenci katalog ekranı" width="100%">
</p>

### Elimdekiler ekranı

Öğrencinin ödünç aldığı veya teslim almayı bekleyen kitapları takip ettiği ekran.

<p align="center">
  <img src="assets/screenshots/student-books.png" alt="Öğrencinin elindeki kitaplar ekranı" width="100%">
</p>

### Okuma geçmişi

Daha önce iade edilen kitapların listelendiği geçmiş ekranı.

<p align="center">
  <img src="assets/screenshots/student-history.png" alt="Okuma geçmişi ekranı" width="100%">
</p>

### Yönetim paneli

Yöneticinin kitap eklediği, düzenlediği ve sildiği ekran.

<p align="center">
  <img src="assets/screenshots/admin-panel.png" alt="Yönetim paneli ekranı" width="100%">
</p>

## Öne çıkan özellikler

- Öğrenci ve yönetici rol ayrımı
- Kullanıcı girişi ve kayıt sistemi
- Kitap ekleme, düzenleme ve silme
- Kitap adına ve yazara göre arama
- Kitap türüne göre filtreleme
- Kitap ödünç alma ve iade etme
- Başkasında olan kitaplar için rezervasyon sırası
- Kullanıcının elindeki kitapları takip etmesi
- İade geçmişi kaydı
- Kitaplara yorum ve yıldız puanı verme
- Profil fotoğrafı değiştirme
- Şifre güncelleme
- Google Books üzerinden kapak görseli çekme
- SQLite ile yerel veri saklama
- Threading ile arayüz donmasını azaltma

## Kullanılan teknolojiler

Bu proje tamamen Python ile yazıldı. Arayüz için CustomTkinter, veritabanı için SQLite kullanıldı. Görselleri işlemek için Pillow, Google Books üzerinden kapak görseli çekmek için Requests kullanılıyor.

Temel bağımlılıklar:

```txt
customtkinter
pillow
requests
```

## Kurulum

Projeyi bilgisayarına aldıktan sonra klasöre gir:

```bash
git clone https://github.com/kullanici-adin/kutuphane-yonetim-sistemi.git
cd kutuphane-yonetim-sistemi
```

Sanal ortam oluşturmak istersen Windows için:

```bash
py -m venv .venv
.venv\Scripts\activate
```

Linux veya macOS için:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Bağımlılıkları yükle:

```bash
pip install -r requirements.txt
```

Uygulamayı çalıştır:

```bash
python main.py
```

## Varsayılan yönetici hesabı

İlk çalıştırmada uygulama otomatik olarak bir yönetici hesabı oluşturur.

```txt
Kullanıcı adı: admin
Şifre: 1234
```

Bu hesap demo amaçlıdır. Gerçek kullanımda giriş yaptıktan sonra şifreyi değiştirmen gerekir.

## Proje yapısı

```txt
kutuphane-yonetim-sistemi/
├── main.py
├── requirements.txt
├── README.md
├── assets/
│   └── screenshots/
│       ├── login.png
│       ├── register.png
│       ├── student-catalog.png
│       ├── student-books.png
│       ├── student-history.png
│       └── admin-panel.png
└── .gitignore
```

Uygulama çalışırken kendi verilerini yerel olarak üretir. Bu dosyalar repoya eklenmemelidir:

```txt
kutuphane.db
profil_resimleri/
kitap_kapaklari/
```

## Veritabanı tarafı

Uygulama ilk açıldığında gerekli SQLite tablolarını otomatik oluşturur. Kullanıcılar, kitaplar, yorumlar, geçmiş işlemler ve rezervasyonlar ayrı tablolarda tutulur.

Bu yapı küçük ölçekli bir kütüphane senaryosu için yeterlidir. Daha büyük bir sistemde kullanıcı şifrelerinin hashlenmesi, yönetici kayıtlarının sınırlandırılması ve daha detaylı yetkilendirme kontrolleri eklenmelidir.

## Geliştirme notları

Bu proje eğitim ve portfolyo amacıyla hazırlanmıştır. Temel işlevleri çalışır durumdadır, ancak gerçek bir kurumda kullanılacaksa bazı noktaların güçlendirilmesi gerekir.

Özellikle şifreler düz metin olarak saklanmamalı, yönetici hesabı oluşturma süreci kontrol altına alınmalı ve form doğrulamaları daha katı hale getirilmelidir. Ayrıca ISBN veya barkod ile kitap bilgisi çekme gibi özellikler projeyi daha kullanışlı hale getirebilir.

## Lisans

Bu projeyi eğitim ve portfolyo amacıyla kullanabilirsin. Açık kaynak olarak paylaşacaksan `MIT License` eklemek uygun olur.

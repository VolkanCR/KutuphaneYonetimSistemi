# Kütüphane Yönetim Sistemi

Python, SQLite ve CustomTkinter ile geliştirilmiş masaüstü kütüphane yönetim sistemi.

Bu proje; kitapları takip etmek, öğrencilerin kitap ödünç almasını sağlamak, iade ve rezervasyon sürecini yönetmek için hazırlanmış sade ama işlevsel bir masaüstü uygulamasıdır. Klasik bir terminal uygulaması yerine modern görünümlü bir arayüz kullanır. Veriler yerel SQLite veritabanında tutulur, bu yüzden kurulumdan sonra ekstra bir sunucuya ihtiyaç duymaz.

## Proje ne yapıyor?

Uygulamada iki temel kullanıcı tipi var: öğrenci ve yönetici.

Öğrenci tarafında kullanıcı kitap kataloğunu görüntüleyebilir, kitap adına veya yazar adına göre arama yapabilir, kitapları türe göre filtreleyebilir. Rafta olan kitaplar ödünç alınabilir. Başka bir kullanıcıda olan kitaplar için rezervasyon sırasına girilebilir. Kullanıcı aldığı kitapları ayrı bir ekranda takip edebilir, iade edebilir ve daha önce okuduğu kitapların geçmişini görebilir.

Yönetici tarafında kitap ekleme, düzenleme ve silme işlemleri yapılır. Kitap eklenirken Google Books üzerinden kapak görseli çekilmeye çalışılır. Bu işlem arayüzü dondurmasın diye ayrı thread içinde çalıştırılır.

Kitaplara yorum ve puan verme sistemi de bulunur. Böylece katalog sadece bir kitap listesi olarak kalmaz; kullanıcıların kitaplar hakkındaki geri bildirimlerini de içerir.

## Ekran görüntüleri

### Giriş ekranı

Kullanıcı adı ve şifre ile oturum açma ekranı.

<img width="1536" height="1024" alt="Ana sayfa" src="https://github.com/user-attachments/assets/69926cac-1ccf-4d5e-b48e-14f801abeb4b" />


### Kayıt ekranı

Yeni kullanıcı oluşturma ekranı. Kullanıcı öğrenci veya yönetici rolüyle kayıt olabilir.

<img width="1536" height="1024" alt="Kayit" src="https://github.com/user-attachments/assets/be0008f3-f85d-4b57-bbd0-4e5c53762fbb" />


### Öğrenci kataloğu

Kitap arama, filtreleme, ödünç alma ve rezervasyon işlemlerinin yapıldığı ana öğrenci ekranı.

<img width="1536" height="1024" alt="Ogrenci sayfasi" src="https://github.com/user-attachments/assets/4fd034b6-b386-4d8f-8587-607cebfae574" />


### Elimdekiler ekranı

Öğrencinin ödünç aldığı veya teslim almayı bekleyen kitapları takip ettiği ekran.



### Okuma geçmişi

Daha önce iade edilen kitapların listelendiği geçmiş ekranı.



### Yönetim paneli

Yöneticinin kitap eklediği, düzenlediği ve sildiği ekran.

<img width="1536" height="1024" alt="Yonetici paneli" src="https://github.com/user-attachments/assets/a56664cc-287c-4147-9099-0aa34aebc736" />


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

# İnsanlık Eli web sitesi (www.insanlik.tr)

Site, bu depodaki dosyalardan otomatik olarak oluşturulur. Bir dosyayı değiştirip
**Commit changes** dediğinizde GitHub siteyi yeniden oluşturur ve 1–2 dakika içinde
yayına alır. Program kurmanız gerekmez, her şey github.com üzerinden yapılır.

## Klasörler

| Klasör | Ne var? |
|---|---|
| `content/news/tr`, `content/news/en`, `content/news/ar` | Haberler (her haber bir dosya) |
| `content/projects/<dil>` | Projeler |
| `content/programs/<dil>` | Programlar |
| `content/i18n/tr.yml`, `en.yml`, `ar.yml` | Sayfalardaki tüm diğer yazılar (menü, ana sayfa, hakkımızda, iletişim…) |
| `content/site.yml` | Telefon, e-posta, adres, banka hesapları, sosyal medya |
| `static/img/...` | Fotoğraflar |

`templates`, `static/css`, `static/js` ve `build.py` sitenin tasarımıdır; içerik için bunlara dokunmanız gerekmez.

## Yeni haber eklemek

1. Fotoğrafı yükleyin: `static/img/news` klasörüne girin → **Add file → Upload files**.
   Dosya adında Türkçe karakter ve boşluk olmasın (ör. `gazze-su-2026-10.jpg`).
2. `content/news/tr` klasörüne girin → **Add file → Create new file**.
3. Dosya adı tarihle başlamalı ve `.md` ile bitmeli: `2026-10-21-gazze-su-dagitimi.md`
4. Şunu yapıştırıp doldurun:

```
---
title: "Haberin başlığı"
date: 2026-10-21
category: "Su, Sanitasyon ve Hijyen (WASH)"
image: /img/news/gazze-su-2026-10.jpg
gallery:
  - /img/news/gazze-su-2026-10-2.jpg
instagram: https://www.instagram.com/p/XXXXXXXX/
---

Haberin metni buraya. Paragraflar arasında bir satır boş bırakın.

**Kalın yazı** için iki yıldız kullanın.
```

5. **Commit changes**'e basın. Haber, haberler sayfasında ve ana sayfada kendiliğinden görünür.

- `category`, `gallery` ve `instagram` satırları isteğe bağlıdır; gerekmiyorsa silin.
- Aynı haberin İngilizcesi/Arapçası için `content/news/en` veya `content/news/ar` klasörüne
  **aynı dosya adıyla** bir dosya ekleyin. Böylece dil düğmesi doğru habere geçer.
- Bir haberi yayından kaldırmak ama silmemek için `---` bloğuna `draft: true` satırını ekleyin.

## Program ve proje fotoğrafları

Bir programın veya projenin fotoğrafı yoksa, `static/img/programs` (veya `static/img/projects`)
klasörüne o programın dosya adıyla bir `.jpg` yükleyin; site onu otomatik kullanır.
Örneğin `content/programs/tr/health.md` için `static/img/programs/health.jpg`.
Fotoğraf yatay olmalı (4:3 veya 16:9), en fazla 1600 piksel genişlikte.

## Yazıları değiştirmek

`content/i18n/tr.yml` dosyasını açın, kalem simgesine (✏️) basın, iki noktadan (`:`) sonraki
yazıyı değiştirin. Satır başındaki boşlukları değiştirmeyin. İçinde iki nokta geçen bir yazıyı
tırnak içine alın: `title: "Gazze: Su dağıtımı"`.

## Bir şey ters giderse

Değişiklikten sonra site güncellenmezse depodaki **Actions** sekmesine bakın. Kırmızı çarpılı
satıra tıklayın → **build** → hata mesajında hangi dosyada neyin eksik olduğu yazar
(örneğin "title: is missing" veya "image was not found"). Dosyayı düzeltip tekrar kaydedin.
Hata varken eski site yayında kalmaya devam eder, yani siteyi bozamazsınız.

---

### English summary

Content lives in `content/` (news, projects, programmes as Markdown files; all other text in
`content/i18n/<lang>.yml`; contact and bank details in `content/site.yml`). Images go in
`static/img/`. Every commit to `main` runs `.github/workflows/deploy.yml`, which builds the
site with `python build.py` and publishes `_site/` to GitHub Pages. To preview locally:
`pip install -r requirements.txt && python build.py`, then open `_site/` with any static server
(e.g. `python -m http.server -d _site`).

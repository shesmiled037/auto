import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
import feedparser
import os
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")
RSS_URL = "https://curtainsblinds.shop/rss/"
LAST_POSTED_FILE = "last_posted.txt"

# Mapping kategori ke ID WordPress
CATEGORY_MAP = {
    "Prediksi Togel Sidney": 4,
    "Prediksi Togel Hongkong": 2,
    "Prediksi Togel Singapore": 5,
    "Prediksi Togel Kingkong": 3,
    "Bocoran Togel SDY" : 8,
    "Bocoran Data HK": 7,
    "Bocoran kingkongpools" : 9,
    "Bocoran SGP Hari Ini" : 6,
    "Prediksi HK Akurat" : 10,
    "Uncategorized": 1
}

def get_categories_from_title(judul):
    judul = judul.lower()
    categories = []

    if "sidney" in judul or "sdy" in judul:
        categories.append("Prediksi Togel Sidney")
        categories.append("Bocoran Togel SDY")

    if "hongkong" in judul or "hk" in judul:
        categories.append("Prediksi Togel Hongkong")
        categories.append("Bocoran Data HK")
        categories.append("Prediksi HK Akurat")

    if "singapore" in judul or "sgp" in judul:
        categories.append("Prediksi Togel Singapore")
        categories.append("Bocoran SGP Hari Ini")

    if "kingkong" in judul:
        categories.append("Prediksi Togel Kingkong")
        categories.append("Bocoran kingkongpools")

    if not categories:
        categories.append("Uncategorized")

    return categories


def get_image_url_from_title(judul):
    judul = judul.lower()
    if "sidney" in judul or "sydney" in judul:
        return "https://gbg-coc.org/wp-content/uploads/sidney.jpg"
    elif "hongkong" in judul or "hk" in judul:
        return "https://gbg-coc.org/wp-content/uploads/hongkong.jpg"
    elif "singapore" in judul or "sgp" in judul:
        return "https://gbg-coc.org/wp-content/uploads/singapore.jpg"
    elif "kingkong" in judul:
        return "https://gbg-coc.org/wp-content/uploads/kingkong.jpg"
    else:
        return None

def ekstrak_konten_format(soup):
    judul = soup.find("h1").get_text(strip=True)

    angka_main = soup.find("div", string=lambda x: x and "-" in x)
    angka_main = angka_main.get_text(strip=True) if angka_main else "0-0-0-0"

    shio = soup.find("div", string=lambda x: x and any(sh in x.upper() for sh in ["KUDA", "KERBAU", "TIKUS", "NAGA", "ULAR"]))
    shio = shio.get_text(strip=True) if shio else "KUDA"

    macau = soup.find("div", string=lambda x: x and "/" in x)
    macau = macau.get_text(strip=True) if macau else "13 / 48"

    colok = soup.find_all("div", string=lambda x: x and "/" in x)
    colok = colok[1].get_text(strip=True) if len(colok) > 1 else "0 / 0"

    kepala_ekor = soup.find("div", string=lambda x: x and "–" in x)
    kepala_ekor = kepala_ekor.get_text(strip=True) if kepala_ekor else "091 – 423"

    bb_2d_lines = []
    for div in soup.find_all("div"):
        text = div.get_text(strip=True)
        if len(text.split()) == 4 and all(len(num) == 2 and num.isdigit() for num in text.split()):
            bb_2d_lines.append(text)
        if len(bb_2d_lines) >= 5:
            break

    bb_2d = "<br>".join(bb_2d_lines) if bb_2d_lines else "94 83 23 07<br>04 51 87 91<br>05 34 93 23"

    konten_html = f"""
    <h2 style="color: red; text-align:center;">{judul}</h2>
    <p style="text-align:center;"><em>adalah sebagai berikut :</em></p>
    <h3 style="text-align:center; color:#111;">Angka Main</h3>
    <div style="border:2px solid red; background:#fff0f0; font-size:26px; font-weight:bold; text-align:center; color:green; padding:12px; margin:10px auto; width:200px; border-radius:8px;">
    {angka_main}</div>
    <h3 style="text-align:center; color:#111;">Shio :</h3>
    <div style="border:2px solid teal; background:#e0ffff; font-size:24px; text-align:center; color:#006d77; padding:10px; margin:10px auto; width:200px;">
    {shio}</div>
    <h3 style="text-align:center; color:#111;">Macau :</h3>
    <div style="border:2px solid magenta; background:#ffe6ff; font-size:24px; text-align:center; color:green; padding:10px; margin:10px auto; width:200px;">
    {macau}</div>
    <h3 style="text-align:center; color:#111;">Colok Bebas :</h3>
    <div style="border:2px solid blue; background:#e6f0ff; font-size:24px; text-align:center; color:green; padding:10px; margin:10px auto; width:200px;">
    {colok}</div>
    <h3 style="text-align:center; color:#111;">2D Angka Jitu BB :</h3>
    <div style="font-size:22px; text-align:center; color:#333; background:#f9f9f9; padding:10px; width:300px; margin:10px auto;">
    {bb_2d}</div>
    <h3 style="text-align:center; color:#111;">Kepala – Ekor :</h3>
    <div style="border:2px solid #111; background:#f4f4f4; font-size:24px; text-align:center; color:blue; padding:10px; margin:10px auto; width:220px;">
    {kepala_ekor}</div>
    """
    return judul, konten_html

def ambil_dan_edit_konten(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    judul, angka_konten = ekstrak_konten_format(soup)

    paragraf_html = ""
    paragraf_set = set()
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if len(text) > 50 and text.lower() not in paragraf_set:
            paragraf_set.add(text.lower())
            paragraf_html += f"<p>{text}</p>\n"

    if not paragraf_html:
        for div in soup.find_all("div"):
            text = div.get_text(strip=True)
            if len(text) > 50 and text.lower() not in paragraf_set:
                paragraf_set.add(text.lower())
                paragraf_html += f"<p>{text}</p>\n"
                if len(paragraf_set) >= 3:
                    break

    image_url = get_image_url_from_title(judul)
    gambar_html = f'<img src="{image_url}" alt="{judul}" style="max-width:100%; margin-bottom:20px;">' if image_url else ""

    konten_html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background: #fdfdfd; color: #111;">
    {gambar_html}
    {angka_konten}
    <br>
    {paragraf_html}
    <p style="text-align:center; font-size:14px; color:gray;">Prediksi disediakan oleh <strong>388hero</strong></p>
    </div>
    """

    konten_html = konten_html.replace("Surgatogel", "388hero ").replace("SurgaTogel", "388hero ").replace("SURGATOGEL", "388HERO ")
    return judul, konten_html

def post_ke_wordpress(judul, konten_html):
    kategori_list = get_categories_from_title(judul)
    kategori_ids = [CATEGORY_MAP.get(kat, 1) for kat in kategori_list]

    data = {
        "title": judul,
        "content": konten_html,
        "status": "publish",
        "categories": kategori_ids
    }

    auth = HTTPBasicAuth(WP_USER, WP_APP_PASS)
    response = requests.post(WP_URL, json=data, auth=auth)
    response.raise_for_status()
    print(f"✅ Berhasil posting ke kategori {kategori_list}: {judul}")


def sudah_dipost(link):
    if os.path.exists(LAST_POSTED_FILE):
        with open(LAST_POSTED_FILE, "r") as f:
            posted_links = f.read().splitlines()
            return link in posted_links
    return False

def simpan_link(link):
    with open(LAST_POSTED_FILE, "a") as f:
        f.write(link + "\n")

def main():
    feed = feedparser.parse(RSS_URL)
    for entry in reversed(feed.entries):  # Urutkan dari yang lama ke baru
        if sudah_dipost(entry.link):
            print(f"⏩ Lewat: {entry.link}")
            continue
        try:
            print(f"🔄 Memproses: {entry.link}")
            judul, konten = ambil_dan_edit_konten(entry.link)
            post_ke_wordpress(judul, konten)
            simpan_link(entry.link)
        except Exception as e:
            print(f"❌ Gagal posting dari {entry.link}: {e}")

if __name__ == "__main__":
    main()

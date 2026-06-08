"""
=============================================================================
  SISTEM MANAJEMEN DATA MAHASISWA
  Jalankan: python manajemen_mahasiswa.py
  Browser akan terbuka otomatis di http://localhost:8080
=============================================================================
  Fitur:
    * CRUD  (Input, Edit, Hapus, Tampilkan)
    * File I/O  (simpan / muat JSON otomatis)
    * OOP  (class, enkapsulasi, pewarisan, polimorfisme)
    * Pencarian  (Linear, Sequential, Binary Search)
    * Pengurutan  (Bubble, Insertion, Selection, Merge, Shell Sort)
    * Validasi Regex  (NIM, Nama, IPK, Telepon, Email)
    * Exception Handling  (custom exception hierarchy)
    * Time Complexity info
  Dependensi: HANYA Python 3.7+ standard library (tidak perlu pip install)
=============================================================================
"""

# ─── IMPORT STANDARD LIBRARY ──────────────────────────────────────────────────
import http.server
import threading
import webbrowser
import json
import os
import re
import time
from datetime import datetime
from typing import List, Dict, Optional


# ─── KONSTANTA ─────────────────────────────────────────────────────────────────
PORT       = 8080
FILE_DATA  = "data_mahasiswa.json"
FILE_LOG   = "log_aktivitas.txt"
TAHUN_MIN  = 2000
TAHUN_MAX  = datetime.now().year
JURUSAN    = [
    "Teknik Informatika", "Sistem Informasi", "Teknik Elektro",
    "Teknik Mesin", "Manajemen", "Akuntansi",
    "Hukum", "Psikologi", "Kedokteran", "Farmasi",
]


# ==============================================================================
#  1. CUSTOM EXCEPTION  (OOP — hierarchy)
# ==============================================================================

class AppException(Exception):
    """Base exception — semua error turunan dari sini."""
    def __init__(self, pesan: str, kode: int = 0):
        super().__init__(pesan)
        self.pesan = pesan
        self.kode  = kode
    def __str__(self) -> str:
        return f"[Err {self.kode}] {self.pesan}"


class NIMDuplikatError(AppException):
    def __init__(self, nim: str):
        super().__init__(f"NIM '{nim}' sudah terdaftar.", 101)


class NIMTidakDitemukanError(AppException):
    def __init__(self, nim: str):
        super().__init__(f"NIM '{nim}' tidak ditemukan.", 102)


class InputTidakValidError(AppException):
    def __init__(self, field: str, aturan: str):
        super().__init__(f"'{field}' tidak valid — {aturan}", 103)


class FileIOError(AppException):
    def __init__(self, operasi: str, detail: str):
        super().__init__(f"Gagal {operasi}: {detail}", 104)


# ==============================================================================
#  2. VALIDATOR — REGULAR EXPRESSION
# ==============================================================================

class Validator:
    """
    Validasi input dengan Regex.
    Time Complexity semua method: O(m) — m = panjang string.
    """
    _NIM   = re.compile(r"^\d{8}$")
    _NAMA  = re.compile(r"^[A-Za-z\s'.]{3,50}$")
    _IPK   = re.compile(r"^([0-3]\.\d{1,2}|4(\.0{1,2})?)$")
    _TELP  = re.compile(r"^(\+62|62|0)[0-9]{9,12}$")
    _EMAIL = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    _TAHUN = re.compile(r"^\d{4}$")

    @staticmethod
    def nim(v: str) -> bool:
        return bool(Validator._NIM.match(v.strip()))

    @staticmethod
    def nama(v: str) -> bool:
        return bool(Validator._NAMA.match(v.strip()))

    @staticmethod
    def ipk(v: str) -> bool:
        if not Validator._IPK.match(str(v).strip()):
            return False
        try:
            n = float(v)
            return 0.0 <= n <= 4.0
        except (ValueError, TypeError):
            return False

    @staticmethod
    def telepon(v: str) -> bool:
        return bool(Validator._TELP.match(v.strip()))

    @staticmethod
    def email(v: str) -> bool:
        return bool(Validator._EMAIL.match(v.strip()))

    @staticmethod
    def tahun(v: str) -> bool:
        if not Validator._TAHUN.match(str(v).strip()):
            return False
        try:
            t = int(v)
            return TAHUN_MIN <= t <= TAHUN_MAX
        except (ValueError, TypeError):
            return False

    @staticmethod
    def jurusan(v: str) -> bool:
        return v.strip() in JURUSAN

    @staticmethod
    def semester(v) -> bool:
        try:
            s = int(v)
            return 1 <= s <= 12
        except (ValueError, TypeError):
            return False


# ==============================================================================
#  3. OOP — CLASS (Enkapsulasi, Pewarisan, Polimorfisme)
# ==============================================================================

class Orang:
    """Base class — enkapsulasi atribut dasar."""
    def __init__(self, nama: str, telepon: str, email: str):
        self._nama    = nama.strip()
        self._telepon = telepon.strip()
        self._email   = email.strip().lower()

    @property
    def nama(self) -> str:
        return self._nama

    @nama.setter
    def nama(self, v: str):
        if not Validator.nama(v):
            raise InputTidakValidError("Nama", "Hanya huruf & spasi, 3-50 karakter.")
        self._nama = v.strip()

    @property
    def telepon(self) -> str:
        return self._telepon

    @telepon.setter
    def telepon(self, v: str):
        if not Validator.telepon(v):
            raise InputTidakValidError("Telepon", "Format 08xx / +62xx, 10-13 digit.")
        self._telepon = v.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, v: str):
        if not Validator.email(v):
            raise InputTidakValidError("Email", "Format: nama@domain.com")
        self._email = v.strip().lower()

    def info(self) -> dict:
        """Polimorfisme — subclass override."""
        return {"nama": self._nama, "telepon": self._telepon, "email": self._email}


class Mahasiswa(Orang):
    """
    Mewarisi Orang (Pewarisan).
    Enkapsulasi lengkap dengan getter / setter.
    """
    def __init__(
        self,
        nim: str,
        nama: str,
        jurusan: str,
        semester: int,
        ipk: float,
        tahun_masuk: int,
        telepon: str,
        email: str,
        tgl_daftar: Optional[str] = None,
    ):
        super().__init__(nama, telepon, email)
        self._nim         = nim.strip()
        self._jurusan     = jurusan.strip()
        self._semester    = int(semester)
        self._ipk         = round(float(ipk), 2)
        self._tahun_masuk = int(tahun_masuk)
        self._tgl_daftar  = tgl_daftar or datetime.now().strftime("%d %b %Y")

    # ── Getter ────────────────────────────────────────────────────────────────
    @property
    def nim(self)         -> str:   return self._nim
    @property
    def jurusan(self)     -> str:   return self._jurusan
    @property
    def semester(self)    -> int:   return self._semester
    @property
    def ipk(self)         -> float: return self._ipk
    @property
    def tahun_masuk(self) -> int:   return self._tahun_masuk
    @property
    def tgl_daftar(self)  -> str:   return self._tgl_daftar

    # ── Setter ────────────────────────────────────────────────────────────────
    @jurusan.setter
    def jurusan(self, v: str):
        if not Validator.jurusan(v):
            raise InputTidakValidError("Jurusan", "Pilih dari daftar.")
        self._jurusan = v.strip()

    @semester.setter
    def semester(self, v):
        if not Validator.semester(v):
            raise InputTidakValidError("Semester", "Antara 1 dan 12.")
        self._semester = int(v)

    @ipk.setter
    def ipk(self, v):
        if not (0.0 <= float(v) <= 4.0):
            raise InputTidakValidError("IPK", "Antara 0.00 dan 4.00.")
        self._ipk = round(float(v), 2)

    def status_akademik(self) -> str:
        if self._ipk >= 3.50: return "Cumlaude"
        if self._ipk >= 3.00: return "Sangat Memuaskan"
        if self._ipk >= 2.50: return "Memuaskan"
        if self._ipk >= 2.00: return "Cukup"
        return "Perlu Perhatian"

    def info(self) -> dict:
        """Override (Polimorfisme) — tambahkan field mahasiswa."""
        base = super().info()
        base.update({
            "nim": self._nim, "jurusan": self._jurusan,
            "semester": self._semester, "ipk": self._ipk,
            "tahun_masuk": self._tahun_masuk, "tgl_daftar": self._tgl_daftar,
            "status": self.status_akademik(),
        })
        return base

    def ke_dict(self) -> dict:
        return {
            "nim": self._nim, "nama": self._nama,
            "jurusan": self._jurusan, "semester": self._semester,
            "ipk": self._ipk, "tahun_masuk": self._tahun_masuk,
            "telepon": self._telepon, "email": self._email,
            "tgl_daftar": self._tgl_daftar,
        }

    @classmethod
    def dari_dict(cls, d: dict) -> "Mahasiswa":
        return cls(
            nim=d["nim"], nama=d["nama"], jurusan=d["jurusan"],
            semester=d["semester"], ipk=d["ipk"],
            tahun_masuk=d["tahun_masuk"], telepon=d["telepon"],
            email=d["email"], tgl_daftar=d.get("tgl_daftar"),
        )

    def __repr__(self) -> str:
        return f"Mahasiswa({self._nim}, {self._nama}, IPK={self._ipk})"

    def __eq__(self, other) -> bool:
        return isinstance(other, Mahasiswa) and self._nim == other._nim


# ==============================================================================
#  4. FILE I/O
# ==============================================================================

class FileManager:
    """Simpan & muat data JSON + log aktivitas."""

    def __init__(self, file_data: str = FILE_DATA, file_log: str = FILE_LOG):
        self._file_data = file_data
        self._file_log  = file_log

    def simpan(self, daftar: List[Mahasiswa]) -> bool:
        """O(n) — serialisasi ke JSON."""
        try:
            data = [m.ke_dict() for m in daftar]
            with open(self._file_data, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log(f"SIMPAN {len(daftar)} record")
            return True
        except (IOError, OSError) as e:
            raise FileIOError("menyimpan", str(e))

    def muat(self) -> List[Mahasiswa]:
        """O(n) — parse JSON ke objek Mahasiswa."""
        if not os.path.exists(self._file_data):
            return []
        try:
            with open(self._file_data, "r", encoding="utf-8") as f:
                raw = json.load(f)
            hasil = []
            for item in raw:
                try:
                    hasil.append(Mahasiswa.dari_dict(item))
                except Exception:
                    pass
            self.log(f"MUAT {len(hasil)} record")
            return hasil
        except json.JSONDecodeError as e:
            raise FileIOError("membaca JSON", str(e))
        except (IOError, OSError) as e:
            raise FileIOError("membaca file", str(e))

    def log(self, pesan: str):
        """O(1) — append satu baris ke log."""
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self._file_log, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {pesan}\n")
        except Exception:
            pass


# ==============================================================================
#  5. ALGORITMA PENCARIAN
# ==============================================================================

class AlgoritmaCari:
    """
    Linear Search    : O(n) — partial match
    Sequential Search: O(n) — exact NIM
    Binary Search    : O(log n) — data WAJIB terurut NIM
    Rentang IPK      : O(n) — filter range
    """

    @staticmethod
    def linear(
        daftar: List[Mahasiswa], query: str, field: str = "nama"
    ) -> List[Mahasiswa]:
        q = query.lower().strip()
        return [m for m in daftar if q in str(getattr(m, field, "")).lower()]

    @staticmethod
    def sequential(
        daftar: List[Mahasiswa], nim: str
    ) -> Optional[Mahasiswa]:
        target = nim.strip()
        for m in daftar:
            if m.nim == target:
                return m
        return None

    @staticmethod
    def binary(
        daftar_urut: List[Mahasiswa], nim: str
    ) -> Optional[Mahasiswa]:
        lo, hi = 0, len(daftar_urut) - 1
        target = nim.strip()
        while lo <= hi:
            mid     = (lo + hi) // 2
            nim_mid = daftar_urut[mid].nim
            if nim_mid == target:
                return daftar_urut[mid]
            elif nim_mid < target:
                lo = mid + 1
            else:
                hi = mid - 1
        return None

    @staticmethod
    def rentang_ipk(
        daftar: List[Mahasiswa], ipk_min: float, ipk_max: float
    ) -> List[Mahasiswa]:
        return [m for m in daftar if ipk_min <= m.ipk <= ipk_max]


# ==============================================================================
#  6. ALGORITMA PENGURUTAN
# ==============================================================================

class AlgoritmaUrut:
    """
    Bubble Sort    : O(n²) / best O(n)
    Insertion Sort : O(n²) / best O(n)
    Selection Sort : O(n²)
    Merge Sort     : O(n log n)
    Shell Sort     : O(n^1.5)
    """

    @staticmethod
    def _key(m: Mahasiswa, field: str):
        val = getattr(m, field, m.nim)
        return val.lower() if isinstance(val, str) else val

    @staticmethod
    def bubble(
        daftar: List[Mahasiswa], field: str = "nim", naik: bool = True
    ) -> List[Mahasiswa]:
        a = list(daftar)
        n = len(a)
        for i in range(n):
            swapped = False
            for j in range(n - i - 1):
                v1 = AlgoritmaUrut._key(a[j], field)
                v2 = AlgoritmaUrut._key(a[j + 1], field)
                if (v1 > v2) if naik else (v1 < v2):
                    a[j], a[j + 1] = a[j + 1], a[j]
                    swapped = True
            if not swapped:
                break
        return a

    @staticmethod
    def insertion(
        daftar: List[Mahasiswa], field: str = "nim", naik: bool = True
    ) -> List[Mahasiswa]:
        a = list(daftar)
        for i in range(1, len(a)):
            cur = a[i]
            vc  = AlgoritmaUrut._key(cur, field)
            j   = i - 1
            while j >= 0:
                vj = AlgoritmaUrut._key(a[j], field)
                if (vj > vc) if naik else (vj < vc):
                    a[j + 1] = a[j]
                    j -= 1
                else:
                    break
            a[j + 1] = cur
        return a

    @staticmethod
    def selection(
        daftar: List[Mahasiswa], field: str = "nim", naik: bool = True
    ) -> List[Mahasiswa]:
        a = list(daftar)
        n = len(a)
        for i in range(n):
            idx = i
            for j in range(i + 1, n):
                vj  = AlgoritmaUrut._key(a[j],   field)
                vi  = AlgoritmaUrut._key(a[idx],  field)
                if (vj < vi) if naik else (vj > vi):
                    idx = j
            if idx != i:
                a[i], a[idx] = a[idx], a[i]
        return a

    @staticmethod
    def merge(
        daftar: List[Mahasiswa], field: str = "nim", naik: bool = True
    ) -> List[Mahasiswa]:
        if len(daftar) <= 1:
            return list(daftar)
        mid = len(daftar) // 2
        L   = AlgoritmaUrut.merge(daftar[:mid], field, naik)
        R   = AlgoritmaUrut.merge(daftar[mid:], field, naik)
        res: List[Mahasiswa] = []
        i = j = 0
        while i < len(L) and j < len(R):
            vl = AlgoritmaUrut._key(L[i], field)
            vr = AlgoritmaUrut._key(R[j], field)
            if (vl <= vr) if naik else (vl >= vr):
                res.append(L[i]); i += 1
            else:
                res.append(R[j]); j += 1
        res.extend(L[i:])
        res.extend(R[j:])
        return res

    @staticmethod
    def shell(
        daftar: List[Mahasiswa], field: str = "nim", naik: bool = True
    ) -> List[Mahasiswa]:
        a   = list(daftar)
        n   = len(a)
        gap = 1
        while gap < n // 3:
            gap = gap * 3 + 1
        while gap >= 1:
            for i in range(gap, n):
                tmp = a[i]
                vt  = AlgoritmaUrut._key(tmp, field)
                j   = i
                while j >= gap:
                    vj = AlgoritmaUrut._key(a[j - gap], field)
                    if (vj > vt) if naik else (vj < vt):
                        a[j] = a[j - gap]
                        j -= gap
                    else:
                        break
                a[j] = tmp
            gap //= 3
        return a

    @staticmethod
    def benchmark(
        daftar: List[Mahasiswa], field: str = "nim"
    ) -> Dict[str, float]:
        """Benchmark 5 algoritma, 5 run tiap algoritma."""
        fn_map = {
            "Bubble Sort":    AlgoritmaUrut.bubble,
            "Insertion Sort": AlgoritmaUrut.insertion,
            "Selection Sort": AlgoritmaUrut.selection,
            "Merge Sort":     AlgoritmaUrut.merge,
            "Shell Sort":     AlgoritmaUrut.shell,
        }
        hasil: Dict[str, float] = {}
        for nama, fn in fn_map.items():
            runs = []
            for _ in range(5):
                t0 = time.perf_counter()
                fn(daftar, field)
                runs.append(time.perf_counter() - t0)
            hasil[nama] = sum(runs) / len(runs)
        return hasil


# ==============================================================================
#  7. MANAGER — CRUD CONTROLLER
# ==============================================================================

class ManagerMahasiswa:
    """Satu-satunya yang boleh mengubah database."""

    def __init__(self):
        self._fm: FileManager     = FileManager()
        self._db: List[Mahasiswa] = []
        self._muat_awal()

    def _muat_awal(self):
        try:
            self._db = self._fm.muat()
        except FileIOError as e:
            print(f"  [Peringatan] {e}")
            self._db = []

    def _simpan(self):
        try:
            self._fm.simpan(self._db)
        except FileIOError as e:
            print(f"  [Peringatan simpan] {e}")

    # ── CREATE — O(n) ─────────────────────────────────────────────────────────
    def tambah(self, mhs: Mahasiswa) -> bool:
        if AlgoritmaCari.sequential(self._db, mhs.nim):
            raise NIMDuplikatError(mhs.nim)
        self._db.append(mhs)
        self._simpan()
        self._fm.log(f"TAMBAH NIM={mhs.nim} nama={mhs.nama}")
        return True

    # ── READ — O(1) / O(n) ────────────────────────────────────────────────────
    def semua(self) -> List[Mahasiswa]:
        return self._db

    def cari_nim(self, nim: str) -> Optional[Mahasiswa]:
        return AlgoritmaCari.sequential(self._db, nim)

    def jumlah(self) -> int:
        return len(self._db)

    # ── UPDATE — O(n) ─────────────────────────────────────────────────────────
    def edit(self, nim: str, patch: dict) -> bool:
        mhs = AlgoritmaCari.sequential(self._db, nim)
        if not mhs:
            raise NIMTidakDitemukanError(nim)
        try:
            if patch.get("nama"):     mhs.nama     = patch["nama"]
            if patch.get("jurusan"):  mhs.jurusan  = patch["jurusan"]
            if patch.get("semester"): mhs.semester = int(patch["semester"])
            if patch.get("ipk"):      mhs.ipk      = float(patch["ipk"])
            if patch.get("telepon"):  mhs.telepon  = patch["telepon"]
            if patch.get("email"):    mhs.email    = patch["email"]
        except InputTidakValidError:
            raise
        self._simpan()
        self._fm.log(f"EDIT NIM={nim}")
        return True

    # ── DELETE — O(n) ─────────────────────────────────────────────────────────
    def hapus(self, nim: str) -> Mahasiswa:
        idx = next(
            (i for i, m in enumerate(self._db) if m.nim == nim.strip()), -1
        )
        if idx == -1:
            raise NIMTidakDitemukanError(nim)
        removed = self._db.pop(idx)
        self._simpan()
        self._fm.log(f"HAPUS NIM={nim} nama={removed.nama}")
        return removed

    # ── STATISTIK — O(n) ──────────────────────────────────────────────────────
    def statistik(self) -> dict:
        if not self._db:
            return {}
        ipks  = [m.ipk for m in self._db]
        total = len(ipks)
        avg   = sum(ipks) / total
        jur: Dict[str, int] = {}
        for m in self._db:
            jur[m.jurusan] = jur.get(m.jurusan, 0) + 1
        return {
            "total": total,
            "avg":   round(avg, 2),
            "max":   max(ipks),
            "min":   min(ipks),
            "jurusan": jur,
        }


# ==============================================================================
#  8. HTML — ANTARMUKA WEB (inline CSS + JS, single file)
# ==============================================================================

def buat_html() -> str:
    jurusan_options = "\n".join(
        f'<option value="{j}">{j}</option>' for j in JURUSAN
    )

    # Catatan: kurung kurawal ganda {{ }} di f-string = literal { }
    # Kurung tunggal { } = interpolasi Python
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SIM Mahasiswa</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0f1117;--bg2:#161b27;--bg3:#1e2435;--bg4:#252d42;
  --ac:#7c6af7;--ac2:#a594ff;--ac3:#5548d9;
  --tl:#2dd4bf;--co:#f87171;--am:#fbbf24;--gr:#4ade80;
  --bd:rgba(255,255,255,.07);--bd2:rgba(255,255,255,.13);
  --tx:#e2e8f0;--tx2:#94a3b8;--tx3:#4a5568;
  --r:10px;--rl:14px;
  --fn:'Segoe UI',system-ui,sans-serif;
  --mo:'Cascadia Code','Consolas','Courier New',monospace;
}}
body{{font-family:var(--fn);background:var(--bg);color:var(--tx);font-size:14px;min-height:100vh}}
::-webkit-scrollbar{{width:5px}}::-webkit-scrollbar-thumb{{background:var(--bg4);border-radius:99px}}
.app{{display:flex;height:100vh;overflow:hidden}}
/* SIDEBAR */
.sb{{width:220px;flex-shrink:0;background:var(--bg2);border-right:1px solid var(--bd);display:flex;flex-direction:column;overflow-y:auto}}
.sb-brand{{padding:20px 18px 16px;border-bottom:1px solid var(--bd)}}
.sb-ic{{width:38px;height:38px;background:linear-gradient(135deg,var(--ac),var(--ac3));border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;margin-bottom:10px}}
.sb-t{{font-size:13px;font-weight:600}}
.sb-s{{font-size:11px;color:var(--tx3);margin-top:2px}}
.nav-sec{{font-size:10px;font-weight:600;color:var(--tx3);letter-spacing:.1em;text-transform:uppercase;padding:16px 18px 5px}}
.nav-it{{display:flex;align-items:center;gap:10px;padding:9px 18px;cursor:pointer;font-size:13px;color:var(--tx2);border-left:2px solid transparent;transition:all .15s;user-select:none}}
.nav-it:hover{{color:var(--tx);background:rgba(255,255,255,.03)}}
.nav-it.active{{color:var(--ac2);background:rgba(124,106,247,.1);border-left-color:var(--ac);font-weight:500}}
.sb-ft{{margin-top:auto;padding:14px 18px;border-top:1px solid var(--bd);font-size:11px;color:var(--tx3)}}
.db-badge{{display:inline-flex;align-items:center;gap:5px;background:rgba(45,212,191,.1);border:1px solid rgba(45,212,191,.2);color:var(--tl);font-size:11px;padding:3px 9px;border-radius:99px;margin-top:5px}}
/* MAIN */
.main{{flex:1;display:flex;flex-direction:column;overflow:hidden}}
.topbar{{display:flex;align-items:center;gap:12px;padding:13px 22px;border-bottom:1px solid var(--bd);background:var(--bg2);flex-shrink:0}}
.tb-ti{{font-size:15px;font-weight:600;flex:1}}
.tb-mt{{font-size:12px;color:var(--tx3);font-family:var(--mo)}}
.content{{flex:1;overflow-y:auto;padding:22px}}
/* PANEL */
.panel{{display:none;animation:fadeUp .2s ease}}
.panel.active{{display:block}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
/* STATS */
.sg{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px}}
.sc{{background:var(--bg2);border:1px solid var(--bd);border-radius:var(--rl);padding:14px 16px;position:relative;overflow:hidden}}
.sc::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--cc,var(--ac));border-radius:2px 2px 0 0}}
.sc-ic{{font-size:20px;margin-bottom:8px;color:var(--cc,var(--ac))}}
.sc-lb{{font-size:10px;color:var(--tx3);font-weight:600;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px}}
.sc-v{{font-size:24px;font-weight:700}}
.sc-s{{font-size:11px;color:var(--tx3);margin-top:2px}}
/* CARD */
.card{{background:var(--bg2);border:1px solid var(--bd);border-radius:var(--rl);overflow:hidden}}
.card-hdr{{padding:12px 16px;border-bottom:1px solid var(--bd);font-size:13px;font-weight:500;display:flex;align-items:center;gap:8px;color:var(--tx2)}}
/* TOOLBAR */
.tb{{padding:10px 14px;border-bottom:1px solid var(--bd);display:flex;gap:8px;align-items:center;flex-wrap:wrap;background:var(--bg2)}}
.tb input,.tb select{{height:32px;background:var(--bg3);border:1px solid var(--bd2);border-radius:var(--r);padding:0 10px;font-size:12px;color:var(--tx);font-family:var(--fn);outline:none;transition:border-color .15s}}
.tb input:focus,.tb select:focus{{border-color:var(--ac)}}
.tb input{{flex:1;min-width:150px}}
/* BTN */
.btn{{height:32px;padding:0 13px;border-radius:var(--r);font-size:12px;font-family:var(--fn);cursor:pointer;display:inline-flex;align-items:center;gap:6px;white-space:nowrap;border:1px solid var(--bd2);background:transparent;color:var(--tx2);transition:all .15s;font-weight:500;user-select:none}}
.btn:hover{{background:var(--bg4);color:var(--tx)}}
.btn:active{{transform:scale(.97)}}
.btn-p{{background:var(--ac);color:#fff;border-color:var(--ac)}}
.btn-p:hover{{background:var(--ac2);border-color:var(--ac2);color:#fff}}
.btn-sm{{height:27px;padding:0 9px;font-size:11px}}
.btn-d{{color:var(--co);border-color:rgba(248,113,113,.2)}}
.btn-d:hover{{background:rgba(248,113,113,.1)}}
.btn-t{{color:var(--tl);border-color:rgba(45,212,191,.2)}}
.btn-t:hover{{background:rgba(45,212,191,.1)}}
/* TABLE */
.tw{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
thead th{{text-align:left;padding:9px 14px;font-size:10px;font-weight:700;color:var(--tx3);text-transform:uppercase;letter-spacing:.07em;border-bottom:1px solid var(--bd);background:var(--bg3);white-space:nowrap}}
tbody td{{padding:9px 14px;border-bottom:1px solid var(--bd);vertical-align:middle}}
tbody tr:last-child td{{border-bottom:none}}
tbody tr:hover td{{background:rgba(255,255,255,.02)}}
.nc{{font-family:var(--mo);font-size:12px;color:var(--ac2)}}
/* IPK BAR */
.ib{{display:flex;align-items:center;gap:7px}}
.it{{width:48px;height:4px;background:var(--bg4);border-radius:99px;overflow:hidden}}
.if{{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--ac3),var(--ac2))}}
/* BADGE */
.badge{{display:inline-block;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:500}}
.b-pu{{background:rgba(124,106,247,.15);color:var(--ac2)}}
.b-te{{background:rgba(45,212,191,.12);color:var(--tl)}}
.b-am{{background:rgba(251,191,36,.12);color:var(--am)}}
.b-co{{background:rgba(248,113,113,.12);color:var(--co)}}
.b-gr{{background:rgba(255,255,255,.07);color:var(--tx2)}}
/* FORM */
.fw{{max-width:540px}}
.fg{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}}
.fi{{display:flex;flex-direction:column;gap:4px}}
.fi.full{{grid-column:1/-1}}
.fi label{{font-size:12px;font-weight:500;color:var(--tx2)}}
.fi input,.fi select{{height:36px;background:var(--bg3);border:1px solid var(--bd2);border-radius:var(--r);padding:0 11px;font-size:13px;color:var(--tx);font-family:var(--fn);outline:none;width:100%;transition:border-color .15s,box-shadow .15s}}
.fi input:focus,.fi select:focus{{border-color:var(--ac);box-shadow:0 0 0 3px rgba(124,106,247,.13)}}
.fi input.inv{{border-color:var(--co)}}
.fi input.ok{{border-color:var(--gr)}}
.er{{font-size:11px;color:var(--co);min-height:14px}}
.req{{color:var(--co);margin-left:2px}}
/* ALERT */
.al{{padding:10px 14px;border-radius:var(--r);font-size:13px;margin-bottom:14px;display:none;align-items:center;gap:8px;border:1px solid}}
.al.show{{display:flex}}
.al-ok{{background:rgba(74,222,128,.1);color:var(--gr);border-color:rgba(74,222,128,.25)}}
.al-er{{background:rgba(248,113,113,.1);color:var(--co);border-color:rgba(248,113,113,.25)}}
/* SEARCH */
.mbs{{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}}
.mb{{height:32px;padding:0 13px;border-radius:var(--r);font-size:12px;font-family:var(--fn);cursor:pointer;border:1px solid var(--bd2);background:transparent;color:var(--tx2);font-weight:500;transition:all .15s}}
.mb:hover{{background:var(--bg3)}}
.mb.active{{background:rgba(124,106,247,.15);border-color:var(--ac);color:var(--ac2)}}
.sd{{background:var(--bg3);border:1px solid var(--bd);border-radius:var(--r);padding:10px 13px;font-size:12px;color:var(--tx2);margin-bottom:12px;line-height:1.7}}
.sd b{{color:var(--ac2)}}
.si{{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center}}
.si input,.si select{{height:34px;background:var(--bg3);border:1px solid var(--bd2);border-radius:var(--r);padding:0 10px;font-size:13px;color:var(--tx);font-family:var(--fn);outline:none;transition:border-color .15s}}
.si input:focus,.si select:focus{{border-color:var(--ac)}}
.si input{{flex:1;min-width:160px}}
.rb{{background:var(--bg3);border:1px solid var(--bd);border-radius:var(--rl);padding:14px;min-height:80px;margin-top:12px}}
.rm{{font-size:11px;color:var(--tx3);margin-bottom:10px;font-family:var(--mo)}}
.rc{{background:var(--bg2);border:1px solid var(--bd);border-radius:var(--r);padding:13px;margin-bottom:9px}}
.rc:last-child{{margin-bottom:0}}
.rch{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
.rdg{{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}}
.di{{background:var(--bg3);border-radius:8px;padding:7px 10px}}
.di .dl{{font-size:10px;color:var(--tx3);text-transform:uppercase;letter-spacing:.06em}}
.di .dv{{font-size:13px;font-weight:500;margin-top:2px}}
/* SORT */
.ag{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:12px}}
.ac{{background:var(--bg3);border:1px solid var(--bd);border-radius:var(--r);padding:11px;cursor:pointer;transition:all .15s;user-select:none}}
.ac:hover{{border-color:var(--ac);background:rgba(124,106,247,.05)}}
.ac.sel{{border-color:var(--ac);background:rgba(124,106,247,.1)}}
.ac h4{{font-size:13px;font-weight:600}}
.ac p{{font-size:11px;color:var(--tx3);margin-top:2px}}
.ac-c{{font-size:10px;font-family:var(--mo);color:var(--ac2);margin-top:5px;font-weight:500}}
.sc2{{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center}}
.sc2 select{{height:32px;background:var(--bg3);border:1px solid var(--bd2);border-radius:var(--r);padding:0 9px;font-size:12px;color:var(--tx);font-family:var(--fn);outline:none}}
/* BENCHMARK */
.bw{{margin-top:14px}}
.bt{{font-size:12px;font-weight:600;color:var(--tx2);margin-bottom:10px;text-transform:uppercase;letter-spacing:.06em}}
.br{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.bn{{font-size:12px;color:var(--tx2);width:130px;flex-shrink:0}}
.bw2{{flex:1;height:16px;background:var(--bg4);border-radius:99px;overflow:hidden}}
.bb{{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--ac3),var(--ac));transition:width .6s cubic-bezier(.22,.68,0,1.2)}}
.bb.fast{{background:linear-gradient(90deg,#0f766e,var(--tl))}}
.bti{{font-size:12px;font-family:var(--mo);width:80px;text-align:right}}
/* TC */
.tc-tabs{{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}}
.tc-tab{{height:30px;padding:0 13px;border-radius:var(--r);font-size:12px;font-family:var(--fn);cursor:pointer;border:1px solid var(--bd2);background:transparent;color:var(--tx2);font-weight:500;transition:all .15s}}
.tc-tab:hover{{background:var(--bg3)}}
.tc-tab.active{{background:rgba(124,106,247,.15);border-color:var(--ac);color:var(--ac2)}}
.tc-t{{width:100%;border-collapse:collapse;font-size:12px}}
.tc-t th{{text-align:left;padding:9px 12px;font-size:10px;font-weight:700;color:var(--tx3);text-transform:uppercase;letter-spacing:.07em;border-bottom:1px solid var(--bd);background:var(--bg3)}}
.tc-t td{{padding:9px 12px;border-bottom:1px solid var(--bd)}}
.tc-t tr:last-child td{{border-bottom:none}}
.tc-gd{{color:var(--gr);font-family:var(--mo);font-weight:500}}
.tc-md{{color:var(--am);font-family:var(--mo);font-weight:500}}
.tc-bd{{color:var(--co);font-family:var(--mo);font-weight:500}}
.tc-leg{{display:flex;gap:16px;margin-top:12px;padding:10px 14px;font-size:11px}}
.tc-leg span{{display:flex;align-items:center;gap:5px}}
.dot{{width:8px;height:8px;border-radius:50%;display:inline-block}}
/* MODAL */
.ov{{position:fixed;inset:0;background:rgba(0,0,0,.6);backdrop-filter:blur(4px);display:none;align-items:center;justify-content:center;z-index:100}}
.ov.show{{display:flex}}
.modal{{background:var(--bg2);border:1px solid var(--bd2);border-radius:var(--rl);padding:22px 26px;max-width:350px;width:90%;box-shadow:0 4px 24px rgba(0,0,0,.4);animation:fadeUp .2s ease}}
.modal h3{{font-size:15px;font-weight:600;margin-bottom:7px}}
.modal p{{font-size:13px;color:var(--tx2);margin-bottom:18px;line-height:1.6}}
.modal-act{{display:flex;gap:8px;justify-content:flex-end}}
/* TOAST */
.tw2{{position:fixed;bottom:22px;right:22px;z-index:200;display:flex;flex-direction:column;gap:7px}}
.toast{{background:var(--bg2);border:1px solid var(--bd2);border-radius:var(--r);padding:11px 15px;font-size:13px;color:var(--tx);display:flex;align-items:center;gap:8px;box-shadow:0 4px 16px rgba(0,0,0,.4);animation:tsIn .25s ease;min-width:230px;max-width:320px}}
.toast.tok{{border-left:3px solid var(--gr)}}
.toast.ter{{border-left:3px solid var(--co)}}
@keyframes tsIn{{from{{opacity:0;transform:translateX(16px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes tsOut{{from{{opacity:1}}to{{opacity:0;transform:translateX(16px)}}}}
.empty{{text-align:center;padding:44px;color:var(--tx3)}}
.tbl-ft{{padding:9px 14px;font-size:11px;color:var(--tx3);border-top:1px solid var(--bd)}}
.dg2{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}}
</style>
</head>
<body>
<div class="app">
  <!-- SIDEBAR -->
  <aside class="sb">
    <div class="sb-brand">
      <div class="sb-ic">&#127979;</div>
      <div class="sb-t">SIM Mahasiswa</div>
      <div class="sb-s">Sistem Informasi Akademik</div>
    </div>
    <div class="nav-sec">Data</div>
    <div class="nav-it active" onclick="gP('dashboard',this)"><span>&#128203;</span><span>Dashboard</span></div>
    <div class="nav-it" onclick="gP('daftar',this)"><span>&#128101;</span><span>Daftar Mahasiswa</span></div>
    <div class="nav-it" onclick="gP('tambah',this)"><span>&#10133;</span><span>Tambah Baru</span></div>
    <div class="nav-sec">Algoritma</div>
    <div class="nav-it" onclick="gP('cari',this)"><span>&#128269;</span><span>Pencarian</span></div>
    <div class="nav-it" onclick="gP('sort',this)"><span>&#128260;</span><span>Pengurutan</span></div>
    <div class="nav-it" onclick="gP('tc',this)"><span>&#9201;</span><span>Time Complexity</span></div>
    <div class="sb-ft">
      <div>Data tersimpan otomatis</div>
      <div class="db-badge">&#128190; <span id="sbn">0</span> mahasiswa</div>
    </div>
  </aside>

  <!-- MAIN -->
  <main class="main">
    <div class="topbar">
      <div class="tb-ti" id="pgtit">Dashboard</div>
      <div class="tb-mt" id="pgmt"></div>
    </div>
    <div class="content">

      <!-- DASHBOARD -->
      <div class="panel active" id="panel-dashboard">
        <div class="sg" id="sg"></div>
        <div class="dg2">
          <div class="card">
            <div class="card-hdr">&#128101; Mahasiswa Terbaru</div>
            <div class="tw"><table>
              <thead><tr><th>NIM</th><th>Nama</th><th>IPK</th><th>Status</th></tr></thead>
              <tbody id="tb-rec"></tbody>
            </table></div>
          </div>
          <div class="card">
            <div class="card-hdr">&#128200; Distribusi Jurusan</div>
            <div style="padding:14px 16px" id="jbar"></div>
          </div>
        </div>
      </div>

      <!-- DAFTAR -->
      <div class="panel" id="panel-daftar">
        <div class="card">
          <div class="tb">
            <input type="text" id="tq" placeholder="Cari NIM, nama, jurusan..." oninput="rT()">
            <select id="ts" onchange="rT()">
              <option value="nim">Urut: NIM</option>
              <option value="nama">Urut: Nama</option>
              <option value="ipk">Urut: IPK</option>
              <option value="semester">Urut: Semester</option>
            </select>
            <select id="td" onchange="rT()">
              <option value="asc">&#8593; Naik</option>
              <option value="desc">&#8595; Turun</option>
            </select>
            <button class="btn btn-p" onclick="gTambah()">&#10133; Tambah</button>
            <button class="btn btn-t" onclick="expCSV()">&#8615; CSV</button>
          </div>
          <div class="tw"><table>
            <thead><tr><th>#</th><th>NIM</th><th>Nama</th><th>Jurusan</th><th>Sem</th><th>IPK</th><th>T.Masuk</th><th>Status</th><th>Aksi</th></tr></thead>
            <tbody id="tbm"></tbody>
          </table></div>
          <div id="tbe" class="empty" style="display:none"><div style="font-size:32px;margin-bottom:8px">&#128220;</div>Belum ada data mahasiswa</div>
          <div class="tbl-ft" id="tbf"></div>
        </div>
      </div>

      <!-- TAMBAH / EDIT -->
      <div class="panel" id="panel-tambah">
        <div class="fw">
          <div class="al al-ok" id="alok">&#9989; <span id="alokm"></span></div>
          <div class="al al-er" id="aler">&#10060; <span id="alerm"></span></div>
          <div class="card" style="padding:18px 20px">
            <div class="fg">
              <div class="fi">
                <label>NIM<span class="req">*</span></label>
                <input type="text" id="fnim" placeholder="12345678" maxlength="8" oninput="vf('nim')">
                <span class="er" id="enim"></span>
              </div>
              <div class="fi">
                <label>Tahun Masuk<span class="req">*</span></label>
                <input type="number" id="ftah" placeholder="2022" min="2000" max="2025" oninput="vf('tahun')">
                <span class="er" id="etah"></span>
              </div>
              <div class="fi full">
                <label>Nama Lengkap<span class="req">*</span></label>
                <input type="text" id="fnam" placeholder="Andi Pratama" oninput="vf('nama')">
                <span class="er" id="enam"></span>
              </div>
              <div class="fi">
                <label>Jurusan<span class="req">*</span></label>
                <select id="fjur" onchange="vf('jurusan')">
                  <option value="">-- Pilih Jurusan --</option>
                  {jurusan_options}
                </select>
                <span class="er" id="ejur"></span>
              </div>
              <div class="fi">
                <label>Semester<span class="req">*</span></label>
                <select id="fsem" onchange="vf('semester')">
                  <option value="">-- Pilih --</option>
                  <option>1</option><option>2</option><option>3</option><option>4</option>
                  <option>5</option><option>6</option><option>7</option><option>8</option>
                  <option>9</option><option>10</option><option>11</option><option>12</option>
                </select>
                <span class="er" id="esem"></span>
              </div>
              <div class="fi">
                <label>IPK<span class="req">*</span></label>
                <input type="number" id="fipk" placeholder="3.75" min="0" max="4" step="0.01" oninput="vf('ipk')">
                <span class="er" id="eipk"></span>
              </div>
              <div class="fi">
                <label>Telepon<span class="req">*</span></label>
                <input type="text" id="ftelp" placeholder="081234567890" oninput="vf('telp')">
                <span class="er" id="etelp"></span>
              </div>
              <div class="fi full">
                <label>Email<span class="req">*</span></label>
                <input type="text" id="feml" placeholder="nama@student.ac.id" oninput="vf('email')">
                <span class="er" id="eeml"></span>
              </div>
            </div>
            <div style="display:flex;gap:8px">
              <button class="btn btn-p" id="btsub" onclick="submitForm()">&#128190; Simpan</button>
              <button class="btn" onclick="resetForm()">&#8635; Reset</button>
              <button class="btn" onclick="gP('daftar',null)">Batal</button>
            </div>
          </div>
        </div>
      </div>

      <!-- PENCARIAN -->
      <div class="panel" id="panel-cari">
        <div class="mbs">
          <button class="mb active" id="mb-linear"     onclick="setMode('linear')">Linear Search</button>
          <button class="mb"        id="mb-sequential" onclick="setMode('sequential')">Sequential Search</button>
          <button class="mb"        id="mb-binary"     onclick="setMode('binary')">Binary Search</button>
          <button class="mb"        id="mb-ipk"        onclick="setMode('ipk')">Rentang IPK</button>
        </div>
        <div class="sd" id="sdsc"></div>
        <div class="si" id="sinp"></div>
        <button class="btn btn-p" onclick="doSearch()">&#128269; Cari Sekarang</button>
        <div class="rb" id="rbox">
          <div style="text-align:center;padding:20px;color:var(--tx3)">
            <div style="font-size:28px;margin-bottom:8px">&#128269;</div>Hasil pencarian akan tampil di sini
          </div>
        </div>
      </div>

      <!-- PENGURUTAN -->
      <div class="panel" id="panel-sort">
        <div class="ag">
          <div class="ac sel" onclick="selA(this,'bubble')"><h4>Bubble Sort</h4><p>Swap berdekatan</p><div class="ac-c">O(n&#178;)</div></div>
          <div class="ac"     onclick="selA(this,'insertion')"><h4>Insertion Sort</h4><p>Sisip satu-satu</p><div class="ac-c">O(n&#178;)</div></div>
          <div class="ac"     onclick="selA(this,'selection')"><h4>Selection Sort</h4><p>Pilih minimum</p><div class="ac-c">O(n&#178;)</div></div>
          <div class="ac"     onclick="selA(this,'merge')"><h4>Merge Sort</h4><p>Divide &amp; Conquer</p><div class="ac-c">O(n log n)</div></div>
          <div class="ac"     onclick="selA(this,'shell')"><h4>Shell Sort</h4><p>Gap Knuth</p><div class="ac-c">O(n^1.5)</div></div>
        </div>
        <div class="sc2">
          <select id="sk"><option value="nim">Kunci: NIM</option><option value="nama">Kunci: Nama</option><option value="ipk">Kunci: IPK</option><option value="semester">Kunci: Semester</option><option value="tahun_masuk">Kunci: Tahun Masuk</option></select>
          <select id="sdir"><option value="asc">&#8593; Naik</option><option value="desc">&#8595; Turun</option></select>
          <button class="btn btn-p" onclick="doSort()">&#128260; Urutkan</button>
          <button class="btn btn-t" onclick="doBench()">&#128202; Benchmark</button>
        </div>
        <div id="sres"></div>
        <div id="bwrap" style="display:none">
          <div class="bw">
            <div class="bt">Benchmark &mdash; rata-rata 5 run &bull; n=<span id="bnn">0</span></div>
            <div id="bbars"></div>
          </div>
        </div>
      </div>

      <!-- TIME COMPLEXITY -->
      <div class="panel" id="panel-tc">
        <div class="tc-tabs">
          <button class="tc-tab active" id="tct-crud"   onclick="showTC('crud')">CRUD</button>
          <button class="tc-tab"        id="tct-search" onclick="showTC('search')">Pencarian</button>
          <button class="tc-tab"        id="tct-sort"   onclick="showTC('sort')">Pengurutan</button>
          <button class="tc-tab"        id="tct-io"     onclick="showTC('io')">File I/O</button>
        </div>
        <div class="card">
          <div class="tw" id="tcc"></div>
          <div class="tc-leg">
            <span><span class="dot" style="background:var(--gr)"></span>Efisien</span>
            <span><span class="dot" style="background:var(--am)"></span>Sedang</span>
            <span><span class="dot" style="background:var(--co)"></span>Kurang efisien</span>
          </div>
        </div>
      </div>

    </div>
  </main>
</div>

<!-- MODAL -->
<div class="ov" id="ov">
  <div class="modal">
    <h3 id="mt">Konfirmasi</h3>
    <p  id="mp">Yakin?</p>
    <div class="modal-act">
      <button class="btn" onclick="closeM()">Batal</button>
      <button class="btn btn-d" id="mok">&#128465; Hapus</button>
    </div>
  </div>
</div>

<!-- TOAST -->
<div class="tw2" id="tw2"></div>

<script>
var DB=[],editNim=null,curAlgo='bubble',sMode='linear',mCb=null;
var RX={{
  nim:/^\\d{{8}}$/,
  nama:/^[A-Za-z\\s'..]{{3,50}}$/,
  ipk:/^([0-3]\\.\\d{{1,2}}|4(\\.0{{1,2}})?)$/,
  telp:/^(\\+62|62|0)[0-9]{{9,12}}$/,
  email:/^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$/,
  tahun:/^\\d{{4}}$/
}};
var ERRS={{nim:'Harus 8 digit angka',nama:'Hanya huruf & spasi, 3-50 karakter',ipk:'0.00 s/d 4.00',telp:'Format: 08xx/+62xx, 10-13 digit',email:'Contoh: nama@domain.com',tahun:'Tahun 2000-2025',jurusan:'Pilih jurusan',semester:'Pilih semester'}};

// STATUS
function status(ipk){{
  if(ipk>=3.5)return{{l:'Cumlaude',c:'b-pu'}};
  if(ipk>=3.0)return{{l:'Sangat Memuaskan',c:'b-te'}};
  if(ipk>=2.5)return{{l:'Memuaskan',c:'b-am'}};
  if(ipk>=2.0)return{{l:'Cukup',c:'b-gr'}};
  return{{l:'Perlu Perhatian',c:'b-co'}};
}}

// IPK BAR
function ib(ipk){{
  return `<div class="ib"><div class="it"><div class="if" style="width:${{(ipk/4*100).toFixed(0)}}%"></div></div>${{parseFloat(ipk).toFixed(2)}}</div>`;
}}

// SORTING
function kv(m,k){{var v=m[k];return typeof v==='string'?v.toLowerCase():v;}}
var Sort={{
  bubble:function(a,k,asc){{
    var arr=[...a],n=arr.length;
    for(var i=0;i<n;i++){{var sw=false;for(var j=0;j<n-i-1;j++){{if(asc?kv(arr[j],k)>kv(arr[j+1],k):kv(arr[j],k)<kv(arr[j+1],k)){{var t=arr[j];arr[j]=arr[j+1];arr[j+1]=t;sw=true;}}}}if(!sw)break;}}return arr;
  }},
  insertion:function(a,k,asc){{
    var arr=[...a];
    for(var i=1;i<arr.length;i++){{var cur=arr[i],vc=kv(cur,k),j=i-1;while(j>=0&&(asc?kv(arr[j],k)>vc:kv(arr[j],k)<vc)){{arr[j+1]=arr[j];j--;}}arr[j+1]=cur;}}return arr;
  }},
  selection:function(a,k,asc){{
    var arr=[...a],n=arr.length;
    for(var i=0;i<n;i++){{var idx=i;for(var j=i+1;j<n;j++)if(asc?kv(arr[j],k)<kv(arr[idx],k):kv(arr[j],k)>kv(arr[idx],k))idx=j;if(idx!==i){{var t=arr[i];arr[i]=arr[idx];arr[idx]=t;}}}}return arr;
  }},
  merge:function(a,k,asc){{
    if(a.length<=1)return[...a];
    var mid=a.length>>1,L=Sort.merge(a.slice(0,mid),k,asc),R=Sort.merge(a.slice(mid),k,asc),res=[],i=0,j=0;
    while(i<L.length&&j<R.length)(asc?kv(L[i],k)<=kv(R[j],k):kv(L[i],k)>=kv(R[j],k))?res.push(L[i++]):res.push(R[j++]);
    return res.concat(L.slice(i)).concat(R.slice(j));
  }},
  shell:function(a,k,asc){{
    var arr=[...a],n=arr.length,gap=1;
    while(gap<Math.floor(n/3))gap=gap*3+1;
    while(gap>=1){{for(var i=gap;i<n;i++){{var tmp=arr[i],vt=kv(tmp,k),j=i;while(j>=gap&&(asc?kv(arr[j-gap],k)>vt:kv(arr[j-gap],k)<vt)){{arr[j]=arr[j-gap];j-=gap;}}arr[j]=tmp;}}gap=Math.floor(gap/3);}}return arr;
  }}
}};

// SEARCHING
var Search={{
  linear:function(arr,q,field){{var ql=q.toLowerCase().trim();return arr.filter(function(m){{return String(m[field]||'').toLowerCase().indexOf(ql)>=0;}});}},
  sequential:function(arr,nim){{var t=nim.trim();for(var i=0;i<arr.length;i++)if(arr[i].nim===t)return arr[i];return null;}},
  binary:function(arr,nim){{
    var sorted=Sort.merge(arr,'nim',true),lo=0,hi=sorted.length-1,t=nim.trim();
    while(lo<=hi){{var mid=(lo+hi)>>1;if(sorted[mid].nim===t)return sorted[mid];sorted[mid].nim<t?lo=mid+1:hi=mid-1;}}return null;
  }},
  byIPK:function(arr,mn,mx){{return arr.filter(function(m){{return m.ipk>=mn&&m.ipk<=mx;}});}}
}};

// API CALLS
async function apiGet(){{var r=await fetch('/api/data');DB=await r.json();updMeta();}}
async function apiPost(d){{var r=await fetch('/api/data',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(d)}});return await r.json();}}
async function apiPut(nim,d){{var r=await fetch('/api/data/'+nim,{{method:'PUT',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(d)}});return await r.json();}}
async function apiDel(nim){{var r=await fetch('/api/data/'+nim,{{method:'DELETE'}});return await r.json();}}

function updMeta(){{
  document.getElementById('sbn').textContent=DB.length;
  document.getElementById('pgmt').textContent=DB.length+' mahasiswa';
}}

// PANEL
function gP(id,navEl){{
  document.querySelectorAll('.panel').forEach(function(p){{p.classList.remove('active');}});
  document.getElementById('panel-'+id).classList.add('active');
  document.querySelectorAll('.nav-it').forEach(function(n){{n.classList.remove('active');}});
  if(navEl)navEl.classList.add('active');
  var titles={{dashboard:'Dashboard',daftar:'Daftar Mahasiswa',tambah:editNim?'Edit Mahasiswa':'Tambah Mahasiswa',cari:'Pencarian Data',sort:'Pengurutan Data',tc:'Time Complexity'}};
  document.getElementById('pgtit').textContent=titles[id]||id;
  if(id==='dashboard')rDash();
  if(id==='daftar')rT();
  if(id==='tambah'&&!editNim)resetForm();
  if(id==='cari')initSearch();
  if(id==='tc')showTC('crud');
}}

// TOAST
function toast(type,msg){{
  var w=document.getElementById('tw2'),el=document.createElement('div');
  el.className='toast '+(type==='ok'?'tok':'ter');
  el.innerHTML=(type==='ok'?'&#9989;':'&#10060;')+' '+msg;
  w.appendChild(el);
  setTimeout(function(){{el.style.animation='tsOut .25s ease forwards';setTimeout(function(){{el.remove();}},250);}},3000);
}}

// MODAL
function openM(title,msg,cb){{
  document.getElementById('mt').textContent=title;
  document.getElementById('mp').textContent=msg;
  document.getElementById('ov').classList.add('show');
  mCb=cb;
  document.getElementById('mok').onclick=function(){{if(mCb)mCb();closeM();}};
}}
function closeM(){{document.getElementById('ov').classList.remove('show');}}

// DASHBOARD
function rDash(){{
  if(!DB.length){{document.getElementById('sg').innerHTML='<div style="grid-column:1/-1;color:var(--tx3);padding:20px">Belum ada data.</div>';return;}}
  var ipks=DB.map(function(m){{return m.ipk;}}),avg=(ipks.reduce(function(a,b){{return a+b;}},0)/ipks.length).toFixed(2);
  var jur={{}};DB.forEach(function(m){{jur[m.jurusan]=(jur[m.jurusan]||0)+1;}});
  document.getElementById('sg').innerHTML=
    '<div class="sc" style="--cc:var(--ac)"><div class="sc-ic">&#128101;</div><div class="sc-lb">Total Mahasiswa</div><div class="sc-v">'+DB.length+'</div><div class="sc-s">terdaftar</div></div>'+
    '<div class="sc" style="--cc:var(--tl)"><div class="sc-ic" style="color:var(--tl)">&#128200;</div><div class="sc-lb">IPK Rata-rata</div><div class="sc-v">'+avg+'</div><div class="sc-s">dari 4.00</div></div>'+
    '<div class="sc" style="--cc:var(--am)"><div class="sc-ic" style="color:var(--am)">&#127942;</div><div class="sc-lb">IPK Tertinggi</div><div class="sc-v">'+Math.max.apply(null,ipks).toFixed(2)+'</div><div class="sc-s">terbaik</div></div>'+
    '<div class="sc" style="--cc:var(--co)"><div class="sc-ic" style="color:var(--co)">&#127979;</div><div class="sc-lb">Program Studi</div><div class="sc-v">'+Object.keys(jur).length+'</div><div class="sc-s">jurusan</div></div>';
  var recent=DB.slice(-5).reverse();
  document.getElementById('tb-rec').innerHTML=recent.map(function(m){{var st=status(m.ipk);return '<tr><td class="nc">'+m.nim+'</td><td style="font-weight:500">'+m.nama+'</td><td>'+ib(m.ipk)+'</td><td><span class="badge '+st.c+'">'+st.l+'</span></td></tr>';}}).join('');
  var maxJ=Math.max.apply(null,Object.values(jur));
  document.getElementById('jbar').innerHTML=Object.entries(jur).sort(function(a,b){{return b[1]-a[1];}}).slice(0,7).map(function(e){{
    var j=e[0],n=e[1];
    return '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px"><div style="font-size:11px;color:var(--tx3);width:115px;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+j+'</div><div style="flex:1;height:7px;background:var(--bg4);border-radius:99px;overflow:hidden"><div style="height:100%;width:'+(n/maxJ*100).toFixed(0)+'%;background:linear-gradient(90deg,var(--ac3),var(--ac2));border-radius:99px"></div></div><div style="font-size:12px;font-family:var(--mo);color:var(--tx2);width:20px;text-align:right">'+n+'</div></div>';
  }}).join('');
}}

// TABLE
function rT(){{
  var q=(document.getElementById('tq').value||'').toLowerCase();
  var k=document.getElementById('ts').value,asc=document.getElementById('td').value==='asc';
  var data=q?DB.filter(function(m){{return(m.nim+m.nama+m.jurusan+m.email).toLowerCase().indexOf(q)>=0;}}):DB.slice();
  data=Sort.merge(data,k,asc);
  var tbody=document.getElementById('tbm'),empty=document.getElementById('tbe');
  if(!data.length){{tbody.innerHTML='';empty.style.display='block';document.getElementById('tbf').textContent='';return;}}
  empty.style.display='none';
  document.getElementById('tbf').textContent='Menampilkan '+data.length+' dari '+DB.length+' mahasiswa';
  tbody.innerHTML=data.map(function(m,i){{
    var st=status(m.ipk);
    return '<tr><td style="color:var(--tx3)">'+(i+1)+'</td><td class="nc">'+m.nim+'</td><td style="font-weight:500">'+m.nama+'</td><td style="color:var(--tx2)">'+m.jurusan+'</td><td style="text-align:center">'+m.semester+'</td><td>'+ib(m.ipk)+'</td><td style="font-family:var(--mo);color:var(--tx3)">'+m.tahun_masuk+'</td><td><span class="badge '+st.c+'">'+st.l+'</span></td><td><div style="display:flex;gap:4px"><button class="btn btn-sm" onclick="editM(&quot;'+m.nim+'&quot;)">&#9998;</button><button class="btn btn-sm btn-d" onclick="hapus(&quot;'+m.nim+'&quot;)">&#128465;</button></div></td></tr>';
  }}).join('');
}}

// FORM VALIDATION
function vf(field){{
  var map={{
    nim    :{{el:'fnim', er:'enim', fn:function(v){{return RX.nim.test(v.trim());}}}},
    nama   :{{el:'fnam', er:'enam', fn:function(v){{return RX.nama.test(v.trim());}}}},
    ipk    :{{el:'fipk', er:'eipk', fn:function(v){{var n=parseFloat(v);return RX.ipk.test(v.trim())&&!isNaN(n)&&n>=0&&n<=4;}}}},
    telp   :{{el:'ftelp',er:'etelp',fn:function(v){{return RX.telp.test(v.trim());}}}},
    email  :{{el:'feml', er:'eeml', fn:function(v){{return RX.email.test(v.trim());}}}},
    tahun  :{{el:'ftah', er:'etah', fn:function(v){{var n=parseInt(v);return RX.tahun.test(v.trim())&&n>=2000&&n<=2025;}}}},
    jurusan:{{el:'fjur', er:'ejur', fn:function(v){{return v.trim()!=='';}}}},
    semester:{{el:'fsem',er:'esem', fn:function(v){{return v.trim()!=='';}}}}
  }};
  var r=map[field];if(!r)return true;
  var val=document.getElementById(r.el).value,ok=r.fn(val),inp=document.getElementById(r.el);
  if(inp.type!=='select-one'){{inp.classList.toggle('ok',ok&&val.trim()!=='');inp.classList.toggle('inv',!ok&&val.trim()!=='');}}
  document.getElementById(r.er).textContent=ok?'':(ERRS[field]||'Tidak valid');
  return ok;
}}
function valAll(){{return['nim','nama','ipk','telp','email','tahun','jurusan','semester'].every(function(f){{return vf(f);}});}}

async function submitForm(){{
  if(!valAll()){{toast('err','Perbaiki input yang tidak valid.');return;}}
  var data={{
    nim:document.getElementById('fnim').value.trim(),
    nama:document.getElementById('fnam').value.trim(),
    jurusan:document.getElementById('fjur').value,
    semester:parseInt(document.getElementById('fsem').value),
    ipk:parseFloat(document.getElementById('fipk').value),
    tahun_masuk:parseInt(document.getElementById('ftah').value),
    telepon:document.getElementById('ftelp').value.trim(),
    email:document.getElementById('feml').value.trim().toLowerCase()
  }};
  try{{
    var res;
    if(editNim){{
      res=await apiPut(editNim,data);
      if(res.ok){{toast('ok','Data berhasil diperbarui!');await apiGet();editNim=null;document.getElementById('fnim').disabled=false;document.getElementById('btsub').innerHTML='&#128190; Simpan';gP('daftar',null);}}
      else toast('err',res.error||'Gagal update.');
    }}else{{
      res=await apiPost(data);
      if(res.ok){{toast('ok','Mahasiswa '+data.nama+' ditambahkan!');await apiGet();resetForm();}}
      else toast('err',res.error||'Gagal menyimpan.');
    }}
  }}catch(e){{toast('err','Error: '+e.message);}}
}}

function resetForm(){{
  ['fnim','fnam','fipk','ftelp','feml','ftah'].forEach(function(id){{var el=document.getElementById(id);el.value='';el.classList.remove('ok','inv');el.disabled=false;}});
  ['fjur','fsem'].forEach(function(id){{document.getElementById(id).selectedIndex=0;}});
  ['enim','enam','eipk','etelp','eeml','etah','ejur','esem'].forEach(function(id){{document.getElementById(id).textContent='';}});
  ['alok','aler'].forEach(function(id){{document.getElementById(id).classList.remove('show');}});
  editNim=null;document.getElementById('btsub').innerHTML='&#128190; Simpan';
}}
function gTambah(){{editNim=null;resetForm();gP('tambah',null);}}
function editM(nim){{
  var m=DB.find(function(x){{return x.nim===nim;}});if(!m)return;
  editNim=nim;
  document.getElementById('fnim').value=m.nim;document.getElementById('fnim').disabled=true;
  document.getElementById('fnam').value=m.nama;document.getElementById('fjur').value=m.jurusan;
  document.getElementById('fsem').value=m.semester;document.getElementById('fipk').value=m.ipk;
  document.getElementById('ftah').value=m.tahun_masuk;document.getElementById('ftelp').value=m.telepon;
  document.getElementById('feml').value=m.email;
  document.getElementById('btsub').innerHTML='&#128190; Update';
  gP('tambah',null);
}}
async function hapus(nim){{
  var m=DB.find(function(x){{return x.nim===nim;}});if(!m)return;
  openM('Hapus Mahasiswa','Yakin hapus '+m.nama+' ('+nim+')? Tidak bisa dibatalkan.',async function(){{
    var res=await apiDel(nim);
    if(res.ok){{toast('ok','Mahasiswa '+m.nama+' dihapus.');await apiGet();rT();rDash();}}
    else toast('err',res.error||'Gagal hapus.');
  }});
}}

// CSV EXPORT
function expCSV(){{
  var h='NIM,Nama,Jurusan,Semester,IPK,Tahun Masuk,Telepon,Email\\n';
  var rows=DB.map(function(m){{return m.nim+','+m.nama+','+m.jurusan+','+m.semester+','+parseFloat(m.ipk).toFixed(2)+','+m.tahun_masuk+','+m.telepon+','+m.email;}}).join('\\n');
  var b=new Blob([h+rows],{{type:'text/csv;charset=utf-8;'}});
  var a=document.createElement('a');a.href=URL.createObjectURL(b);
  a.download='mahasiswa_'+new Date().toISOString().slice(0,10)+'.csv';a.click();URL.revokeObjectURL(a.href);
  toast('ok','Data diekspor ke CSV!');
}}

// PENCARIAN
var sDescs={{
  linear    :'<b>Linear Search</b> &mdash; menelusuri semua data dari awal ke akhir. Partial match. Urutan bebas.<br><b>Time Complexity: O(n)</b> &mdash; Best O(1) | Worst O(n)',
  sequential:'<b>Sequential Search</b> &mdash; exact match NIM satu per satu. Tidak butuh urutan.<br><b>Time Complexity: O(n)</b> &mdash; Best O(1) | Worst O(n)',
  binary    :'<b>Binary Search</b> &mdash; bagi dua setiap langkah. Data diurutkan Merge Sort dulu.<br><b>Time Complexity: O(log n)</b> setelah sort O(n log n)',
  ipk       :'<b>Rentang IPK</b> &mdash; filter linear berdasarkan rentang nilai IPK.<br><b>Time Complexity: O(n)</b>',
}};
var sInputs={{
  linear    :'<input type="text" id="sq" placeholder="Kata kunci..."><select id="sf"><option value="nama">Cari: Nama</option><option value="jurusan">Cari: Jurusan</option><option value="email">Cari: Email</option><option value="nim">Cari: NIM</option></select>',
  sequential:'<input type="text" id="sn" placeholder="NIM (8 digit)" maxlength="8">',
  binary    :'<input type="text" id="sn2" placeholder="NIM (8 digit)" maxlength="8">',
  ipk       :'<input type="number" id="smn" placeholder="IPK min" min="0" max="4" step="0.01" style="max-width:140px"><input type="number" id="smx" placeholder="IPK max" min="0" max="4" step="0.01" style="max-width:140px">',
}};
function initSearch(){{setMode('linear');}}
function setMode(m){{
  sMode=m;
  document.querySelectorAll('.mb').forEach(function(b){{b.classList.remove('active');}});
  document.getElementById('mb-'+m).classList.add('active');
  document.getElementById('sdsc').innerHTML=sDescs[m];
  document.getElementById('sinp').innerHTML=sInputs[m];
  document.getElementById('rbox').innerHTML='<div style="text-align:center;padding:20px;color:var(--tx3)"><div style="font-size:28px;margin-bottom:8px">&#128269;</div>Hasil pencarian akan tampil di sini</div>';
}}
function doSearch(){{
  var t0=performance.now(),found=[];
  if(sMode==='linear'){{var q=document.getElementById('sq').value,f=document.getElementById('sf').value;if(!q.trim()){{toast('err','Isi kata kunci!');return;}}found=Search.linear(DB,q,f);}}
  else if(sMode==='sequential'){{var nim=document.getElementById('sn').value;if(!RX.nim.test(nim.trim())){{toast('err','NIM harus 8 digit.');return;}}var r=Search.sequential(DB,nim);found=r?[r]:[];}}
  else if(sMode==='binary'){{var nim=document.getElementById('sn2').value;if(!RX.nim.test(nim.trim())){{toast('err','NIM harus 8 digit.');return;}}var r=Search.binary(DB,nim);found=r?[r]:[];}}
  else{{var mn=parseFloat(document.getElementById('smn').value)||0,mx=parseFloat(document.getElementById('smx').value)||4;found=Search.byIPK(DB,mn,mx);}}
  var ms=(performance.now()-t0).toFixed(3);rRes(found,ms);
}}
function rRes(found,ms){{
  var box=document.getElementById('rbox');
  if(!found.length){{box.innerHTML='<div class="rm">Waktu: '+ms+' ms | n='+DB.length+'</div><div style="text-align:center;padding:24px;color:var(--tx3)"><div style="font-size:28px;margin-bottom:8px">&#128533;</div>Tidak ditemukan</div>';return;}}
  box.innerHTML='<div class="rm">Ditemukan: <b style="color:var(--ac2)">'+found.length+'</b> | Waktu: '+ms+' ms | n='+DB.length+'</div>'+
  found.map(function(m){{
    var st=status(m.ipk);
    return '<div class="rc"><div class="rch"><div style="width:36px;height:36px;border-radius:10px;background:rgba(124,106,247,.15);display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:var(--ac2)">'+m.nama.charAt(0)+'</div><div><div style="font-weight:600">'+m.nama+'</div><div style="font-size:12px;color:var(--tx3);font-family:var(--mo)">'+m.nim+'</div></div><div style="margin-left:auto"><span class="badge '+st.c+'">'+st.l+'</span></div></div>'+
    '<div class="rdg"><div class="di"><div class="dl">Jurusan</div><div class="dv">'+m.jurusan+'</div></div><div class="di"><div class="dl">Semester</div><div class="dv">'+m.semester+'</div></div><div class="di"><div class="dl">IPK</div><div class="dv">'+parseFloat(m.ipk).toFixed(2)+'</div></div><div class="di"><div class="dl">Tahun</div><div class="dv">'+m.tahun_masuk+'</div></div><div class="di"><div class="dl">Telepon</div><div class="dv" style="font-family:var(--mo)">'+m.telepon+'</div></div><div class="di"><div class="dl">Email</div><div class="dv">'+m.email+'</div></div></div></div>';
  }}).join('');
}}

// SORTING UI
var sNames={{bubble:'Bubble Sort',insertion:'Insertion Sort',selection:'Selection Sort',merge:'Merge Sort',shell:'Shell Sort'}};
var sCmp={{bubble:'O(n&#178;)',insertion:'O(n&#178;)',selection:'O(n&#178;)',merge:'O(n log n)',shell:'O(n^1.5)'}};
function selA(el,algo){{document.querySelectorAll('.ac').forEach(function(c){{c.classList.remove('sel');}});el.classList.add('sel');curAlgo=algo;}}
function doSort(){{
  var k=document.getElementById('sk').value,asc=document.getElementById('sdir').value==='asc';
  var t0=performance.now(),sorted=Sort[curAlgo](DB.slice(),k,asc),ms=(performance.now()-t0).toFixed(3);
  document.getElementById('bwrap').style.display='none';
  document.getElementById('sres').innerHTML=
    '<div style="font-size:12px;color:var(--tx2);margin-bottom:10px;display:flex;gap:12px;flex-wrap:wrap">'+
    '<span>&#128260; '+sNames[curAlgo]+'</span>'+
    '<span style="color:var(--tx3)">Kunci: <b style="color:var(--ac2)">'+k+'</b></span>'+
    '<span style="color:var(--tx3)">Complexity: <b style="color:var(--am);font-family:var(--mo)">'+sCmp[curAlgo]+'</b></span>'+
    '<span style="color:var(--tx3)">Waktu: <b style="color:var(--gr);font-family:var(--mo)">'+ms+' ms</b></span></div>'+
    '<div class="card"><div class="tw"><table><thead><tr><th>#</th><th>NIM</th><th>Nama</th><th>Jurusan</th><th>Sem</th><th>IPK</th></tr></thead><tbody>'+
    sorted.map(function(m,i){{return '<tr><td style="color:var(--tx3)">'+(i+1)+'</td><td class="nc">'+m.nim+'</td><td style="font-weight:500">'+m.nama+'</td><td style="color:var(--tx2)">'+m.jurusan+'</td><td style="text-align:center">'+m.semester+'</td><td>'+parseFloat(m.ipk).toFixed(2)+'</td></tr>';}}).join('')+
    '</tbody></table></div></div>';
}}
function doBench(){{
  document.getElementById('sres').innerHTML='';
  var k=document.getElementById('sk').value,asc=document.getElementById('sdir').value==='asc';
  var order=['bubble','insertion','selection','shell','merge'],res={{}};
  order.forEach(function(algo){{
    var runs=[];for(var i=0;i<6;i++){{var t0=performance.now();Sort[algo](DB.slice(),k,asc);runs.push(performance.now()-t0);}}
    res[algo]=runs.reduce(function(a,b){{return a+b;}},0)/runs.length;
  }});
  var mx=Math.max.apply(null,Object.values(res));
  document.getElementById('bnn').textContent=DB.length;
  document.getElementById('bbars').innerHTML=order.map(function(a){{
    var ms=res[a],pct=(ms/mx*100).toFixed(0),fast=a==='merge'||a==='shell';
    return '<div class="br"><div class="bn">'+sNames[a]+'</div><div class="bw2"><div class="bb'+(fast?' fast':'')+'" style="width:'+pct+'%"></div></div><div class="bti">'+ms.toFixed(3)+' ms</div></div>';
  }}).join('');
  document.getElementById('bwrap').style.display='block';
}}

// TIME COMPLEXITY
var TCD={{
  crud  :{{cols:['Operasi','Best','Average','Worst','Space'],rows:[['Tambah','O(n)','O(n)','O(n)','O(1)'],['Lihat semua','O(1)','O(1)','O(1)','O(n)'],['Cari NIM','O(1)','O(n)','O(n)','O(1)'],['Edit data','O(1)','O(n)','O(n)','O(1)'],['Hapus data','O(1)','O(n)','O(n)','O(1)'],['Statistik','O(n)','O(n)','O(n)','O(1)']]}},
  search:{{cols:['Algoritma','Best','Average','Worst','Keterangan'],rows:[['Linear Search','O(1)','O(n)','O(n)','Partial, bebas urutan'],['Sequential Search','O(1)','O(n)','O(n)','Exact NIM, bebas'],['Binary Search','O(1)','O(log n)','O(log n)','Data HARUS terurut'],['+ Merge Sort (prep)','O(n log n)','O(n log n)','O(n log n)','Sort sebelum binary'],['Rentang IPK','O(n)','O(n)','O(n)','Filter range']]}},
  sort  :{{cols:['Algoritma','Best','Average','Worst','Space'],rows:[['Bubble Sort','O(n)','O(n&#178;)','O(n&#178;)','O(1)'],['Insertion Sort','O(n)','O(n&#178;)','O(n&#178;)','O(1)'],['Selection Sort','O(n&#178;)','O(n&#178;)','O(n&#178;)','O(1)'],['Merge Sort','O(n log n)','O(n log n)','O(n log n)','O(n)'],['Shell Sort','O(n log n)','O(n^1.5)','O(n&#178;)','O(1)']]}},
  io    :{{cols:['Operasi','Best','Average','Worst','Keterangan'],rows:[['Simpan JSON','O(n)','O(n)','O(n)','Serialize'],['Muat JSON','O(n)','O(n)','O(n)','Parse'],['Ekspor CSV','O(n)','O(n)','O(n)','Build string'],['Validasi Regex','O(m)','O(m)','O(m)','m=panjang input'],['Tulis log','O(1)','O(1)','O(1)','Append']]}}
}};
function tcC(v){{
  if(!v.startsWith('O('))return'';
  if(v.indexOf('n&#178;')>=0||v.indexOf('n²')>=0)return'tc-bd';
  if(v==='O(1)'||v.indexOf('log n')>=0)return'tc-gd';
  return'tc-md';
}}
function showTC(tab){{
  document.querySelectorAll('.tc-tab').forEach(function(t){{t.classList.remove('active');}});
  document.getElementById('tct-'+tab).classList.add('active');
  var d=TCD[tab];
  document.getElementById('tcc').innerHTML='<table class="tc-t"><thead><tr>'+d.cols.map(function(c){{return'<th>'+c+'</th>';}}).join('')+'</tr></thead><tbody>'+
    d.rows.map(function(row){{return'<tr>'+row.map(function(cell,ci){{return'<td class="'+(ci>=1&&ci<=3?tcC(cell):'')+'">'+cell+'</td>';}}).join('')+'</tr>';}}).join('')+
  '</tbody></table>';
}}

// INIT
(async function(){{
  await apiGet();
  rDash();
}})();
</script>
</body>
</html>"""


# ==============================================================================
#  9. HTTP SERVER + REST API
# ==============================================================================

# Instance global manager
manager = ManagerMahasiswa()


class Handler(http.server.BaseHTTPRequestHandler):
    """
    Mini REST API server.
    GET  /           → halaman HTML
    GET  /api/data   → JSON semua mahasiswa
    POST /api/data   → tambah mahasiswa
    PUT  /api/data/<nim> → edit
    DELETE /api/data/<nim> → hapus
    """

    def log_message(self, fmt, *args):
        pass  # Suppress log agar terminal bersih

    def _json(self, data, code: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html: str):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        n   = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n).decode("utf-8") if n else "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _nim_from_path(self) -> str:
        parts = self.path.strip("/").split("/")
        return parts[-1] if len(parts) >= 3 else ""

    # ── GET ───────────────────────────────────────────────────────────────────
    def do_GET(self):
        try:
            if self.path in ("/", "/index.html"):
                self._html(buat_html())
            elif self.path == "/api/data":
                self._json([m.ke_dict() for m in manager.semua()])
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    # ── POST (tambah) ─────────────────────────────────────────────────────────
    def do_POST(self):
        try:
            if self.path != "/api/data":
                self.send_response(404); self.end_headers(); return

            p = self._body()
            try:
                # Validasi server-side (Try-Catch + Custom Exception)
                if not Validator.nim(str(p.get("nim", ""))):
                    raise InputTidakValidError("NIM", "Harus 8 digit angka.")
                if not Validator.nama(str(p.get("nama", ""))):
                    raise InputTidakValidError("Nama", "Hanya huruf/spasi, 3-50 karakter.")
                if not Validator.ipk(str(p.get("ipk", ""))):
                    raise InputTidakValidError("IPK", "Antara 0.00 dan 4.00.")
                if not Validator.telepon(str(p.get("telepon", ""))):
                    raise InputTidakValidError("Telepon", "Format tidak valid.")
                if not Validator.email(str(p.get("email", ""))):
                    raise InputTidakValidError("Email", "Format tidak valid.")
                if not Validator.tahun(str(p.get("tahun_masuk", ""))):
                    raise InputTidakValidError("Tahun Masuk", f"{TAHUN_MIN}-{TAHUN_MAX}.")
                if not Validator.jurusan(str(p.get("jurusan", ""))):
                    raise InputTidakValidError("Jurusan", "Pilih dari daftar.")
                if not Validator.semester(p.get("semester", "")):
                    raise InputTidakValidError("Semester", "Antara 1 dan 12.")

                mhs = Mahasiswa(
                    nim         = p["nim"],
                    nama        = p["nama"],
                    jurusan     = p["jurusan"],
                    semester    = p["semester"],
                    ipk         = p["ipk"],
                    tahun_masuk = p["tahun_masuk"],
                    telepon     = p["telepon"],
                    email       = p["email"],
                )
                manager.tambah(mhs)
                self._json({"ok": True})

            except (NIMDuplikatError, InputTidakValidError, AppException) as e:
                self._json({"ok": False, "error": str(e)})

        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    # ── PUT (edit) ────────────────────────────────────────────────────────────
    def do_PUT(self):
        try:
            nim = self._nim_from_path()
            p   = self._body()
            try:
                manager.edit(nim, p)
                self._json({"ok": True})
            except (NIMTidakDitemukanError, InputTidakValidError, AppException) as e:
                self._json({"ok": False, "error": str(e)})
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    # ── DELETE (hapus) ────────────────────────────────────────────────────────
    def do_DELETE(self):
        try:
            nim = self._nim_from_path()
            try:
                manager.hapus(nim)
                self._json({"ok": True})
            except (NIMTidakDitemukanError, AppException) as e:
                self._json({"ok": False, "error": str(e)})
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    # ── OPTIONS (CORS) ────────────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ==============================================================================
#  10. ENTRY POINT
# ==============================================================================

def muat_data_demo():
    """Tambahkan 10 data mahasiswa demo jika database kosong."""
    demo = [
        dict(nim="22410001", nama="Andi Pratama",    jurusan="Teknik Informatika", semester=6,  ipk=3.75, tahun_masuk=2022, telepon="081234567890", email="andi@student.ac.id"),
        dict(nim="22410002", nama="Budi Santoso",    jurusan="Sistem Informasi",   semester=6,  ipk=3.45, tahun_masuk=2022, telepon="082345678901", email="budi@student.ac.id"),
        dict(nim="22410003", nama="Citra Dewi",      jurusan="Teknik Informatika", semester=6,  ipk=3.90, tahun_masuk=2022, telepon="083456789012", email="citra@student.ac.id"),
        dict(nim="21310001", nama="Dodi Firmansyah", jurusan="Teknik Elektro",     semester=8,  ipk=2.80, tahun_masuk=2021, telepon="084567890123", email="dodi@student.ac.id"),
        dict(nim="21310002", nama="Eka Putri",       jurusan="Manajemen",          semester=8,  ipk=3.20, tahun_masuk=2021, telepon="085678901234", email="eka@student.ac.id"),
        dict(nim="20210001", nama="Fajar Nugroho",   jurusan="Akuntansi",          semester=10, ipk=3.55, tahun_masuk=2020, telepon="086789012345", email="fajar@student.ac.id"),
        dict(nim="20210002", nama="Gita Rahayu",     jurusan="Psikologi",          semester=10, ipk=3.80, tahun_masuk=2020, telepon="087890123456", email="gita@student.ac.id"),
        dict(nim="23510001", nama="Hendra Wijaya",   jurusan="Teknik Mesin",       semester=4,  ipk=2.95, tahun_masuk=2023, telepon="088901234567", email="hendra@student.ac.id"),
        dict(nim="23510002", nama="Indah Lestari",   jurusan="Hukum",              semester=4,  ipk=3.65, tahun_masuk=2023, telepon="089012345678", email="indah@student.ac.id"),
        dict(nim="24610001", nama="Joko Susilo",     jurusan="Farmasi",            semester=2,  ipk=3.15, tahun_masuk=2024, telepon="081123456789", email="joko@student.ac.id"),
    ]
    loaded = 0
    for d in demo:
        try:
            manager.tambah(Mahasiswa(**d))
            loaded += 1
        except AppException:
            pass
    if loaded:
        print(f"  ✓ {loaded} data demo dimuat.")


def main():
    url = f"http://localhost:{PORT}"

    # Muat demo jika kosong
    if manager.jumlah() == 0:
        muat_data_demo()

    # Jalankan server di background thread
    server = http.server.HTTPServer(("", PORT), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    # Info terminal
    print("=" * 56)
    print("  SISTEM MANAJEMEN DATA MAHASISWA")
    print("=" * 56)
    print(f"  Server aktif : {url}")
    print(f"  File data    : {FILE_DATA}")
    print(f"  File log     : {FILE_LOG}")
    print(f"  Mahasiswa    : {manager.jumlah()} terdaftar")
    print("=" * 56)
    print("  Browser membuka otomatis dalam 1 detik...")
    print("  Tekan Ctrl+C untuk menghentikan server.")
    print("=" * 56)

    # Buka browser (delay agar server siap)
    def buka():
        time.sleep(0.9)
        webbrowser.open(url)

    threading.Thread(target=buka, daemon=True).start()

    # Tunggu Ctrl+C
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n  Server dihentikan. Data tersimpan di '{FILE_DATA}'.")
        server.shutdown()


if __name__ == "__main__":
    main()

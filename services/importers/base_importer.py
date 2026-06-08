"""
Base importer class + shared utilities for all Excel importers.
"""
import os
from datetime import datetime, date
from typing import Optional


def clean_str(val, upper=False, title=False) -> Optional[str]:
    if val is None: return None
    s = str(val).strip()
    if not s or s.lower() in ('none','nan','n/a','-',''): return None
    if upper: s = s.upper()
    if title: s = s.title()
    return s


def clean_float(val, default=0.0) -> float:
    if val is None: return default
    s = str(val).strip().upper()
    if not s or s in ('NONE','NAN','N/A','-','','GRATUIT'): return default
    import re
    m = re.search(r'[\d]+(?:[.,]\d+)?', s.replace(',','.'))
    return float(m.group().replace(',','.')) if m else default


def clean_int(val, default=0) -> int:
    return int(clean_float(val, default))


def clean_bool(val) -> bool:
    if val is None: return False
    s = str(val).strip().upper()
    return s in ('1','TRUE','OUI','YES','O','Y','✓','VRAI')


def clean_date(val) -> Optional[date]:
    if val is None: return None
    if isinstance(val, datetime): return val.date()
    if isinstance(val, date): return val
    s = str(val).strip()
    if not s or s.lower() in ('none','nan','n/a','-',''): return None
    for fmt in ('%d/%m/%Y','%d-%m-%Y','%Y-%m-%d','%d/%m/%y','%Y/%m/%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


class ImportResult:
    def __init__(self):
        self.inserted = 0
        self.updated  = 0
        self.skipped  = 0
        self.errors   = []
        self.warnings = []

    @property
    def total(self):
        return self.inserted + self.updated + self.skipped

    def add_error(self, row_num, msg):
        self.errors.append(f"Ligne {row_num}: {msg}")

    def add_warning(self, row_num, msg):
        self.warnings.append(f"Ligne {row_num}: {msg}")

    def summary(self) -> str:
        lines = [
            f"✅ Insérés:  {self.inserted}",
            f"♻️  Mis à jour: {self.updated}",
            f"⏭  Ignorés:  {self.skipped}",
            f"❌ Erreurs:  {len(self.errors)}",
        ]
        if self.errors:
            lines.append("\nErreurs détaillées:")
            lines.extend(f"  {e}" for e in self.errors[:10])
            if len(self.errors) > 10:
                lines.append(f"  … et {len(self.errors)-10} autres")
        if self.warnings:
            lines.append("\nAvertissements:")
            lines.extend(f"  {w}" for w in self.warnings[:5])
        return "\n".join(lines)

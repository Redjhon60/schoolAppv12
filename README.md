# Le Schéma SGS v3 — Système de Gestion Scolaire

## 🚀 Démarrage rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Importer les données initiales depuis Excel (première fois)
python import_excel.py --xlsx sch.xlsx --year 2024-25

# 3. Lancer l'application
python main.py
```

## 🔐 Identifiants par défaut
| Rôle       | Login      | Mot de passe |
|------------|------------|--------------|
| Admin      | admin      | admin123     |
| Comptable  | comptable  | compta123    |
| Secrétaire | secretaire | secr123      |

---

## 📥 Centre d'Import Excel (nouveau en v3)

Accessible depuis la sidebar : **📥 Import Excel**

### Fonctionnement
1. Sélectionnez le module (Élèves, Personnel, Dépenses, Transport, Emploi du Temps, Paiements)
2. Téléchargez le template Excel pré-rempli avec des données d'exemple
3. Remplissez-le avec vos données
4. Importez-le — la détection des colonnes est automatique

### Modules supportés
| Module         | Template                        | Colonnes clés                          |
|----------------|---------------------------------|----------------------------------------|
| 📚 Élèves      | template_eleves.xlsx            | Matricule, Nom, Classe, Mensualité + mois |
| 👥 Personnel   | template_personnel.xlsx         | Prénom, Nom, Poste, Salaire            |
| 💸 Dépenses    | template_depenses.xlsx          | Catégorie, Type, Montant, Date         |
| 🚌 Transport   | template_transport.xlsx         | Nom bus, Plaque, Capacité, Chauffeur   |
| 📅 Emploi dt   | template_emploi_du_temps.xlsx   | Classe, Jour, Heure, Matière           |
| 💳 Paiements   | template_paiements.xlsx         | Code élève, Type, Mois, Montant        |

### Modes de doublon
- **Ignorer** (défaut) — conserve les données existantes
- **Mettre à jour** — écrase les champs modifiés

---

## ✅ Fonctionnalités v3

### Nouvelles classes
16 classes dont **1BAC SM** et **2BAC** partout.

### Mois NAN
- Cellules jaunes ou valeur `NAN` → statut `⊘ NAN` (non inscrit)
- Exclus des calculs de paiements impayés

### Re-inscription
- Statut par élève : ✅ Oui / ❌ Non / ⏳ En attente
- Filtre, stats dashboard, export Excel dédié

### Paiement corrigé
- Vue complète des 10 mois dans un dialogue unique
- Sélection multiple, pas de doublons

---

## 📁 Structure

```
school_app_v3/
├── main.py
├── import_excel.py              ← Import initial depuis sch.xlsx
├── requirements.txt
├── models/database.py           ← Modèles + migration auto
├── services/
│   ├── receipt_service.py       ← PDF reçus
│   ├── template_generator.py    ← Génération templates Excel
│   └── importers/
│       ├── base_importer.py     ← Utilitaires partagés
│       ├── students_importer.py
│       ├── employees_importer.py
│       ├── expenses_importer.py
│       ├── transport_importer.py
│       ├── timetable_importer.py
│       └── payments_importer.py
├── ui/
│   ├── import_center.py         ← Centre d'import (nouveau)
│   ├── dashboard.py
│   ├── students.py
│   ├── payment_dialog.py
│   └── ...
└── themes/style.py
```

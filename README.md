# 🚀 G-Parc : Gestion de Parc Informatique Moderne

G-Parc est une application web robuste et intuitive conçue pour la gestion complète du matériel informatique au sein d'une organisation. Développée avec **Django**, elle offre une interface moderne, sécurisée et adaptée à différents rôles utilisateurs.

![Django](https://img.shields.io/badge/Framework-Django%205.0-092e20?style=for-the-badge&logo=django)
![Python](https://img.shields.io/badge/Language-Python%203.10+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![Unfold](https://img.shields.io/badge/Admin-Unfold%20Tailwind-38bdf8?style=for-the-badge)

## ✨ Fonctionnalités Clés

### 👤 Gestion des Rôles & Accès
- **Administrateur** : Contrôle total sur les équipements, les utilisateurs et les statistiques.
- **Technicien IT** : Gestion de la maintenance, résolution des tickets et suivi technique.
- **Utilisateur Standard** : Consultation du matériel assigné et signalement de problèmes via des tickets.
- **Support Google OAuth** : Connexion sécurisée avec un compte Google.

### 💻 Inventaire & Équipements
- **Suivi complet** : Gestion des catégories (Laptops, Écrans, Accessoires, etc.).
- **QR Code Automatique** : Chaque appareil génère son propre QR Code unique pour un inventaire rapide.
- **Historique** : Suivi détaillé de toutes les actions effectuées sur chaque appareil (attribution, retour, réparation).

### 🛠️ Maintenance & Tickets
- **Signalement facile** : Les utilisateurs peuvent créer des tickets pour tout incident technique.
- **Flux de travail technique** : Les techniciens peuvent prendre en charge les tickets, rédiger des rapports et suivre les coûts de réparation.

---

## 🛠️ Installation

### 1. Cloner le projet
```bash
git clone https://github.com/Dominique12345678/gestion_parc_informatique_django.git
cd gestion_parc_informatique_django
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv
# Sur Windows
venv\Scripts\activate
# Sur Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement
Créez un fichier `.env` à la racine (basé sur `.env.example`) :
```env
EMAIL_HOST_PASSWORD=votre_mot_de_passe_application_gmail
GOOGLE_CLIENT_ID=votre_client_id
GOOGLE_CLIENT_SECRET=votre_secret
```

### 5. Migrer la base de données
```bash
python manage.py migrate
```

### 6. Créer un super-utilisateur
```bash
python manage.py createsuperuser
```

### 7. Lancer le serveur
```bash
python manage.py runserver
```

---

## 📸 Aperçu de l'Interface

L'application utilise l'interface **Unfold** pour un dashboard administrateur moderne basé sur Tailwind CSS, offrant une expérience utilisateur fluide et responsive.

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour des changements majeurs, veuillez ouvrir une discussion au préalable.

## 📄 Licence

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.

---

⭐ *Si ce projet vous aide, n'hésitez pas à lui donner une étoile sur GitHub !*

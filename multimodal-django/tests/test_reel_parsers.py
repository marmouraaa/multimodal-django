"""
TESTS REELS - PARSERS D'INGESTION
Ces tests utilisent de vrais fichiers (pas de mocks).
Les fichiers de test sont dans le dossier tests/assets/
"""
import os
import sys
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "multimodal_project.settings")
django.setup()

import pytest
from pathlib import Path

# Chemin vers les fichiers de test réels
ASSETS = Path(__file__).parent / "assets"


# ================================================================
# FIXTURES — vrais fichiers créés sur disque
# ================================================================

@pytest.fixture(scope="session")
def asset_txt(tmp_path_factory):
    f = tmp_path_factory.mktemp("assets") / "contrat.txt"
    f.write_text(
        "CONTRAT DE PRESTATION DE SERVICES\n\n"
        "Article 1 - Duree\n"
        "Le present contrat est conclu pour une duree de 12 mois a compter du 1er janvier 2025.\n\n"
        "Article 2 - Remuneration\n"
        "Le prestataire percevra une remuneration mensuelle de 3500 euros HT.\n\n"
        "Article 3 - Confidentialite\n"
        "Toutes les informations echangees dans le cadre de ce contrat sont strictement confidentielles.\n\n"
        "Article 4 - Resiliation\n"
        "Chaque partie peut resilier le contrat avec un preavis de 30 jours.\n",
        encoding="utf-8"
    )
    return str(f)


@pytest.fixture(scope="session")
def asset_csv(tmp_path_factory):
    f = tmp_path_factory.mktemp("assets") / "ventes.csv"
    f.write_text(
        "produit,quantite,prix_unitaire,total,region\n"
        "Laptop Pro,15,1200,18000,Paris\n"
        "Smartphone X,42,800,33600,Lyon\n"
        "Tablette Z,28,450,12600,Marseille\n"
        "Casque Audio,67,120,8040,Bordeaux\n"
        "Moniteur 4K,19,650,12350,Lille\n"
        "Clavier Meca,55,90,4950,Paris\n"
        "Souris Gaming,89,60,5340,Lyon\n"
        "Webcam HD,34,75,2550,Marseille\n",
        encoding="utf-8"
    )
    return str(f)


@pytest.fixture(scope="session")
def asset_json(tmp_path_factory):
    import json
    f = tmp_path_factory.mktemp("assets") / "employes.json"
    data = [
        {"id": 1, "nom": "Martin", "prenom": "Sophie", "poste": "Developpeur Senior", "salaire": 52000, "anciennete": 5},
        {"id": 2, "nom": "Dupont", "prenom": "Lucas", "poste": "Chef de Projet", "salaire": 61000, "anciennete": 8},
        {"id": 3, "nom": "Bernard", "prenom": "Emma", "poste": "Designer UX", "salaire": 45000, "anciennete": 3},
        {"id": 4, "nom": "Petit", "prenom": "Thomas", "poste": "DevOps Engineer", "salaire": 58000, "anciennete": 6},
        {"id": 5, "nom": "Robert", "prenom": "Julie", "poste": "Data Scientist", "salaire": 65000, "anciennete": 4},
    ]
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(f)


@pytest.fixture(scope="session")
def asset_pdf(tmp_path_factory):
    f = tmp_path_factory.mktemp("assets") / "rapport.pdf"
    pdf_bytes = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 280 >>
stream
BT
/F1 14 Tf
50 750 Td
(RAPPORT ANNUEL 2025) Tj
0 -30 Td
/F1 11 Tf
(Chiffre d affaires: 2 500 000 euros) Tj
0 -20 Td
(Benefice net: 380 000 euros) Tj
0 -20 Td
(Nombre d employes: 47 personnes) Tj
0 -20 Td
(Croissance: 12 pourcent) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000596 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
675
%%EOF"""
    f.write_bytes(pdf_bytes)
    return str(f)


@pytest.fixture(scope="session")
def asset_image(tmp_path_factory):
    """Crée une vraie image PNG avec du contenu visuel (facture)"""
    f = tmp_path_factory.mktemp("assets") / "facture.png"
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (400, 300), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 380, 280], outline=(0, 0, 0), width=3)
        draw.rectangle([20, 20, 380, 60], fill=(70, 130, 180), outline=(0, 0, 0), width=3)
        draw.text((30, 30), "FACTURE #2025-001", fill=(255, 255, 255))
        draw.text((30, 80), "Client: Entreprise ABC", fill=(0, 0, 0))
        draw.text((30, 110), "Date: 18 avril 2025", fill=(0, 0, 0))
        draw.text((30, 140), "Produit: Licence logicielle", fill=(0, 0, 0))
        draw.text((30, 170), "Quantite: 5 unites", fill=(0, 0, 0))
        draw.text((30, 200), "Prix unitaire: 299 EUR", fill=(0, 0, 0))
        draw.text((30, 230), "TOTAL: 1495 EUR", fill=(200, 0, 0))
        img.save(str(f))
    except ImportError:
        # Fallback : PNG minimal valide sans Pillow
        import struct, zlib
        def chunk(name, data):
            c = name + data
            return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        header = b'\x89PNG\r\n\x1a\n'
        ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 100, 100, 8, 2, 0, 0, 0))
        raw = b'\x00' + b'\xff\x00\x00' * 100
        idat = chunk(b'IDAT', zlib.compress(raw * 100))
        iend = chunk(b'IEND', b'')
        f.write_bytes(header + ihdr + idat + iend)
    return str(f)


# ================================================================
# TESTS REELS — parse_txt
# ================================================================

class TestParseTxtReel:

    def test_lit_contenu_complet(self, asset_txt):
        from ingestion_app.parsers import parse_txt
        r = parse_txt(asset_txt)
        assert r["error"] is None
        assert len(r["text"]) > 100

    def test_contient_article_1(self, asset_txt):
        from ingestion_app.parsers import parse_txt
        r = parse_txt(asset_txt)
        assert "Article 1" in r["text"]

    def test_contient_duree_12_mois(self, asset_txt):
        from ingestion_app.parsers import parse_txt
        r = parse_txt(asset_txt)
        assert "12 mois" in r["text"]

    def test_contient_montant_3500(self, asset_txt):
        from ingestion_app.parsers import parse_txt
        r = parse_txt(asset_txt)
        assert "3500" in r["text"]

    def test_encoding_detecte(self, asset_txt):
        from ingestion_app.parsers import parse_txt
        r = parse_txt(asset_txt)
        assert r.get("encoding") in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    def test_pas_de_caracteres_null(self, asset_txt):
        from ingestion_app.parsers import parse_txt
        r = parse_txt(asset_txt)
        assert "\x00" not in r["text"]


# ================================================================
# TESTS REELS — parse_csv
# ================================================================

class TestParseCsvReel:

    def test_lit_fichier_sans_erreur(self, asset_csv):
        from ingestion_app.parsers import parse_csv
        r = parse_csv(asset_csv)
        assert r["error"] is None

    def test_texte_non_vide(self, asset_csv):
        from ingestion_app.parsers import parse_csv
        r = parse_csv(asset_csv)
        assert len(r["text"]) > 50

    def test_contient_nom_produit(self, asset_csv):
        from ingestion_app.parsers import parse_csv
        r = parse_csv(asset_csv)
        assert "Laptop Pro" in r["text"] or "laptop" in r["text"].lower()

    def test_contient_statistiques(self, asset_csv):
        """Le parser CSV doit générer des statistiques sur les colonnes numériques"""
        from ingestion_app.parsers import parse_csv
        r = parse_csv(asset_csv)
        texte = r["text"].lower()
        assert "moyenne" in texte or "min" in texte or "max" in texte or "mean" in texte

    def test_contient_dimensions(self, asset_csv):
        """Le texte doit mentionner les dimensions du fichier"""
        from ingestion_app.parsers import parse_csv
        r = parse_csv(asset_csv)
        assert "8" in r["text"]  # 8 lignes

    def test_contient_colonnes(self, asset_csv):
        from ingestion_app.parsers import parse_csv
        r = parse_csv(asset_csv)
        assert "produit" in r["text"].lower() or "quantite" in r["text"].lower()


# ================================================================
# TESTS REELS — parse_json
# ================================================================

class TestParseJsonReel:

    def test_lit_liste_employes(self, asset_json):
        from ingestion_app.parsers import parse_json
        r = parse_json(asset_json)
        assert r["error"] is None
        assert len(r["text"]) > 50

    def test_contient_noms_colonnes(self, asset_json):
        from ingestion_app.parsers import parse_json
        r = parse_json(asset_json)
        texte = r["text"].lower()
        assert "nom" in texte or "salaire" in texte or "poste" in texte

    def test_contient_donnees_numeriques(self, asset_json):
        """Les salaires doivent apparaître dans l'output"""
        from ingestion_app.parsers import parse_json
        r = parse_json(asset_json)
        assert "52000" in r["text"] or "65000" in r["text"] or "salaire" in r["text"].lower()

    def test_contient_statistiques_numeriques(self, asset_json):
        """Comme CSV, les colonnes numériques doivent générer des stats"""
        from ingestion_app.parsers import parse_json
        r = parse_json(asset_json)
        texte = r["text"].lower()
        assert "moyenne" in texte or "min" in texte or "max" in texte or "salaire" in texte


# ================================================================
# TESTS REELS — parse_pdf
# ================================================================

class TestParsePdfReel:

    def test_lit_pdf_sans_erreur(self, asset_pdf):
        from ingestion_app.parsers import parse_pdf
        r = parse_pdf(asset_pdf)
        assert r["error"] is None

    def test_compte_pages(self, asset_pdf):
        from ingestion_app.parsers import parse_pdf
        r = parse_pdf(asset_pdf)
        assert r["page_count"] == 1

    def test_extrait_titre(self, asset_pdf):
        from ingestion_app.parsers import parse_pdf
        r = parse_pdf(asset_pdf)
        assert "RAPPORT" in r["text"] or "2025" in r["text"]

    def test_extrait_chiffres(self, asset_pdf):
        from ingestion_app.parsers import parse_pdf
        r = parse_pdf(asset_pdf)
        assert "2 500 000" in r["text"] or "380 000" in r["text"] or "47" in r["text"]

    def test_texte_long_enough(self, asset_pdf):
        from ingestion_app.parsers import parse_pdf
        r = parse_pdf(asset_pdf)
        assert len(r["text"]) > 30


# ================================================================
# TESTS REELS — parse_image
# ================================================================

class TestParseImageReel:

    def test_charge_image_sans_erreur(self, asset_image):
        from ingestion_app.parsers import parse_image
        r = parse_image(asset_image)
        assert r["error"] is None

    def test_dimensions_positives(self, asset_image):
        from ingestion_app.parsers import parse_image
        r = parse_image(asset_image)
        assert r["width"] > 0
        assert r["height"] > 0

    def test_description_non_vide(self, asset_image):
        from ingestion_app.parsers import parse_image
        r = parse_image(asset_image)
        assert len(r["description"]) > 0

    def test_description_contient_dimensions(self, asset_image):
        from ingestion_app.parsers import parse_image
        r = parse_image(asset_image)
        assert str(r["width"]) in r["description"]
        assert str(r["height"]) in r["description"]


# ================================================================
# TESTS REELS — run_parsing_pipeline (pipeline complet)
# ================================================================

class TestPipelineCompletReel:

    def test_pipeline_txt_succes(self, asset_txt):
        from ingestion_app.parsers import run_parsing_pipeline
        r = run_parsing_pipeline(asset_txt, "contrat.txt")
        assert r["success"] is True
        assert r["modality"] == "document"
        assert len(r["extracted_text"]) > 100
        assert r["errors"] == []

    def test_pipeline_csv_succes(self, asset_csv):
        from ingestion_app.parsers import run_parsing_pipeline
        r = run_parsing_pipeline(asset_csv, "ventes.csv")
        assert r["success"] is True
        assert r["modality"] == "structured"
        assert len(r["extracted_text"]) > 50

    def test_pipeline_json_succes(self, asset_json):
        from ingestion_app.parsers import run_parsing_pipeline
        r = run_parsing_pipeline(asset_json, "employes.json")
        assert r["success"] is True
        assert r["modality"] == "structured"
        assert len(r["extracted_text"]) > 50

    def test_pipeline_pdf_succes(self, asset_pdf):
        from ingestion_app.parsers import run_parsing_pipeline
        r = run_parsing_pipeline(asset_pdf, "rapport.pdf")
        assert r["success"] is True
        assert r["modality"] == "document"
        assert "RAPPORT" in r["extracted_text"] or len(r["extracted_text"]) > 10

    def test_pipeline_image_succes(self, asset_image):
        from ingestion_app.parsers import run_parsing_pipeline
        r = run_parsing_pipeline(asset_image, "facture.png")
        assert r["success"] is True
        assert r["modality"] == "image"
        assert r["extra"]["width"] > 0
        assert r["extra"]["height"] > 0

    def test_pipeline_fichier_inconnu_echec(self, tmp_path):
        from ingestion_app.parsers import run_parsing_pipeline
        f = tmp_path / "test.xyz"
        f.write_bytes(b"contenu binaire inconnu")
        r = run_parsing_pipeline(str(f), "test.xyz")
        assert r["success"] is False
        assert len(r["errors"]) > 0

    def test_pipeline_txt_contenu_correct(self, asset_txt):
        from ingestion_app.parsers import run_parsing_pipeline
        r = run_parsing_pipeline(asset_txt, "contrat.txt")
        assert "12 mois" in r["extracted_text"]
        assert "3500" in r["extracted_text"]

    def test_pipeline_csv_contenu_correct(self, asset_csv):
        from ingestion_app.parsers import run_parsing_pipeline
        r = run_parsing_pipeline(asset_csv, "ventes.csv")
        assert "Laptop" in r["extracted_text"] or "produit" in r["extracted_text"].lower()


# ================================================================
# TESTS REELS — ModalityClassifier sur vrais fichiers
# ================================================================

class TestClassifierReel:

    def test_classifie_txt_comme_document(self, asset_txt):
        from router_app.classifier import ModalityClassifier
        c = ModalityClassifier()
        r = c.classify(asset_txt)
        assert r.modality in ["document", "structured"]
        assert r.confidence > 0.0

    def test_classifie_csv_comme_structured(self, asset_csv):
        from router_app.classifier import ModalityClassifier
        c = ModalityClassifier()
        r = c.classify(asset_csv)
        assert r.modality == "structured"
        assert r.confidence >= 0.9
        assert r.method == "csv_content"

    def test_classifie_json_comme_structured(self, asset_json):
        from router_app.classifier import ModalityClassifier
        c = ModalityClassifier()
        r = c.classify(asset_json)
        assert r.modality == "structured"
        assert r.confidence >= 0.9
        assert r.method == "json_content"

    def test_classifie_pdf_comme_document(self, asset_pdf):
        from router_app.classifier import ModalityClassifier
        c = ModalityClassifier()
        r = c.classify(asset_pdf)
        assert r.modality == "document"
        assert r.confidence >= 0.9

    def test_classifie_png_comme_image(self, asset_image):
        from router_app.classifier import ModalityClassifier
        c = ModalityClassifier()
        r = c.classify(asset_image)
        assert r.modality == "image"
        assert r.confidence >= 0.9

    def test_fichier_inexistant(self):
        from router_app.classifier import ModalityClassifier
        c = ModalityClassifier()
        r = c.classify("/chemin/qui/nexiste/pas.pdf")
        assert r.modality == "unknown"
        assert r.confidence == 0.0
        assert r.method == "file_not_found"

    def test_mime_type_renseigne(self, asset_csv):
        from router_app.classifier import ModalityClassifier
        c = ModalityClassifier()
        r = c.classify(asset_csv)
        assert r.mime is not None
        assert len(r.mime) > 0

    def test_method_renseignee(self, asset_json):
        from router_app.classifier import ModalityClassifier
        c = ModalityClassifier()
        r = c.classify(asset_json)
        assert r.method is not None
        assert r.method != ""


# ================================================================
# TESTS REELS — Modèles IA avec Ollama
# Nécessite : ollama serve + modèles installés
# Ces tests sont marqués 'ollama' — lancer avec : pytest -m ollama
# ================================================================

@pytest.mark.ollama
class TestOllamaTextModelReel:

    def test_repond_question_sur_contrat(self, asset_txt):
        """Test réel : llama3.2 répond à une question sur le contrat"""
        from ingestion_app.parsers import parse_txt
        from ingestion_app.ai_models import DocumentModel

        contenu = parse_txt(asset_txt)["text"]
        model = DocumentModel()
        response = model.answer("Quelle est la duree du contrat ?", contenu)

        assert response.answer != ""
        assert response.confidence > 0.0
        assert response.modality == "document"
        assert response.error is None
        # La réponse doit mentionner 12 mois
        assert "12" in response.answer or "mois" in response.answer.lower() or "an" in response.answer.lower()

    def test_repond_question_remuneration(self, asset_txt):
        from ingestion_app.parsers import parse_txt
        from ingestion_app.ai_models import DocumentModel

        contenu = parse_txt(asset_txt)["text"]
        model = DocumentModel()
        response = model.answer("Quel est le montant de la remuneration mensuelle ?", contenu)

        assert response.answer != ""
        assert "3500" in response.answer or "3 500" in response.answer or "euros" in response.answer.lower()

    def test_temps_traitement_raisonnable(self, asset_txt):
        """La réponse doit arriver en moins de 120 secondes"""
        from ingestion_app.parsers import parse_txt
        from ingestion_app.ai_models import DocumentModel

        contenu = parse_txt(asset_txt)["text"]
        model = DocumentModel()
        response = model.answer("Resume ce document en une phrase.", contenu)

        assert response.processing_time < 120
        assert response.processing_time > 0


@pytest.mark.ollama
class TestOllamaStructuredModelReel:

    def test_repond_question_csv(self, asset_csv):
        from ingestion_app.parsers import parse_csv
        from ingestion_app.ai_models import StructuredDataModel

        contenu = parse_csv(asset_csv)["text"]
        model = StructuredDataModel()
        response = model.answer("Combien de produits differents sont dans ce fichier ?", contenu)

        assert response.answer != ""
        assert response.confidence > 0.0
        assert response.error is None

    def test_repond_question_json(self, asset_json):
        from ingestion_app.parsers import parse_json
        from ingestion_app.ai_models import StructuredDataModel

        contenu = parse_json(asset_json)["text"]
        model = StructuredDataModel()
        response = model.answer("Quel est le salaire le plus eleve parmi les employes ?", contenu)

        assert response.answer != ""
        assert "65000" in response.answer or "65 000" in response.answer or "data scientist" in response.answer.lower()


@pytest.mark.ollama
class TestOllamaVisionModelReel:

    def test_repond_question_image(self, asset_image):
        from ingestion_app.ai_models import ImageModel

        model = ImageModel()
        response = model.answer("Que vois-tu sur cette image ?", "", file_path=asset_image)

        assert response.answer != ""
        assert response.confidence > 0.0
        assert response.error is None

    def test_detecte_texte_dans_image(self, asset_image):
        from ingestion_app.ai_models import ImageModel

        model = ImageModel()
        response = model.answer("Y a-t-il du texte sur cette image ? Si oui, cite-le.", "", file_path=asset_image)

        # L'image contient "FACTURE" - le modèle devrait le voir
        texte_reponse = response.answer.lower()
        assert any(mot in texte_reponse for mot in ["facture", "invoice", "texte", "text", "oui", "yes"])


@pytest.mark.ollama
class TestRouterCompletReel:

    def test_pipeline_document_complet(self, asset_txt):
        """Test end-to-end : TXT → classifier → TextModel → réponse"""
        from ingestion_app.parsers import run_parsing_pipeline
        from router_app.classifier import ModalityClassifier
        from ingestion_app.ai_models import DocumentModel

        # Étape 1 : parsing
        parsed = run_parsing_pipeline(asset_txt, "contrat.txt")
        assert parsed["success"] is True

        # Étape 2 : classification
        c = ModalityClassifier()
        classification = c.classify(asset_txt)
        assert classification.modality == "document"

        # Étape 3 : IA
        model = DocumentModel()
        response = model.answer("Quelle est la duree du contrat ?", parsed["extracted_text"])
        assert response.answer != ""
        assert response.error is None

    def test_pipeline_structured_complet(self, asset_csv):
        """Test end-to-end : CSV → classifier → StructuredModel → réponse"""
        from ingestion_app.parsers import run_parsing_pipeline
        from router_app.classifier import ModalityClassifier
        from ingestion_app.ai_models import StructuredDataModel

        parsed = run_parsing_pipeline(asset_csv, "ventes.csv")
        assert parsed["success"] is True

        c = ModalityClassifier()
        classification = c.classify(asset_csv)
        assert classification.modality == "structured"

        model = StructuredDataModel()
        response = model.answer("Quel produit a le total le plus eleve ?", parsed["extracted_text"])
        assert response.answer != ""
        assert response.error is None

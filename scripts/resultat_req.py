import duckdb
import pandas as pd
import numpy as np
from scipy import stats
import os
import sys
from datetime import datetime 
from pathlib import Path

# paramètres des tests

ca_total_attendu = 70568.60
nb_vin_mil =30
file_fusion =714

con = None
# répertoire des fichiers
BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = Path.cwd()

output_dir = OUT_DIR / "data/exports"

timestamp = datetime.now().strftime("%Y%m%d")
db_path =BASE_DIR / "data/processed/fichiersql.duckdb"

timestamp_rpt = datetime.now().strftime("%d/%m/%Y")
print(f"--- GENERATION DU RAPPORT du {timestamp_rpt} ---")

try: 
    con = duckdb.connect(db_path)
    
    # =========================
    # Génération du Rapport
     # =========================
    query_ca = """
    SELECT 
        e.product_id,
        l.id_web,
        w.post_title AS nom_produit,
        e.price AS prix_unitaire,
        COALESCE(w.total_sales, 0) AS ventes_totales,
        ROUND(e.price * COALESCE(w.total_sales, 0), 2) AS chiffre_affaires,
        e.stock_quantity AS stock
    FROM erp e
    INNER JOIN liaison l ON e.product_id = l.product_id
    INNER JOIN web w ON l.id_web = w.id_web
    ORDER BY chiffre_affaires DESC;
    """
    
    df_ca = con.execute(query_ca).df()
    file_ca = os.path.join(
        output_dir, f"rapport_chiffre_affaires_{timestamp}.xlsx"
    )
    df_ca.to_excel(file_ca, index=False, engine="openpyxl")
    print ("\n-----------------------------------------------------------------------") 
    print(f"Fichier Excel CA généré : {file_ca}")
    print(f" CA attendu : {ca_total_attendu}")
    if ca_total_attendu != file_ca :
        print("\n### Problème entre CA attendu et CA calculé ###\n")
    else :
        print("\n### test vérification CA réussi ###\n")
    ca_total = df_ca['chiffre_affaires'].sum()
    print(f"Chiffre d'Affaires Total  : {ca_total:,.2f} €")
    if file_fusion !=  len(df_ca) :
        print (f"Problème entre fichier fusionné attendu : {file_fusion} et calculé :{len(df_ca)}")
    else :
        print("\n### test vérification nb fichier fusionné réussi ###\n")
    print ("----------------------------------------------------------------------")



    # -------------------------------------------------------------
    # CALCUL DU Z-SCORE STATISTIQUE SUR L'ENSEMBLE DES PRIX
    # -------------------------------------------------------------
    # Z-Score = (prix - moyenne_prix) / ecart_type_prix
    cte_zscore = """
        WITH dataset AS (
            SELECT 
                e.product_id,
                l.id_web,
                w.post_title AS nom_produit,
                e.price AS prix_unitaire,
                COALESCE(w.total_sales, 0) AS ventes_totales,
                ROUND(e.price * COALESCE(w.total_sales, 0), 2) AS chiffre_affaires,
                e.stock_quantity AS stock,
                -- Calcul de la moyenne et de l'écart-type sur le périmètre
                AVG(e.price) OVER () AS avg_price,
                STDDEV(e.price) OVER () AS std_price
            FROM erp e
            INNER JOIN liaison l ON e.product_id = l.product_id
            INNER JOIN web w ON l.id_web = w.id_web
        )
        SELECT 
            product_id,
            id_web,
            nom_produit,
            prix_unitaire,
            ROUND((prix_unitaire - avg_price) / std_price, 4) AS z_score,
            ventes_totales,
            chiffre_affaires,
            stock
        FROM dataset
    """
    # -------------------------------------------------------------
    # EXTRACTION : Vins Premium (Z-Score > 2) (.csv)
    # -------------------------------------------------------------
    query_premium = f"""
        {cte_zscore}
        WHERE (prix_unitaire - avg_price) / std_price > 2
        ORDER BY z_score DESC;
    """
    df_premium = con.execute(query_premium).df()    
    fichier_premium = os.path.join( output_dir, f"vins_premium_{timestamp}.csv")
    df_premium.to_csv(fichier_premium, index=False, encoding="utf-8")
    print ("\n-----------------------------------------------------------------------") 
    print(f"Fichier CSV vins premium (Z-Score > 2) généré : {fichier_premium}")  
    print(f"Nombre de vins millésimes : {len(df_premium)}") 
    print(f"Nombre de vins millésimes attendus: {nb_vin_mil}") 
    if nb_vin_mil != len(df_premium) :
        print("\n### Problème entre vins millésimes attendu et vins millésimes calculé ###\n")
    else :
        print("\n### test nombre vins millésimes réussi ###\n")
    print ("----------------------------------------------------------------------")
    # -------------------------------------------------------------
    #  EXTRACTION : Vins Ordinaires (Z-Score <= 2) (.csv)
    # -------------------------------------------------------------
    query_ordinaires = f"""
        {cte_zscore}
        WHERE (prix_unitaire - avg_price) / std_price <= 2
        ORDER BY z_score DESC;
    """
    df_ordinaires = con.execute(query_ordinaires).df()
    fichier_ordinaire = os.path.join(output_dir, f"vins_ordinaires_{timestamp}.csv")
    df_ordinaires.to_csv(fichier_ordinaire, index=False, encoding="utf-8")
    
    print ("\n-----------------------------------------------------------------------") 
    print(f"Fichier CSV Vins Ordinaires (Z-Score <= 2) généré  : {fichier_ordinaire}")
    print ("----------------------------------------------------------------------")
    
    
except AssertionError as e:
    print (f"Erreur echec du script: {e}", file=sys.stderr)
    sys.exit(1)   
except Exception as e :
    print (f"Erreur echec du script: {e}", file=sys.stderr)
    sys.exit(1)    
finally :
    if con is not None :
        con.close()
        print("Close connexion SQL")

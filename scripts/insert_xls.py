import duckdb
import pandas as pd
import numpy as np
from scipy import stats
import os
import sys
from pathlib import Path

# paramètres de test
nb_lig_erp_after = 825 
nb_lig_liaison_after = 825 
nb_lig_web_after = 1428
nb_lig_web_after_db = 714

print("--- DEBUT DU PIPELINE INSERTION ---\n")

# répertoire des fichiers
BASE_DIR = Path(__file__).resolve().parent.parent
XLS_DIR = BASE_DIR /  "data/xls"
PROCESSED_DIR = BASE_DIR / "data/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Lecture fichier ERP
df_erp_xls = None
try:
    df_erp_xls = pd.read_excel(f"{XLS_DIR}/Fichier_erp.xlsx",sheet_name="Sheet1")
    print("Fichier ERP lu avec succès !")

except FileNotFoundError:
    print("Erreur : Le fichier ERP est introuvable. Vérifiez le chemin ou le nom.")
    sys.exit(1)

except ValueError as e:
    # Capturé si le format n'est pas supporté ou le fichier n'est pas un vrai Excel
    print(f"Erreur de format/valeur fichier erp : {e}")
    sys.exit(1)

except Exception as e:
    # Attrape les autres erreurs (fichier corrompu, manque d'une dépendance comme openpyxl/xlrd...)
    print(f"Une erreur inattendue est survenue sur fichier erp : {e}")
    sys.exit(1)


# lecture fichier liaison
df_liaison_xls = None
try:
    df_liaison_xls = pd.read_excel(f"{XLS_DIR}/fichier_liaison.xlsx",sheet_name="Sheet1")
    print("Fichier liaison lu avec succès !")


except FileNotFoundError:
    print("Erreur : Le fichier liaison est introuvable. Vérifiez le chemin ou le nom.")
    sys.exit(1)

except ValueError as e:
    # Capturé si le format n'est pas supporté ou le fichier n'est pas un vrai Excel
    print(f"Erreur de format/valeur fichier liaison: {e}")
    sys.exit(1)

except Exception as e:
    # Attrape les autres erreurs (fichier corrompu, manque d'une dépendance comme openpyxl/xlrd...)
    print(f"Une erreur inattendue est survenue fichier liaison : {e}")
    sys.exit(1)


# Lecture fichier web
df_web_xls =None
try:
    df_web_xls = pd.read_excel(f"{XLS_DIR}/Fichier_web.xlsx",sheet_name="Sheet1")
    print("Fichier web lu avec succès !")


except FileNotFoundError:
    print("Erreur : Le fichier web est introuvable. Vérifiez le chemin ou le nom.")
    sys.exit(1)

except ValueError as e:
    # Capturé si le format n'est pas supporté ou le fichier n'est pas un vrai Excel
    print(f"Erreur de format/valeur fichier web : {e}")
    sys.exit(1)

except Exception as e:
    # Attrape les autres erreurs (fichier corrompu, manque d'une dépendance comme openpyxl/xlrd...)
    print(f"Une erreur inattendue est survenue fichier web : {e}")
    sys.exit(1)

# Nombre de ligne de chaque fichier

nb_ligne_erp = len (df_erp_xls)
nb_ligne_liaison = len (df_liaison_xls)
nb_ligne_web = len (df_web_xls)
print ("\n") 
print ("--- Nombre de ligne des différents fichiers XLS --- ")
print (f"Nombre de ligne erp : {nb_ligne_erp} - Nombre de ligne liaison : {nb_ligne_liaison} - Nombre de ligne web : {nb_ligne_web}")


# ------------------------------------------------------------------------------------------
# nettoyage des data frames ( supression des id Nan  , renommage colonne  et choix product)
# ------------------------------------------------------------------------------------------

df_erp_xls_clean = df_erp_xls.dropna (subset= ['product_id'] )

df_liaison_xls["id_web"] =pd.to_numeric(df_liaison_xls["id_web"] , errors ='coerce').astype('Int64') # changement du type de la colonne
df_liaison_xls_clean = df_liaison_xls.dropna (subset= ['product_id'] )


df_liaison_xls_clean = df_liaison_xls_clean.dropna (subset= ['id_web'] )
df_liaison_xls_clean = df_liaison_xls_clean.dropna (subset= ['product_id'] )

df_web_xls["sku"] =pd.to_numeric(df_web_xls["sku"] , errors ='coerce').astype('Int64') # changement du type de la colonne
df_web_xls_clean = df_web_xls.dropna(subset=["sku"])

df_web_xls_clean = df_web_xls_clean.rename ( columns={ "sku" :"id_web"} ) # renommage pour être conforme au nom des colonnes 
df_web_xls_clean = df_web_xls_clean[df_web_xls_clean['post_type'] == 'product'].copy()

# nombre de ligne sans NaN

nb_ligne_erp_clean = len (df_erp_xls_clean)
nb_ligne_liaison_clean = len (df_liaison_xls_clean)
nb_ligne_web_clean= len (df_web_xls_clean)
print ("\n") 
print ("--- Nombre de ligne sans NaN après suppression ---")
print (f"Nombre de ligne erp : {nb_ligne_erp_clean} - Nombre de ligne liaison : {nb_ligne_liaison_clean} - Nombre de ligne web : {nb_ligne_web_clean}")


if nb_ligne_web_clean *2 != nb_lig_web_after :
    print(f"\n---> Problème entre  data frame WEB calculé : {nb_ligne_web_clean *2} et ligne WEB attendu : {nb_lig_web_after}\n")
else :
    print("\nTest vérification ligne WEB réussi n")

# ---------------------------------
# nombre de doublon par data frame
# ---------------------------------

nb_doublon_erp = df_erp_xls_clean['product_id'].duplicated().sum() # doublon sur la colonne product_id
nb_doublon_liaison = df_liaison_xls_clean[['product_id','id_web']].duplicated().sum() # doublon sur le couple product_id et id_web
nb_doublon_web = df_web_xls_clean['id_web'].duplicated().sum() # doublon sur la colonne id_web ( anciennement sku )
print ("\n") 
print ("--- Nombre de doublon dans les data frames ---")
print (f"Product_id du fichier erp : {nb_doublon_erp} - product_id / id_web du fichier liaison : {nb_doublon_liaison} - id_web du fichier web : {nb_doublon_web} " )
nb_d_w =  nb_doublon_web *2 
if nb_d_w != nb_lig_web_after_db :
    print(f"\n---> Problème (dédoublé ) entre  data frame WEB analysée : {nb_d_w} et  WEB  attendu{nb_lig_web_after_db} ")
else :
    print("\nTest vérification ligne WEB réussi ###\n")


# ---------------------------------
# Détection des prix Nan ou = 0 
# ---------------------------------

invalid_prices_mask = df_erp_xls_clean['price'].isna() | (df_erp_xls_clean['price'] == 0)
# Compter le nombre de cas
nb_nan = df_erp_xls_clean['price'].isna().sum()
nb_zero = (df_erp_xls_clean['price'] == 0).sum()
nb_total_invalide = invalid_prices_mask.sum()

print(f"--- Rapport de contrôle des prix (ERP) ---")
print(f"Prix NaN (manquants) : {nb_nan}")
print(f"Prix égaux à 0       : {nb_zero}")
print(f"Total prix invalides : {nb_total_invalide}")
print ("\n") 

# Suppression des lignes erronées et affichage du message
print ("\n") 
if nb_total_invalide > 0:
    df_erp_xls_clean = df_erp_xls_clean[~invalid_prices_mask].copy()
    print(f"---> Nettoyage data frame ERP : {nb_total_invalide} ligne(s) avec  prix invalide (NaN ou 0) ont été supprimée(s).")
else:
    print("--- Nettoyage data frame ERP Aucun prix invalide détecté. ---")

# ---------------------------------
# insertion dans la base duckDB
# ---------------------------------
db_path =BASE_DIR / "data/processed/fichiersql.duckdb"

con = None
try: 
    con = duckdb.connect(db_path)
    # Enregistrement des DataFrames dans DuckDB
    con.register('erp_temp', df_erp_xls_clean)
    con.execute ("CREATE or REPLACE TABLE erp as select * from erp_temp" )
    
    con.register('liaison_temp', df_liaison_xls_clean)
    con.execute ("CREATE or REPLACE TABLE liaison as select * from liaison_temp" )
    
    con.register('web_temp', df_web_xls_clean)
    con.execute ("CREATE or REPLACE TABLE web as select * from web_temp" )

    con.execute ("CHECKPOINT")
    print ("\nInsertion des fichiers terminé")
    
    
except AssertionError as e:
    print (f"Erreur echec du script: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e :
    print (f"Erreur echec du script: {e}", file=sys.stderr)
    sys.exit(1)
finally :
    if con is not None :
        con.close()
        print("Close connexion insert SQL ")

# ---------------------------------
# Affichage du nombre de ligne SQL
# ---------------------------------
con = None
try: 
    con = duckdb.connect(db_path)
    
    query_erp ="select count(*) from erp"
    df_result_erp = con.execute(query_erp).df().iloc[0,0]

    query_liaison ="select count(*) from liaison"
    df_result_liaison = con.execute(query_liaison).df().iloc[0,0]

    query_web ="select count(*) from web"
    df_result_web = con.execute(query_web).df().iloc[0,0]
   
    print ("\n--- Nombre de ligne de chaque table de la base duckDB ---")
    print (f"ERP : {df_result_erp} - Liaison : {df_result_liaison} - Web : {df_result_web}")
    print ("\n") 
except AssertionError as e:
    print (f"Erreur echec req affichage: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e :
    print (f"Erreur echec req affichage: {e}", file=sys.stderr)
    sys.exit(1)
finally :
    if con is not None :
        con.close()
        print("Close connexion affichage  data SQL")






# bdtopo2refhydro
Methods and processing to create a reference hydrologic network from the IGN BD TOPO product

Mise en application sur la BD TOPO 2021 sur la France métropolitaine

## Création d'un référentiel des exutoires
Le référentiel des exutoires vise à créer une ligne de référence permettant d'identifier et de sélectionner l'ensemble des exutoires des fleuves français. Ce référentiel doit être en mesure de pouvoir sélectionnner l'ensemble d'un réseau hydrographique bien orienté et connecté en remontant vers l'amont. Le référentiel prend en compte : 
- La couche limite_terre_mer de la BD TOPO pour les exutoires marins.
- Deux plans d'eau particuliers, le lac du Bourget, le lac d'Annecy
- Des Lagunes méditerranéennes comme celle de Thau car le réseau hydrographique de la couche cours d'eau de l'IGN ne va pas toujours au dela de la lagune et la couche limite_terre_mer ne rentre pas tooujours dans les lagunes. Il y a donc une déconnexion entre les exutoires et la mer.
- Les frontières pour les réseaux des bassins qui s'écoulent en dehors de la France

Traitements de création du référentiel des exutoires QGIS (dans le geopackage "referentiel_exutoires") : 
- Couche "limite_terre_mer"
  - Extraction de la couche
- Couche "plan_d_eau"
  - Sélection manuelle et extraction de lacs et lagunes méditerranéenne issus de la couche plan_d_eau
  - Polygones vers polylignes, couche "plan_d_eau_ligne"
- Couche bassin_versant_topographique
  - Fusion des polygones de la couche 
  - réparer les géométries
  - Polygones vers polylignes, couche "bassin_versant_topographique_ligne"
  - suppression et ajustement manuelle pour faire correspondre les frontières aux limites terre mer. Couche "frontiere"
- Les trois couches vecteur
  - Fusionner des couches vecteur
  - Edition, calculatrice de champ, mise à jour du champ "fid", @row_number
  - buffer 50m

- create_exutoire.py pour créer les différentes couches exutoire à partir de la limite terre mer, les plans d'eau sélectionnés et les frontières ajustées aux limites terre mer.

## Création du référentiel hydrographique de la France métropolitaine

Le référentiel hydrographique vise à être réseau des cours d'eau français, coulant et topologiquement juste. On doit pouvoir retrouver l'ensemble des affluents d'un fleuve en remontant le sens de l'écoulement vers l'amont à partr de l'exutoire. 

Depuis la couche troncon_hydrographique de la BD TOPO:
- prendre les tronçons avec liens_vers_cours_d_eau IS NOT NULL or EMPTY
  - SELECT * FROM troncon_hydrographique WHERE liens_vers_cours_d_eau IS NOT NULL AND liens_vers_cours_d_eau != ''; Le nom de la couche est troncon_hydrographique_cours_d_eau.
- Quatre types d'erreur à corriger mais les corrections ne se font pas directement dans la couche troncon_hydrographique_cours_d_eau pour mieux assurer la tracabilité et la reproductibilité à une autre version de la BD TOPO : 
  - Des confluences non connectées ou des cours d'eau trop loin des exutoire. Il s'agit alors de regarder sur la couche troncon_hydrographique complète les tronçons, sélectionner les tronçons manquant, les enregistrer dans une nouvelle couche geopackage et leur mettre l'identifiant de cours d'eau auquels ils sont rattachés dans le champ liens_vers_cours_d_eau. Le nom de cette couche est troncon_hydrographique_cours_d_eau_conn.
  - Des confluences non connectées ou des cours d'eau trop loin des exutoire mais sans troncons existant pour compléter les connexions. Il faut alors modifier la géométrie d'un tronçon pour permettre la liaison ou l'extension du cours d'eau. Il s'agit alors de sélectionner le tronçon à modifier, l'enregister dans une couche de modification puis modifier cette nouvelle entité dans cette même couche. La couche de modification est troncon_hydrographique_cours_d_eau_modif_geom
  - Des sens d'écoulement sont erronnés et doivent être inversé. Les tronçons concernés sont sélectionnés puis enregistrés depuis troncon_hydrographique_cours_d_eau_corr_dir_ecoulement.
  - Les deux configuration peuvent parfois être présentes, il faut donc ajouter un tronçon puis inverser le sens d'écoulement. La couche de modification est troncon_hydrographique_conn_corr_dir_ecoulement.
- Ces corrections sont effectuées à partir des fichiers gpkg créés avec un script pyqgis pour chaque type d'erreur.
- IdentifyNetworkNodes de la FCT QGIS
- sélection spatiale depuis le buffer de la couche exutoire
- SelectConnectedReaches de la FCT QGIS avec option upstream/downstream pour sélectionner tous les tronçons amont et aval connectés
- export des tronçons sélectionnées (troncon_hydrographique_corr_reaches_connected)
- vérification des doublons
- AggregateStreamSegments de la FCT QGIS pour refaire la segmentation des tronçons aux intersections, couche referentiel_hydrographique
- A FAIRE! découper les tronçons avec l'emprise du MNT utilisé pour la FCT

![Production workflow](referentiels_workflow.png)
## Création du référentiel hydrographique de la France métropolitaine sur les surfaces hydrographiques

Pour les cours d'eau supérieur à 5m de large et faire correspondre la carte d'occupation du sol au réseau hydrographique le référentiel hydrographique est découpé selon la surface en eau de nature "écoulement naturel"

Depuis le référentiel hydrographique (1_referentiel_hydrographique) : 
- Supprimer les colonnes GID, LENGTH, CATEGORYn NODEA, NODEB.
- QGIS splitwithlines
- QGIS multiparttosingleparts
- Python FeatureInPolygonWithDistance (voir github Louis Manière gis_python_tools avec la couche surface_hydrographique nature = 'Ecoulement naturel')
- QGIS deleteduplicategeometries
- FCT-QGIS IdentifiedNetworkNodes
- FCT-QGIS AggregateStreamSegments (2_referentiel_hydrographique_surface)

## Mise application QGIS

Import des données IGN SQL dans une base de données PostgreSQL/PostGIS

Ajout de la couche tronçon hydrographique : 
```
SELECT * FROM troncon_hydrographique WHERE liens_vers_cours_d_eau IS NOT NULL AND liens_vers_cours_d_eau != '';
```
Enregistrement dans le geopackage reference_hydrographique.gpkg|troncon_hydrographique_cours_d_eau_corr

Lancement des script de correction dans la console Python de QGIS : 

```
import os

os.chdir("path/to/")

./correction_files/fix_connection_and_direction.py
./correction_files/fix_connection.py
./correction_files/fix_direction.py
./correction_files/fix_modified_geom.py
```

## Autre

SELECTION DE PAR ORDRE DE STRAHLER ??
Couche troncons_hydrographiques:
- cpx_toponyme_de_cours_d_eau NOT NULL
- IdentifyNetworkNodes, sélection de l'exutoire puis de tous les troncons amonts
- MeasureNetworkFrom Outlet + Hack Order + Stralher
- LENGTH > 5000 OR STRALHER > 1
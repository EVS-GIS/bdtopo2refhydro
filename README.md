# bdtopo2refhydro

BDTOPO2REFHYDRO vise la création d'un réseau hydrographique utilisable pour l'analyse hydromorphologique sur le territoire métropolitain à partir de la BD TOPO de l'IGN.
Ce référentiel hydrographique est un réseau des cours d'eau français, coulant d'amont vers l'aval et topologiquement juste. On doit pouvoir retrouver l'ensemble des affluents d'un fleuve en remontant le sens de l'écoulement vers l'amont à partr des exutoires.

Mise en application sur la BD TOPO IGN 2021 sur la France métropolitaine.

**Dépendance**
Le plugin Fluvial Corridor Toolbox est nécessaire pour effectuer l'ensemble des opérations. Pour l'installation, se reporter au [github](https://github.com/tramebleue/fct-qgis).
Développé et testé sur QGIS 3.22.16 et la Fluvial Corridor Toolbox 1.0.9

## Création de la bande des exutoires
La bande des exutoires vise à créer une zone permettant de sélectionner l'ensemble des exutoires des fleuves français. L'objectif est de pouvoir sélectionnner l'ensemble d'un réseau hydrographique bien orienté et connecté en remontant vers l'amont.

La bande des exutoires prend en compte des données issues de la BD TOPO IGN et sont enregistrées dans creation_exutoire.gpkg : 
- La limite terre mer de la France métropolitaine pour les exutoires marins ("SELECT * FROM limite_terre_mer;" puis sélection manuelle de la France métropolitaine). => couche "limite_terre_mer".
- Des plans d'eau et lagunes. Deux plans d'eau particuliers : le lac du Bourget, le lac d'Annecy et des lagunes méditerranéennes comme celle de Thau car le réseau hydrographique de la couche cours d'eau de l'IGN ne va pas toujours au delà de la lagune et la couche limite_terre_mer ne rentre pas toujours suffisamment dans les lagunes pour atteindre le réseau hydrographique. Il y a donc une déconnexion entre les exutoires et la mer. Sélection manuelle depuis la couche plan_d_eau => plan_d_eau_selected
- Les frontières pour les réseaux des bassins qui s'écoulent en dehors de la France. Quelques traitements ont été nécessaires : 
  - Fusion des polygones bassin_versant_topographique de la BD TOPO
  - Réparer les géométries
  - Polygones vers polylignes => "bassin_versant_topographique_ligne"
  - Suppressions et ajustements manuels pour faire correspondre les frontières aux limites terre mer. => Couche "frontiere"

La création de la bande des exutoires est effectué par le script "create_exutoire.py".
## Création du référentiel hydrographique

Les tronçons hydrographiques de la BD TOPO IGN sont ajustés afin d'avoir un réseau continu des cours d'eau qui s'écoulent le l'amont vers l'aval sans rupture.
Depuis la couche troncon_hydrographique de la BD TOPO:
- Sélection des cours d'eau depuis les tronçons hydrographiques :
  - SELECT * FROM troncon_hydrographique WHERE liens_vers_cours_d_eau IS NOT NULL AND liens_vers_cours_d_eau != ''; Les noms du fichier gpkg et de la couche est troncon_hydrographique_cours_d_eau. troncon_hydrographique_cours_d_eau_corr est une copie de troncon_hydrographique_cours_d_eau sur lesquels les corrections sont effectuées.
- Cinq types d'erreur sont à corriger, les entités sont enregistées dans des couches distinctes dans ./inputs/corr_reseau_hydrographique.gpkg et sont alimentées au fur manuellement pour assurer la traçabilité des modifications.
  - "troncon_hydrographique_cours_d_eau_conn" rétablie des connections du réseau ou vers les exutoires finaux. Les tronçons sont issus de troncon_hydrographique non filtrée, identifiant du cours d'eau auquels ils sont rattachés est ajouté au champ liens_vers_cours_d_eau.
  - "troncon_hydrographique_cours_d_eau_modif_geom" sont des modifications de la géométrie de tronçons pour permettre la liaison aux exutoires finaux ou la connection lorsque des tronçons n'exsite pas dans la couche troncon_hydrographique non filtrée.
  - "troncon_hydrographique_cours_d_eau_corr_dir_ecoulement" contient les tronçons dont le sens d'écoulement doit être inversé pour permettre une continuité amont-aval.
  - "troncon_hydrographique_conn_corr_dir_ecoulement" mélange deux types de correction. Les tronçons de la couche doivent être ajouté pour assurer des connections puis leur sens d'écoulement inversé pour assurer l'écoulement vers l'aval.
  - "troncon_hydrographique_corr_suppr_canal" contient les canaux à supprimer pour avoir un réseau des cours d'eau uniquement (les cours d'eau chenalisés sont néanmoins conservés).
- Depuis la bande des exutoires, les exutoires des tronçons hydrographiques corrigés sont sélectionnés puis le réseau hydrographique connecté à ces exutoires sont sélectionnées en remontant l'écoulement (la direction des segments du réseau). Une sortie par tronçon est exporté "reference_hydrographique_troncon" avec ces tronçons sélectionnés. Une autre sortie est générée avec les tronçons aggrégés à chaque intersection du réseau.

![Production workflow](referentiels_workflow.png)

## Mise application QGIS

Import des données IGN SQL dans une base de données PostgreSQL/PostGIS

Extraction de la couche tronçon hydrographique depuis cette base de données : 
``` sql
SELECT * FROM troncon_hydrographique WHERE liens_vers_cours_d_eau IS NOT NULL AND liens_vers_cours_d_eau != '';
```

**Pas de régionalisation actuellement**
<!-- ou extraction dans une zone spécifique, exemple dans la région hydrographique de l'Isère : 
``` sql
SELECT troncon_hydrographique.*
FROM troncon_hydrographique , region_hydrographique
WHERE (liens_vers_cours_d_eau IS NOT NULL AND liens_vers_cours_d_eau != '')
AND (ST_Within(troncon_hydrographique.geom, region_hydrographique.geom)
	 AND region_hydrographique.cdregionhy = 'W')
``` -->

Enregistrement dans le geopackage ./outputs/troncon_hydrographique_cours_d_eau_corr.gpkg|troncon_hydrographique_cours_d_eau_corr

Le programme create_reference_hydro_workflow.py permet de lancer les différents scripts de corrections sur troncon_hydrographique_cours_d_eau_corr, créer la couche d'éxutoire et extraire de l'ensemble du réseau hydrographique en remontant depuis ces exutoires et enregister le référentiel hydrographique dans reference_hydrographique.gpkg. Ce programme se lance directement depuis la console Python de QGIS.

## Création du référentiel hydrographique des cours d'eau de plus de 5m de large de la France métropolitaine sur les surfaces hydrographiques

Dans la définition de la BD TOPO, les surfaces en eaux des cours d'eau de plus 5m de large sont enregistrées dans la couche surface_hydrographique. On y trouve donc les surfaces en eau des écoulements naturels du réseau hydrographique mais également les retenues des barrages, situées sur l'écoulement naturel. L'objectif est t'utiliser les surfaces hydrographiques pour obtenir un réseau hydrographique des cours d'eau de plus 5m de large. La mise en application peut s'effectuer à différentes échelle, ici par région hydrographique. Ce réseau est donc effectué sur la référence hydrographique produite à partir de la BD TOPO des autres outils, au choix sur les tronçons ou les segments (plus rapide sur les segments).

La couche surface_hydrographique doit donc être chargé dans une base de données PostgreSQL/PostGIS.

Extraction des données d'écoulement naturel et des lacs de retenue des barrages.
``` sql
SELECT * FROM surface_hydrographique WHERE nature LIKE 'Ecoulement_naturel' OR nature LIKE 'Retenue-barrage'
```

Si effectué sur une zone spécifique : 
- Extraire selon la zone de travail souhaité, QGIS:extractbylocation (est à l'intérieur), dans outputs/hydrographie_cours_d_eau_5m.gpkg | surface_hydrographique_naturel_retenue
- Extraire selon la zone de travail souhaité, QGIS:extractbylocation (est à l'intérieur), dans outputs/hydrographie_cours_d_eau_5m.gpkg | reference_hydrographique_segment_zone

Lancer create_5m_width_hydro_network pour créer reference_hydrographique_5m dans reference_hydrographique.gpkg.

## TODO

### Régionalisation
Possibilité de créer le réseau de référence en mettant en entrée un autre réseau autre que celui de la France métropolitaine dans sa totalité.

### Agrégation par cours d'eau ?
- Aggregation by liens_vers_cours_d_eau  - Non trop d'erreur ou de particularités sans correction auto (prendre une référence, exutoire ou source que l'on propage en amont ou à l'aval)
- Correction des noms de cours : 
  - changement de nom uniquement aux confluence, sinon poursuite le nom de l'amont prioritaire sur l'aval? (voir outputs/test_corr_nom_cours_d_eau.gpkg)

### Suppr canal
- En cours

### Multichenaux
- voir fct principal stem
### Ajout des Ordre de Strahler?
Couche troncons_hydrographiques:
- cpx_toponyme_de_cours_d_eau NOT NULL
- IdentifyNetworkNodes, sélection de l'exutoire puis de tous les troncons amonts
- MeasureNetworkFrom Outlet + Hack Order + Stralher
- LENGTH > 5000 OR STRALHER > 1


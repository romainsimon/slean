import VersoManual
import Slean

open Verso.Genre Manual
open Verso.Genre.Manual.InlineLean

#doc (Manual) "Slean" =>
%%%
shortTitle := "Slean"
%%%

Suivre une décision de recherche jusqu'aux éléments qui l'étayent.

Slean est une bibliothèque Lean 4 et un outil JSON qui permettent d'examiner un dossier de recherche. Il vérifie la structure, les références, la chronologie, les règles décimales exactes et une trace source bornée. Le premier exemple est synthétique ; Slean ne démontre aucune affirmation empirique.

Version de développement · schéma 0.2.0 · Lean 4.28.0. Aucun tag n'est sélectionné pour ce build.

Exécutez le cas vérifié depuis la racine du dépôt :

```
lake exe slean validate examples/valid.json
```

L'outil renvoie :

```
{"case_id":"synthetic-decision-1","events":10,"ok":true}
```

Poursuivez avec le guide de démarrage pour examiner un préfixe du journal et l'export destiné à l'agent.

# Commencer par un cas vérifié
%%%
file := "commencer-par-un-cas-verifie"
tag := "commencer-par-un-cas-verifie"
%%%

La première étape consiste à valider le dossier synthétique fourni avec ce dépôt. Avec Lean 4.28.0 et Lake installés, exécutez ces commandes depuis la racine du dépôt :

```
lake build
lake exe slean validate examples/valid.json
lake exe slean replay examples/valid.json 7
lake exe slean export examples/valid.json agent
```

La commande de validation renvoie :

```
{"case_id":"synthetic-decision-1","events":10,"ok":true}
```

Le rejeu du préfixe renvoie l'état après sept événements. L'export pour l'agent retire les objets réservés au propriétaire avant de calculer le dossier visible. L'exemple est synthétique et ne contient aucun résultat scientifique.

Le même dossier peut être construit en Lean :

```lean
#check Slean.CaseFile
#check Slean.replay
#check Slean.assessExact
```

Ces déclarations sont compilées avec la version de Lean fixée par le projet lors de la construction du manuel. L'exemple typé complet se trouve dans `examples/Synthetic.lean` ; `bash tests/check.sh` le compile et compare, octet par octet, son export JSON pour l'agent avec celui de l'exemple JSON.

# Lire la décision
%%%
file := "lire-la-decision"
tag := "lire-la-decision"
%%%

Une `Observation` indique une exécution antérieure, une métrique, une unité, une valeur ou un état inconnu, une référence d'artefact et une date. Une `Assessment` cite des observations antérieures selon un protocole figé. Une promotion ordinaire (`promote`) exige une évaluation locale exacte et positive. Une dérogation humaine (`override`) exige une justification et reste distincte d'un résultat `pass`.

```lean
#check Slean.FrozenProtocol
#check Slean.Observation
#check Slean.Assessment
#check Slean.PromotionDecision
```

Une seule métrique décimale exacte et une seule observation peuvent suffire au comparateur local. Les règles externes peuvent citer plusieurs observations, mais conservent l'état `external_unverified`. La réussite de la compilation ne transforme pas une comparaison de modèles externes en vérité scientifique.

# Suivre la provenance
%%%
file := "suivre-la-provenance"
tag := "suivre-la-provenance"
%%%

Le schéma 0.2 peut conserver un manifeste source entièrement analysé, un protocole et un flux d'événements sous forme de chaînes JSON canoniques réservées au propriétaire. L'adaptateur borné vérifie un premier gel unique, l'ordre des événements source, les liens entre prédictions et observations, la cohérence de l'achèvement avec le manifeste et la couverture typée de chaque observation source.

```lean
#check Slean.SourceRecord
#check Slean.validateSourceTrace
```

L'adaptateur source lit une trace en mémoire et n'affiche qu'un rapport agrégé. Il n'enregistre pas le dossier privé. Les octets des artefacts source restent à leur emplacement d'origine ; l'adaptateur calcule leur SHA-256 et Lean vérifie les liens vers les empreintes fournies. Slean n'exécute ni ne certifie l'évaluateur externe.

# Format et API
%%%
file := "format-et-api"
tag := "format-et-api"
%%%

`schema/v0.1.0.schema.json` décrit la structure initiale du dossier sur le fil. `schema/v0.2.0.schema.json` ajoute les enregistrements source. `schema_version` et `semantics_version` doivent correspondre à une paire prise en charge. Il n'y a pas de migration implicite.

```lean
#check Slean.Event
#check Slean.step
#check Slean.project
#check Slean.view
```

La CLI prend en charge `validate`, `replay`, `export`, `view` et `proof` avec un chemin de dossier ou `-` pour l'entrée standard. Exécutez `lake exe slean proof-statement` pour consulter l'unique énoncé de théorème local fixé par le projet et la version de l'outillage. Un texte d'état de preuve importé ne suffit jamais à accorder `kernel_checked`.

# Limites et état du développement
%%%
file := "limites-et-etat-du-developpement"
tag := "limites-et-etat-du-developpement"
%%%

Il s'agit d'un prototype local antérieur à toute publication. L'évaluation de la trace source reste `external_unverified` ; le contenu des artefacts, les horloges externes, la logique de l'évaluateur, la vérification indépendante des preuves et l'exactitude scientifique ne sont pas couverts par le théorème Lean. La licence publique, la visibilité du dépôt, le déploiement d'un domaine et les intégrations nécessitent encore des décisions distinctes.

La construction compile les exemples et exécute les tests avant de créer l'artefact du site. Le fichier `build-info.json`, dans le répertoire du site généré, enregistre le commit de base et indique si l'arbre source était propre. Une construction sur un arbre propre identifie exactement son commit source.

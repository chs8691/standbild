# Hugo album collection based on hugo-theme-gallery by Nico Kaiser

Jedes Bild wird als Post angelegt und in genau ein Album eingeordnet. Die Haupseite listet die Albums nach dem letzten Update. Ein Album wird als 'Album-Card' mit seinem neuesten Foto dargestellt. Das Album mit dem neuesten Bild wird als 'featured' groß dargestellt. 

Mit der Taxonomie von Hugo können die Bilder darüberhinaus nach Attributen (Terms) dargestellt werden. Die Liste der Taxonomien wird as Button-Reihe auf der Hautseite gelistet.

Die Posts liegen als Bundle-Verzeichnis direkt in den Album-Verzeichnissen, alles liegt in `/content`. Für jedes Bild ist ein Post in einem Verzeichnis mit der Bilddatei und der `index.md`-Datei anzulegen.


## Installation
Beschreibt, wie das hugo-Projekt mit dem Theme als git submodel incl. den Demo-Bildern erstellt wird.

Hugo muss installiert sein.
Installationsverzeichnis: `~/dev/standbild`
Repository auschecken.

```zsh
cd ~/dev/
git clone https://github.com/chs8691/standbild.git
cd standbild
git submodule add --depth=1 https://github.com/nicokaiser/hugo-theme-gallery.git themes/gallery
```

## Template and data organization

Das urspüngliche Gallary-Theme wurde um `Section` erweitert - so können die Bilder als Posts abgelegt werden können.

```plain
content/
├── arbeitswelten/     <--- Album
│   ├── _index.md      <--- Definiert hiermit eine Section
│   ├── 20250101/      <--- Post
│   |   ├── index.md
│   |   ├── img01.jpg
│   └── 20250102/
│       ├── index.md
│       └── img02.jpg
├── album2/
|     ... 
├── filmsimulation/    <--- Taxonomy
│   ├── _index.md      <--- Taxonomy's meta data 
│   ├── classic-neg/   <--- Term
│   |   └── _index.md  <--- Term's meta data
│   ...
```

## Datenbereitstellung mittels Skript.
Alles für den Aufbau und zur Darstellung soll in den Index-Dateien liegen. Das Template ist dahingehend konzipiert und so sind wenig Anpassungen nöitg.
Das bedeutet aber, dass mit jedem neuen Post die Index-Dateien das betroffene Albums sowie des Featured-Albums anzupassen sind. Dazu dient das Python-Script in `/scripts`. Das Import-Verzeichnis dieht als Eingang. Original-Dateien werden hier hineingeworfen. 

Die Aufgaben des Skriptings sind:

- Auslesen der Meta-Daten aus einm Bild
  - /import: JPG --> PY-DICT
  - PY: Ermitteln des Albums
- Verkleinern eines Bildes
  -  /import: JPG --> JPG
- Erstellen der index-Datei für den Post
  -  /import: index.md
- Anlegen des Posts:
  - /content: Verzeichnis erstellen und Dateien mv
- Aktualisieren des Featured-Flag
  - isolierte Funktion, unabhängig vom Import
  - /content
    - Lies alle Albumdaten ein
    - Bestimme Featured Album
    - Update der alten Albums
    - Update des neuen Albums



Das `import`-Verzeichnis:
- Flache Struktur, Unterverzeichnisse werden nicht berücksichtigt
- Verarbeitete Bilder und erzeugt MDs werden aus dem Verzeichnis gelöscht




## Troubleshooting

### Not allowed to load local resource
E.g. file:///livereload.js?mindelay=10&v=2&port=1313&path=livereload
Die lokal gestartete Website zeigt keine Style und die Kosole wirft diese Fehler.

Wahrscheinlich wurde die Datei index.html geöffnet, anstatt den Server aufzurufen:

    http://localhost:1313

### failed to load modules
Falls es beim Starten es Servers zum Fehler kommt:
    
    Error: command error: failed to load modules: module "github.com/nicokaiser/hugo-theme-gallery/v4" not found 

Dann muss Section `[module]` ais config/_default/hugo.toml entfernt werden:

    [module]
        [module.hugoVersion]
            min = "0.121.2"
        [[module.imports]]
            path = "github.com/nicokaiser/hugo-theme-gallery/v4"

### <.Page.Permalink>: nil pointer evaluating page.Page.Permalink
Der Build mit `hugo` scheitert, wenn es keinen einzigen Post gibt.


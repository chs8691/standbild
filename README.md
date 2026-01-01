# Hugo album collection based on hugo-theme-gallery by Nico Kaiser

Jedes Bild wird als Post angelegt und in genau ein Album eingeordnet. Die Haupseite listet die Albums nach dem letzten Post sortiert auf. Ein Album wird als 'Album-Card' mit seinem neuesten Foto dargestellt. Das Album mit dem neuesten Bild wird als 'featured' groß dargestellt. 

Mit der Taxonomie von Hugo können die Bilder darüberhinaus nach Attributen (Terms) dargestellt werden. Die Liste der Taxonomien wird as Button-Reihe auf der Hautseite gelistet.

Die Posts liegen als Bundle-Verzeichnis direkt in den Album-Verzeichnissen, alles liegt in `/content`. Für jedes Bild ist ein Post in einem Verzeichnis mit der Bilddatei und der `index.md`-Datei anzulegen.

```mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```

## Installation und Setup gitHub
Beschreibt, wie das hugo-Projekt mit dem Theme als git submodel incl. den Demo-Bildern erstellt wird.

Hugo muss installiert sein.
Installationsverzeichnis: `~/dev/standbild`
Repository auschecken.

```zsh
cd ~/kollegen/
git clone https://github.com/chs8691/standbild.git
cd standbild
git submodule add --depth=1 https://github.com/nicokaiser/hugo-theme-gallery.git themes/gallery
```

Als Vorlage das Verzeichnis `/content` und das Import-Verzeichnis für das Skript erstellen:

```zsh
mkdir content
cp -r content-template/* content/
mkdir import
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

## Datenbereitstellung der Posts mittels Skript.

Neue Bilder werden per Skript eingearbeitet, indem dafür ein **Post** angelegt wird. Dafür müssen die Bilder EXIF-Tags enthalten. Diese Tag-Informationen werden vom Skript in die index.md-Datei des Posts eingearbeitet (`index.md`). Die Hugo-Templates sorgen dafür, das die Website nur anhand dieser Informationen aufgebaut wird. Die Index-Datei von Album und Taxonomie dageben beinhalten lediglich statische Beschreibungen (`_index.md`). Das Album mit dem neusten Bild wird als automatisch als _featured_ dargestellt. Sortierung und Bildauswahl erfolgt ebenfalls anhand der Posts.

Übersicht über die relevante Dateistruktur:

```plain
├── content/           <--- Zielverzeichnis 
├── import/            <--- Quellverzeichnis, Original hier hineinkopieren
├── scripts/           <--- Python-Bereich
│   ├── import.py      <--- Skript 
```

### Felder in Index.md

Exif-Tags werden wie folgt gemappt:

| Exif-Tag|index.md-Tag|Info|Beispielwert in index.md
|-|-|-|-
|XMP:Caption|title|  | Die Bekanntmachung 
|EXIF:DateTimeOriginal|date|  | 2020-11-01T13| | |59| | |39
|EXIF:DateTimeOriginal|year|  | 2020
|XMP:TagsList|recipe| Taxonomy | Kodak Portra 160 v2
|XMP:TagsList|recipe_source| Taxonomy | Fuji X Weekly
|EXIF:Make|make|  | FUJIFILM
|EXIF:LensModel|lens| Taxonomy | XF18-55mmF2.8-4 R LM OIS
|EXIF:Model|model| Taxonomy | X-E2S
|XMP:TagsList|sooc|  | True
|XMP:TagsList|filmsimulation| Taxonomy | Classic Chrome
|XMP:TagsList|bw|  | False
|EXIF:ImageDescription|description|  | > <br>   &ensp;Orte 23
|EXIF:GPSLatitude<br>EXIF:GPSLatitudeRef|lat| Taxonomy | 50.3458452000389
|EXIF:GPSLongitudeRef<br>EXIF:GPSLongitude|lon| Taxonomy | 9.55684890000278

Struktur der XMP:TagsList beinhalten **Album**, **Filmsimulation** und **Recipe**:
* `Fuji-X/[BW|Color]/<ALBUM_NAME>` bestimmt das Album
  * z.B. `Fuji-X/color/Classic Chrome`
* `Serie/<ALBUM_NAME>` bestimmt das Album
  * z.B. `Serie/pendel`
* `Recipe/<REZEPT_QUELLE><REZEPT_NAME>` bestimmt das Rezept
  * z.B. `Recipe/Fuji X Weekly/Agfa APX 400`

Aus den **GEO-Koordinaten** wird die Andresse ermittelt: _country_, _state_, _region_, _city_ und _plz_.

Feld **location** wird aus diesen Werten ermittelt (Skript-Parameter _treshold_), je nach der Anzahl der Bilder in einer Stadt, Region oder Bundesland. 


Die Aufgaben des Skriptings sind:

- Auslesen der Meta-Daten aus einm Bild
  - /import: JPG --> PY-DICT
  - PY: Ermitteln des Albums
- Verkleinern des Bildes
  -  /import: JPG --> /import/tmp/JPG
- Erstellen der index-Datei für den Post
  -  /import/tmp: index.md
- Anlegen des Posts:
  - /import/tmp/ --> /content/\<ALBUM\>/
- Bestimmen von Location durch Analyse/Update aller Posts
  - /content/\*/index.md --> /content/\*/index.md


Das `import`-Verzeichnis:
- Zu verarbeitende **Kopien** der Originalen Foto-Dateien.
- ACHTUNG: Alle Dateien im `Import`-Verzeichnis werden nach erfolgreicher Verarbeitung gelöscht.
- Verkleinerte Bilder und erzeugte index.md werden aus dem content-Verzeichnis gelöscht (Unterverzeichnis `tmp`).

### Ausführen

Einmalig ins script-Verzeichnis wechseln und eine venv mit `requirement.txt` aufsetzen. Dann die getaggten Bilder in das Import-Verzeichnis kopieren. 

Post erstellen, Addressen ermitteln und Location aller Bilder neu bestimmen:

```plain
 venv/bin/python import.py -s ../import -d ../content --location --address --check
```

Mit `--check` wird geprüft, ob ein Bild mehrfach vorkommt. 


## Lokaler Test mit Hugo

Hugo wacht über Änderungen in dem Verzeichnis und stellt einen lokalen Webserver zur Verfügung. Starten:

```zsh
hugo server -D
```
bzw.
```zsh
rm -r public && hugo server -D
```

Wird die Seite erfolgreich generiert, kann diese dann im Browser gestartet werden.

```zsh
Web Server is available at http://localhost:1313/ (bind address 127.0.0.1) 
Press Ctrl+C to stop
```

## Verteilung


```plantuml
node github {
  rectangle standbild
}
node "uberspace:Kollegen" as uberspace {
  rectangle "~/html" as html
}
node  macbook {
  rectangle "~/kollegen"  { 
  rectangle "/standbild" as working {
    rectangle "/public" as public
  }
  }
}

standbild -- working: git
html <-- public: deploy.sh

```

## Setup Uberspace

Die generierte Website wird mit dem html-Verzeichnis auf Ueberspace synchronisiert. Es liegt dort also nur der fertige Content. 

Das Publishing erfolgt in das Website-Vezeichnis /home/kollegen/html/standbild. Der zugreifende Gitea-User muss den ssh-Key konfigurierte haben, damit git und rsync per ssh genutzt werden kann. 
Hugo wird nicht benötigt; stattdessen wird der fertige Content hochgeladen.

### Subdomain

Die Seite soll unter der Subdomain standbild.kollegen.uber.space erreichbar sein 
(und nicht unter kollegen.uber.space/standbild). 

Einrichten der Subdomain:

```zsh
[kollegen@despina ~]$ uberspace web domain add standbild.kollegen.uber.space
```

Der Webcontent für diese Subdomain muss in einem gleichnamigen Verzeichnis neben dem html-Verzeichnis liegen. 
Dieser Content wird per lokalem Skript `deploy.sh` angelegt. Es wird einmalig das leere Verzeichnis 
angelegt und ein symbolischer Link im Home-Verzeichnis erstellt:


```zsh
[kollegen@despina ~]$ mkdir /var/www/virtual/kollegen/standbild.kollegen.uber.space
[kollegen@despina ~]$ ln -s /var/www/virtual/kollegen/standbild.kollegen.uber.space ~/standbild.kollegen.uber.space
```

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


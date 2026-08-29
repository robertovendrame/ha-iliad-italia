# Iliad Italia for Home Assistant

Custom integration non ufficiale per Home Assistant che legge i dati dell'Area Personale Iliad Italia.

> Stato: **testata con account Iliad reali**, inclusa la configurazione contemporanea di due SIM/account nella stessa istanza Home Assistant.

## Versioni

- stabile: **v0.6.0**
- sviluppo/test: nessuna pre-release corrente

Le GitHub Releases sono il riferimento per installazione e aggiornamento tramite HACS. Le versioni `alpha`, `beta` e `rc` vengono pubblicate come pre-release.

## Funzioni

Ogni account/SIM crea un device separato con:

- ID utente Iliad mostrato dal portale;
- numero di telefono della linea;
- nome offerta/piano quando riconosciuto;
- costo dell'offerta al rinnovo;
- credito disponibile;
- plafond dati ufficiale quando presente nella pagina Iliad;
- dati utilizzati e residui;
- dati totali calcolati (`usati + residui`) come valore di compatibilità/diagnostica;
- percentuale dati utilizzati e residui;
- plafond dati estero/roaming;
- dati utilizzati e residui estero;
- percentuale dati utilizzati e residui estero;
- durata chiamate del periodo corrente;
- costo chiamate;
- SMS inviati e relativo costo extra;
- MMS inviati e relativo costo;
- data rinnovo e giorni al rinnovo;
- inizio e fine periodo di riferimento;
- consumo medio giornaliero stimato;
- budget dati giornaliero fino al rinnovo;
- dati previsti al rinnovo;
- binary sensor **Rischio esaurimento prima del rinnovo**;
- binary sensor **Dati in esaurimento**;
- binary sensor **Credito basso**;
- ultimo aggiornamento riuscito;
- pulsante **Aggiorna ora**.

Quando il plafond ufficiale è disponibile, le percentuali vengono calcolate su quel valore; in caso contrario l'integrazione usa `dati usati + dati residui` come fallback.

## Installazione tramite HACS

1. Apri HACS.
2. Vai in **Custom repositories**.
3. Aggiungi `https://github.com/robertovendrame/ha-iliad-italia` come **Integration**.
4. Installa **Iliad Italia**.
5. Riavvia Home Assistant.
6. Vai in **Impostazioni → Dispositivi e servizi → Aggiungi integrazione → Iliad Italia**.

Per provare una futura beta, abilita le pre-release per la repository HACS e scegli la versione desiderata.

## Multi-SIM

Ogni account Iliad usa una sessione HTTP e un cookie jar dedicati. Questo evita conflitti tra più SIM configurate nella stessa istanza Home Assistant.

Il comportamento multi-SIM è stato verificato con due account Iliad reali contemporaneamente.

## Offerta e plafond dati

Dalla versione **0.5.0** l'integrazione tenta di leggere direttamente dalla pagina Iliad anche il nome commerciale dell'offerta, il plafond dati ufficiale e il costo al rinnovo.

Il parser è stato irrobustito per gestire markup suddiviso, etichette generiche del portale e separatori decorativi. Quando il plafond ufficiale non è disponibile, le percentuali continuano a usare `dati usati + dati residui` come fallback.

## Roaming / Estero

Dalla versione **0.6.0** l'integrazione legge anche il contatore dati separato della sezione Estero quando presente nel portale Iliad.

Sono esposti:

- plafond dati estero;
- dati utilizzati estero;
- dati residui estero;
- percentuale utilizzata estero;
- percentuale residua estero.

Il parser supporta valori espressi in B, KB, MB, GB e TB e normalizza i dati in GB. Se Iliad espone uso e plafond ma non un valore residuo separato, il residuo viene derivato come `plafond - utilizzato`.

Il supporto è stato verificato su due offerte reali con plafond roaming differenti, rispettivamente da 23 GB e 12 GB.

## Voce, SMS e MMS

Dalla versione **0.6.0** vengono letti anche i riepiloghi del periodo corrente mostrati nella pagina consumi:

- durata complessiva chiamate;
- costo chiamate;
- numero SMS inviati;
- costo SMS extra;
- numero MMS inviati;
- costo MMS.

L'integrazione non importa lo storico delle singole comunicazioni e non raccoglie i numeri telefonici presenti nel dettaglio chiamate/SMS/MMS.

## Identificativi account e linea

Dalla versione **0.6.0** vengono esposti anche:

- **Utente Iliad**, corrispondente all'`ID utente` mostrato dal portale;
- **Numero di telefono**, corrispondente alla `Linea` mostrata nel menu account.

Questi valori vengono letti dal blocco account comune del portale, utilizzando le etichette esplicite `ID utente:` e `Linea:` per evitare di interpretare altri numeri presenti nelle pagine.

Per motivi di privacy, ID utente e numero di telefono non vengono inclusi nella diagnostica e non vengono utilizzati come unique ID delle entità.

## Branding locale

Dalla versione **0.5.2** il progetto include un set brand locale completo per Home Assistant sotto `custom_components/iliad_ita/brand/`, con icone e logo per temi chiari e scuri. L'icona utilizza una SIM bianca con `i` rossa e ombra, in modo da mantenere contrasto su sfondi diversi.

HACS può continuare a mostrare `icon not available` nella propria lista repository anche quando Home Assistant usa correttamente gli asset locali: il comportamento dipende dal supporto HACS al branding delle custom integration.

## Rinnovo, periodo e proiezioni

L'integrazione legge il periodo di riferimento reale dalla pagina Iliad. Quando la data di rinnovo esplicita non è disponibile nell'HTML statico, viene derivata come giorno successivo alla fine del periodo.

Il consumo medio giornaliero usa l'inizio reale del periodo. Il budget giornaliero divide i GB residui per i giorni mancanti al rinnovo. La previsione dei dati residui al rinnovo applica il consumo medio corrente ai giorni rimanenti.

Queste proiezioni sono calcolate localmente e non sono valori forniti direttamente da Iliad.

## Opzioni per ogni SIM

Da **Impostazioni → Dispositivi e servizi → Iliad Italia → Configura** puoi impostare:

- soglia dati residui in GB, default `10 GB`;
- soglia dati residui in %, default `10%`;
- soglia credito, default `5 €`;
- intervallo aggiornamento da `1` a `24` ore, default `6`.

## Diagnostica, privacy e sicurezza

Dalla versione **0.5.1** la diagnostica non include ID account/unique ID, titolo della config entry, credito esatto o quantità esatte di dati usati/residui. Mantiene soltanto le informazioni necessarie a capire se il parser ha riconosciuto i campi e alcuni metadati non di autenticazione.

Dalla versione **0.6.0**, anche ID utente Iliad e numero di telefono sono esclusi esplicitamente dalla diagnostica. La diagnostica relativa a roaming e voce/SMS/MMS riporta soltanto se i campi sono stati riconosciuti, senza esporre valori identificativi o dettagli delle singole comunicazioni.

L'integrazione usa esclusivamente endpoint Iliad in HTTPS e mantiene una sessione/cookie jar separata per ogni account. Le sessioni vengono chiuse esplicitamente quando l'integrazione viene scaricata o se il setup iniziale fallisce.

Non pubblicare mai username/ID Iliad, password, cookie, header di autenticazione, file HAR o HTML completo catturato da un account reale. Consulta `SECURITY.md` per la policy completa e per la segnalazione privata di vulnerabilità.

## Test automatici

La pipeline **Validate** esegue:

- compilazione Python;
- test automatici `pytest` del parser su HTML realistico anonimizzato;
- HACS Action;
- Home Assistant Hassfest.

Le GitHub Actions usate dalla pipeline sono fissate a commit SHA immutabili e la pipeline di validazione opera con permessi repository in sola lettura.

I test coprono almeno:

- credito, dati usati e residui;
- nome offerta e normalizzazione dei separatori decorativi;
- selezione del nome commerciale rispetto alle etichette generiche del portale;
- plafond ufficiale;
- costo offerta;
- periodo di riferimento;
- rinnovo esplicito e fallback dal termine del periodo;
- roaming/estero con layout e unità differenti;
- riepiloghi voce/SMS/MMS, inclusi valori pari a zero;
- parsing privacy-aware di ID utente e linea;
- compatibilità con pagine senza i nuovi metadati commerciali.

## Segnalazioni

La repository include moduli GitHub dedicati per:

- **Bug report**, con richiesta di versione HA/integrazione e diagnostica privacy-safe;
- **Feature request**, con indicazione del dato Iliad e del caso d'uso in Home Assistant.

Per problemi di sicurezza che potrebbero esporre credenziali, cookie o dati account, non aprire un issue pubblico: segui `SECURITY.md`.

## Come funziona

La versione corrente non usa API Iliad pubbliche documentate. Effettua il login all'Area Personale e legge:

`https://www.iliad.it/account/consumi-e-credito`

Il parser interpreta l'HTML della pagina e i metadati del menu account condiviso. Modifiche al portale Iliad possono quindi richiedere un aggiornamento dell'integrazione.

## Compatibilità

Sviluppata e testata con riferimento a Home Assistant 2026.8.x.

## Ciclo di release

1. aggiorna `custom_components/iliad_ita/manifest.json`;
2. aggiorna `CHANGELOG.md`;
3. verifica che **Validate** sia verde;
4. apri **Actions → Release → Run workflow**;
5. inserisci la versione senza prefisso `v`.

Il workflow verifica la corrispondenza con il manifest, estrae le note dal changelog e crea tag e GitHub Release. Versioni `alpha`, `beta` e `rc` vengono marcate come pre-release.

## Roadmap

Prossimi dati/funzioni da valutare solo se recuperabili in modo affidabile dal portale reale:

- eventuali dettagli aggiuntivi dell'offerta realmente utili in Home Assistant;
- ulteriore hardening del parser;
- ampliamento delle fixture di test con ulteriori varianti del portale Iliad.

Lo storico dettagliato delle singole chiamate/SMS/MMS non è attualmente previsto, per mantenere l'integrazione semplice e limitare il trattamento di dati personali non necessari.

## Origine e attribuzione

Il progetto nasce dallo studio del componente GPL-3.0 `masoneff3/ha_iliad_ita`, che ha dimostrato la fattibilità del login e del recupero dei dati dall'Area Personale Iliad.

Questa implementazione è stata riscritta con architettura Home Assistant moderna: config entries, config flow, client asincrono, DataUpdateCoordinator, supporto multi-account, unique ID e device dedicati.

## Licenza

GPL-3.0. Vedi `LICENSE`.

Iliad e i relativi marchi appartengono ai rispettivi proprietari. Questo progetto non è affiliato né approvato da Iliad Italia S.p.A.

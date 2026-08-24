# Iliad Italia for Home Assistant

Custom integration non ufficiale per Home Assistant che legge i dati dell'Area Personale Iliad Italia.

> Stato: **sperimentale / pre-test**. La versione corrente non è ancora stata validata con un account Iliad reale su Home Assistant.

## Funzioni

Ogni account/SIM configurato crea un device separato con:

- Credito disponibile (`EUR`)
- Dati utilizzati (`GB`)
- Dati residui (`GB`)

L'integrazione supporta:

- più SIM/account Iliad nella stessa istanza Home Assistant;
- installazione della stessa integrazione su più istanze Home Assistant;
- configurazione da UI tramite `config_flow`;
- riautenticazione quando le credenziali non sono più valide;
- riconfigurazione del nome della SIM e delle credenziali;
- sessioni/cookie separati per ogni account configurato;
- aggiornamento cloud ogni 6 ore;
- identificativi stabili senza esporre in chiaro l'ID Iliad negli `unique_id`.

## Installazione tramite HACS — test

La repository è già strutturata come custom repository HACS di tipo **Integration**.

1. Apri HACS.
2. Vai nelle repository personalizzate / **Custom repositories**.
3. Aggiungi `https://github.com/robertovendrame/ha-iliad-italia`.
4. Seleziona la categoria **Integration**.
5. Installa **Iliad Italia**.
6. Riavvia Home Assistant.
7. Vai in **Impostazioni → Dispositivi e servizi → Aggiungi integrazione → Iliad Italia**.

Finché non viene completato il primo test reale, questa installazione va considerata sperimentale.

## Installazione manuale

Copia la cartella:

`custom_components/iliad_ita`

in:

`/config/custom_components/iliad_ita`

Riavvia Home Assistant e vai in:

**Impostazioni → Dispositivi e servizi → Aggiungi integrazione → Iliad Italia**

Per ogni SIM inserisci:

- un nome libero, ad esempio `SIM Casetta`, `SIM Lavoro`, `SIM Backup`;
- ID utente Iliad;
- password Iliad.

Le credenziali vengono salvate nella config entry di Home Assistant e non devono essere inserite nel repository.

## Multi-SIM

Ogni account Iliad usa una sessione HTTP con cookie dedicati. Questo evita che due SIM configurate nella stessa istanza Home Assistant condividano o sovrascrivano la sessione di autenticazione.

Lo stesso account non può essere aggiunto due volte nella stessa istanza, mentre la stessa integrazione può essere usata su istanze Home Assistant differenti.

## Come funziona

La versione corrente non usa API Iliad pubbliche documentate. Effettua il login all'Area Personale e legge la pagina:

`https://www.iliad.it/account/consumi-e-credito`

Il parser interpreta l'HTML della pagina e normalizza i valori di traffico in GB. Modifiche al portale Iliad possono quindi richiedere un aggiornamento dell'integrazione.

## Compatibilità

Sviluppata con riferimento a Home Assistant 2026.8.x.

## Validazione

La repository contiene una GitHub Action che esegue:

- HACS Action, categoria `integration`;
- Home Assistant Hassfest.

La presenza del workflow non sostituisce il test funzionale con un account Iliad reale. Prima della prima release stabile vanno verificati login, parsing dei consumi e comportamento multi-account.

## Roadmap immediata

Dopo il primo test reale verrà verificata la possibilità di aggiungere, se presenti nella pagina Iliad:

- data di rinnovo;
- offerta/piano;
- plafond dati totale;
- numero linea o altro identificativo utile;
- eventuali soglie/stato rinnovo.

## Origine e attribuzione

Il progetto nasce dallo studio del componente GPL-3.0 `masoneff3/ha_iliad_ita`, che ha dimostrato la fattibilità del login e del recupero dei dati dall'Area Personale Iliad.

Questa implementazione è stata riscritta con architettura Home Assistant moderna: config entries, config flow, client asincrono, DataUpdateCoordinator, supporto multi-account, unique ID e device dedicati.

Repository di riferimento:
`https://github.com/masoneff3/ha_iliad_ita`

## Licenza

GPL-3.0. Vedi `LICENSE`.

Iliad e i relativi marchi appartengono ai rispettivi proprietari. Questo progetto non è affiliato né approvato da Iliad Italia S.p.A.

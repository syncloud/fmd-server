# FMD Server for Syncloud

Syncloud package for [FMD Server](https://gitlab.com/fmd-foss/fmd-server), the backend for the
[FMD (FindMyDevice)](https://f-droid.org/packages/de.nulide.findmydevice/) Android app:
locate, ring, lock and wipe your own devices.

Location data and pictures are end-to-end encrypted by the app; the server stores ciphertext
only and never sees the key.

## Accounts and access

There is no Syncloud SSO in front of the app: FMD accounts are not Syncloud accounts. Each
account is a phone, identified by an FMD ID, and its password derives — in your browser or in
the app, never on the server — the key that decrypts that phone's locations and pictures. The
server only ever holds a hash and ciphertext, so no external login can unlock the data.

Accounts are created **from the FMD Android app**, not from the web UI (which only has a login
form): point the app at the app URL, set a password, and give it the registration token below.
The server hands back a generated FMD ID; log into the web UI with that ID and the same
password.

Every account is a peer — the server has no admin/user roles. Operator-level tasks are the
`ctl` command below, which needs shell access to the device.

## Registration token

Registration is closed by default: the installer generates a random registration token and
writes it into the server config. The FMD app must supply it when registering an account.

The token is shown at **`/syncloud`** on the app's own domain, reachable from the "Get
registration token" link that nginx injects into the FMD page. That page is the one path
behind Syncloud SSO, so only the device owner can read it.

Over ssh it is also available as:

    snap run fmd-server.registration-token

and stored in `/var/snap/fmd-server/current/registration.token`.

## Admin CLI

Upstream's admin tool is wrapped as a snap app:

    snap run fmd-server.ctl listusers
    snap run fmd-server.ctl deleteusers --help

## Layout

| Path | What |
|---|---|
| `/var/snap/fmd-server/current/db` | SQLite database (accounts, locations, pictures) |
| `/var/snap/fmd-server/current/config` | generated `fmd-server.yml` and `nginx.conf` |
| `/var/snap/fmd-server/current/fmd.sock` | nginx → fmd-server |
| `/var/snap/fmd-server/common/web.socket` | platform → nginx |

## Logs

    snap logs fmd-server
    journalctl -u snap.fmd-server.fmd-server

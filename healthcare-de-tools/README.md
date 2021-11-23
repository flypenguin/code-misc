# Healthcare Tools

## kvid.py

Generate or validate a [German KV ID](https://de.wikipedia.org/wiki/Krankenversichertennummer) number. Usage:

```bash
$ ./kvid.py gen
B123456782
$ ./kvid.py val B123456782
KV ID is valid.
$ ./kvid.py val B123456783
Invalid KV ID. Checksum should be '2', is: '3'
```

These are valid examples (checked by i-Solutions KIS system):

* `T065283299`
* `T022490904`
* `B123456782`
* `T160509689`
* `T016341281`
* `T098105596`

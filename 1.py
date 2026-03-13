with open('20260205_raw.bin', 'rb') as f:
    raw = f.read(64)

print(raw.hex(' '))
print(len(raw))
#
#adsadwasd

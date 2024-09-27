## m3u8_cutter

Cut video from m3u8 link by time interval

Convert video from `m3u8` to `mp4`

### Example

#### Convert no needed
```bash
python main.py -u https://exemple.com/file.m3u8 -s 00:00:01 -e 00:00:05 -o ouput.m3u8
```

#### Convert needed

`ffpmeg` is required

```bash
python main.py -u https://exemple.com/file.m3u8 -s 00:00:01 -e 00:00:05 -o ouput.m3u8 -c True
```

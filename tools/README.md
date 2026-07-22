# Protocol tools

- Purpose: optional protocol inspection and reference implementations.
- Browser dependency: none.
- Configuration writes: unavailable in both native probes.

## Python reference codec

- File: `w910_protocol.py`.
- Dependencies: none.
- Coverage: frames, actions, macros, lighting, and vendor-profile conversion.
- Tests: `tests/test_w910_protocol.py`.

## macOS and Linux probe

- File: `w910_probe.c`.
- Mode: read-only.
- Functions: list HID collections, dump known records, and dump macro slots.
- Dependency: hidapi.

```sh
cc -std=c11 -Wall -Wextra -O2 tools/w910_probe.c \
  $(pkg-config --cflags --libs hidapi) -o w910_probe

./w910_probe list
./w910_probe dump
./w910_probe dump-macro 0
```

- Alternative pkg-config name: `hidapi-hidraw`.
- Linux permissions: use an appropriate udev rule.
- Root execution: not recommended as a permission workaround.

## Windows probe

- File: `w910_winprobe.c`.
- Mode: read-only.
- APIs: Windows SetupAPI and HID.
- Build environment: Visual Studio Developer Command Prompt.

```bat
cl /W4 /O2 tools\w910_winprobe.c setupapi.lib hid.lib
w910_winprobe.exe dump
w910_winprobe.exe dump-macro 0
```

- Read transaction: send the feature-report read request, then receive the response.
- Configuration-write commands: not exposed.

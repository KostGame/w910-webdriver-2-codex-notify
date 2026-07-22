import assert from "node:assert/strict";
import test from "node:test";

import {
  ALL_CONTROLS,
  BLE_CHARACTERISTIC_UUID,
  BLE_MANUFACTURER_ID,
  BLE_MANUFACTURER_PREFIX,
  BLE_SERVICE_UUID,
  decodeAction,
  decodeLightingRecord,
  decodeMacro,
  defaultProfile,
  DEVICE_FILTERS,
  encodeLightingRecord,
  encodeMacro,
  frameReport,
  getControlRecord,
  LED_MODES,
  MAIN_CONTROLS,
  macroAction,
  normalizeProtocolReport,
  profilesEqual,
  readFirmwareInfo,
  validateProfile,
  WebBluetoothTransport,
  writeControlSetting,
  writeLightingSelection,
  writeLightingSetting,
  writePowerSetting,
  writeProfile,
} from "../web/protocol.js";

test("WebHID filters include wired and 2.4 GHz devices", () => {
  assert.ok(DEVICE_FILTERS.some(({ vendorId, productId }) => vendorId === 0xb6a4 && productId === 0x4100));
  assert.ok(DEVICE_FILTERS.some(({ vendorId, productId }) => vendorId === 0xb6a4 && productId === 0x4101));
});

test("all 20 physical inputs include the underside RGB light switch", () => {
  assert.equal(ALL_CONTROLS.length, 20);
  assert.equal(ALL_CONTROLS.find(({ id }) => id === "rgb_light_switch")?.label, "RGB light switch");
});

function fakeBluetoothDevice(responseData = [0x00, 0x63, 0x00], { notify = true } = {}) {
  const writes = [];
  const characteristic = new EventTarget();
  characteristic.properties = { read: true, notify: true, writeWithoutResponse: true };
  characteristic.startNotifications = async () => characteristic;
  let currentValue = new DataView(new ArrayBuffer(0));
  characteristic.readValue = async () => currentValue;
  characteristic.writeValueWithoutResponse = async (value) => {
    const request = Uint8Array.from(value);
    writes.push(request);
    if ((request[3] & 0x80) === 0) return;
    const response = request.slice(0, 9 + responseData.length);
    response[8] = responseData.length;
    response.set(responseData, 9);
    currentValue = new DataView(response.buffer, response.byteOffset, response.byteLength);
    if (!notify) return;
    queueMicrotask(() => {
      Object.defineProperty(characteristic, "value", {
        configurable: true,
        value: currentValue,
      });
      characteristic.dispatchEvent(new Event("characteristicvaluechanged"));
    });
  };
  const service = {
    async getCharacteristic(uuid) {
      assert.equal(uuid, BLE_CHARACTERISTIC_UUID);
      return characteristic;
    },
  };
  const server = {
    connected: false,
    async getPrimaryService(uuid) {
      assert.equal(uuid, BLE_SERVICE_UUID);
      return service;
    },
  };
  const device = new EventTarget();
  device.name = "SXS-W910BT";
  device.gatt = {
    connected: false,
    async connect() {
      this.connected = true;
      server.connected = true;
      return server;
    },
    disconnect() {
      this.connected = false;
      server.connected = false;
      device.dispatchEvent(new Event("gattserverdisconnected"));
    },
  };
  return { device, characteristic, writes };
}

test("Web Bluetooth uses FFF0/FFF1 and exchanges complete W910 frames", async () => {
  const { device, writes } = fakeBluetoothDevice([0x00, 0x63, 0x00]);
  const transport = new WebBluetoothTransport(device);
  const status = await transport.query(0x81, 0, 0, 3);
  assert.deepEqual(status, Uint8Array.from([0x00, 0x63, 0x00]));
  assert.equal(writes.length, 1);
  assert.equal(writes[0].length, 41);
  assert.deepEqual(Array.from(writes[0].slice(0, 9)), [0x06, 0x00, 0x01, 0x81, 0x01, 0x00, 0x00, 0x00, 0x03]);
  await transport.close();
});

test("Web Bluetooth disconnect rejects pending reads and reports device loss", async () => {
  const { device, characteristic } = fakeBluetoothDevice();
  characteristic.writeValueWithoutResponse = async () => {};
  const transport = new WebBluetoothTransport(device);
  let disconnected = false;
  transport.onDisconnect = () => { disconnected = true; };
  const pending = transport.query(0x82, 3, 0, 2);
  await new Promise((resolve) => setTimeout(resolve, 0));
  device.gatt.disconnect();
  await assert.rejects(pending, /connection closed/);
  assert.equal(disconnected, true);
});

test("Web Bluetooth reads FFF1 directly when Chrome drops the notification", async () => {
  const { device } = fakeBluetoothDevice([0x2c, 0x01], { notify: false });
  const transport = new WebBluetoothTransport(device);
  assert.deepEqual(await transport.query(0x82, 3, 0, 2), Uint8Array.from([0x2c, 0x01]));
  await transport.close();
});

test("Web Bluetooth authorizes by manufacturer data and reuses the device in the same page", async (context) => {
  const originalNavigator = Object.getOwnPropertyDescriptor(globalThis, "navigator");
  context.after(() => {
    if (originalNavigator) Object.defineProperty(globalThis, "navigator", originalNavigator);
    else delete globalThis.navigator;
  });
  const { device } = fakeBluetoothDevice();
  let requestedOptions = null;
  let requestCount = 0;
  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    value: {
      bluetooth: {
        async requestDevice(options) {
          requestCount += 1;
          requestedOptions = options;
          return device;
        },
      },
    },
  });
  const transport = await WebBluetoothTransport.request();
  assert.deepEqual(requestedOptions, {
    filters: [{ manufacturerData: [{ companyIdentifier: BLE_MANUFACTURER_ID, dataPrefix: BLE_MANUFACTURER_PREFIX }] }],
    optionalServices: [BLE_SERVICE_UUID],
  });
  await transport.close();
  const reconnected = await WebBluetoothTransport.request();
  assert.equal(requestCount, 1);
  assert.equal(reconnected.device, device);
  await reconnected.close();
});

function verifiedMemoryTransport() {
  const memory = new Map();
  const writes = [];
  const bank = (command, selector) => {
    const key = `${command}:${selector}`;
    if (!memory.has(key)) memory.set(key, new Uint8Array(1024));
    return memory.get(key);
  };
  return {
    writes,
    async write(command, selector, address, data) {
      writes.push({ command, selector, address, data: Array.from(data) });
      bank(command, selector).set(data, address);
    },
    async query(command, selector, address, length) {
      return bank(command & 0x7f, selector).slice(address, address + length);
    },
  };
}

test("frame matches the captured B-to-A write", () => {
  const report = frameReport(0x04, 0, 0, 0x20, [0x02, 0x04, 0x00, 0x00]);
  assert.equal(Buffer.from(report.slice(0, 13)).toString("hex"), "06000104000020000402040000");
});

test("default profile contains the physical W910 mappings", () => {
  const profile = defaultProfile(0);
  assert.equal(profile.banks.normal.main.length, 160);
  assert.deepEqual(getControlRecord(profile, "normal", { bank: "main", ...MAIN_CONTROLS.find((control) => control.id === "key_b") }), [0x02, 0x05, 0x00, 0x00]);
  assert.deepEqual(profile.banks.normal.scroll[0], [0x04, 0xe9, 0x00, 0x00]);
  assert.deepEqual(profile.banks.fn.scroll[0], [0x04, 0xea, 0x00, 0x00]);
  assert.deepEqual(profile.lighting.records[1].enabled, [false, false, false, false, true, false, false]);
  assert.deepEqual(profile.lighting.records[4].enabled, [false, false, false, false, true, false, false]);
  assert.equal(validateProfile(profile), profile);
});

test("known and raw actions decode without loss", () => {
  assert.equal(decodeAction(Uint8Array.from([0x04, 0xe9, 0, 0])).label, "Volume up");
  assert.deepEqual(decodeAction(macroAction(7, 2)), { kind: "macro", mode: 2, slot: 7, label: "Macro 8" });
  assert.equal(decodeAction(Uint8Array.from([0x0a, 0xff, 0, 0])).kind, "raw");
  assert.equal(decodeAction(Uint8Array.from([0xaa, 0xbb, 0xcc, 0xdd])).kind, "raw");
});

test("macro golden values and mixed-event round trip", () => {
  assert.equal(Buffer.from(encodeMacro([{ type: "keyboard", usage: 0x29, pressed: true, delay: 20 }], 1)).toString("hex"), "010002002914");
  const events = [
    { type: "keyboard", usage: 0x04, pressed: true, delay: 10 },
    { type: "keyboard", usage: 0x04, pressed: false, delay: 180 },
    { type: "mouse_button", button: "left", pressed: true, delay: 4 },
    { type: "wheel", value: 0xff, delay: 30 },
    { type: "move", x: -120, y: 42, delay: 300 },
  ];
  assert.deepEqual(decodeMacro(encodeMacro(events, 3)), { repeat: 3, events });
});

test("lighting uses the verified G,R,B byte order", () => {
  const record = {
    speed: 4,
    direction: 1,
    brightness: 6,
    enabled: Array(7).fill(true),
    colors: ["#FFFF00", "#0000FF", "#FFA500", "#00FF00", "#FF0000", "#00FFFF", "#800080"],
  };
  const bytes = encodeLightingRecord(record);
  assert.equal(Buffer.from(bytes).toString("hex"), "0401007fffff000000ffa5ff00ff000000ff00ff00ff008080");
  assert.deepEqual(decodeLightingRecord(bytes), record);
});

test("single-color lighting preserves the captured one-hot palette selection", () => {
  const record = {
    speed: 5,
    direction: 0,
    brightness: 6,
    enabled: [false, false, false, false, true, false, false],
    colors: ["#FFFF00", "#0000FF", "#FFA500", "#00FF00", "#123456", "#00FFFF", "#800080"],
  };
  const bytes = encodeLightingRecord(record);
  assert.equal(bytes[3], 0x10);
  assert.deepEqual(Array.from(bytes.slice(16, 19)), [0x34, 0x12, 0x56]);
});

test("lighting mode controls match the captured vendor UI", () => {
  const controls = Object.fromEntries(LED_MODES.map(({ code, controls, palette }) => [code, { controls, palette }]));
  assert.deepEqual(controls, {
    0x81: { controls: ["brightness", "color"], palette: "single" },
    0x82: { controls: ["brightness", "speed", "direction", "color"], palette: "multi" },
    0x83: { controls: ["brightness", "speed", "direction"], palette: null },
    0x84: { controls: ["brightness", "speed", "color"], palette: "single" },
    0x85: { controls: ["brightness", "speed", "color"], palette: "multi" },
    0x86: { controls: ["brightness", "speed", "color"], palette: "multi" },
    0x87: { controls: ["brightness", "speed"], palette: null },
    0x88: { controls: ["brightness", "speed", "direction"], palette: null },
    0x89: { controls: [], palette: null },
  });
});

test("firmware information uses the statically identified read selectors", async () => {
  const queries = [];
  const transport = {
    async query(command, selector, address, length) {
      queries.push([command, selector, address, length]);
      if (command === 0xf0 && selector === 1) return Uint8Array.from(Buffer.from("2.3.0001"));
      if (command === 0xf0 && selector === 2) return Uint8Array.from([...Buffer.from("K2008-250612"), 0, 0, 0]);
      return new Uint8Array(8);
    },
  };
  assert.deepEqual(await readFirmwareInfo(transport), {
    firmwareVersion: "2.3.0001",
    firmwareCustomId: "K2008-250612",
    dongleFirmwareVersion: null,
  });
  assert.deepEqual(queries, [[0xf0, 1, 0, 8], [0xf0, 2, 0, 16], [0xf1, 1, 0, 8]]);
});

test("profile comparison ignores status and raw macro cache", () => {
  const left = defaultProfile(1);
  const right = structuredClone(left);
  right.status.battery = 22;
  assert.equal(profilesEqual(left, right), true);
});

test("profile validation rejects malformed imported macro data", () => {
  const profile = defaultProfile(0);
  profile.macros[0] = {
    repeat: 1,
    events: [{ type: "move", x: '0\" autofocus onfocus=alert(1)', y: 0, delay: 20 }],
  };
  assert.throws(() => validateProfile(profile), /Mouse movement/);
});

test("profile validation rejects a missing referenced macro", () => {
  const profile = defaultProfile(0);
  profile.banks.normal.main[0] = Array.from(macroAction(3, 0));
  assert.throws(() => validateProfile(profile), /missing macro slot 3/);
});

test("WebHID feature report representations normalize without data loss", () => {
  const frame = frameReport(0x81, 7, 0, 0, new Uint8Array(3));
  assert.deepEqual(normalizeProtocolReport(frame), frame);
  assert.deepEqual(normalizeProtocolReport(frame.slice(1)), frame);
  assert.throws(() => normalizeProtocolReport(frame.slice(2)), /Invalid W910 report length/);
});

test("complete profile write never touches vendor generation tokens", async () => {
  const writes = [];
  const transport = {
    async write(command, selector, address, data) {
      writes.push({ command, selector, address, data: Array.from(data) });
    },
  };
  await writeProfile(transport, defaultProfile(0));
  assert.ok(writes.some(({ command, selector }) => command === 0x02 && selector === 2));
  assert.ok(writes.some(({ command }) => command === 0x04));
  assert.ok(writes.some(({ command }) => command === 0x05));
  assert.ok(writes.some(({ command }) => command === 0x09));
  assert.equal(writes.some(({ command, selector }) => command === 0x02 && selector === 1), false);
});

test("single-control write updates and verifies only the addressed action", async () => {
  const transport = verifiedMemoryTransport();
  const profile = defaultProfile(0);
  const control = { bank: "main", ...MAIN_CONTROLS.find(({ id }) => id === "key_b") };
  profile.banks.normal.main[control.index] = [0x02, 0x04, 0x00, 0x00];
  await writeControlSetting(transport, profile, "normal", control);
  assert.deepEqual(transport.writes.map(({ command }) => command), [0x02, 0x04]);
  assert.deepEqual(transport.writes.at(-1), { command: 0x04, selector: 0, address: control.index * 4, data: [0x02, 0x04, 0x00, 0x00] });
});

test("macro assignment writes its stream before the one addressed action", async () => {
  const transport = verifiedMemoryTransport();
  const profile = defaultProfile(1);
  const control = { bank: "main", ...MAIN_CONTROLS.find(({ id }) => id === "key_c") };
  profile.macros[7] = { repeat: 1, events: [{ type: "keyboard", usage: 0x04, pressed: true, delay: 20 }] };
  profile.banks.fn.main[control.index] = Array.from(macroAction(7, 0));
  await writeControlSetting(transport, profile, "fn", control);
  assert.deepEqual(transport.writes.map(({ command }) => command), [0x02, 0x08, 0x04]);
  assert.equal(transport.writes.at(-1).selector, 1);
});

test("lighting and power partial writes address only their own records", async () => {
  const transport = verifiedMemoryTransport();
  const profile = defaultProfile(0);
  await writeLightingSelection(transport, profile);
  await writeLightingSetting(transport, profile, 8);
  await writePowerSetting(transport, profile, "sleepSeconds");
  assert.deepEqual(transport.writes.map(({ command, selector, address }) => [command, selector, address]), [
    [0x02, 2, 0], [0x09, 0, 0], [0x09, 0, 200],
    [0x02, 2, 0], [0x09, 0, 0], [0x09, 0, 200],
    [0x02, 2, 0], [0x02, 3, 0],
  ]);
});

test("lighting effect selection writes the selected mode immediately and verifies readback", async () => {
  const transport = verifiedMemoryTransport();
  const profile = defaultProfile(1);
  profile.lighting.mode = 0x83;
  await writeLightingSelection(transport, profile);
  assert.deepEqual(transport.writes.map(({ command, selector, address }) => [command, selector, address]), [
    [0x02, 2, 0], [0x09, 0, 0], [0x09, 0, 75],
  ]);
  assert.equal(transport.writes.at(-2).data[0], 0x83);
});

import assert from "node:assert/strict";
import test from "node:test";

import { appendTimedMacroEvent } from "../web/macro-recording.js";

test("recorded macro timing is stored on the preceding event", () => {
  const events = [];
  let timestamp = null;
  timestamp = appendTimedMacroEvent(events, { type: "keyboard", usage: 0x04, pressed: true }, 1000, timestamp);
  timestamp = appendTimedMacroEvent(events, { type: "keyboard", usage: 0x04, pressed: false }, 1087, timestamp);
  assert.equal(timestamp, 1087);
  assert.deepEqual(events, [
    { type: "keyboard", usage: 0x04, pressed: true, delay: 87 },
    { type: "keyboard", usage: 0x04, pressed: false, delay: 0 },
  ]);
});

test("recording rolls back an event that exceeds device macro storage", () => {
  const events = Array.from({ length: 254 }, (_, index) => ({
    type: "keyboard",
    usage: 0x04,
    pressed: index % 2 === 0,
    delay: 1,
  }));
  const previousDelay = events.at(-1).delay;
  assert.throws(
    () => appendTimedMacroEvent(events, { type: "keyboard", usage: 0x04, pressed: true }, 10, 0),
    /512-byte/,
  );
  assert.equal(events.length, 254);
  assert.equal(events.at(-1).delay, previousDelay);
});

import { encodeMacro } from "./protocol.js";

export function appendTimedMacroEvent(events, event, timestamp, previousTimestamp, repeat = 1) {
  const previous = events.at(-1);
  const originalDelay = previous?.delay;
  if (previous && previousTimestamp !== null) {
    previous.delay = Math.max(0, Math.min(0xffffff, Math.round(timestamp - previousTimestamp)));
  }
  events.push({ ...event, delay: 0 });
  try {
    encodeMacro(events, repeat);
  } catch (error) {
    events.pop();
    if (previous) previous.delay = originalDelay;
    throw error;
  }
  return timestamp;
}

/**
 * Dev-only logger.
 *
 * Wraps the native `console` so that debugging statements never leak into
 * production bundles. Use `logger.error(...)` / `logger.warn(...)` /
 * `logger.info(...)` in place of `console.*`.
 *
 * In production (`process.env.NODE_ENV === 'production'`) only `error`
 * is forwarded so that actual runtime failures can still be surfaced
 * via reporting tools, but info/warn traces stay silent.
 */

type LogFn = (...args: unknown[]) => void;

const IS_PROD = process.env.NODE_ENV === "production";

const noop: LogFn = () => {};

export interface Logger {
  info: LogFn;
  warn: LogFn;
  error: LogFn;
  debug: LogFn;
}

export const logger: Logger = {
  info: IS_PROD ? noop : (...args) => console.info(...args),
  warn: IS_PROD ? noop : (...args) => console.warn(...args),
  // eslint-disable-next-line no-console
  error: (...args) => console.error(...args),
  debug: IS_PROD ? noop : (...args) => console.debug(...args),
};

export default logger;

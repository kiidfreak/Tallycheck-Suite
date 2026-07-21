import { Observable, map } from 'rxjs';

/**
 * Envelope helpers.
 *
 * The backend wraps every success as `{ message, data }`, with `meta` added on
 * paginated collections (libs/py_success/success.py).
 *
 * These are RxJS operators applied at the call site rather than an HTTP
 * interceptor. An interceptor that reshapes response bodies is invisible to the
 * type system: the declared return type says one thing, the runtime body is
 * another, and callers cannot tell whether a body has already been unwrapped.
 * That ambiguity is exactly why three services ended up unwrapping twice.
 */

export interface Meta {
  page?: number;
  per_page?: number;
  total?: number;
  pages?: number;
}

export interface Envelope<T> {
  message: string;
  data: T;
  meta?: Meta;
}

export interface Paged<T> {
  items: T;
  meta: Meta;
}

/** `{message, data}` -> `data`. */
export function unwrap<T>() {
  return (source: Observable<Envelope<T>>): Observable<T> =>
    source.pipe(map((response) => response.data));
}

/**
 * `{message, data, meta}` -> `{items, meta}`.
 *
 * Keeps pagination attached instead of dropping it, which is what forced
 * callers to re-read the raw body.
 */
export function unwrapPaged<T>() {
  return (source: Observable<Envelope<T>>): Observable<Paged<T>> =>
    source.pipe(map((response) => ({ items: response.data, meta: response.meta ?? {} })));
}

/**
 * Narrowing guard, for the transition only.
 *
 * While `authInterceptor` still unwraps some responses, a body may arrive either
 * enveloped or bare depending on the path. Delete this once the interceptor no
 * longer reshapes anything and every caller uses the generated client.
 */
export function isEnvelope<T>(body: unknown): body is Envelope<T> {
  return (
    typeof body === 'object' &&
    body !== null &&
    'data' in body &&
    'message' in body
  );
}

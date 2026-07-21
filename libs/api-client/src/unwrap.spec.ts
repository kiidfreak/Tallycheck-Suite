import { firstValueFrom, of, throwError } from 'rxjs';
import { Envelope, isEnvelope, unwrap, unwrapPaged } from './unwrap';

describe('unwrap', () => {
  it('returns the payload', async () => {
    const source = of<Envelope<{ id: number }>>({ message: 'Success', data: { id: 7 } });
    await expect(firstValueFrom(source.pipe(unwrap()))).resolves.toEqual({ id: 7 });
  });

  it('preserves an array payload', async () => {
    const source = of<Envelope<number[]>>({ message: 'Success', data: [1, 2, 3] });
    await expect(firstValueFrom(source.pipe(unwrap()))).resolves.toEqual([1, 2, 3]);
  });

  it('preserves a null payload rather than coercing it', async () => {
    // Delete handlers legitimately return null data. Coercing it to {} or []
    // would hide the difference between "no result" and "empty result".
    const source = of<Envelope<null>>({ message: 'Deleted', data: null });
    await expect(firstValueFrom(source.pipe(unwrap()))).resolves.toBeNull();
  });

  it('does not swallow errors', async () => {
    const source = throwError(() => new Error('boom'));
    await expect(firstValueFrom(source.pipe(unwrap()))).rejects.toThrow('boom');
  });
});

describe('unwrapPaged', () => {
  it('keeps meta alongside the items', async () => {
    const source = of<Envelope<string[]>>({
      message: 'Success',
      data: ['a', 'b'],
      meta: { page: 2, per_page: 25, total: 51, pages: 3 },
    });
    await expect(firstValueFrom(source.pipe(unwrapPaged()))).resolves.toEqual({
      items: ['a', 'b'],
      meta: { page: 2, per_page: 25, total: 51, pages: 3 },
    });
  });

  it('defaults meta to an empty object when the server omits it', async () => {
    // The backend omits `meta` entirely when it is None, so callers must not
    // have to null-check it.
    const source = of<Envelope<string[]>>({ message: 'Success', data: [] });
    await expect(firstValueFrom(source.pipe(unwrapPaged()))).resolves.toEqual({
      items: [],
      meta: {},
    });
  });
});

describe('isEnvelope', () => {
  it('accepts a real envelope', () => {
    expect(isEnvelope({ message: 'Success', data: 1 })).toBe(true);
  });

  it.each([
    ['a bare array', [1, 2]],
    ['a bare object', { id: 1 }],
    ['data without message', { data: 1 }],
    ['null', null],
    ['a string', 'nope'],
  ])('rejects %s', (_label, value) => {
    expect(isEnvelope(value)).toBe(false);
  });

  it('accepts an envelope whose data is null', () => {
    // `{message, data: null}` is a valid delete response and must not be
    // mistaken for an already-unwrapped body.
    expect(isEnvelope({ message: 'Deleted', data: null })).toBe(true);
  });
});

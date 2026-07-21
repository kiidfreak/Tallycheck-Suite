/**
 * Copy a source tree to an output directory, skipping anything the build
 * generates itself.
 *
 * The website is deliberately static — no framework, so no bundler to do this.
 * `styles/` is excluded because sass writes the compiled CSS there; copying the
 * .scss sources over the top would ship them publicly and, depending on order,
 * clobber the output.
 */
import { cp, mkdir, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';

const [, , src, dest] = process.argv;

if (!src || !dest) {
  console.error('usage: copy-static.mjs <src> <dest>');
  process.exit(1);
}

if (!existsSync(src)) {
  console.error(`copy-static: source not found: ${src}`);
  process.exit(1);
}

// Clean first so a renamed or deleted page cannot linger in the output.
await rm(dest, { recursive: true, force: true });
await mkdir(dest, { recursive: true });

await cp(src, dest, {
  recursive: true,
  filter: (entry) => {
    const rel = path.relative(src, entry);
    if (!rel) return true;
    const [top] = rel.split(path.sep);
    return top !== 'styles';
  },
});

console.log(`copy-static: ${src} -> ${dest}`);

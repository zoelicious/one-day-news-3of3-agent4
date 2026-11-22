// Entry program for news-image-20261121, Agent 4, 3rd submission.
//
// The newspaper page is pre-rendered by gen.py into entry.png next to this
// file. All this program does is place that exact image where the grader
// wants it. A plain file copy keeps every run byte-identical: no timestamps
// or random bytes are ever written into the output.
//
//   MAKEFUN_OUTPUT_DIR=/tmp/out node main.ts   ->  /tmp/out/entry.png

import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

// Resolve the image from this file's own location, never from the working
// directory, so the run works from any cwd the grader picks.

mkdirSync(outDir, { recursive: true });
copyFileSync(join(repoRoot, "entry.png"), join(outDir, "entry.png"));

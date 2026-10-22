import assert from 'node:assert/strict';
import test from 'node:test';

import {exerciseOptions} from '../trainer/static/exercise-options.js';

test('exercise controls stay consistent across every mode', () => {
  assert.deepEqual(exerciseOptions('new', false),
    {generate: false, generateDisabled: false, difficultyDisabled: true});
  assert.deepEqual(exerciseOptions('new', true),
    {generate: true, generateDisabled: false, difficultyDisabled: false});
  assert.deepEqual(exerciseOptions('targeted', false),
    {generate: true, generateDisabled: true, difficultyDisabled: false});
  for (const mode of ['review', 'cram']) assert.deepEqual(exerciseOptions(mode, true),
    {generate: false, generateDisabled: true, difficultyDisabled: true});
});

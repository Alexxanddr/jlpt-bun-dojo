export function exerciseOptions(mode, newGeneration) {
  if (mode === 'targeted') return {generate: true, generateDisabled: true, difficultyDisabled: false};
  if (mode === 'review' || mode === 'cram') return {generate: false, generateDisabled: true, difficultyDisabled: true};
  return {generate: newGeneration, generateDisabled: false, difficultyDisabled: !newGeneration};
}

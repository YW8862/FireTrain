import { describe, expect, it } from 'vitest';

import { getLevelTagType, getScoreTagType } from '../src/utils/common';

describe('common utils', () => {
  it('maps score ranges to tag types', () => {
    expect(getScoreTagType(95)).toBe('success');
    expect(getScoreTagType(80)).toBe('success');
    expect(getScoreTagType(60)).toBe('warning');
    expect(getScoreTagType(59)).toBe('danger');
  });

  it('maps performance levels to tag types', () => {
    expect(getLevelTagType('excellent')).toBe('success');
    expect(getLevelTagType('good')).toBe('success');
    expect(getLevelTagType('pass')).toBe('warning');
    expect(getLevelTagType('fail')).toBe('danger');
    expect(getLevelTagType('unknown')).toBe('info');
  });
});

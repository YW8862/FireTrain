import { afterEach, describe, expect, it } from 'vitest';

import { resolveUploadBaseUrl } from '../src/api/upload';

const originalUploadBaseUrl = import.meta.env.VITE_UPLOAD_BASE_URL;
const originalApiBaseUrl = import.meta.env.VITE_API_BASE_URL;

describe('upload api config', () => {
  afterEach(() => {
    import.meta.env.VITE_UPLOAD_BASE_URL = originalUploadBaseUrl;
    import.meta.env.VITE_API_BASE_URL = originalApiBaseUrl;
  });

  it('prefers dedicated upload base url when provided', () => {
    import.meta.env.VITE_UPLOAD_BASE_URL = 'https://uploads.example.com/api/';
    import.meta.env.VITE_API_BASE_URL = '/api';

    expect(resolveUploadBaseUrl()).toBe('https://uploads.example.com/api');
  });

  it('falls back to standard api base url by default', () => {
    import.meta.env.VITE_UPLOAD_BASE_URL = '';
    import.meta.env.VITE_API_BASE_URL = '/api';

    expect(resolveUploadBaseUrl()).toBe('/api');
  });
});

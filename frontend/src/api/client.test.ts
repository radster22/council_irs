import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './client';

describe('attachment requests', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('uses the shared authenticated request path and returns the file blob', async () => {
    const file = new Blob(['report attachment']);
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/pdf' }),
      blob: vi.fn().mockResolvedValue(file),
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await api.downloadAttachment('submission/1', 'attachment 2', 'access-token');

    expect(result).toBeInstanceOf(Blob);
    expect(await result.text()).toBe('report attachment');
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/submissions/submission%2F1/attachments/attachment%202',
      expect.objectContaining({
        method: 'GET',
        headers: { Authorization: 'Bearer access-token' },
      }),
    );
  });

  it('uses the shared API error handling for failed downloads', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('Attachment unavailable.', { status: 404 })));

    await expect(api.downloadAttachment('submission-1', 'attachment-1', 'access-token'))
      .rejects.toThrow('Attachment unavailable.');
  });
});

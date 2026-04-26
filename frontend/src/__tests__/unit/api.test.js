import API, { getNews, openChat, getPolicies } from '../api';
import MockAdapter from 'axios-mock-adapter';

const mock = new MockAdapter(API);

describe('API functions', () => {
  afterEach(() => {
    mock.reset();
  });

  it('getNews fetches news correctly', async () => {
    const mockData = { news: [{ id: 1, title: 'Test' }] };
    mock.onGet('/api/news').reply(200, mockData);

    const response = await getNews();
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
  });

  it('getPolicies fetches policies correctly', async () => {
    const mockData = { policies: [{ id: 'ins-001' }] };
    mock.onGet('/api/policies').reply(200, mockData);

    const response = await getPolicies();
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
  });

  it('openChat sends chat correctly', async () => {
    const mockData = { response: 'AI reply' };
    mock.onPost('/api/chat/open').reply(200, mockData);

    const response = await openChat('session-1', 'Hello');
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
  });
});

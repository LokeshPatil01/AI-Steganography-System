import api from './api';

export const keyService = {
  async getMyPublicKey() {
    const response = await api.get('/keys/public-key');
    return response.data;
  },

  async getRecipientPublicKey(recipientUserId) {
    const response = await api.get(`/keys/user/${recipientUserId}/public-key`);
    return response.data;
  },

  async regenerateKeys() {
    const response = await api.post('/keys/regenerate');
    return response.data;
  },

  async getMyPrivateKey() {
    const response = await api.get('/keys/private-key');
    return response.data;
  },
};

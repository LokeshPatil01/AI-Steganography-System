import api from './api';

export const operationService = {
  async getOperationHistory(limit = 50) {
    const response = await api.get(`/operations/history?limit=${limit}`);
    return response.data;
  },

  async recordOperation(auditData) {
    const response = await api.post('/operations/audit', auditData);
    return response.data;
  },

  async getOperationById(id) {
    const response = await api.get(`/operations/${id}`);
    return response.data;
  },
};

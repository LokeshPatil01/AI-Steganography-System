using StegoApi.Models.Entities;

namespace StegoApi.Services.Interfaces;

public interface ITokenService
{
    (string Token, DateTime ExpiresAt) GenerateToken(User user);
}

using StegoApi.Models.DTOs;

namespace StegoApi.Services.Interfaces;

public interface IAuthService
{
    Task<(bool Success, string? ErrorMessage, AuthResponseDto? Response)> RegisterAsync(RegisterRequestDto request);
    Task<(bool Success, string? ErrorMessage, AuthResponseDto? Response)> LoginAsync(LoginRequestDto request);
    Task<UserProfileDto?> GetUserProfileAsync(Guid userId);
}
